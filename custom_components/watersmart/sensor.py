from homeassistant.components.sensor import SensorEntity
from datetime import datetime
from homeassistant.helpers.service import async_register_admin_service
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Watersmart sensors from a config entry."""
    client = hass.data[DOMAIN][config_entry.entry_id]

    try:
        # Fetch data from the client
        usage_data = await client.usage()

        # Filter data starting from today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_data = [
            entry for entry in usage_data
            if datetime.utcfromtimestamp(entry["read_datetime"]) >= today_start
        ]

        # Log the filtered data
        _LOGGER.debug("Filtered sensor data for today: %s", daily_data)

        # Create sensors
        daily_total_sensor = WatersmartDailyTotalSensor(daily_data, client)
        raw_data_sensor = WatersmartRawDataSensor(client)

        async_add_entities([daily_total_sensor, raw_data_sensor], update_before_add=True)

        # Register a service to manually fetch data
        async def manually_fetch_data(call):
            """Service to manually fetch new data for all sensors."""
            await daily_total_sensor.fetch_new_data()
            await raw_data_sensor.async_update()

        async_register_admin_service(hass, DOMAIN, "fetch_data", manually_fetch_data)

    except Exception as e:
        _LOGGER.error("Error setting up Watersmart sensor: %s", e)


class WatersmartDailyTotalSensor(SensorEntity):
    """Representation of a Watersmart daily total sensor."""

    def __init__(self, daily_data, client):
        """Initialize the sensor with daily data."""
        self._daily_data = daily_data
        self._client = client
        self._name = "Daily Water Usage"
        self._state = self.calculate_total()
        self._unit = "gal"
        self._unique_id = "watersmart_daily_total"
        self._icon = "mdi:water-outline"
        self._device_class = "water"
        self._state_class = "total_increasing"
        self._last_fetch = None
        self._latest_read_datetime = None

    def calculate_total(self):
        """Calculate the total gallons for the day."""
        if self._daily_data:
            self._latest_read_datetime = max(
                entry["read_datetime"] for entry in self._daily_data
            )
        return sum(entry["value"] for entry in self._daily_data)  # Sum gallons directly

    def update_with_new_data(self, new_data):
        """Include totals of all new data points."""
        for entry in new_data:
            if entry["read_datetime"] > (self._latest_read_datetime or 0):
                self._daily_data.append(entry)
                self._state += entry["value"]
                self._latest_read_datetime = entry["read_datetime"]

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
        attributes = {
            "last_reset": datetime.utcnow().isoformat(),
        }
        if self._latest_read_datetime:
            attributes["read_datetime"] = datetime.utcfromtimestamp(
                self._latest_read_datetime
            ).isoformat()
        return attributes

    async def async_update(self):
        """Fetch updated state data for the sensor."""
        now = datetime.utcnow()
        if self._last_fetch is None or (now - self._last_fetch).seconds >= 3600:  # Fetch data every hour
            await self.fetch_new_data()

    async def fetch_new_data(self):
        """Manually fetch new data and update the state."""
        self._last_fetch = datetime.utcnow()
        try:
            usage_data = await self._client.usage()
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            new_data = [
                entry for entry in usage_data
                if datetime.utcfromtimestamp(entry["read_datetime"]) >= today_start
            ]
            self.update_with_new_data(new_data)
            _LOGGER.info("Manually fetched new data: %s", self._daily_data)
        except Exception as e:
            _LOGGER.error("Error manually fetching updated data: %s", e)


class WatersmartRawDataSensor(SensorEntity):
    """Representation of raw water usage data for long-term statistics."""

    def __init__(self, client):
        """Initialize the raw data sensor."""
        self._client = client
        self._name = "Raw Water Usage Data"
        self._state = None
        self._unit = "gal"
        self._unique_id = "watersmart_raw_data"
        self._device_class = "water"
        self._state_class = "measurement"
        self._last_fetch = None
        self._latest_entry = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the most recent raw data point."""
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
    def device_class(self):
        """Return the device class for the sensor."""
        return self._device_class

    @property
    def state_class(self):
        """Return the state class for long-term statistics."""
        return self._state_class

    @property
    def extra_state_attributes(self):
        """Return additional attributes including latest raw data entry."""
        attributes = {}
        if self._latest_entry:
            attributes["raw_data"] = self._latest_entry
        return attributes

    async def async_update(self):
        """Fetch updated raw data."""
        now = datetime.utcnow()
        if self._last_fetch is None or (now - self._last_fetch).seconds >= 3600:
            self._last_fetch = now
            try:
                usage_data = await self._client.usage()
                if usage_data:
                    self._latest_entry = usage_data[-1]  # Get the most recent data point
                    self._state = self._latest_entry["value"]
                    _LOGGER.info("Updated raw water usage data: %s", self._latest_entry)
            except Exception as e:
                _LOGGER.error("Error updating raw water usage data: %s", e)
