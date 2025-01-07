from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WaterSmart sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    sensors = [
        WaterSmartSensor(coordinator, "daily_usage"),
        WaterSmartSensor(coordinator, "monthly_usage"),
        WaterSmartSensor(coordinator, "hourly_usage"),
    ]
    async_add_entities(sensors)

class WaterSmartSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self.type = sensor_type

    @property
    def name(self):
        return f"WaterSmart {self.type}"

    @property
    def state(self):
        return self.coordinator.data.get(self.type)

    @property
    def unique_id(self):
        return f"watersmart_{self.type}"

    @property
    def device_class(self):
        return "water"

    async def async_update(self):
        await self.coordinator.async_request_refresh()
