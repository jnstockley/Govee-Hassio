"""Govee Cloud API Implementation for Smart Tower Fan"""
from dataclasses import dataclass

from custom_components.govee.devices import GoveeAPIUtil


@dataclass
class H7102_Device:
    power_state: bool
    oscillation_state: bool
    work_mode: int
    work_mode_enum: str
    mode_value: int
    percentage: float


class H7102:
    work_mode_dict = {1: "Normal", 5: "Sleep", 6: "Nature", 2: "Custom"}

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

    def get_power_state(self) -> bool:
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "powerSwitch":
                return int(capability["state"]["value"]) == 1

    def turn_on_oscillation(self):
        capability = {"type": "devices.capabilities.toggle", "instance": "oscillationToggle", "value": 1}

        success = GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability)

        if success:
            return self.update()

    def turn_off_oscillation(self):
        capability = {"type": "devices.capabilities.toggle", "instance": "oscillationToggle", "value": 0}

        success = GoveeAPIUtil.control_device(self.api_key, self.sku, self.device, capability)

        if success:
            return self.update()

    def get_oscillation_state(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "oscillationToggle":
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
                        "percentage": (mode_value / 8) * 100}

    def update(self):
        device_state = GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device)

        for capability in device_state:
            if capability["instance"] == "workMode":
                work_mode = int(capability["state"]["value"]["workMode"])
                mode_value = int(capability["state"]["value"]["modeValue"])
                try:
                    mode_enum = self.work_mode_dict[work_mode]
                except KeyError:
                    mode_enum = "Unknown"

                work_mode = work_mode
                work_mode_enum = mode_enum
                mode_value = mode_value
                percentage = (mode_value / 8) * 100
            elif capability["instance"] == "oscillationToggle":
                oscillation_state = int(capability["state"]["value"]) == 1
            elif capability["instance"] == "powerSwitch":
                power_state = int(capability["state"]["value"]) == 1

        return H7102_Device(power_state=power_state, oscillation_state=oscillation_state, work_mode=work_mode,
                            work_mode_enum=work_mode_enum, mode_value=mode_value, percentage=percentage)
