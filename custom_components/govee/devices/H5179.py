"""Govee Cloud API Implementation for Wi-Fi Thermometer"""
import logging
from dataclasses import dataclass

from custom_components.govee.devices import GoveeAPIUtil

log = logging.getLogger()


@dataclass
class H5179_Device:
    temperature: float
    humidity: int


class H5179:
    def __init__(self, api_key: str, sku: str, device: str, hass):
        self.api_key = api_key
        self.sku = sku
        self.device = device
        self.hass = hass

    async def get_temperature(self) -> float:
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        for capability in device_state:
            if capability["instance"] == "sensorTemperature":
                return float(capability["state"]["value"])

    async def get_humidity(self) -> int:
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        for capability in device_state:
            if capability["instance"] == "sensorHumidity":
                return int(capability["state"]["value"]["currentHumidity"])

    async def update(self):
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        temperature = -999.0
        humidity = -1.0

        log.info(f"Device State: {device_state}")

        for capability in device_state:
            if capability["instance"] == "sensorTemperature":
                temperature = float(capability["state"]["value"])
            elif capability["instance"] == "sensorHumidity":
                humidity = int(capability["state"]["value"]["currentHumidity"])

        return H5179_Device(temperature=temperature, humidity=humidity)
