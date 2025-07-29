import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

class ScrutinyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Scrutiny."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input["base_url"].rstrip('/'))
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title="Scrutiny", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("Scrutiny URL"): str,
                vol.Required("Verify SSL Certificate", default=True): bool,
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ScrutinyOptionsFlowHandler(config_entry)


class ScrutinyOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Scrutiny options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    "scan_interval",
                    default=self.config_entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                ): int,
            })
        )
