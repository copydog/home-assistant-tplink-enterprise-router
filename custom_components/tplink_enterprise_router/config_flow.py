import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    DEFAULT_INSTANCE_NAME,
    DEFAULT_HOST,
)


class TPLinkEnterpriseRouterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not user_input.get("host"):
                errors["host"] = "host_required"
            if not user_input.get("username"):
                errors["username"] = "username_required"
            if not user_input.get("password"):
                errors["password"] = "password_required"

            if not errors:
                return self.async_create_entry(
                    title=user_input["instance_name"],
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("instance_name", default=DEFAULT_INSTANCE_NAME): str,
                vol.Required("host", default=DEFAULT_HOST): str,
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Required("update_interval", default=30): int,
                vol.Required("enable_syslog_event", default=False): bool,
                vol.Required("enable_poll_event", default=False): bool,
                vol.Required("debug", default=False): bool,
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        from .options_flow import TPLinkEnterpriseRouterOptionsFlowHandler
        return TPLinkEnterpriseRouterOptionsFlowHandler(config_entry)
