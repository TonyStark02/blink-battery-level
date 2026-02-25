"""Blink battery level sensors."""

from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import PERCENTAGE, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 600

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    interval = config[CONF_SCAN_INTERVAL]

    try:
        from blinkpy.blinkpy import Blink
    except Exception as exc:  # pragma: no cover
        _LOGGER.error("Unable to import blinkpy: %s", exc)
        return

    blink = Blink()

    async def _async_fetch_data():
        # Initial login/session creation if needed
        if not getattr(blink, "user", None):
            blink.user = {
                "username": username,
                "password": password,
            }
        await hass.async_add_executor_job(blink.start)

        cameras = {}
        for cam_name, cam in blink.cameras.items():
            battery = None
            # Try common fields exposed by blinkpy camera objects
            for attr in ("battery", "battery_level", "battery_percentage"):
                battery = getattr(cam, attr, None)
                if battery is not None:
                    break

            # fallback from generic data blob if available
            if battery is None:
                try:
                    battery = cam.attributes.get("battery")
                except Exception:
                    battery = None

            cameras[cam_name] = {
                "battery": battery,
                "serial": getattr(cam, "serial", cam_name),
            }

        return cameras

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="blink_battery_level",
        update_method=_async_fetch_data,
        update_interval=timedelta(seconds=interval),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = [
        BlinkBatterySensor(coordinator, cam_name)
        for cam_name in coordinator.data.keys()
    ]
    async_add_entities(entities)


class BlinkBatterySensor(CoordinatorEntity, SensorEntity):
    """Battery sensor for a Blink camera."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery"

    def __init__(self, coordinator: DataUpdateCoordinator, cam_name: str) -> None:
        super().__init__(coordinator)
        self._cam_name = cam_name
        self._attr_name = f"Blink {cam_name} Battery"
        self._attr_unique_id = f"blink_battery_{cam_name.lower().replace(' ', '_')}"

    @property
    def native_value(self):
        cam = self.coordinator.data.get(self._cam_name, {})
        val = cam.get("battery")
        if val in (None, "", "unknown"):
            return None
        try:
            return int(float(val))
        except Exception:
            return None
