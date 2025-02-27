import json
import time
import boto3

from meter import config
from meter.sources.base import BaseSource

iot = boto3.client('iot-data')


class ACHeater(BaseSource):
    """AC Heater

    The meter shows the current room temperature. When the heater is
    enabled, the blue light will illuminate. When the heat is on, the
    red light will illuminate.

    """
    OPTIONS = [
        (['--thing-name'], {"default": "ac-heater"})
    ]

    def update(self, reported):
        response = iot.get_thing_shadow(thingName=self.opts.thing_name)
        status = json.load(response['payload'])
        reported = status['state']['reported']

        if reported['current_t'] < reported['current_set_t']:
            meter = max(
                0,
                10 - ((reported['current_set_t'] - reported['current_t']) * 2)
            )

        else:
            meter = 10 + (
                0.25 * (reported['current_t'] - reported['current_set_t']) * 80
            )

        if not hasattr(self, 'last_tick') or reported['counter'] != self.last_tick:
            self.last_tick = reported['counter']
            self.last_tick_time = time.time()
            self.log(f"current_t: {reported['current_t']} meter: {meter}")
        
        return {
            'meter': meter,
            'red': 50 if (time.time() - self.last_tick_time) > 120 else 0,
            'green': 20 if status['state']['reported']['heat_cmd'] == 'on' else 0,
            'blue': 5 if status['state']['reported']['enable'] else 0,
        }
