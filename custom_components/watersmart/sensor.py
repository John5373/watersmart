# import asyncio
# import logging

# from homeassistant.config_entries import ConfigEntry
# from homeassistant.core import HomeAssistant
# from homeassistant.exceptions import ConfigEntryNotReady

# from .const import DOMAIN
# from .watersmart_client import WatersmartClient, WatersmartClientError

# _LOGGER = logging.getLogger(__name__)

# async def async_setup(hass: HomeAssistant, config: dict):
#     """Set up the Watersmart integration."""
#     return True

# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Set up Watersmart from a config entry."""
#     hass.data.setdefault(DOMAIN, {})

#     config = entry.data
#     client = WatersmartClient(
#         url=config["url"],
#         email=config["email"],
#         password=config["password"],
#     )

#     try:
#         await client._login()
#     except WatersmartClientError as ex:
#         _LOGGER.error("Failed to connect to Watersmart API: %s", ex)
#         raise ConfigEntryNotReady from ex

#     hass.data[DOMAIN][entry.entry_id] = client

#     hass.async_create_task(
#         hass.config_entries.async_forward_entry_setup(entry, "sensor")
#     )

#     return True

# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Unload a config entry."""
#     await hass.data[DOMAIN][entry.entry_id]._close()
#     hass.data[DOMAIN].pop(entry.entry_id)

#     await hass.config_entries.async_forward_entry_unload(entry, "sensor")

#     return True





# from homeassistant.components.sensor import SensorEntity
# from homeassistant.const import CONF_URL, CONF_EMAIL, CONF_PASSWORD

# from .const import DOMAIN

# async def async_setup_entry(hass, config_entry, async_add_entities):
#     """Set up Watersmart sensors from a config entry."""
#     client = hass.data[DOMAIN][config_entry.entry_id]

#     sensors = []

#     # Assuming the API provides a list of metrics (e.g., water usage data)
#     usage_data = await client.usage()
#     for metric in usage_data:
#         sensors.append(WatersmartSensor(metric))

#     async_add_entities(sensors, update_before_add=True)


# class WatersmartSensor(SensorEntity):
#     """Representation of a Watersmart sensor."""

#     def __init__(self, metric):
#         self._metric = metric
#         self._name = metric.get("name", "Unknown Sensor")
#         self._state = metric.get("value", None)
#         self._unit = metric.get("unit", None)

#     @property
#     def name(self):
#         """Return the name of the sensor."""
#         return self._name

#     @property
#     def state(self):
#         """Return the state of the sensor."""
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         """Return the unit of measurement."""
#         return self._unit

#     async def async_update(self):
#         """Fetch new state data for the sensor."""
#         self._state = self._metric.get("value")


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
