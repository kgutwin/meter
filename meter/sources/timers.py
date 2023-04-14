import time
from datetime import datetime

from meter.sources.base import BaseSource


class Pomodoro(BaseSource):
    """Pomodoro timer
    """
    OPTIONS = [
        (['--work-time'], {'type': int, 'default': 25, 'metavar': 'MINUTES',
                           'help': 'work period is MINUTES long'}),
        (['--break-time'], {'type': int, 'default': 5, 'metavar': 'MINUTES',
                            'help': 'break period is MINUTES long'}),
        (['--direction'], {'choices': ['up', 'down'], 'default': 'down',
                           'help': 'if "down", meter moves from 100 to 0'}),
    ]

    def init(self):
        self.phase = 'work'
        self.phase_start = time.time()
    
    def update(self, reported):
        if self.phase == 'work':
            phase_dur = self.opts.work_time * 60
        else:
            phase_dur = self.opts.break_time * 60
            
        phase_end = self.phase_start + phase_dur

        if time.time() > phase_end:
            self.phase_start = phase_end
            self.phase = 'break' if self.phase == 'work' else 'work'

        meter_val = (time.time() - self.phase_start) / phase_dur
        meter_val *= 100.0
        if self.opts.direction == 'down':
            meter_val = 100.0 - meter_val
            
        return {
            'meter': meter_val,
            'green': 50 if self.phase == 'break' else 0
        }


class CountdownTimer(BaseSource):
    """Countdown timer
    """
    OPTIONS = [
        (['end_time'], {'type': str}),
        (['--duration'], {'action': 'store_true', 'config_save': False,
                          'help': 'time is duration, not end time'}),
    ]

    def init(self):
        self.start_time = datetime.now()
        if self.opts.duration:
            self.end_time = datetime.now() + (
                datetime.strptime(self.opts.end_time, '%H:%M') -
                datetime.strptime('0:00', '%H:%M')
            )
        else:
            self.end_time = datetime.combine(
                datetime.now().date(),
                datetime.strptime(self.opts.end_time, '%H:%M').time()
            )
        self.expected_duration = (self.end_time - self.start_time).total_seconds()

    def update(self, reported):
        meter_val = ((self.end_time - datetime.now()).total_seconds() / self.expected_duration) * 100
        meter_val = max(0, meter_val)

        return {
            'meter': meter_val,
            'red': 100 - (meter_val * 10) if meter_val <= 10 else 0
        }
