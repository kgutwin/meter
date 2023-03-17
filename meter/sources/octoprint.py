import json
from urllib.request import Request, urlopen

from meter.sources.base import BaseSource


class OctoPrint(BaseSource):
    """OctoPrint current print status
    """
    OPTIONS = [
        (['--hostname'], {"required": True}),
        (['--api-key'], {"required": True}),
        (['--by-time'], {"action": "store_true"}),
    ]

    def init(self):
        self.history = [-1] * 5
    
    def update(self, reported):
        url = f'http://{self.opts.hostname}/api/job'
        req = Request(url, headers={'X-Api-Key': self.opts.api_key})
        job = json.load(urlopen(req))
        if self.opts.by_time:
            print_time = job['progress'].get('printTime')
            print_time_left = job['progress'].get('printTimeLeft')
            if print_time is not None and print_time_left is not None:
                completion = (print_time / (print_time + print_time_left)) * 100.0
            else:
                completion = 0
            self.log(f"{job['state']} {completion:.1f}%")
        else:
            self.log(f"{job['state']} {job['progress']}")
            completion = job.get('progress', {}).get('completion', 0.0) or 0.0
        state = {
            'meter': completion,
            'red': 0,
            'green': 0,
            'blue': 0,
        }
        self.history.append(completion)
        self.history.pop(0)
        if all(i == self.history[0] for i in self.history[1:]):
            # job state is flat, it's probably paused from filament sensor
            state['blue'] = 25
        if job['state'] == 'Operational':
            state['green'] = 25
        elif job['state'] != 'Printing':
            state['red'] = 25
        return state
