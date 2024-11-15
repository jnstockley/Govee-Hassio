"""Platform for fan integration"""
import logging
from datetime import timedelta
from typing import Any

import async_timeout
from homeassistant.const import CONF_DEVICE_ID, CONF_API_KEY, CONF_NAME, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType, ConfigType
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.fan import (
    PLATFORM_SCHEMA,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from custom_components.govee.devices.H7102 import H7102, H7102_Device

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

    #coordinator = MyCoordinator(hass, device)

    #await coordinator.async_refresh()

    new_device = await device.update()

    async_add_entities(
        [GoveeFan(device_id, sku, api_key, new_device)])


'''class MyCoordinator(DataUpdateCoordinator):

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
'''


class GoveeFan(FanEntity):
    mode_enum = {"Normal": 1, "Custom": 2, "Sleep": 5, "Nature": 6}
    reversed_mode_enum = {1: "Normal", 2: "Custom", 3: "Normal", 5: "Sleep", 6: "Nature"}

    _attr_current_direction = None
    _attr_is_on = False
    _attr_oscillating = False
    _attr_percentage = 0
    _attr_preset_mode = None
    _attr_preset_modes = list(reversed_mode_enum.values())
    _attr_speed_count = 8
    _attr_unique_id = CONF_DEVICE_ID
    _attr_name = "Govee Smart Tower Fan"

    def __init__(self, device_id: str, sku: str, api_key: str, device: H7102_Device) -> None:
        log.info(f"Setting up fan: {device_id} - {sku} - {api_key}")
        self.device_id = device_id
        self.sku = sku
        self.api_key = api_key

        self._attr_is_on = device.power_state
        self._attr_oscillating = device.oscillation_state
        self._attr_percentage = device.percentage
        self._attr_preset_mode = self.reversed_mode_enum[device.work_mode]


    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        features = FanEntityFeature(0)
        features |= FanEntityFeature.SET_SPEED
        features |= FanEntityFeature.OSCILLATE
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

    async def async_turn_on(self, percentage: int | None = None, **kwargs: Any) -> None:
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        log.info(f"Device: {device}")

        await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_on()

        if device.oscillation_state:
            await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_on_oscillation()
        else:
            await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_off_oscillation()

        await H7102(self.api_key, self.sku, self.device_id, self.hass).set_percentage(int((percentage / 100) * 8))

        await H7102(self.api_key, self.sku, self.device_id, self.hass).set_work_mode(self.mode_enum[device.work_mode])

        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        self._attr_is_on = device.power_state
        self._attr_oscillating = device.oscillation_state
        self._attr_percentage = device.percentage
        self._attr_preset_mode = self.reversed_mode_enum[device.work_mode]


    async def async_turn_off(self, **kwargs: Any) -> None:
        await H7102(self.api_key, self.sku, self.device_id, self.hass).turn_off()
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        log.info(f"Turned off: {device}")
        self._attr_is_on = device.power_state


    async def async_set_percentage(self, percentage: int) -> None:
        await H7102(self.api_key, self.sku, self.device_id, self.hass).set_percentage(int((percentage / 100) * 8))
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        self._attr_percentage = device.percentage

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await H7102(self.api_key, self.sku, self.device_id, self.hass).set_work_mode(self.mode_enum[preset_mode])
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        self._attr_preset_mode = self.reversed_mode_enum[device.work_mode]

    async def async_update(self) -> None:
        log.info(f"Updating fan for device {self.device_id} - {self.sku}")
        device: H7102_Device = await H7102(self.api_key, self.sku, self.device_id, self.hass).update()
        log.info(f"Device: {device}")
        self._attr_is_on = device.power_state
        self._attr_oscillating = device.oscillation_state
        self._attr_percentage = device.percentage
        self._attr_preset_mode = self.reversed_mode_enum[device.work_mode]
