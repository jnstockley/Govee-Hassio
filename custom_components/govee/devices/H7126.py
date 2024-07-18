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

    def __init__(self, api_key: str, sku: str, device: str):
        self.api_key = api_key
        self.sku = sku
        self.device = device

    def turn_on(self):
        capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 1}

        success = GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability)

        if success:
            return self.update()

    def turn_off(self):
        capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 0}

        success = GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability)

        if success:
            return self.update()

    def get_power_state(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "powerSwitch":
                return int(capability["state"]["value"]) == 1

    # TODO Be able to set with percentage, and enum
    def set_work_mode(self, work_mode: int, mode_value: int):
        capability = {"type": "devices.capabilities.work_mode", "instance": "workMode",
                      "value": {"workMode": work_mode, "modeValue": mode_value}}

        success = GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability)

        if success:
            return self.update()

    def get_work_mode(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

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

    def get_filter_life_time(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "filterLifeTime":
                return float(capability["state"]["value"])

    def get_air_quality(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "airQuality":
                return int(capability["state"]["value"])

    def update(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

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
