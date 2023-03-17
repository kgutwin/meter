import subprocess
from datetime import datetime, timedelta
from meter.sources.base import BaseSource


COMMAND = [
    'icalBuddy',
    '--includeOnlyEventsFromNowOn',
    '--limitItems', '1',
    '--includeCals', '@@CALENDAR@@',
    '--includeEventProps', 'datetime',
    '--timeFormat', '%Y-%m-%dT%H:%M:%S',
    '--bullet', '',
    'eventsToday'
]


class Meetings(BaseSource):
    """Meeting countdown timer

    Requires icalBuddy to be installed (https://hasseg.org/icalBuddy/).

    """
    OPTIONS = [
        (['--calendar'], {"required": True, 'help': 'Calendar name'}),
    ]

    def init(self):
        self.last_update = datetime.min
    
    def update(self, reported):
        if datetime.now() > self.last_update + timedelta(minutes=1):
            cmd = [
                self.opts.calendar if c == '@@CALENDAR@@' else c
                for c in COMMAND
            ]
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8')
            self.last_update = datetime.now()
            if result.stdout.strip():
                start, end = result.stdout.strip().split(' - ')
                self.start = datetime.fromisoformat(start)
                self.end = datetime.fromisoformat(end)
            else:
                self.start = self.end = None

        if self.start is None and self.end is None:
            return {'meter': 0, 'green': 0, 'red': 0}
                
        duration = (self.end - self.start).total_seconds()
        position = (datetime.now() - self.start).total_seconds()
        if position < 0:
            value = 0
        elif position > duration:
            value = 0.001
        else:
            value = ((duration - position) / duration) * 100
            
        self.log(f'{self.start} {self.end} {value}')
        return {
            'meter': value,
            'green': 50 if value and position < 90 else 0,
            'red': 50 if value < 2 and value > 0 else 0,
        }
