import logging
from datetime import datetime

from homeassistant.const import CONF_DEVICE_ID, CONF_API_KEY, CONF_NAME, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import ConfigType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)

from custom_components.govee_v2.devices.H5179 import H5179

log = logging.getLogger()

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_NAME): cv.string,
})


def setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallback,
                   discovery_info: DiscoveryInfoType | None = None) -> None:
    device = config[CONF_DEVICE_ID]
    sku = config[CONF_NAME]
    api_key = config[CONF_API_KEY]



    add_entities([GoveeTemperature(device, sku, api_key), GoveeHumidity(device, sku, api_key)])


class GoveeTemperature(SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_last_reset = datetime.now()
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_native_value = -999
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_unique_id = f"{CONF_DEVICE_ID}-temp"
    _attr_name = "Temperature"

    def __init__(self, device: str, sku: str, api_key: str) -> None:
        self.device_id = device
        self.sku = sku
        self.api_key = api_key

    def update(self):
        device = H5179(api_key=self.api_key, sku=self.sku, device=self.device_id).update()
        self._attr_native_value = device.temperature
        _attr_last_reset = datetime.now()


class GoveeHumidity(SensorEntity):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_last_reset = datetime.now()
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_value = -1
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_unique_id = f"{CONF_DEVICE_ID}-humidity"
    _attr_name = "Humidity"

    def __init__(self, device: str, sku: str, api_key: str) -> None:
        self.device_id = device
        self.sku = sku
        self.api_key = api_key

    def update(self):
        device = H5179(api_key=self.api_key, sku=self.sku, device=self.device_id).update()
        self._attr_native_value = device.humidity
        _attr_last_reset = datetime.now()
