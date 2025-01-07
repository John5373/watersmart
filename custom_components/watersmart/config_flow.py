from homeassistant import config_entries
import voluptuous as vol
from aiohttp import ClientError

from .const import DOMAIN
from .watersmart_client import WatersmartClient, WatersmartClientError

class WatersmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Watersmart."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the input
            try:
                client = WatersmartClient(
                    url=user_input["url"],
                    email=user_input["email"],
                    password=user_input["password"],
                )
                await client._login()  # Test login
            except WatersmartClientError:
                errors["base"] = "cannot_connect"
            except ClientError:
                errors["base"] = "client_error"
            else:
                # Save the configuration
                return self.async_create_entry(title="Watersmart", data=user_input)

        # Define the input schema
        data_schema = vol.Schema(
            {
                vol.Required("url"): str,
                vol.Required("email"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
