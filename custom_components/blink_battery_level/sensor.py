"""Blink battery level sensors."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, PERCENTAGE
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import create_coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Backward-compatible YAML setup."""
    try:
        coordinator = await create_coordinator(
            hass,
            {
                "username": config[CONF_USERNAME],
                "password": config[CONF_PASSWORD],
                "scan_interval": config[CONF_SCAN_INTERVAL],
            },
        )
    except Exception as exc:
        _LOGGER.error("Blink Battery Level setup failed: %s", exc)
        return

    entities = [BlinkBatterySensor(coordinator, cam_name) for cam_name in coordinator.data.keys()]
    async_add_entities(entities)


async def async_setup_entry(hass, entry, async_add_entities):
    """Config-entry setup (v2)."""
    try:
        coordinator = await create_coordinator(hass, entry.data)
    except Exception as exc:
        _LOGGER.error("Blink Battery Level entry setup failed: %s", exc)
        return

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = [BlinkBatterySensor(coordinator, cam_name) for cam_name in coordinator.data.keys()]
    async_add_entities(entities)


class BlinkBatterySensor(CoordinatorEntity, SensorEntity):
    """Battery sensor for a Blink camera."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery"

    def __init__(self, coordinator, cam_name: str) -> None:
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
