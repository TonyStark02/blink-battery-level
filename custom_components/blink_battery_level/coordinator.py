"""Coordinator for Blink battery polling."""

from __future__ import annotations

from datetime import timedelta
import logging

from blinkpy.auth import BlinkTwoFARequiredError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _extract_battery(cam) -> int | None:
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


class BlinkBatteryCoordinator(DataUpdateCoordinator):
    """Coordinator for Blink battery integration with 2FA support."""

    def __init__(self, hass, blink, scan_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="blink_battery_level",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.blink = blink
        self.awaiting_2fa = False

    async def _async_update_data(self):
        try:
            await self.blink.start()
            self.awaiting_2fa = False
        except BlinkTwoFARequiredError as exc:
            self.awaiting_2fa = True
            raise UpdateFailed(
                "2FA required. Call service blink_battery_level.submit_2fa_code with your SMS code."
            ) from exc
        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc

        cameras = {}
        for cam_name, cam in self.blink.cameras.items():
            cameras[cam_name] = {
                "battery": _extract_battery(cam),
                "serial": getattr(cam, "serial", cam_name),
            }
        return cameras

    async def async_submit_2fa_code(self, code: str) -> bool:
        try:
            ok = await self.blink.send_2fa_code(code)
            if ok:
                self.awaiting_2fa = False
                await self.async_request_refresh()
                return True
            return False
        except Exception as exc:
            _LOGGER.error("2FA submit failed: %s", exc)
            return False


async def create_coordinator(hass, config: dict):
    try:
        from blinkpy.blinkpy import Blink
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Unable to import blinkpy: {exc}") from exc

    username = config.get("username")
    password = config.get("password")
    scan_interval = int(config.get("scan_interval", DEFAULT_SCAN_INTERVAL))

    blink = Blink()
    blink.auth.no_prompt = True
    blink.auth.data["username"] = username
    blink.auth.data["password"] = password

    coordinator = BlinkBatteryCoordinator(hass, blink, scan_interval)
    return coordinator
