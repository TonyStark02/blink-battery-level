"""Coordinator for Blink battery polling."""

from __future__ import annotations

from datetime import timedelta
import logging

from blinkpy.auth import BlinkTwoFARequiredError, LoginError, TokenRefreshFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components import persistent_notification

from .const import DEFAULT_SCAN_INTERVAL, CONF_AUTH_DATA

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


NOTIF_ID = "blink_battery_level_2fa_required"


class BlinkBatteryCoordinator(DataUpdateCoordinator):
    """Coordinator for Blink battery integration with 2FA support."""

    def __init__(self, hass, blink, scan_interval, entry_id: str | None = None):
        super().__init__(
            hass,
            _LOGGER,
            name="blink_battery_level",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.blink = blink
        self.awaiting_2fa = False
        self.entry_id = entry_id
        self._started = False

    async def _async_update_data(self):
        try:
            if not self._started:
                ok = await self.blink.start()
                if not ok:
                    raise UpdateFailed("Blink start failed")
                self._started = True
            else:
                await self.blink.refresh(force=True)
            self.awaiting_2fa = False
        except BlinkTwoFARequiredError as exc:
            self.awaiting_2fa = True
            persistent_notification.async_create(
                self.hass,
                "Blink demande un code SMS. Va dans Outils de développement > Actions, puis exécute le service `blink_battery_level.submit_2fa_code` avec `code: \"123456\"`.",
                title="Blink Battery Level: code 2FA requis",
                notification_id=NOTIF_ID,
            )
            raise UpdateFailed(
                "2FA required. Submit code via blink_battery_level.submit_2fa_code"
            ) from exc
        except (LoginError, TokenRefreshFailed) as exc:
            self._started = False
            raise UpdateFailed(
                "Login failed (Blink). Vérifie les identifiants ou attends 10-15 min si Blink a temporairement bloqué la connexion."
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

    def auth_data(self) -> dict:
        try:
            return self.blink.auth.login_attributes
        except Exception:
            return {}

    async def async_submit_2fa_code(self, code: str) -> bool:
        try:
            ok = await self.blink.send_2fa_code(code)
            if ok:
                self.awaiting_2fa = False
                self._started = True
                persistent_notification.async_dismiss(self.hass, NOTIF_ID)
                await self.async_request_refresh()
                return True
            return False
        except Exception as exc:
            _LOGGER.error("2FA submit failed: %s", exc)
            return False

    async def async_close(self) -> None:
        """Close underlying Blink aiohttp session to avoid unclosed session warnings."""
        try:
            session = getattr(getattr(self.blink, "auth", None), "session", None)
            if session and not session.closed:
                await session.close()
        except Exception as exc:
            _LOGGER.debug("Error while closing blink session: %s", exc)


async def create_coordinator(hass, config: dict, entry_id: str | None = None):
    try:
        from blinkpy.blinkpy import Blink
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Unable to import blinkpy: {exc}") from exc

    username = config.get("username")
    password = config.get("password")
    scan_interval = int(config.get("scan_interval", DEFAULT_SCAN_INTERVAL))

    blink = Blink()
    blink.auth.no_prompt = True

    auth_data = config.get(CONF_AUTH_DATA) or {}
    if isinstance(auth_data, dict) and auth_data:
        blink.auth.data.update(auth_data)

    blink.auth.data["username"] = username
    blink.auth.data["password"] = password

    coordinator = BlinkBatteryCoordinator(hass, blink, scan_interval, entry_id=entry_id)
    return coordinator
