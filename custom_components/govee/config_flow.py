"""Config flow for Govee integration."""

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


class GoveeConfigFlow(config_entries.ConfigFlow, domain="govee"):
    """Example config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def _show_setup_form(self, errors: dict[str, str] | None = None) -> ConfigFlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Required(CONF_API_KEY): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        self._async_abort_entries_match(
            {
                CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                CONF_API_KEY: user_input[CONF_API_KEY],
                CONF_NAME: user_input[CONF_NAME],
            }
        )

        errors = {}

        device_id = user_input.get(CONF_DEVICE_ID)
        api_key = user_input.get(CONF_API_KEY)
        name = user_input.get(CONF_NAME).lower()

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

        """device = AdGuardHome(
            user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            username=username,
            password=password,
            tls=user_input[CONF_SSL],
            verify_ssl=user_input[CONF_VERIFY_SSL],
            #session=session,
        )"""

        await device.update(api)

        return self.async_create_entry(
            title="Govee",
            data={
                CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                CONF_API_KEY: user_input.get(CONF_API_KEY),
                CONF_NAME: user_input[CONF_NAME],
            },
        )
