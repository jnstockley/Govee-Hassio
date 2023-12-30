"""Platform for sensor integration."""
from __future__ import annotations

import logging

from custom_components.govee.devices import H5179
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_DEVICE_ID, CONF_API_KEY
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
})


log = logging.getLogger()


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""

    device_id = config[CONF_DEVICE_ID]
    api_key = config[CONF_API_KEY]

    add_entities([H5179TempSensor(device_id, api_key), H5179HumiditySensor(device_id, api_key)])


class H5179TempSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_unique_id = f"{CONF_DEVICE_ID}-temp"
    _attr_name = "Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device_id: str, api_key:str) -> None:
        self._device_id = device_id
        self._api_key = api_key

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = H5179.get_data(api_key=self._api_key, device_id=self._device_id).temperature


class H5179HumiditySensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Humidity"
    _attr_unique_id = f"{CONF_DEVICE_ID}-humidity"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device_id: str, api_key:str) -> None:
        self._device_id = device_id
        self._api_key = api_key

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = H5179.get_data(api_key=self._api_key, device_id=self._device_id).humidity
