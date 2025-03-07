from meter.utils import c_to_f
from meter.sources.base import BaseSource


class InsideTemp(BaseSource):
    """Temperature reported from Raspberry Pi Pico W
    """

    def update(self, reported):
        self.log(f'Temp: {c_to_f(reported["temp"])}')
        return {
            'meter': c_to_f(reported['temp'])
        }
    
