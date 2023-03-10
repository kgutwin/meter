import time

from meter.sources.base import BaseSource


class Pomodoro(BaseSource):
    """Pomodoro timer
    """
    OPTIONS = [
        (['--work-time'], {'type': int, 'default': 25}),
        (['--break-time'], {'type': int, 'default': 5}),
        (['--direction'], {'choices': ['up', 'down'], 'default': 'down'}),
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
