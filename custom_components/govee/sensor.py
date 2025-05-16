"""Govee Sensor Platform for Home Assistant."""

import logging
from pprint import pformat

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from devices.thermometer.h5179 import H5179
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME, UnitOfTemperature
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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

    :param entry: The config entry for the Govee device.
    :param async_add_entities: Callback to add entities.
    :return: None
    """
    # Add devices
    _LOGGER.info("Setting up fan entry: %s", entry.data)

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
            async_add_entities(
                [
                    GoveeOnlineSensor(sensor, api, device),
                    GoveeFilterLifeSensor(sensor, api, device),
                    GoveeAirQualitySensor(sensor, api, device),
                ]
            )
        case "h7102":
            device = H7102(sensor["device_id"])
            await device.update(api)
            async_add_entities([GoveeOnlineSensor(sensor, api, device)])
        case "h5179":
            device = H5179(sensor["device_id"])
            await device.update(api)
            async_add_entities(
                [
                    GoveeOnlineSensor(sensor, api, device),
                    GoveeHumiditySensor(sensor, api, device),
                    GoveeTemperatureSensor(sensor, api, device),
                ]
            )
        case _:
            _LOGGER.warning("Unknown device name: %s", sensor["name"])


class GoveeOnlineSensor(SensorEntity):
    """Representation of a Govee Online Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device: H5179 | H7126 | H7102) -> None:
        """
        Initialize an Govee Online Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_online"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.

        :return: bool
        """
        return self._online

    @property
    def name(self) -> str:
        """
        Return the display name of this sensor.

        :return: str
        """
        return "Status"

    @property
    def device_class(self) -> str:
        """
        Return the device class of this sensor.

        :return: str
        """
        return SensorDeviceClass.ENUM

    @property
    def options(self) -> list[str]:
        """
        Return the list of options for the sensor.

        :return: list[str]
        """
        return ["Online", "Offline", "Unknown"]

    @property
    def native_value(self) -> str:
        """
        Return the status of the sensor.

        :return: str
        """
        if self._online:
            return "Online"
        if self._sensor.online is False:
            return "Offline"
        return "Unknown"

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return device information for the sensor.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku,
        )

    async def async_update(self) -> None:
        """
        Update the sensor state.

        :return: None
        """
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online


class GoveeFilterLifeSensor(SensorEntity):
    """Representation of a Govee Filter Life Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device: H7126) -> None:
        """
        Initialize an Govee Filter Life Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_filter_life"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "filter_life"):
            self._filter_life = self._sensor.filter_life
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.

        :return: bool
        """
        return self._online

    @property
    def name(self) -> str:
        """
        Return the display name of this sensor.

        :return: str
        """
        return "Filter Life"

    @property
    def device_class(self) -> str:
        """
        Return the device class of this sensor.

        :return: str
        """
        return SensorDeviceClass.POWER_FACTOR

    @property
    def native_value(self) -> int:
        """
        Return the filter life value.

        :return: int
        """
        return self._filter_life

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return device information for the sensor.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku,
        )

    async def async_update(self) -> None:
        """
        Update the sensor state.

        :return: None
        """
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "filter_life"):
            self._filter_life = self._sensor.filter_life


class GoveeAirQualitySensor(SensorEntity):
    """Representation of a Govee Air Quality Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device: H7126) -> None:
        """
        Initialize an Govee Fan.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_air_quality"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "air_quality"):
            self._air_quality = self._sensor.air_quality
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.

        :return: bool
        """
        return self._online

    @property
    def name(self) -> str:
        """
        Return the display name of this sensor.

        :return: str
        """
        return "Air Quality"

    @property
    def device_class(self) -> str:
        """
        Return the device class of this sensor.

        :return: str
        """
        return SensorDeviceClass.AQI

    @property
    def native_value(self) -> int:
        """
        Return the air quality value.

        :return: int
        """
        return self._air_quality

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return device information for the sensor.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku,
        )

    async def async_update(self) -> None:
        """
        Update the sensor state.

        :return: None
        """
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "air_quality"):
            self._air_quality = self._sensor.air_quality


class GoveeHumiditySensor(SensorEntity):
    """Representation of a Govee Humidity Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device: H5179) -> None:
        """
        Initialize an Govee Humidity Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_humidity"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "humidity"):
            self._humidity = self._sensor.humidity
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.

        :return: bool
        """
        return self._online

    @property
    def name(self) -> str:
        """
        Return the display name of this sensor.

        :return: str
        """
        return "Humidity"

    @property
    def device_class(self) -> str:
        """
        Return the device class of this sensor.

        :return: str
        """
        return SensorDeviceClass.HUMIDITY

    @property
    def native_unit_of_measurement(self) -> str:
        """
        Return the unit of measurement for the sensor.

        :return: str
        """
        return "%"

    @property
    def native_value(self) -> float:
        """
        Return the air quality value.

        :return: int
        """
        return self._humidity

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return device information for the sensor.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku,
        )

    async def async_update(self) -> None:
        """
        Update the sensor state.

        :return: None
        """
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "humidity"):
            self._humidity = self._sensor.humidity


class GoveeTemperatureSensor(SensorEntity):
    """Representation of a Govee Temperature Sensor."""

    def __init__(self, sensor: dict, api: GoveeAPI, device: H5179) -> None:
        """
        Initialize an Govee Humidity Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_temperature"
        self._api = api
        self._sensor = device

        if hasattr(self._sensor, "temperature"):
            self._temperature = self._sensor.temperature
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.

        :return: bool
        """
        return self._online

    @property
    def name(self) -> str:
        """
        Return the display name of this sensor.

        :return: str
        """
        return "Temperature"

    @property
    def device_class(self) -> str:
        """
        Return the device class of this sensor.

        :return: str
        """
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str:
        """
        Return the unit of measurement for the sensor.

        :return: str
        """
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_value(self) -> float:
        """
        Return the air quality value.

        :return: int
        """
        return self._temperature

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return device information for the sensor.

        :return: DeviceInfo
        """
        identifiers = {
            (DOMAIN, self._sensor.device_id),
        }
        return DeviceInfo(
            identifiers=identifiers,
            name=self._sensor.device_name,
            manufacturer="Govee",
            model=self._sensor.sku,
            model_id=self._sensor.sku,
        )

    async def async_update(self) -> None:
        """
        Update the sensor state.

        :return: None
        """
        await self._sensor.update(self._api)
        if hasattr(self._sensor, "temperature"):
            self._temperature = self._sensor.temperature
