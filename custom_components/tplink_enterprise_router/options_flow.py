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
        self._init_data = {}

    async def async_step_init(self, user_input=None):
        data = self._config_entry.options or self._config_entry.data

        if user_input is not None:
            if user_input.get("enable_syslog_event"):
                self._init_data = user_input
                return await self.async_step_syslog_config()

            await self.hass.config_entries.async_reload(self._config_entry.entry_id)

            return self.async_create_entry(
                title=user_input["instance_name"], data=user_input
            )

        scheme = {
            vol.Required("instance_name", default=data.get("instance_name", DEFAULT_INSTANCE_NAME)): str,
            vol.Required("host", default=data.get("host", DEFAULT_HOST)): str,
            vol.Required("username", default=data.get("username", "")): str,
            vol.Required("password", default=data.get("password", "")): str,
            vol.Required("update_interval", default=data.get("update_interval", 30)): int,
            vol.Required("enable_syslog_event", default=data.get("enable_syslog_event", False)): bool,
            vol.Required("enable_poll_event", default=False): bool,
            vol.Required("debug", default=False): bool,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(scheme))

    async def async_step_syslog_config(self, user_input=None):
        data = self._config_entry.options or self._config_entry.data
        errors = {}

        if user_input is not None:
            merged_data = {**self._init_data, **user_input}
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data=merged_data,
                options=merged_data,
            )

            await self.hass.config_entries.async_reload(self._config_entry.entry_id)

            return self.async_create_entry(
                title=data["instance_name"], data=merged_data
            )

        return self.async_show_form(
            step_id="syslog_config",
            data_schema=vol.Schema({
                vol.Required("syslog_event", default=data.get("syslog_event", "syslog_receiver_message")): str,
                vol.Required("enable_dedicated_event", default=data.get("enable_dedicated_event", False)): bool,
                vol.Required("enable_universal_event", default=data.get("enable_universal_event", False)): bool,
            }),
            errors=errors,
        )
