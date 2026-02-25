"""Config flow for Blink Battery Level."""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    CONF_AUTH_DATA,
)

_LOGGER = logging.getLogger(__name__)


class BlinkBatteryLevelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Blink Battery Level with inline 2FA."""

    VERSION = 3

    def __init__(self):
        self._pending_input = None
        self._blink = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            try:
                from blinkpy.blinkpy import Blink
                from blinkpy.auth import BlinkTwoFARequiredError, LoginError, TokenRefreshFailed

                self._pending_input = user_input
                self._blink = Blink()
                self._blink.auth.no_prompt = True
                self._blink.auth.data["username"] = user_input[CONF_USERNAME]
                self._blink.auth.data["password"] = user_input[CONF_PASSWORD]

                try:
                    ok = await self._blink.start()
                except BlinkTwoFARequiredError:
                    return await self.async_step_2fa()
                except (LoginError, TokenRefreshFailed):
                    errors["base"] = "invalid_auth"
                    ok = False

                if not ok and "base" not in errors:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_USERNAME].lower()}")
                    self._abort_if_unique_id_configured()
                    data = dict(user_input)
                    data[CONF_AUTH_DATA] = self._blink.auth.login_attributes
                    return self.async_create_entry(
                        title=f"Blink Battery ({user_input[CONF_USERNAME]})",
                        data=data,
                    )
            except Exception as exc:
                _LOGGER.error("Config flow setup failed: %s", exc)
                errors["base"] = "cannot_connect"

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

    async def async_step_2fa(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            try:
                code = user_input["code"].strip()
                if not self._blink or not self._pending_input:
                    errors["base"] = "unknown"
                else:
                    ok = await self._blink.send_2fa_code(code)
                    if not ok:
                        errors["base"] = "invalid_auth"
                    else:
                        data = dict(self._pending_input)
                        data[CONF_AUTH_DATA] = self._blink.auth.login_attributes
                        await self.async_set_unique_id(f"{DOMAIN}_{self._pending_input[CONF_USERNAME].lower()}")
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=f"Blink Battery ({self._pending_input[CONF_USERNAME]})",
                            data=data,
                        )
            except Exception as exc:
                _LOGGER.error("2FA submit failed in config flow: %s", exc)
                errors["base"] = "invalid_auth"

        schema = vol.Schema({vol.Required("code"): str})
        return self.async_show_form(
            step_id="2fa",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "hint": "Entrez le code SMS Blink"
            },
        )
