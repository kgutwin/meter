try:
    from apcaccess import status as apc
except ImportError:
    apc = None

from meter.sources.base import BaseSource


class ApcUps(BaseSource):
    """APC UPS current battery level

    To use this, ensure that the `apcaccess` Python module is installed:

        pip install apcaccess

    """
    OPTIONS = [
        (['--hostname'], {"required": True}),
    ]

    def update(self, reported):
        if apc is None:
            return {}
        
        result = apc.parse(apc.get(host=self.opts.hostname), strip_units=True)

        return {
            'meter': float(result['BCHARGE']),
            'red': 25 if 'ONBATT' in result['STATUS'] else 0,
            'green': 25 if 'ONLINE' in result['STATUS'] else 0
        }
