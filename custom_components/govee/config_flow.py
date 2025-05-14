"""Config flow for Govee integration."""
import asyncio
import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from devices.air_purifier.h7126 import H7126
from devices.fan.h7102 import H7102
from devices.thermometer.h5179 import H5179
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME, CONF_DEVICES
from homeassistant.core import callback
from util.govee_api import GoveeAPI

supported_skus = ['H7126', 'H7102', 'H5179']

_LOGGER = logging.getLogger(__name__)


class GoveeConfigFlow(config_entries.ConfigFlow, domain="govee"):
    """Config flow for Govee."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api_key = None
        self.discovered_devices = None
        self.selected_devices = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step - API key entry."""
        errors = {}

        # Handle the case when called with pre-existing data (for continuing the flow)
        if user_input is not None and "selected_devices" in user_input:
            self.api_key = user_input[CONF_API_KEY]
            self.discovered_devices = user_input.get("discovered_devices", [])
            self.selected_devices = user_input.get("selected_devices", [])
            return await self.async_step_add_device()

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

                if not self.discovered_devices:
                    errors["base"] = "no_devices_found"
                else:
                    return await self.async_step_select_devices()
            except Exception as e:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Error connecting to Govee API", exc_info=e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): cv.string,
            }),
            errors=errors,
        )

    async def async_step_select_devices(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle device selection step."""
        errors = {}

        if user_input is not None:
            selected_devices = user_input[CONF_DEVICES]

            if not selected_devices:
                errors["base"] = "no_devices_selected"
            else:
                # Store selected devices for processing
                self.selected_devices = selected_devices

                # Proceed to device setup step
                return await self.async_step_add_device()

        # Create a list of devices for selection
        device_labels = {
            d["device"]: f"{d['deviceName']} - {d['sku']} ({d['device']})"
            for d in self.discovered_devices
        }

        return self.async_show_form(
            step_id="select_devices",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICES): cv.multi_select(device_labels),
            }),
            errors=errors,
        )

    async def async_step_add_device(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Process one device at a time."""
        if not self.selected_devices:
            # No more devices to add, we're done
            return self.async_abort(reason="devices_added")

        # Pop the first device from our list
        device_id = self.selected_devices[0]
        device_info = next((d for d in self.discovered_devices if d["device"] == device_id), None)

        if not device_info:
            # Skip invalid devices
            self.selected_devices.pop(0)
            if self.selected_devices:
                # Try the next device
                return await self.async_step_add_device()
            else:
                # No more devices
                return self.async_abort(reason="devices_added")

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

        # Remove this device from the list
        self.selected_devices.pop(0)

        # If we have more devices to add, move to the next one
        if self.selected_devices:
            result = self.async_create_entry(title=title, data=data)
            self.hass.async_create_task(self._handle_next_device())
            return result
        else:
            # Return entry for the last device
            return self.async_create_entry(title=title, data=data)

    async def _handle_next_device(self):
        """Handle adding the next device."""
        flow = await self.hass.config_entries.flow.async_init(
            "govee",
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_API_KEY: self.api_key,
                "discovered_devices": self.discovered_devices,
                "selected_devices": self.selected_devices
            }
        )

    @callback
    def _async_schedule_add_next_device(self):
        """Schedule adding the next device after a short delay."""
        async def _add_next_device(_):
            """Add the next device."""
            if self.hass:
                # Create a new flow to add the next device
                await self.hass.config_entries.flow.async_init(
                    "govee",
                    context={"source": config_entries.SOURCE_USER},
                    data={
                        "api_key": self.api_key,
                        "devices": self.selected_devices,
                    },
                )

        # Schedule task to run soon but not immediately
        self.hass.async_create_task(_add_next_device(None))

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
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

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
            _LOGGER.error("Error connecting to Govee API", exc_info=e)
            return await self._show_setup_form(errors)