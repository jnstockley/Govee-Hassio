"""Sensor platform for Your Integration."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from util.govee_api import GoveeAPI

from .const import DOMAIN, TEMPERATURE_SENSOR, HUMIDITY_SENSOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
):
    """Set up sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    entities = [
        TemperatureSensor(coordinator, entry, api),
        HumiditySensor(coordinator, entry, api),
    ]

    async_add_entities(entities)


class TemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = TEMP_FAHRENHEIT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, api: GoveeAPI):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{TEMPERATURE_SENSOR}"
        self._attr_name = "Temperature"
        self._entry = entry

    @property
    def native_value(self):
        """Return the temperature value."""
        if self.coordinator.data:
            return self.coordinator.data.get("temperature")
        return None

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Your Integration Device",
            "manufacturer": "Your Company",
            "model": "Temperature & Humidity Sensor",
        }


class HumiditySensor(CoordinatorEntity, SensorEntity):
    """Representation of a humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, api: GoveeAPI):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{HUMIDITY_SENSOR}"
        self._attr_name = "Humidity"
        self._entry = entry

    @property
    def native_value(self):
        """Return the humidity value."""
        if self.coordinator.data:
            return self.coordinator.data.get("humidity")
        return None

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Your Integration Device",
            "manufacturer": "Your Company",
            "model": "Temperature & Humidity Sensor",
        }