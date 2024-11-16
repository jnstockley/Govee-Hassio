import logging
from datetime import timedelta

import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_DEVICE_ID,
    CONF_NAME,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.govee.devices.H5179 import H5179, H5179_Device

log = logging.getLogger()

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_NAME): cv.string,
})


async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback,
                               discovery_info: DiscoveryInfoType | None = None) -> None:
    device_id = config[CONF_DEVICE_ID]
    sku = config[CONF_NAME]
    api_key = config[CONF_API_KEY]

    device = H5179(api_key=api_key, sku=sku, device=device_id)

    coordinator = MyCoordinator(hass, device)

    await coordinator.async_config_entry_first_refresh()

    new_device = await device.update()

    async_add_entities(
        [GoveeTemperature(device_id, sku, api_key, new_device), GoveeHumidity(device_id, sku, api_key, new_device)])


class MyCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, device):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            log,
            # Name of the data. For logging purposes.
            name="Govee W-Fi Thermometer",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=5),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True
        )

        self.device = device

    async def _async_update_data(self):
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                return await self.device.update()
        except Exception as e:
            log.error(f"Failed to update device: {e}")
            raise e


class GoveeTemperature(SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_native_value = -999
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_unique_id = f"{CONF_DEVICE_ID}-temp"
    _attr_name = "Temperature"

    def __init__(self, device_id: str, sku: str, api_key: str, device: H5179_Device) -> None:
        log.info(f"Setting up temperature: {device_id} - {sku} - {api_key}")
        self.device_id = device_id
        self.sku = sku
        self.api_key = api_key
        self._attr_native_value = device.temperature

    async def async_update(self) -> None:
        log.info(f"Updating temperature for device {self.device_id} - {self.sku}")
        device = await H5179(api_key=self.api_key, sku=self.sku, device=self.device_id).update()
        log.info(f"Device: {device}")
        self._attr_native_value = device.temperature


class GoveeHumidity(SensorEntity):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_value = -1
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_unique_id = f"{CONF_DEVICE_ID}-humidity"
    _attr_name = "Humidity"

    def __init__(self, device_id: str, sku: str, api_key: str, device: H5179_Device) -> None:
        log.info(f"Setting up humidity: {device_id} - {sku} - {api_key}")
        self.device_id = device_id
        self.sku = sku
        self.api_key = api_key
        self._attr_native_value = device.temperature

    async def async_update(self) -> None:
        log.info(f"Updating humidity for device {self.device_id} - {self.sku}")
        device = await H5179(api_key=self.api_key, sku=self.sku, device=self.device_id).update()
        log.info(f"Device: {device}")
        self._attr_native_value = device.humidity
