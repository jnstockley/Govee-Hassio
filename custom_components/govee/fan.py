"""Platform for fan integration"""
import logging
from datetime import timedelta
from typing import Any, Optional

import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.fan import (
    PLATFORM_SCHEMA,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.govee.devices.H7102 import H7102, H7102_Device
from custom_components.govee.devices.H7126 import H7126

log = logging.getLogger()


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_NAME): cv.string,
})


async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback,
                               discovery_info: DiscoveryInfoType | None = None) -> None:
    device_id = config[CONF_DEVICE_ID]
    sku = config[CONF_NAME]
    api_key = config[CONF_API_KEY]

    device = H7102(api_key=api_key, sku=sku, device=device_id, hass=hass)

    coordinator = MyCoordinator(hass, device)

    await coordinator.async_refresh()

    new_device = await device.update()

    async_add_entities(
        [GoveeFan(device_id, sku, api_key, new_device)])


class MyCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, device):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            log,
            # Name of the data. For logging purposes.
            name="Govee W-Fi Tower Fan",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=5),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True
        )

        self.device = device

    async def _async_update_data(self):
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                return await self.device.update()
        except Exception as e:
            log.error(f"Failed to update device: {e}")
            raise e



class GoveeFan(FanEntity):
    h7102_mode_enum = {"Normal": 1, "Custom": 2, "Sleep": 5, "Nature": 6}
    h7102_reversed_mode_enum = {1: "Normal", 2: "Custom", 5: "Sleep", 6: "Nature"}

    h7126_mode_enum = {"Sleeping": 1, "Low": 2, "High": 3, "Custom": 4}
    h7126_reversed_mode_enum = {1: "Sleeping", 2: "Low", 3: "High", 0: "Custom"}

    _attr_current_direction = None
    _attr_is_on = False
    _attr_oscillating = False
    _attr_percentage = 0
    _attr_preset_mode = None
    _attr_speed_count = 8

    def __init__(self, device_id: str, sku: str, api_key: str, device: H7102_Device) -> None:
        log.info(f"Setting up fan: {device_id} - {sku} - {api_key}")
        self.device_id = device_id
        self.sku = sku
        self.api_key = api_key

        self._attr_is_on = device.power_state
        self._attr_preset_mode = "Normal"
        self._attr_unique_id = device_id
        self._attr_name = self.device_id

        if self.sku == "H7102":
            self._attr_oscillating = device.oscillation_state
            self._attr_percentage = device.percentage
            self._attr_name = "Smart Tower Fan"
            self._attr_preset_modes = list(self.h7102_mode_enum.keys())
        elif self.sku == "H7126":
            self._attr_name = "Smart Air Purifier"
            self._attr_preset_modes = list(self.h7126_mode_enum.keys())


    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        features = FanEntityFeature(0)
        if self.sku == "H7102":
            features |= FanEntityFeature.SET_SPEED
            features |= FanEntityFeature.OSCILLATE
            features |= FanEntityFeature.TURN_ON
            features |= FanEntityFeature.TURN_OFF
            features |= FanEntityFeature.PRESET_MODE
        elif self.sku == "H7126":
            features |= FanEntityFeature.TURN_ON
            features |= FanEntityFeature.TURN_OFF
            features |= FanEntityFeature.PRESET_MODE

        return features

    async def async_oscillate(self, oscillating: bool) -> None:
        if oscillating:
            await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_on_oscillation()
        else:
            await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_off_oscillation()

        log.info(f"Oscillation: {oscillating}")
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        self._attr_oscillating = device.oscillation_state

    async def async_turn_on(self, speed: Optional[str] = None, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        if self.sku == "H7102":
            device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
            log.info(f"Device: {device}")

            await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_on()

            if device.oscillation_state:
                await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_on_oscillation()
            else:
                await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_off_oscillation()

            await H7102(self.api_key, self.sku, self.device_id, self.hass).set_percentage(int((percentage / 100) * 8))

            await H7102(self.api_key, self.sku, self.device_id, self.hass).set_work_mode(self.h7102_mode_enum[device.work_mode])

            device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
            self._attr_is_on = device.power_state
            self._attr_oscillating = device.oscillation_state
            self._attr_percentage = device.percentage
            self._attr_preset_mode = self.h7102_reversed_mode_enum[device.work_mode]
        elif self.sku == "H7126":
            device: H7126 = H7126(self.api_key, self.device_id, self.hass)
            await device.get_device_state()

            log.info(f"Device: {device}")

            await device.turn_on()

            await device.set_preset_mode(self.h7126_mode_enum[device.preset_mode])

            device: H7126 = await device.get_device_state()
            self._attr_is_on = device.is_on
            self._attr_preset_mode = device.preset_mode

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.sku == "H7102":
            await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_off()
            device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
            log.info(f"Turned off: {device}")
            self._attr_is_on = device.power_state
        elif self.sku == "H7126":
            device: H7126 = H7126(self.api_key, self.device_id, self.hass)
            await device.turn_off()
            device: H7126 = await device.get_device_state()
            log.info(f"Turned off: {device}")
            self._attr_is_on = device.is_on

    async def async_set_percentage(self, percentage: int) -> None:
        await H7102(self.api_key, self.sku, self.device_id, self.hass).set_percentage(int((percentage / 100) * 8))
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        self._attr_percentage = device.percentage

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if self.sku == "H7102":
            await H7102(self.api_key, self.sku, self.device_id, self.hass).set_work_mode(self.h7102_mode_enum[preset_mode])
            device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
            self._attr_preset_mode = self.h7102_reversed_mode_enum[device.work_mode]
        elif self.sku == "H7126":
            device: H7126 = H7126(self.api_key, self.device_id, self.hass)
            await device.set_preset_mode(self.h7126_mode_enum[preset_mode])
            device: H7126 = await device.get_device_state()
            self._attr_preset_mode = device.preset_mode

    async def async_update(self) -> None:
        log.info(f"Updating fan for device {self.device_id} - {self.sku}")
        if self.sku == "H7102":
            device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
            log.info(f"Device: {device}")
            self._attr_is_on = device.power_state
            self._attr_oscillating = device.oscillation_state
            self._attr_percentage = device.percentage
            self._attr_preset_mode = self.h7102_reversed_mode_enum[device.work_mode]
        elif self.sku == "H7126":
            device: H7126 =  H7126(self.api_key, self.device_id, self.hass)
            await device.get_device_state()
            log.info(f"Device: {device}")
            self._attr_is_on = device.is_on
            self._attr_preset_mode = device.preset_mode
