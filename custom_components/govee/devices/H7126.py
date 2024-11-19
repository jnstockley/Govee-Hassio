from homeassistant.core import HomeAssistant

from custom_components.govee.devices import GoveeAPIUtil


class H7126:

    sku = "H7126"
    preset_mode_dict = {1: "Sleeping", 2: "Low", 3: "High", 0: "Custom"}
    is_online: bool
    is_on: bool
    preset_mode: str
    filter_life: int
    air_quality: int

    def __init__(self, api_key: str, device_id: str, hass: HomeAssistant):
        self.api_key = api_key
        self.device_id = device_id
        self.hass = hass

    async def turn_on(self):
        capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 1}
        await GoveeAPIUtil.control_device(self.api_key, self.sku, self.device_id, capability, self.hass, appliance_api=True)

        await self.get_device_state()

    async def turn_off(self):
        capability = {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 1}
        await GoveeAPIUtil.control_device(self.api_key, self.sku, self.device_id, capability, self.hass, appliance_api=True)

        await self.get_device_state()

    async def set_preset_mode(self, work_mode: int):
        capability = {"type": "devices.capabilities.work_mode", "instance": "workMode", "value": {"workMode": 1, "modeValue": work_mode}}
        await GoveeAPIUtil.control_device(self.api_key, self.sku, self.device_id, capability, self.hass)

        await self.get_device_state()

    async def get_device_state(self):
        capabilities: dict = await GoveeAPIUtil.get_device_state(self.api_key, self.sku, self.device_id, self.hass)

        for capability in capabilities:
            if capability["type"] == "devices.capabilities.online":
                self.is_online = str(capability["state"]["value"]) == 'true'
            elif capability["type"] == "devices.capabilities.on_off":
                self.is_on = int(capability["state"]["value"]) == 1
            elif capability["type"] == "devices.capabilities.work_mode":
                self.preset_mode = self.preset_mode_dict[capability["state"]["value"]["modeValue"]]
            elif capability["type"] == "devices.capabilities.property" and capability["instance"] == "filterLifeTime":
                self.filter_life = int(capability["state"]["value"])
            elif capability["type"] == "devices.capabilities.property" and capability["instance"] == "airQuality":
                self.air_quality = int(capability["state"]["value"])
