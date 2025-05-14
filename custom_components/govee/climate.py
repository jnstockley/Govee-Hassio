"""Platform for climate integration."""

from __future__ import annotations

import logging
from pprint import pformat
from typing import TYPE_CHECKING

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from devices.thermometer.h5179 import H5179
from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_DEVICE_ID,
    CONF_NAME,
    PRECISION_TENTHS,
    UnitOfTemperature,
)
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

from util.govee_api import GoveeAPI

from custom_components.govee.const import DOMAIN

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
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the Govee sensor platform from a config entry.

    :param entry: Config entry.
    :param async_add_entities: Callback to add entities.
    :return: None
    """
    _LOGGER.info("Setting up climate entry: %s", entry.data)

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

    def __init__(self, thermometer: dict, api: GoveeAPI, device: H5179) -> None:
        """
        Initialize the Govee thermometer.

        :param thermometer: Dictionary containing device configuration
        :param api: GoveeAPI instance
        :param device: H5179 device instance
        """
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
        """
        Return the name of the device.

        :return: str
        """
        return self._name

    @property
    def current_humidity(self) -> float:
        """
        Return the current humidity.

        :return: float
        """
        return self._humidity

    @property
    def temperature_unit(self) -> str:
        """
        Return the unit of measurement used by the device.

        :return: str
        """
        return UnitOfTemperature.FAHRENHEIT

    @property
    def precision(self) -> float:
        """
        Return the precision of the temperature measurement.

        :return: float
        """
        return PRECISION_TENTHS

    @property
    def hvac_mode(self) -> None:
        """
        Return the current HVAC operation mode.

        :return: None
        """
        return None

    @property
    def hvac_modes(self) -> None:
        """
        Return the list of available HVAC operation modes.

        :return:
        """
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return the device info.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._thermometer.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._thermometer.device_name,
            manufacturer="Govee",
            model=self._thermometer.sku,
            model_id=self._thermometer.sku,
        )

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """
        Return the list of supported features.

        :return: ClimateEntityFeature
        """
        features = ClimateEntityFeature(0)
        features |= ClimateEntityFeature.TARGET_HUMIDITY
        return features

    @property
    def current_temperature(self) -> float:
        """
        Return the current temperature.

        :return: float
        """
        return self._temperature

    async def async_set_humidity(self, humidity: float) -> None:
        """
        Set the target humidity.

        :param humidity: The target humidity to set
        :return: None
        """
        self._humidity = humidity
        await self._thermometer.update(self._api)
        await self.async_update()

    async def async_update(self) -> None:
        """
        Update the device state.

        :return: None
        """
        await self._thermometer.update(self._api)
        if hasattr(self._thermometer, "temperature"):
            self._temperature = self._thermometer.temperature
        if hasattr(self._thermometer, "humidity"):
            self._humidity = self._thermometer.humidity
