"""Config flow for Scrutiny integration."""
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class ScrutinyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Scrutiny."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        if user_input is not None:
            # Map the user-friendly keys back to the internal variable names.
            data_to_store = {
                "base_url": user_input["Scrutiny URL"].rstrip('/'),
                "verify_ssl": user_input["Verify SSL Certificate"]
            }

            await self.async_set_unique_id(data_to_store["base_url"])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title="Scrutiny", data=data_to_store)

        # Use the desired, user-friendly labels directly in the schema.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("Scrutiny URL"): str,
                vol.Required("Verify SSL Certificate", default=True): bool,
            })
        )