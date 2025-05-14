"""Platform for climate integration."""
from __future__ import annotations

import logging
from pprint import pformat

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from devices.thermometer.h5179 import H5179
from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_DEVICE_ID,
    CONF_NAME,
    PRECISION_TENTHS,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from util.govee_api import GoveeAPI

from custom_components.govee.const import DOMAIN

_LOGGER = logging.getLogger("govee")

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_NAME): cv.string,
})


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Govee climate platform from a config entry."""
    _LOGGER.info(f"Setting up climate entry: {entry.data}")

    thermometer = {
        "device_id": entry.data[CONF_DEVICE_ID],
        "api_key": entry.data[CONF_API_KEY],
        "name": entry.data[CONF_NAME],
    }

    api = GoveeAPI(thermometer["api_key"])

    match thermometer["name"].lower():
        case "h5179":
            device = H5179(thermometer["device_id"])
            await device.update(api)
        case _:
            device = None

    async_add_entities([GoveeThermometer(thermometer, api, device)])

class GoveeThermometer(ClimateEntity):
    """Representation of a Govee Fan."""

    def __init__(self, thermometer: dict, api: GoveeAPI, device: H5179):
        """Initialize the Govee Fan."""
        _LOGGER.info(pformat(thermometer))
        self._attr_unique_id = thermometer["device_id"]
        self._api = api
        self._thermometer = device

        if hasattr(self._thermometer, "device_name"):
            self._name = self._thermometer.device_name
        if hasattr(self._thermometer, "temperature"):
            self._temperature = self._thermometer.temperature
        if hasattr(self._thermometer, "humidity"):
            self._humidity = self._thermometer.humidity

    @property
    def name(self) -> str:
        """Return the display name of this fan."""
        return self._name

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._humidity

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the device."""
        return UnitOfTemperature.FAHRENHEIT

    @property
    def precision(self):
        return PRECISION_TENTHS

    @property
    def hvac_mode(self):
        return None

    @property
    def hvac_modes(self):
        return None

    @property
    def device_info(self) -> DeviceInfo:
        identifiers = {
            (DOMAIN, self._thermometer.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._thermometer.device_name,
            manufacturer="Govee",
            model=self._thermometer.sku,
            model_id=self._thermometer.sku
        )

    @property
    def supported_features(self):
        """Return the supported features."""
        features = ClimateEntityFeature(0)
        features |= ClimateEntityFeature.TARGET_HUMIDITY
        return features

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    async def async_set_humidity(self, humidity):
        """Set new target humidity."""
        await self._thermometer.update(self._api)
        await self.async_update()

    async def async_update(self):
        await self._thermometer.update(self._api)
        if hasattr(self._thermometer, "temperature"):
            self._temperature = self._thermometer.temperature
        if hasattr(self._thermometer, "humidity"):
            self._humidity = self._thermometer.humidity
