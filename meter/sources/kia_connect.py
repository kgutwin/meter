try:
    import hyundai_kia_connect_api
    from hyundai_kia_connect_api import const
    has_kia_connect = True
except ImportError:
    has_kia_connect = False

from meter.sources.base import BaseSource


class KiaConnect(BaseSource):
    """EV battery charge data from Hyundai/Kia Connect
    """
    OPTIONS = [
        (['--username'], {"required": True, "help": "Account username"}),
        (['--password'], {"required": True, "help": "Account password"}),
        (['--pin'], {"default": "", "help": "Account PIN"}),
        (['--brand'], {"required": True,
                       "help": "Car brand",
                       "choices": sorted(const.BRANDS.values())}),
        (['--region'], {"default": "USA",
                        "help": "Region",
                        "choices": sorted(const.REGIONS.values())}),
        (['--vehicle'], {"help": "Vehicle name, if more than one"}),
    ]

    def init(self):
        self.min_cycle = max(self.min_cycle, 60.0)
        
        if not has_kia_connect:
            raise Exception("hyundai_kia_connect_api module not installed!")

        region = [
            k for k, v in const.REGIONS.items() if v == self.opts.region
        ][0]
        brand = [
            k for k, v in const.BRANDS.items() if v == self.opts.brand
        ][0]

        self.log(f'Signing in as {self.opts.username}...')
        self.vm = hyundai_kia_connect_api.VehicleManager(
            region=region,
            brand=brand,
            username=self.opts.username,
            password=self.opts.password,
            pin=self.opts.pin,
        )
        self.vm.check_and_refresh_token()
        self.vm.update_all_vehicles_with_cached_state()

        self.vehicle_id = None
        if self.opts.vehicle:
            for vehicle_id, vehicle in self.vm.vehicles.items():
                if vehicle.name == self.opts.vehicle:
                    self.vehicle_id = vehicle_id
                    break
        elif len(self.vm.vehicles) == 1:
            self.vehicle_id = list(self.vm.vehicles.keys())[0]

        if not self.vehicle_id:
            raise Exception("Must specify vehicle name with --vehicle")

    def update(self, reported):
        self.vm.check_and_force_update_vehicles(30 * 60)  # refresh every 30m
        
        vehicle = self.vm.vehicles[self.vehicle_id]

        meter = vehicle.ev_battery_percentage
        charging = vehicle.ev_battery_is_charging

        self.log(f'Charge state: {meter}%, {charging=}')
        return {
            'meter': meter,
            'green': 50 if charging else 0,
        }
