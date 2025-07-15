import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from .const import (
    DEFAULT_INSTANCE_NAME,
    DEFAULT_HOST,
)

class TPLinkEnterpriseRouterOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        data = self._config_entry.options or self._config_entry.data
        schema = vol.Schema(
            {
                vol.Required("instance_name", default=data.get("instance_name", DEFAULT_INSTANCE_NAME)): str,
                vol.Required("host", default=data.get("host", DEFAULT_HOST)): str,
                vol.Required("username", default=data.get("username", "")): str,
                vol.Required("password", default=data.get("password", "")): str,
                vol.Required("update_interval", default=data.get("update_interval", 30)): int,
            }
        )
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data=user_input
            )

            return self.async_create_entry(
                title=user_input["instance_name"], data=user_input
            )
        return self.async_show_form(step_id="init", data_schema=schema)