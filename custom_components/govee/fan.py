"""Platform for fan integration."""
from __future__ import annotations

import logging
from typing import Optional, Any

import voluptuous as vol

from pprint import pformat

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.light import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_API_KEY, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from util.govee_api import GoveeAPI

_LOGGER = logging.getLogger("govee")

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_NAME): cv.string,
})


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Govee fan platform."""
    # Add devices
    _LOGGER.info(pformat(config))

    fan = {
        "device_id": config[CONF_DEVICE_ID],
        "api_key": config[CONF_API_KEY],
        "name": config[CONF_NAME],
    }

    add_entities([GoveeFan(fan)])

class GoveeFan(FanEntity):
    """Representation of a Govee Fan."""

    def __init__(self, fan) -> None:
        """Initialize an Govee Fan."""
        _LOGGER.info(pformat(fan))
        self._api: GoveeAPI = GoveeAPI(fan["api_key"])
        match fan["name"].lower():
            case "h7126":
                self._fan = H7126(fan["device_id"])
            case "h7102":
                self._fan = H7102(fan["device_id"])
            case _:
                self._fan = None
        self._name = self._fan.device_name
        self._current_direction = None
        self._is_on = None
        self._oscillating = None
        self._percentage = None
        self._preset_mode = None
        self._preset_modes = list(self._fan.work_mode_dict.values())
        if hasattr(self._fan, "max_fan_speed"):
            self._speed_count = self._fan.max_fan_speed
        else:
            self._speed_count = None
        self._supported_features = None

    @property
    def name(self) -> str:
        """Return the display name of this fan."""
        return self._name

    @property
    def current_direction(self):
        """"""
        return self._current_direction

    @property
    def is_on(self):
        """"""
        return self._is_on

    @property
    def oscillating(self):
        """"""
        return self._oscillating


    @property
    def percentage(self):
        """"""
        return self._percentage


    @property
    def preset_mode(self):
        """"""
        return self._preset_mode


    @property
    def preset_modes(self):
        """"""
        return self._preset_modes


    @property
    def speed_count(self):
        """"""
        return self.speed_count

    @property
    def supported_features(self):
        features = FanEntityFeature(0)
        match self._fan.sku.lower():
            case "h7102":
                features |= FanEntityFeature.SET_SPEED
                features |= FanEntityFeature.OSCILLATE
                features |= FanEntityFeature.TURN_ON
                features |= FanEntityFeature.TURN_OFF
                features |= FanEntityFeature.PRESET_MODE
            case "h7126":
                features |= FanEntityFeature.TURN_ON
                features |= FanEntityFeature.TURN_OFF
                features |= FanEntityFeature.PRESET_MODE

        return features

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        await self._fan.set_work_mode(self._api, preset_mode)
        self._preset_mode = self._fan.work_mode

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""

    async def async_turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan."""
        await self._fan.turn_off(self._api)
        if percentage:
            await self._fan.set_fan_speed(self._api, percentage)
        if preset_mode:
            await self._fan.set_work_mode(self._api, preset_mode)
        self._is_on = self._fan.power_switch
        if self._fan.sku.lower() == "h7102":
            self._percentage = self._fan.fan_speed
        self._preset_mode = self._fan.work_mode

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._fan.turn_off(self._api)
        self._is_on = self._fan.power_switch

    async def async_oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        await self._fan.toggle_oscillation(self._api, oscillating)
        self._oscillating = self._fan.oscillation_toggle
