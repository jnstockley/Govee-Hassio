'''
List of Sensors
1. Online (All)
2. Filter Life (H7126)
3. Air Quality (H7126)
'''
import logging
from pprint import pformat

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from devices.thermometer.h5179 import H5179
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_API_KEY, CONF_DEVICE_ID
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA, SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant, DOMAIN
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from util.govee_api import GoveeAPI

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
    """Set up the Govee fan platform."""
    # Add devices
    _LOGGER.info(f"Setting up fan entry: {entry.data}")

    sensor = {
        "device_id": entry.data[CONF_DEVICE_ID],
        "api_key": entry.data[CONF_API_KEY],
        "name": entry.data[CONF_NAME],
    }

    api = GoveeAPI(sensor["api_key"])

    match sensor["name"].lower():
        case "h7126":
            device = H7126(sensor["device_id"])
            await device.update(api)
            async_add_entities([
                GoveeOnlineSensor(sensor, api, device),
                GoveeFilterLifeSensor(sensor, api, device),
                GoveeAirQualitySensor(sensor, api, device)
            ])
        case "h7102":
            device = H7102(sensor["device_id"])
            await device.update(api)
            async_add_entities([GoveeOnlineSensor(sensor, api, device)])
        case "h5179":
            device = H5179(sensor["device_id"])
            await device.update(api)
            async_add_entities([GoveeOnlineSensor(sensor, api, device)])
        case _:
            _LOGGER.warning(f"Unknown device name: {sensor['name']}")



class GoveeOnlineSensor(SensorEntity):
    """Representation of a Govee Online Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device) -> None:
        """Initialize an Govee Fan."""
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor["device_id"]}_online"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        return "Status"

    @property
    def device_class(self):
        return SensorDeviceClass.ENUM

    @property
    def options(self):
        return ["Online", "Offline", "Unknown"]

    @property
    def native_value(self):
        if self._online:
            return "Online"
        elif self._sensor.online is False:
            return "Offline"
        else:
            return "Unknown"

    @property
    def device_info(self) -> DeviceInfo:
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku
        )

    async def async_update(self):
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online


class GoveeFilterLifeSensor(SensorEntity):
    """Representation of a Govee Filter Life Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device) -> None:
        """Initialize an Govee Fan."""
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor["device_id"]}_filter_life"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "filter_life"):
            self._filter_life = self._sensor.filter_life

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        return "Filter Life"

    @property
    def device_class(self):
        return SensorDeviceClass.POWER_FACTOR

    @property
    def native_value(self):
        return self._filter_life

    @property
    def device_info(self) -> DeviceInfo:
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku
        )

    async def async_update(self):
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "filter_life"):
            self._filter_life = self._sensor.filter_life


class GoveeAirQualitySensor(SensorEntity):
    """Representation of a Govee Air Quality Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device) -> None:
        """Initialize an Govee Fan."""
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor["device_id"]}_air_quality"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "air_quality"):
            self._air_quality = self._sensor.air_quality

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        return "Air Quality"

    @property
    def device_class(self):
        return SensorDeviceClass.AQI

    @property
    def native_value(self):
        return self._air_quality

    @property
    def device_info(self) -> DeviceInfo:
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku
        )

    async def async_update(self):
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "air_quality"):
            self._air_quality = self._sensor.air_quality
