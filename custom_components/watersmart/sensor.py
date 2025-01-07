from homeassistant.components.sensor import SensorEntity
from datetime import datetime, timedelta
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Watersmart sensors from a config entry."""
    client = hass.data[DOMAIN][config_entry.entry_id]

    try:
        # Fetch data from the client
        usage_data = await client.usage()

        # Filter data for today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_data = [
            entry for entry in usage_data
            if datetime.utcfromtimestamp(entry["read_datetime"]) >= today_start
        ]

        # Log the filtered data
        _LOGGER.debug("Filtered sensor data for today: %s", daily_data)

        # Create a single sensor for the daily total
        sensor = WatersmartDailyTotalSensor(daily_data)
        async_add_entities([sensor], update_before_add=True)
    except Exception as e:
        _LOGGER.error("Error setting up Watersmart sensor: %s", e)


class WatersmartDailyTotalSensor(SensorEntity):
    """Representation of a Watersmart daily total sensor."""

    def __init__(self, daily_data):
        """Initialize the sensor with daily data."""
        self._daily_data = daily_data
        self._name = "Daily Water Usage"
        self._state = self.calculate_total()
        self._unit = "gal"
        self._unique_id = "watersmart_daily_total"
        self._icon = "mdi:water-outline"
        self._device_class = "water"
        self._state_class = "total_increasing"
        self._last_fetch = None

    def calculate_total(self):
        """Calculate the total gallons for the day."""
        return sum(entry["value"] for entry in self._daily_data)  # Sum gallons directly

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon for the sensor."""
        return self._icon

    @property
    def device_class(self):
        """Return the device class for the sensor."""
        return self._device_class

    @property
    def state_class(self):
        """Return the state class for the sensor."""
        return self._state_class

    @property
    def extra_state_attributes(self):
        """Return additional attributes for compatibility with energy dashboard."""
        return {
            "last_reset": datetime.utcnow().isoformat(),
        }

    async def async_update(self):
        """Fetch updated state data for the sensor."""
        now = datetime.utcnow()
        if (now - self._last_fetch).seconds >= 3600:  # Fetch data every hour
            self._last_fetch = now
            try:
                usage_data = await self._client.usage()
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                self._daily_data = [
                    entry for entry in usage_data
                    if datetime.utcfromtimestamp(entry["read_datetime"]) >= today_start
                ]
                self._state = self.calculate_total()
            except Exception as e:
                _LOGGER.error("Error fetching updated data: %s", e)
