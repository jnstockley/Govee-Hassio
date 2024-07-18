"""Govee Cloud API Implementation for Wi-Fi Thermometer"""
from dataclasses import dataclass

from custom_components.govee.devices import GoveeAPIUtil


@dataclass
class H5179_Device:
    temperature: float
    humidity: int


class H5179:
    def __init__(self, api_key: str, sku: str, device: str):
        self.api_key = api_key
        self.sku = sku
        self.device = device

    def get_temperature(self) -> float:
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "sensorTemperature":
                return float(capability["state"]["value"])

    def get_humidity(self) -> int:
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "sensorHumidity":
                return int(capability["state"]["value"]['currentHumidity'])

    def update(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "sensorTemperature":
                temperature = float(capability["state"]["value"])
            elif capability["instance"] == "sensorHumidity":
                humidity = int(capability["state"]["value"]['currentHumidity'])

        return H5179_Device(temperature=temperature, humidity=humidity)
