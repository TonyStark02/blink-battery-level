"""Config flow for Blink Battery Level."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


class BlinkBatteryLevelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Blink Battery Level."""

    VERSION = 2

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_USERNAME].lower()}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Blink Battery ({user_input[CONF_USERNAME]})",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=60, max=3600)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
