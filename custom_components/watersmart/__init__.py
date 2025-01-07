import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Watersmart integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Watersmart from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Assume `client` is instantiated here based on entry data
    client = WatersmartClient(
        url=entry.data["url"],
        email=entry.data["email"],
        password=entry.data["password"],
    )

    hass.data[DOMAIN][entry.entry_id] = client

    try:
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    except Exception as e:
        _LOGGER.error("Error forwarding entry setups for Watersmart: %s", e)
        return False

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
