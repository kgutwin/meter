import re
import time
from datetime import datetime, timedelta
import boto3

from meter import config
from meter.sources.base import BaseSource

cw = boto3.client('cloudwatch')
logs = boto3.client('logs')


def find_key(k, d):
    if isinstance(d, list):
        for i in d:
            if isinstance(i, dict):
                yield from find_key(k, i)
    else:
        for i in d:
            if i == k:
                yield d[i]
            elif isinstance(d[i], (dict, list)):
                yield from find_key(k, d[i])
            

class CloudWatchAlarm(BaseSource):
    """CloudWatch Alarm status

    The meter will show the raw value of the alarm. When the alarm is
    in state ALARM, the red light will illuminate.

    """
    OPTIONS = [
        (['name'], {"config_save": False, 'help': 'CloudWatch alarm name'}),
        (['--composite', '-c'], {"action": "store", "type": config.to_bool,
                                 'help': 'alarm type is composite'}),
    ]

    def update(self, reported):
        alarm_type = 'CompositeAlarm' if self.opts.composite else 'MetricAlarm'
        response = cw.describe_alarms(
            AlarmNames=[self.opts.name],
            AlarmTypes=[alarm_type],
        )
        alarm = response[alarm_type + 's'][0]
        metric_data_q = alarm['Metrics']
        period = max(find_key('Period', metric_data_q))

        # align to period by waiting
        have_updated = getattr(self, 'have_updated', False)
        ahead_of_period = datetime.now().timestamp() % period
        if ahead_of_period > self.min_cycle and have_updated:
            time_to_next_period = period - ahead_of_period
            time_to_wait = time_to_next_period + 3.0
            dest = datetime.now() + timedelta(seconds=time_to_wait)
            self.log(f'waiting {int(time_to_wait)} seconds until {dest}')
            time.sleep(time_to_wait)
        
        response = cw.get_metric_data(
            MetricDataQueries=metric_data_q,
            StartTime=datetime.now() - timedelta(seconds=period),
            EndTime=datetime.now()
        )
        values = response['MetricDataResults'][0]['Values']
        value = values[-1]
        self.log(f'{self.opts.name}: {alarm["StateValue"]} {value}')
        self.have_updated = True
        return {
            'meter': value,
            'red': 50 if alarm['StateValue'] == 'ALARM' else 0,
            'green': 0,
            'blue': 0,
        }


class CloudWatchLogs(BaseSource):
    """CloudWatch Logs filter

    Provide a log group and log stream name, plus a regular expression
    to extract the current value from the log stream. The regular
    expression should have at least one matching group which matches a
    numerical value. If the maximum value is provided, the value from
    the log stream will be scaled appropriately. Providing a value for
    the red, green, or blue regexes will, when matched in the log
    stream, cause the respective colored light to illuminate.

    """
    OPTIONS = [
        (['log_group_name'], {'config_save': False}),
        (['log_stream_name'], {'config_save': False}),
        (['regex'], {'config_save': False}),
        (['--max-value', '-m'],
         {'type': int, 'config_save': False,
          'help': ('if provided, the extracted value will be divided by'
                   'this fixed value')}),
        (['--red-regex', '-R'], {}),
        (['--green-regex', '-G'], {}),
        (['--blue-regex', '-B'], {}),
    ]

    def update(self, reported):
        next_token = getattr(self, 'next_token', None)
        kwargs = {
            'logGroupName': self.opts.log_group_name,
            'logStreamName': self.opts.log_stream_name,
            'limit': 10,
        }
        if next_token:
            kwargs['startFromHead'] = True
            kwargs['nextToken'] = next_token
        else:
            kwargs['startFromHead'] = False

        response = logs.get_log_events(**kwargs)
        self.next_token = response['nextForwardToken']

        # search through the logs with the regex
        data = {
            'meter': None,
            'red': 0,
            'green': 0,
            'blue': 0,
        }
        regexps = {
            'meter': re.compile(self.opts.regex)
        }
        if self.opts.red_regex:
            regexps['red'] = re.compile(self.opts.red_regex)
        if self.opts.green_regex:
            regexps['green'] = re.compile(self.opts.green_regex)
        if self.opts.blue_regex:
            regexps['blue'] = re.compile(self.opts.blue_regex)
        for row in response['events']:
            for k in regexps:
                m = regexps[k].search(row['message'])
                if m is not None:
                    if k == 'meter':
                        value = float(m.groups()[0])
                        self.log(f'{value}: {row["message"].strip()}')
                        data[k] = value
                    else:
                        self.log(f'{k}: {row["message"].strip()}')
                        data[k] = 50

        if data['meter'] is not None:
            if self.opts.max_value:
                data['meter'] = (data['meter'] / self.opts.max_value) * 100.0
            
        else:
            data['meter'] = reported['meter']

        return data
