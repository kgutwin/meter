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
        (['--username'], {"required": True}),
        (['--password'], {"required": True}),
        (['--start-temp'], {"required": True}),
        (['--target-temp'], {"default": "PROBE_SET"}),
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
