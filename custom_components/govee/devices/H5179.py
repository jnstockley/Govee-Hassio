# Govee Wi-Fi Thermo-Hygrometer
# https://us.govee.com/products/wi-fi-temperature-humidity-sensor
import logging

import Generic

log = logging.getLogger()


class H5179:
    def __init__(self, data: dict):
        payload: dict = data['payload']
        capabilities: dict = payload['capabilities']
        self.sku = payload['sku']
        self.device = payload['device']
        for capability in capabilities:
            if capability['type'] == 'devices.capabilities.online':
                self.online: bool = bool(capability['state']['value'])
            elif (capability['type'] == 'devices.capabilities.property' and capability['instance']
                  == 'sensorTemperature'):
                self.temperature: float = (int(capability['state']['value'] / 100) * 1.8) + 32
            elif capability['type'] == 'devices.capabilities.property' and capability['instance'] == 'sensorHumidity':
                self.humidity: float = (int(capability['state']['value']['currentHumidity']) / 100)
            else:
                log.warning(f"Unexpected capability found {capability['type']}")

    def __str__(self):
        return (f'SKU: {self.sku}, Device: {self.device}, Online: {self.online}, Temperature: {self.temperature}, '
                f'Humidity: {self.humidity}')


def get_data(api_key: str, mac_address: str) -> H5179:
    data = Generic.__get_data__(api_key, "H5179", mac_address)

    device = H5179(data)

    return device
