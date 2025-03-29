"""The Your Integration integration."""
import asyncio
import logging
from datetime import timedelta


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from util.govee_api import GoveeAPI

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "fan"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Your Integration component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Your Integration from a config entry."""
    api_key = entry.data[CONF_API_KEY]

    # Create API instance
    # Replace with your actual API client implementation
    api = GoveeAPI(api_key)

    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=lambda: update_data(api),
        update_interval=timedelta(seconds=60),
    )

    # Fetch initial data
    await coordinator.async_refresh()

    if not coordinator.data:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Set up platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def update_data(api: GoveeAPI):
    """Update data from API."""
    try:
        # Replace with your actual data fetching logic
        data = {}

        # Fetch temperature and humidity data
        sensor_data = await api.get_sensor_data()
        data["temperature"] = sensor_data.get("temperature")
        data["humidity"] = sensor_data.get("humidity")

        # Fetch main fan data
        main_fan = await api.get_fan_data("main")
        data["main_fan"] = main_fan

        # Fetch secondary fan data
        secondary_fan = await api.get_fan_data("secondary")
        data["secondary_fan"] = secondary_fan

        return data
    except Exception as err:
        raise UpdateFailed(f"Error communicating with API: {err}")

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
