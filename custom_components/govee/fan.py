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


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    device_id = config[CONF_DEVICE_ID]
    api_key = config[CONF_API_KEY]

    add_entities([GoveeFan(device_id, api_key)])



class GoveeFan(FanEntity):
    _attr_unique_id = CONF_DEVICE_ID
    _attr_name = "Tower Fan"
    _attr_is_on = False
    _attr_oscillating = True
    _attr_percentage = 8
    _attr_preset_modes = ['Normal', 'Sleep', 'Nature', 'Custom']

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        features = FanEntityFeature(0)
        features |= FanEntityFeature.SET_SPEED
        features |= FanEntityFeature.PRESET_MODE
        features |= FanEntityFeature.OSCILLATE

        return features

    def __init__(self, device_id: str, api_key: str) -> None:
        self._device_id = device_id
        self._api_key = api_key

    def oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        H7102.toggle_oscillation(self._api_key, self._device_id, oscillating)
        self._attr_oscillating = H7102.get_data(self._api_key, self._device_id).oscillation

    def turn_on(
            self,
            percentage: int | None = None,
            preset_mode: str | None = None,
            **kwargs: Any,
    ) -> None:
        log.warning("Entering turn on")
        H7102.on_off(api_key=self._api_key, mac_address=self._device_id, on=True)
        '''if percentage is not None:
            _LOGGER.warning("Entering set percentage mode: %s", percentage)
            self.set_percentage(percentage)
        if preset_mode is not None:
            _LOGGER.warning("Entering preset mode: %s", preset_mode)
            self.set_preset_mode(preset_mode)'''
        self._attr_is_on = H7102.get_data(self._api_key, self._device_id).on
        log.warning("Entering New state is %s", self._attr_is_on)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        if not self._attr_is_on:
            self.turn_on()
            return
        log.warning("Entering turn off")
        H7102.on_off(api_key=self._api_key, mac_address=self._device_id, on=False)
        self._attr_is_on = H7102.get_data(self._api_key, self._device_id).on

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""

        speed = int(percentage / 100 * 8)

        if speed == 0:
            speed = 1

        H7102.change_mode_speed(self._api_key, self._device_id, value=speed)
        self._attr_percentage = (H7102.get_data(self._api_key, self._device_id).work_mode['value'] / 8) * 100

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        mode_enum = {'custom': 2, 'normal': 3, 'sleep': 5, 'nature': 6}
        H7102.change_mode_speed(self._api_key, self._device_id, mode=mode_enum[preset_mode.lower()])
        reversed_mode_enum = {1: "normal", 2: "custom", 3: "normal", 5: "sleep", 6: "nature"}
        self._attr_preset_mode = reversed_mode_enum[H7102.get_data(self._api_key, self._device_id).work_mode['mode']]

    def update(self) -> None:
        device = H7102.get_data(self._api_key, self._device_id)
        reversed_mode_enum = {1: "normal", 2: "custom", 3: "normal", 5: "sleep", 6: "nature"}
        log.warning(f"Device On: {self._attr_is_on}")
        self._attr_is_on = device.on
        self._attr_oscillating = device.oscillation
        self._attr_preset_mode = reversed_mode_enum[device.work_mode['mode']]
        self._attr_percentage = (device.work_mode['value'] / 8) * 100
