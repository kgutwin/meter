import boto3

from meter.sources.base import BaseSource

sfn = boto3.client('stepfunctions')


class SfnMapRun(BaseSource):
    """Step Functions Map Run status
    """
    OPTIONS = [
        (['arn'], {"config_save": False}),
        (['--known-failures'], {"config_save": False, 'type': int}),
    ]

    def update(self, reported):
        response = sfn.describe_map_run(
            mapRunArn=self.opts.arn
        )
        num_done = (
            response['itemCounts']['succeeded'] +
            response['itemCounts']['failed'] +
            response['itemCounts']['timedOut']
        )
        num_total = response['itemCounts']['total']
        meter = (num_done / num_total) * 100.0
        num_failed = (
            response['itemCounts']['failed'] +
            response['itemCounts']['timedOut']
        )
        self.log(f'{num_done} of {num_total} ({meter:.1f}%), '
                 f'{num_failed} failed, '
                 f'{response["status"]}')
        
        # apply known failures
        if self.opts.known_failures:
            num_failed = max(0, num_failed - self.opts.known_failures)
        
        return {
            'meter': (num_done / num_total) * 100.0,
            'red': 50 if response['status'] == 'FAILED' else num_failed,
            'green': 50 if response['status'] == 'SUCCEEDED' else 0,
            'blue': 25 if response['status'] == 'ABORTED' else 0,
        }
