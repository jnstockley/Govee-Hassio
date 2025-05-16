"""Config flow for Govee integration."""
import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from devices.thermometer.h5179 import H5179
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME
from util.govee_api import GoveeAPI

supported_skus = ["H7126", "H7102", "H5179"]

_LOGGER = logging.getLogger(__name__)


class GoveeConfigFlow(config_entries.ConfigFlow, domain="govee"):
    """Config flow for Govee."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api_key = None
        self.discovered_devices = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step - API key entry."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            self.api_key = api_key

            try:
                # Call API to get devices
                api = GoveeAPI(api_key)
                devices = await api.get_devices()

                # Filter devices to only include supported devices
                self.discovered_devices = [
                    device for device in devices if device["sku"] in supported_skus
                ]

                # Filter out devices that are already configured
                current_ids = {
                    entry.unique_id for entry in self._async_current_entries()
                    if entry.unique_id is not None
                }

                self.discovered_devices = [
                    device for device in self.discovered_devices
                    if device["device"] not in current_ids
                ]

                if not self.discovered_devices:
                    errors["base"] = "no_devices_found"
                else:
                    return await self.async_step_select_device()
            except Exception as e:
                errors["base"] = "cannot_connect"
                _LOGGER.exception("Error connecting to Govee API", exc_info=e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): cv.string,
            }),
            errors=errors,
        )

    async def async_step_select_device(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle single device selection step."""
        errors = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device_info = next((d for d in self.discovered_devices if d["device"] == device_id), None)

            if not device_info:
                errors["base"] = "invalid_device_selected"
            else:
                # Set unique ID for this device
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                # Map SKU to device type
                device_type = device_info["sku"].lower()

                # Create entry for this device
                title = f"Govee {device_info['deviceName']}"
                data = {
                    CONF_DEVICE_ID: device_id,
                    CONF_API_KEY: self.api_key,
                    CONF_NAME: device_type,
                }

                return self.async_create_entry(title=title, data=data)

        # Create a list of devices for selection
        device_options = {
            d["device"]: f"{d['deviceName']} - {d['sku']} ({d['device']})"
            for d in self.discovered_devices
        }

        if not device_options:
            return self.async_abort(reason="no_unconfigured_devices")

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): vol.In(device_options),
            }),
            errors=errors,
        )

    async def _show_setup_form(self, errors: dict[str, str] | None = None) -> ConfigFlowResult:
        """Show the manual setup form to the user."""
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Required(CONF_API_KEY): cv.string,
                    vol.Required(CONF_NAME, default="h7126"): vol.In(["h7126", "h7102", "h5179"]),
                }
            ),
            errors=errors or {},
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle manual device configuration."""
        if user_input is None:
            return await self._show_setup_form()

        errors = {}

        device_id = user_input.get(CONF_DEVICE_ID)
        api_key = user_input.get(CONF_API_KEY)
        name = user_input.get(CONF_NAME).lower()

        try:
            # Check if this device is already configured
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            api = GoveeAPI(api_key)

            match name:
                case "h7126":
                    device = H7126(device_id)
                case "h7102":
                    device = H7102(device_id)
                case "h5179":
                    device = H5179(device_id)
                case _:
                    errors["base"] = "unknown_device"
                    return await self._show_setup_form(errors)

            await device.update(api)

            return self.async_create_entry(
                title=f"Govee {device.device_name}",
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_API_KEY: api_key,
                    CONF_NAME: name,
                },
            )
        except Exception as e:
            errors["base"] = "cannot_connect"
            _LOGGER.exception("Error connecting to Govee API", exc_info=e)
            return await self._show_setup_form(errors)
