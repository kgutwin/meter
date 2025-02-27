import json
import time
import boto3
import logging
from datetime import datetime, timedelta

from meter.utils import c_to_f

logger = logging.getLogger(__name__)


ROLE_ARN_TEMPLATE = 'arn:aws:iam::{account_id}:role/meter-update'

def is_account_id(v):
    if len(v) != 12:
        return False
    if any(True for i in v if i not in '0123456789'):
        return False
    return True


def create_assume_role(from_acct_id):
    role = 'meter-update'
    sts = boto3.client('sts')
    my_account_id = sts.get_caller_identity()['Account']
    iam = boto3.client('iam')
    try:
        response = iam.get_role(RoleName=role)
        assume_role_policy = json.loads(
            response['Role']['AssumeRolePolicyDocument']
        )
        principals = set(assume_role_policy['Statement'][0]['Principal']['AWS'])
        principals.add(f'arn:aws:iam::{from_acct_id}:root')
        assume_role_policy['Statement'][0]['Principal']['AWS'] = list(principals)
        iam.update_assume_role_policy(
            RoleName=role,
            PolicyDocument=json.dumps(assume_role_policy)
        )
        
    except iam.exceptions.NoSuchEntityException:
        logger.info(f'Creating new role {role}')
        response = iam.create_role(
            RoleName=role,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Principal": { "AWS": [
                        f'arn:aws:iam::{my_account_id}:root',
                        f'arn:aws:iam::{from_acct_id}:root'
                    ]}
                }]
            }),
            Description='get and push IoT data plane updates',
            MaxSessionDuration=12*60*60,
        )
        response = iam.put_role_policy(
            RoleName=role,
            PolicyName='iot-data',
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "iot:GetThingShadow",
                        "iot:UpdateThingShadow"
                    ],
                    "Resource": f"arn:aws:iot:*:{my_account_id}:thing/*"
                }]
            })
        )
    

class DelayCycler:
    def __init__(self, min_cycle):
        self.min_cycle = min_cycle
        self.next_cycle = 0.0

    def cycle(self):
        now = time.time()
        delay = self.next_cycle - now
        if delay > 0:
            time.sleep(delay)
        self.next_cycle = time.time() + self.min_cycle
        return True



class Meter:
    def __init__(self, thing, min_cycle=4.0, assume_role=None, show_temp=False):
        self.thing = thing
        self.min_cycle = min_cycle
        self.assume_role = assume_role
        self.show_temp = show_temp
        
        if self.assume_role:
            if is_account_id(self.assume_role):
                self.assume_role_arn = ROLE_ARN_TEMPLATE.format(
                    account_id=self.assume_role
                )
            else:
                assert self.assume_role.startswith('arn:aws:')
                self.assume_role_arn = self.assume_role

            self.credentials = {'Expiration': datetime.now().astimezone()}

        else:
            self.iot = boto3.client('iot-data')

    def refresh_credentials(self):
        if not self.assume_role:
            return

        remaining = self.credentials['Expiration'] - datetime.now().astimezone()
        if remaining < timedelta(seconds=3600):
            sts = boto3.client('sts')
            response = sts.assume_role(
                RoleArn=self.assume_role_arn,
                RoleSessionName='meter',
                DurationSeconds=12*60*60
            )
            self.credentials = response['Credentials']
            self.credentials['Expiration'] = self.credentials['Expiration']\
                .astimezone()
            logger.info(f'Refreshed credentials,'
                        f' expiration {self.credentials["Expiration"]}')
            self.iot = boto3.client(
                'iot-data',
                aws_access_key_id=self.credentials['AccessKeyId'],
                aws_secret_access_key=self.credentials['SecretAccessKey'],
                aws_session_token=self.credentials['SessionToken']
            )
            
    def loop(self, source):
        cycler = DelayCycler(max(self.min_cycle, source.min_cycle))
        while cycler.cycle():
            self.refresh_credentials()
            response = self.iot.get_thing_shadow(thingName=self.thing)
            reported = json.load(response['payload'])['state']['reported']
            logger.debug(f'Reported: {reported}')
            if self.show_temp:
                temp_f = c_to_f(reported['temp'])
                logger.info(f'Meter temperature: {temp_f:.1f} F')
            desired = source.update(reported)
            if desired != reported:
                logger.debug(f'Update: {desired}')
                self.iot.update_thing_shadow(
                    thingName=self.thing,
                    payload=json.dumps({'state': {'desired': desired}}).encode()
                )

    def clear(self):
        self.refresh_credentials()
        self.iot.update_thing_shadow(
            thingName=self.thing,
            payload=json.dumps({'state': {'desired': {
                'meter': 0.0,
                'red': 0.0,
                'green': 0.0,
                'blue': 0.0,
            }}})
        )
