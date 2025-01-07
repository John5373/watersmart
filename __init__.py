# Create Home Assistant Integration
# File: custom_components/watersmart/__init__.py

import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .watersmart import WaterSmart

DOMAIN = "watersmart"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WaterSmart from a config entry."""
    username = entry.data.get("username")
    password = entry.data.get("password")

    watersmart = WaterSmart(username, password)

    async def async_update_data():
        try:
            return await watersmart.get_usage()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="watersmart",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

# File: custom_components/watersmart/sensor.py
from homeassistant.helpers.entity import Entity
from . import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WaterSmart sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    sensors = [WaterSmartSensor(coordinator, "daily_usage"), WaterSmartSensor(coordinator, "monthly_usage")]
    async_add_entities(sensors)

class WaterSmartSensor(Entity):
    def __init__(self, coordinator, sensor_type):
        self.coordinator = coordinator
        self.type = sensor_type

    @property
    def name(self):
        return f"WaterSmart {self.type}"

    @property
    def state(self):
        return self.coordinator.data.get(self.type)

    async def async_update(self):
        await self.coordinator.async_request_refresh()
