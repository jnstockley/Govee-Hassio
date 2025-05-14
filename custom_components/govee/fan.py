"""Platform for fan integration."""
from __future__ import annotations

import logging
import math
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
from homeassistant.util.percentage import ranged_value_to_percentage, percentage_to_ranged_value
from homeassistant.util.scaling import int_states_in_range
from util.govee_api import GoveeAPI

_LOGGER = logging.getLogger("govee")

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_NAME): cv.string,
})


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
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

    api = GoveeAPI(fan["api_key"])

    match fan["name"].lower():
        case "h7126":
            device = H7126(fan["device_id"])
            await device.update(api)
        case "h7102":
            device = H7102(fan["device_id"])
            await device.update(api)
        case _:
            device = None

    async_add_entities([GoveeFan(fan, api, device)])

class GoveeFan(FanEntity):
    """Representation of a Govee Fan."""

    def __init__(self, fan, api: GoveeAPI, device) -> None:
        """Initialize an Govee Fan."""
        _LOGGER.info(pformat(fan))
        self._attr_unique_id = fan["device_id"]
        self._api = api
        self._fan = device

        if hasattr(self._fan, "device_name"):
            self._name = self._fan.device_name
        if hasattr(self._fan, "power_switch"):
            self._is_on = self._fan.power_switch
        if hasattr(self._fan, "oscillation_toggle"):
            self._oscillating = self._fan.oscillation_toggle
        if hasattr(self._fan, "fan_speed"):
            self._current_speed = self._fan.fan_speed
        if hasattr(self._fan, "work_mode"):
            self._preset_mode = self._fan.work_mode
        if hasattr(self._fan, "work_mode_dict"):
            self._preset_modes = list(self._fan.work_mode_dict.values())
        if hasattr(self._fan, "max_fan_speed"):
            self.speed_range = (self._fan.min_fan_speed, self._fan.max_fan_speed)
        else:
            self.speed_range = (0,0)

    @property
    def name(self) -> str:
        """Return the display name of this fan."""
        return self._name

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
        return ranged_value_to_percentage(self.speed_range, self._current_speed)


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
        return int_states_in_range(self.speed_range)

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
        value_in_range = math.ceil(percentage_to_ranged_value(self.speed_range, percentage))
        await self._fan.set_fan_speed(self._api, value_in_range)
        self._current_speed = self._fan.fan_speed

    async def async_turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan."""
        await self._fan.turn_on(self._api)
        if percentage:
            await self._fan.set_fan_speed(self._api, percentage)
        if preset_mode:
            await self._fan.set_work_mode(self._api, preset_mode)
        await self.async_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._fan.turn_off(self._api)
        self._is_on = self._fan.power_switch

    async def async_oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        await self._fan.toggle_oscillation(self._api, oscillating)
        self._oscillating = self._fan.oscillation_toggle

    async def async_update(self):
        await self._fan.update(self._api)
        self._is_on = self._fan.power_switch
        if hasattr(self._fan, "oscillation_toggle"):
            self._oscillating = self._fan.oscillation_toggle
        if hasattr(self._fan, "fan_speed"):
            self._current_speed = self._fan.fan_speed
        self._preset_mode = self._fan.work_mode
