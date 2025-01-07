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
