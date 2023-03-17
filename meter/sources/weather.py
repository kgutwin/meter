import json
from urllib.request import urlopen
from datetime import datetime, timedelta, timezone

from meter.utils import c_to_f
from meter.sources.base import BaseSource


class OutsideTemp(BaseSource):
    """Ouside temperature from Open-Meteo.com
    """
    OPTIONS = [
        (['--coords'], {"required": True}),
    ]

    def init(self):
        self.last_update = datetime.min
    
    def update(self, reported):
        if datetime.now() > self.last_update + timedelta(hours=1):
            lat, lon = self.opts.coords.split(',')
            url = (f'https://api.open-meteo.com/v1/forecast?'
                   f'latitude={lat}&longitude={lon}&current_weather=true')
            response = json.load(urlopen(url))
            
            # convert the timestamp in the response to our current
            # timezone as a naive datetime object
            self.last_update = datetime.strptime(
                response['current_weather']['time'],
                '%Y-%m-%dT%H:%M'
            ).replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
            
            self.log(response)
            return {
                'meter': c_to_f(response['current_weather']['temperature'])
            }
        
        else:
            return {}
