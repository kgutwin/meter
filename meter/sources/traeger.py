try:
    import traeger
    has_traeger = True
except ImportError:
    has_traeger = False

from meter.sources.base import BaseSource
    

class Traeger(BaseSource):
    """Temperature probe data from Traeger WiFire
    """
    OPTIONS = [
        (['--username'], {"required": True,
                          'help': 'Traeger account username'}),
        (['--password'], {"required": True,
                          'help': 'Traeger account password'}),
        (['--start-temp'], {"required": True, 'metavar': 'T',
                            'help': 'zero on meter is T degrees'}),
        (['--target-temp'], {"default": "PROBE_SET", 'metavar': 'T',
                             'help': ('full-scale on meter is T degrees, or if'
                                      ' "PROBE_SET", the probe set point')}),
    ]

    def init(self):
        if not has_traeger:
            raise Exception("traeger module not installed!")

        self.log(f"Signing in as {self.opts.username}...")
        self.client = traeger.traeger(self.opts.username, self.opts.password)

        self.log("Subscribing to grill status updates...")
        self.updates = self.client.grill_status_subscription()

    def update(self, reported):
        status = next(self.updates)
        #self.log(repr(status))
        
        temp = status['status']['probe']
        start = float(self.opts.start_temp)
        if self.opts.target_temp == 'PROBE_SET':
            end = status['status']['probe_set']
        else:
            end = float(self.opts.target_temp)
        meter = (temp - start) / (end - start) * 100.0
        meter = min(meter, 100.0)
        
        self.log(f'Temp: {temp} {meter:.2f}%')
        return {
            'meter': meter,
            'red': 50 if status['status']['errors'] else 0,
            'green': 50 if meter >= 100 else 0,
        }
