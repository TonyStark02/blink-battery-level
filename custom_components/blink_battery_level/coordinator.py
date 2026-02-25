"""Coordinator for Blink battery polling."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _extract_battery(cam) -> int | None:
    """Best-effort extraction of battery level from blinkpy camera object."""
    for attr in ("battery", "battery_level", "battery_percentage"):
        val = getattr(cam, attr, None)
        if val not in (None, "", "unknown"):
            try:
                return int(float(val))
            except Exception:
                pass

    try:
        attrs = getattr(cam, "attributes", {}) or {}
        for key in ("battery", "battery_level", "battery_percentage"):
            val = attrs.get(key)
            if val not in (None, "", "unknown"):
                return int(float(val))
    except Exception:
        pass

    return None


async def create_coordinator(hass, config: dict):
    """Create a data update coordinator for Blink battery entities."""
    try:
        from blinkpy.blinkpy import Blink
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Unable to import blinkpy: {exc}") from exc

    username = config.get("username")
    password = config.get("password")
    scan_interval = int(config.get("scan_interval", DEFAULT_SCAN_INTERVAL))

    blink = Blink()

    # Ensure non-interactive auth in Home Assistant runtime
    blink.auth.no_prompt = True
    blink.auth.data["username"] = username
    blink.auth.data["password"] = password

    async def _async_fetch_data():
        # blinkpy exposes async start() on recent versions
        await blink.start()

        cameras = {}
        for cam_name, cam in blink.cameras.items():
            cameras[cam_name] = {
                "battery": _extract_battery(cam),
                "serial": getattr(cam, "serial", cam_name),
            }
        return cameras

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="blink_battery_level",
        update_method=_async_fetch_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()
    return coordinator
