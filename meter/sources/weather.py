import json
import time
from urllib.request import urlopen

from meter.utils import c_to_f
from meter.sources.base import BaseSource


class OutsideTemp(BaseSource):
    """Ouside temperature from Open-Meteo.com
    """
    OPTIONS = [
        (['--coords'], {"required": True}),
    ]

    def update(self, reported):
        time.sleep(15)
        lat, lon = self.opts.coords.split(',')
        url = (f'https://api.open-meteo.com/v1/forecast?'
               f'latitude={lat}&longitude={lon}&current_weather=true')
        response = json.load(urlopen(url))
        self.log(response)
        return {
            'meter': c_to_f(response['current_weather']['temperature'])
        }
