"""Example integration using DataUpdateCoordinator."""

from datetime import timedelta
import logging

import async_timeout
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from devices.thermometer.h5179 import H5179

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_DEVICE_ID
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from util.govee_api import GoveeAPI


_LOGGER = logging.getLogger(__name__)

class GoveeCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: GoveeAPI):
        super().__init__(
            hass,
            _LOGGER,
            name="Govee",
            config_entry=entry,
            update_interval=timedelta(seconds=30),
            always_update=True
        )
        self.api = api
        self._device = None

    async def _async_setup(self):
        name = self.config_entry.data[CONF_NAME].lower()
        device_id = self.config_entry.data[CONF_DEVICE_ID]

        match name:
            case "h7126":
                self._device = H7126(device_id)
                await self._device.update(self.api)
            case "h7102":
                self._device = H7102(device_id)
                await self._device.update(self.api)
            case "h5179":
                self._device = H5179(device_id)
                await self._device.update(self.api)

    async def _async_update_data(self):
        _LOGGER.error("Updating data for %s", self._device.sku)
        try:
            async with async_timeout.timeout(10):
                return await self._device.update(self.api)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

class GoveeThermometerCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: GoveeAPI):
        super().__init__(
            hass,
            _LOGGER,
            name="Govee",
            config_entry=entry,
            update_interval=timedelta(minutes=10),
            always_update=True
        )
        self.api = api
        self._device = None

    async def _async_setup(self):
        name = self.config_entry.data[CONF_NAME].lower()
        device_id = self.config_entry.data[CONF_DEVICE_ID]

        match name:
            case "h7126":
                self._device = H7126(device_id)
                await self._device.update(self.api)
            case "h7102":
                self._device = H7102(device_id)
                await self._device.update(self.api)
            case "h5179":
                self._device = H5179(device_id)
                await self._device.update(self.api)

    async def _async_update_data(self):
        _LOGGER.error("Updating data for %s", self._device.sku)
        try:
            async with async_timeout.timeout(10):
                return await self._device.update(self.api)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
