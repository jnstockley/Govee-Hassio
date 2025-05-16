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
from homeassistant.core import DOMAIN, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from util.govee_api import GoveeAPI

from custom_components.govee.coordinator import GoveeCoordinator, GoveeThermometerCoordinator

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
            coordinator = GoveeCoordinator(hass, entry, api)
            device = H7126(sensor["device_id"])
            await device.update(api)
            await coordinator.async_config_entry_first_refresh()
            async_add_entities(
                [GoveeOnlineSensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)] +
                [GoveeFilterLifeSensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)] +
                [GoveeAirQualitySensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)]
            )
        case "h7102":
            coordinator = GoveeCoordinator(hass, entry, api)
            device = H7102(sensor["device_id"])
            await device.update(api)
            await coordinator.async_config_entry_first_refresh()
            async_add_entities(
                GoveeOnlineSensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)
            )
        case "h5179":
            coordinator = GoveeThermometerCoordinator(hass, entry, api)
            device = H5179(sensor["device_id"])
            await device.update(api)
            async_add_entities(
                [GoveeOnlineSensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)] +
                [GoveeHumiditySensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)] +
                [GoveeTemperatureSensor(coordinator, idx, sensor, api, device) for idx, ent in enumerate(coordinator.data)]
            )
        case _:
            _LOGGER.warning("Unknown device name: %s", sensor["name"])


class GoveeOnlineSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee Online Sensor."""

    def __init__(self, coordinator, idx, sensor: dict, api: GoveeAPI, device: H5179 | H7126 | H7102) -> None:
        """
        Initialize an Govee Online Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        super().__init__(coordinator, context=idx)
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_online"
        self._api = api
        self._sensor = device
        self.idx = idx

        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        temp = self.coordinator.data[self.idx]["state"]
        _LOGGER.error("Online sensor state: %s", temp)
        self._attr_is_on = temp
        self.async_write_ha_state()


class GoveeFilterLifeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee Filter Life Sensor."""

    def __init__(self, coordinator, idx, sensor: dict, api: GoveeAPI, device: H7126) -> None:
        """
        Initialize an Govee Filter Life Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        super().__init__(coordinator, context=idx)
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_filter_life"
        self._api = api
        self._sensor = device
        self.idx = idx

        if hasattr(self._sensor, "filter_life"):
            self._filter_life = self._sensor.filter_life
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        temp = self.coordinator.data[self.idx]["state"]
        _LOGGER.error("Filter life sensor state: %s", temp)
        self._attr_is_on = temp
        self.async_write_ha_state()


class GoveeAirQualitySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee Air Quality Sensor."""

    def __init__(self, coordinator, idx, sensor: dict, api: GoveeAPI, device: H7126) -> None:
        """
        Initialize an Govee Fan.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        super().__init__(coordinator, context=idx)
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_air_quality"
        self._api = api
        self._sensor = device
        self.idx = idx

        if hasattr(self._sensor, "air_quality"):
            self._air_quality = self._sensor.air_quality
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

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


class GoveeHumiditySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee Humidity Sensor."""

    def __init__(self, coordinator, idx, sensor: dict, api: GoveeAPI, device: H5179) -> None:
        """
        Initialize an Govee Humidity Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        super().__init__(coordinator, context=idx)
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_humidity"
        self._api = api
        self._sensor = device
        self.idx = idx

        if hasattr(self._sensor, "humidity"):
            self._humidity = self._sensor.humidity
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        temp = self.coordinator.data[self.idx]["state"]
        _LOGGER.error("Humidity sensor state: %s", temp)
        self._attr_is_on = temp
        self.async_write_ha_state()


class GoveeTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee Temperature Sensor."""

    def __init__(self, coordinator, idx, sensor: dict, api: GoveeAPI, device: H5179) -> None:
        """
        Initialize an Govee Humidity Sensor.

        :param sensor: Dictionary containing sensor configuration
        :param api: GoveeAPI instance
        :param device: Device instance
        """
        super().__init__(coordinator, context=idx)
        _LOGGER.info(pformat(sensor))
        self._attr_unique_id = f"{sensor['device_id']}_temperature"
        self._api = api
        self._sensor = device
        self.idx = idx

        if hasattr(self._sensor, "temperature"):
            self._temperature = self._sensor.temperature
        if hasattr(self._sensor, "online"):
            self._online = self._sensor.online

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        temp = self.coordinator.data[self.idx]["state"]
        _LOGGER.error("Temperature sensor state: %s", temp)
        self._attr_is_on = temp
        self.async_write_ha_state()
