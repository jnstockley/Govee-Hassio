"""Govee Cloud API Implementation for Smart Air Purifier"""
from dataclasses import dataclass

from custom_components.govee.devices import GoveeAPIUtil


@dataclass
class H7126_Device:
    power_state: bool
    work_mode: int
    work_mode_enum: str
    mode_value: int
    percentage: float
    filter_life_time: float
    air_quality: int


class H7126:
    work_mode_dict = {1: "Sleeping", 2: "Low", 3: "High", 0: "Custom"}

    def __init__(self, api_key: str, sku: str, device: str, hass):
        self.api_key = api_key
        self.sku = sku
        self.device = device
        self.hass = hass

    async def turn_on(self):
        capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 1}

        success = await GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability, self.hass)

        if success:
            return await self.update()

    async def turn_off(self):
        capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 0}

        success = await GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability, self.hass)

        if success:
            return await self.update()

    async def get_power_state(self):
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        for capability in device_state:
            if capability["instance"] == "powerSwitch":
                return int(capability["state"]["value"]) == 1

    # TODO Be able to set with percentage, and enum
    async def set_work_mode(self, work_mode: int):
        capability = {"name": "mode", "value": work_mode}

        success = await GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability, self.hass, appliance_api=True)

        if success:
            return await self.update()

    async def get_work_mode(self):
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        for capability in device_state:
            if capability["instance"] == "workMode":
                work_mode = int(capability["state"]["value"]["workMode"])
                mode_value = int(capability["state"]["value"]["modeValue"])
                try:
                    mode_enum = self.work_mode_dict[work_mode]
                except KeyError:
                    mode_enum = "Unknown"

                return {"work_mode": work_mode, "mode_enum": mode_enum, "mode_value": mode_value,
                        "percentage": (mode_value / 4) * 100}

    async def get_filter_life_time(self):
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        for capability in device_state:
            if capability["instance"] == "filterLifeTime":
                return float(capability["state"]["value"])

    async def get_air_quality(self):
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        for capability in device_state:
            if capability["instance"] == "airQuality":
                return int(capability["state"]["value"])

    async def update(self):
        device_state = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device, self.hass)

        power_state = None
        work_mode = None
        mode_value = None
        percentage = None
        filter_life_time = None
        air_quality = None
        mode_enum = None

        for capability in device_state:
            if capability["instance"] == "workMode":
                work_mode = int(capability["state"]["value"]["workMode"])
                mode_value = int(capability["state"]["value"]["modeValue"])
                percentage = (mode_value / 4) * 100
                try:
                    mode_enum = self.work_mode_dict[work_mode]
                except KeyError:
                    mode_enum = "Unknown"
            elif capability["instance"] == "powerSwitch":
                power_state = int(capability["state"]["value"]) == 1
            elif capability["instance"] == "filterLifeTime":
                filter_life_time = float(capability["state"]["value"])
            elif capability["instance"] == "airQuality":
                air_quality = int(capability["state"]["value"])

        return H7126_Device(power_state=power_state, work_mode=work_mode, mode_value=mode_value, percentage=percentage,
                            filter_life_time=filter_life_time, air_quality=air_quality, work_mode_enum=mode_enum)
