import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .watersmart_client import WatersmartClient, WatersmartClientError

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Watersmart integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Watersmart from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config = entry.data
    client = WatersmartClient(
        url=config["url"],
        email=config["email"],
        password=config["password"],
    )

    try:
        await client._login()
    except WatersmartClientError as ex:
        _LOGGER.error("Failed to connect to Watersmart API: %s", ex)
        raise ConfigEntryNotReady from ex

    hass.data[DOMAIN][entry.entry_id] = client

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.data[DOMAIN][entry.entry_id]._close()
    hass.data[DOMAIN].pop(entry.entry_id)

    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    return True
