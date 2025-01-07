from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Watersmart sensors from a config entry."""
    client = hass.data[DOMAIN][config_entry.entry_id]

    try:
        # Fetch data from the client
        usage_data = await client.usage()

        # Log the processed data
        _LOGGER.debug("Processed sensor data: %s", usage_data)

        # Create sensors for each metric
        sensors = [WatersmartSensor(metric) for metric in usage_data]
        async_add_entities(sensors, update_before_add=True)
    except Exception as e:
        _LOGGER.error("Error setting up Watersmart sensors: %s", e)


class WatersmartSensor(SensorEntity):
    """Representation of a Watersmart sensor."""

    def __init__(self, metric):
        """Initialize the sensor with a metric."""
        self._metric = metric
        self._name = metric["name"]
        self._state = metric["value"]
        self._unit = metric["unit"]
        self._unique_id = f"watersmart_{metric['read_datetime']}"

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

    async def async_update(self):
        """Fetch updated state data for the sensor."""
        # Updates if needed (not necessary here as data is static per timestamp)
        pass