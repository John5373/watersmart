# File: custom_components/watersmart/config_flow.py
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from .const import DOMAIN

class WaterSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WaterSmart integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            username = user_input.get("username")
            password = user_input.get("password")

            # Validate the credentials here
            try:
                from .watersmart import WaterSmart

                watersmart = WaterSmart(username, password)
                await watersmart._authenticate()
                await watersmart.close()

                return self.async_create_entry(title="WaterSmart", data=user_input)

            except Exception as e:
                errors["base"] = "auth_failed"

        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WaterSmartOptionsFlowHandler(config_entry)

class WaterSmartOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for WaterSmart integration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Optional("update_interval", default=self.config_entry.options.get("update_interval", 5)): int,
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
