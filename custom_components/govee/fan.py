"""Platform for fan integration"""
from __future__ import annotations

import logging
from typing import Any

from custom_components.govee.devices import H7102

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.const import CONF_DEVICE_ID, CONF_API_KEY
from homeassistant.core import HomeAssistant

from homeassistant.components.fan import (
    PLATFORM_SCHEMA,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

log = logging.getLogger()


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
})


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    device_id = config[CONF_DEVICE_ID]
    api_key = config[CONF_API_KEY]

    device = await H7102.get_data(api_key, device_id)

    async_add_entities([GoveeFan(api_key, device_id, device)])


class GoveeFan(FanEntity):
    reversed_mode_enum = {1: "Normal", 2: "Custom", 3: "Normal", 5: "Sleep", 6: "Nature"}

    _attr_unique_id = CONF_DEVICE_ID
    _attr_name = "Tower Fan"

    def __init__(self, api_key: str, device_id: str, device: H7102) -> None:
        self.api_key = api_key
        self.device_id = device_id

        self._attr_is_on = device.on
        self._attr_oscillating = device.oscillation

        if self._attr_is_on:
            self._attr_percentage = (device.work_mode['value'] / 8) * 100
        else:
            self._attr_percentage = 0
        self._attr_speed_count = 3

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        features = FanEntityFeature(0)
        features |= FanEntityFeature.SET_SPEED
        features |= FanEntityFeature.OSCILLATE

        return features

    async def async_oscillate(self, oscillating: bool) -> None:
        current_value: bool = self._attr_oscillating

        self._attr_oscillating = oscillating

        success = await H7102.toggle_oscillation(self.api_key, self.device_id, oscillating)

        if success:
            log.info(f"Set Oscillation to {self._attr_oscillating} and it should be {oscillating}")
        else:
            self._attr_oscillating = current_value
            log.warning(f"Failed setting oscillation to {oscillating}")

    '''async def async_turn_on(self, percentage: int | None = None, **kwargs: Any) -> None:
        current_value_on: bool = self._attr_is_on
        current_value_pct: int = self._attr_percentage

        self._attr_is_on = True
        self._attr_percentage = percentage

        success = await H7102.on_off(self.api_key, self.device_id, True)

        if success:
            log.info(f"Set is_on state to {self._attr_is_on} and it should be True")

        if percentage is not None:
            success = self.async_set_percentage(percentage)
            if success:
                log.info(f"Set percentage to {self._attr_percentage} and it should be {percentage}")
            else:
                self._attr_is_on = current_value_on
                self._attr_percentage = self._attr_percentage
                log.warning(f"Failed to set percentage to {percentage}")'''

    async def async_turn_off(self, **kwargs: Any) -> None:
        current_value = self._attr_is_on

        self._attr_is_on = False

        success = await H7102.on_off(self.api_key, self.device_id, False)

        if success:
            log.info(f"Set is_on to {self._attr_is_on} and it should be False")
        else:
            self._attr_is_on = current_value
            log.warning(f"Failed to set is_on to False")

    async def async_set_percentage(self, percentage: int) -> None:
        current_value_on = self._attr_is_on
        current_value_pct = self._attr_percentage

        speed: int = int((percentage / 100) * 8)

        self._attr_is_on = True
        self._attr_percentage = percentage

        success = await H7102.change_mode_speed(self.api_key, self.device_id, value=speed)

        if success:
            log.info(f"Set percentage to {self._attr_percentage} and it should be {percentage}")
        else:
            self._attr_is_on = current_value_on
            self._attr_percentage = current_value_pct
            log.warning(f"Failed to set percentage to {percentage}")

    async def async_update(self) -> None:
        log.info("Running async_update...")
        device = await H7102.get_data(api_key=self.api_key, device_id=self.device_id)

        self._attr_is_on = device.on
        if not self._attr_is_on:
            self._attr_percentage = 0
        else:
            self._attr_percentage = (device.work_mode['value'] / 8) * 100
        self._attr_oscillating = device.oscillation

        log.info(f"Set is_on to {self._attr_is_on}")
        log.info(f"Set percentage to {self._attr_percentage}")
        log.info(f"Set oscillating to {self._attr_oscillating}")
