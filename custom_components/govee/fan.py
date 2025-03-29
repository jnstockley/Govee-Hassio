"""Fan platform for Your Integration."""
import logging

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN, MAIN_FAN, SECONDARY_FAN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up fans based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    entities = [
        MainFan(coordinator, entry, api),
        SecondaryFan(coordinator, entry, api),
    ]

    async_add_entities(entities)

class MainFan(CoordinatorEntity, FanEntity):
    """Representation of the main fan with full features."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED |
        FanEntityFeature.OSCILLATE |
        FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = ["auto", "normal", "sleep"]
    _speed_count = 3

    def __init__(self, coordinator, entry, api):
        """Initialize the fan."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{MAIN_FAN}"
        self._attr_name = "Main Fan"
        self._entry = entry
        self._api = api
        self._speed_list = ["low", "medium", "high"]

    @property
    def is_on(self):
        """Return true if the fan is on."""
        if self.coordinator.data and "main_fan" in self.coordinator.data:
            return self.coordinator.data["main_fan"]["power"]
        return False

    @property
    def current_direction(self):
        """Return the current direction of the fan."""
        return None  # Not supported by this fan

    @property
    def oscillating(self):
        """Return whether or not the fan is oscillating."""
        if self.coordinator.data and "main_fan" in self.coordinator.data:
            return self.coordinator.data["main_fan"].get("oscillation", False)
        return False

    @property
    def percentage(self):
        """Return the current speed percentage."""
        if not self.is_on:
            return 0

        if self.coordinator.data and "main_fan" in self.coordinator.data:
            current_speed = self.coordinator.data["main_fan"].get("speed", 1)
            speed_index = min(current_speed - 1, len(self._speed_list) - 1)
            return ordered_list_item_to_percentage(self._speed_list, self._speed_list[speed_index])
        return None

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self.coordinator.data and "main_fan" in self.coordinator.data:
            return self.coordinator.data["main_fan"].get("mode", "normal")
        return None

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_fan")},
            "name": "Main Fan",
            "manufacturer": "Your Company",
            "model": "Main Fan Model",
        }

    async def async_set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return

        # Convert percentage to speed
        speed_name = percentage_to_ordered_list_item(self._speed_list, percentage)
        speed_index = self._speed_list.index(speed_name) + 1

        await self._api.set_fan_state("main", speed=speed_index)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode of the fan."""
        if preset_mode in self.preset_modes:
            await self._api.set_fan_state("main", mode=preset_mode)
            await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage=None,
        preset_mode=None,
        **kwargs,
    ):
        """Turn on the fan."""
        data = {"power": True}

        if preset_mode is not None:
            data["mode"] = preset_mode

        if percentage is not None:
            if percentage > 0:
                speed_name = percentage_to_ordered_list_item(self._speed_list, percentage)
                data["speed"] = self._speed_list.index(speed_name) + 1

        await self._api.set_fan_state("main", **data)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn off the fan."""
        await self._api.set_fan_state("main", power=False)
        await self.coordinator.async_request_refresh()

    async def async_oscillate(self, oscillating):
        """Set oscillation."""
        await self._api.set_fan_state("main", oscillation=oscillating)
        await self.coordinator.async_request_refresh()

class SecondaryFan(CoordinatorEntity, FanEntity):
    """Representation of the secondary fan with limited features."""

    _attr_supported_features = FanEntityFeature.PRESET_MODE
    _attr_preset_modes = ["auto", "sleep"]

    def __init__(self, coordinator, entry, api):
        """Initialize the fan."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{SECONDARY_FAN}"
        self._attr_name = "Secondary Fan"
        self._entry = entry
        self._api = api

    @property
    def is_on(self):
        """Return true if the fan is on."""
        if self.coordinator.data and "secondary_fan" in self.coordinator.data:
            return self.coordinator.data["secondary_fan"]["power"]
        return False

    @property
    def percentage(self):
        """Return the current speed percentage."""
        # This fan doesn't support speed control
        return None

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self.coordinator.data and "secondary_fan" in self.coordinator.data:
            return self.coordinator.data["secondary_fan"].get("mode", "auto")
        return None

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_secondary_fan")},
            "name": "Secondary Fan",
            "manufacturer": "Your Company",
            "model": "Secondary Fan Model",
        }

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode of the fan."""
        if preset_mode in self.preset_modes:
            await self._api.set_fan_state("secondary", mode=preset_mode)
            await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage=None,
        preset_mode=None,
        **kwargs,
    ):
        """Turn on the fan."""
        data = {"power": True}

        if preset_mode is not None:
            data["mode"] = preset_mode

        await self._api.set_fan_state("secondary", **data)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn off the fan."""
        await self._api.set_fan_state("secondary", power=False)
        await self.coordinator.async_request_refresh()