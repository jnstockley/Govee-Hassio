"""Platform for fan integration."""

from __future__ import annotations

import logging
import math
from pprint import pformat
from typing import TYPE_CHECKING

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from homeassistant.components.fan import PLATFORM_SCHEMA, FanEntity, FanEntityFeature
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME
from homeassistant.core import DOMAIN
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)
from homeassistant.util.scaling import int_states_in_range
from util.govee_api import GoveeAPI

_LOGGER = logging.getLogger("govee")

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_NAME): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the Govee sensor platform from a config entry.

    :param entry: Config entry.
    :param async_add_entities: Callback to add entities.
    :return: None
    """
    # Add devices
    _LOGGER.info("Setting up fan entry: %s", entry.data)

    fan = {
        "device_id": entry.data[CONF_DEVICE_ID],
        "api_key": entry.data[CONF_API_KEY],
        "name": entry.data[CONF_NAME],
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

    def __init__(self, fan: dict, api: GoveeAPI, device: H7126 | H7102) -> None:
        """
        Initialize the fan entity.

        :param fan: Fan configuration dictionary
        :param api: Govee API instance
        :param device: Device instance (H7126 or H7102)
        """
        _LOGGER.info(pformat(fan))
        self._attr_unique_id = fan["device_id"]
        self._api = api
        self._fan = device

        if hasattr(self._fan, "online"):
            self._online = self._fan.online
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
            self.speed_range = (0, 0)

    @property
    def name(self) -> str:
        """
        Return the display name of this fan.

        :return: str
        """
        return self._name

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.

        :return: bool
        """
        return self._online

    @property
    def is_on(self) -> bool:
        """
        Return True if the fan is on.

        :return: bool
        """
        return self._is_on

    @property
    def oscillating(self) -> bool:
        """
        Return True if the fan is oscillating.

        :return: bool
        """
        return self._oscillating

    @property
    def percentage(self) -> int:
        """
        Return the current speed of the fan as a percentage.

        :return: int
        """
        return ranged_value_to_percentage(self.speed_range, self._current_speed)

    @property
    def preset_mode(self) -> str:
        """
        Return the current preset mode of the fan.

        :return: str
        """
        return self._preset_mode

    @property
    def preset_modes(self) -> list[str]:
        """
        Return the list of available preset modes.

        :return: list[str]
        """
        return self._preset_modes

    @property
    def speed_count(self) -> int:
        """
        Return the number of speed settings available for the fan.

        :return: int
        """
        return int_states_in_range(self.speed_range)

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return the device info for the fan.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._fan.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._fan.device_name,
            manufacturer="Govee",
            model=self._fan.sku,
            model_id=self._fan.sku,
        )

    @property
    def supported_features(self) -> FanEntityFeature:
        """
        Return the supported features of the fan.

        :return: Supported features
        """
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
        """
        Set the preset mode of the fan.

        :param preset_mode: Preset mode to set.
        :return: None
        """
        await self._fan.set_work_mode(self._api, preset_mode)
        self._preset_mode = self._fan.work_mode

    async def async_set_percentage(self, percentage: int) -> None:
        """
        Set the speed of the fan.

        :param percentage: Speed percentage (0-100).
        :return: None
        """
        value_in_range = math.ceil(percentage_to_ranged_value(self.speed_range, percentage))
        await self._fan.set_fan_speed(self._api, value_in_range)
        self._current_speed = self._fan.fan_speed

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None) -> None:
        """
        Turn on the fan with optional percentage and preset mode.

        :param percentage: Optional speed percentage (0-100).
        :param preset_mode: Optional preset mode.
        :return: None
        """
        await self._fan.turn_on(self._api)
        if percentage:
            await self._fan.set_fan_speed(self._api, percentage)
        if preset_mode:
            await self._fan.set_work_mode(self._api, preset_mode)
        await self.async_update()

    async def async_turn_off(self) -> None:
        """
        Turn off the fan.

        :return: None
        """
        await self._fan.turn_off(self._api)
        self._is_on = self._fan.power_switch

    async def async_oscillate(self, oscillating: bool) -> None:
        """
        Set the oscillation state of the fan.

        :param oscillating: True to turn on oscillation, False to turn off
        :return: None
        """
        await self._fan.toggle_oscillation(self._api, oscillating)
        self._oscillating = self._fan.oscillation_toggle

    async def async_update(self) -> None:
        """
        Update the fan state.

        :return: None
        """
        await self._fan.update(self._api)
        self._is_on = self._fan.power_switch
        if hasattr(self._fan, "oscillation_toggle"):
            self._oscillating = self._fan.oscillation_toggle
        if hasattr(self._fan, "fan_speed"):
            self._current_speed = self._fan.fan_speed
        self._preset_mode = self._fan.work_mode
