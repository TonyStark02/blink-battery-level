"""Blink battery level custom component."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, PLATFORMS

SERVICE_SUBMIT_2FA_CODE = "submit_2fa_code"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    async def _submit_2fa(call: ServiceCall):
        code = call.data.get("code", "").strip()
        entry_id = call.data.get("entry_id")
        if not code:
            return

        coordinators = hass.data.get(DOMAIN, {})
        targets = []
        if entry_id:
            c = coordinators.get(entry_id)
            if c:
                targets = [c]
        else:
            targets = list(coordinators.values())

        for coordinator in targets:
            await coordinator.async_submit_2fa_code(code)

    if not hass.services.has_service(DOMAIN, SERVICE_SUBMIT_2FA_CODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SUBMIT_2FA_CODE,
            _submit_2fa,
            schema=vol.Schema({
                vol.Required("code"): str,
                vol.Optional("entry_id"): str,
            }),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return ok
