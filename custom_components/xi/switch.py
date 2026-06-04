"""Switch platform for 자이 integration."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_friendly_name
from .coordinator import XiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: XiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    switches = []
    try:
        for device_id, device in coordinator.data.items():
            device_type = device.get("type") or device.get("device_type") or ""
            # Detect standby power devices
            if "standby" in device_type.lower() or "standby" in device_id.lower():
                room_name = device.get("room_name", "Room")
                switches.append(XiStandbySwitch(coordinator, device, room_name))
    except Exception as err:
        _LOGGER.error("Error setting up switches: %s", err)

    async_add_entities(switches, update_before_add=True)


class XiStandbySwitch(CoordinatorEntity[XiDataUpdateCoordinator], SwitchEntity):
    """Representation of a 자이 Standby Power Switch."""

    def __init__(self, coordinator: XiDataUpdateCoordinator, device_data: dict[str, Any], room_name: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._client = coordinator.client
        self._device_data = device_data
        self._device_id = device_data["device_id"]
        self._room_name = room_name
        self._attr_name = get_device_friendly_name(room_name, device_data)
        self._attr_unique_id = f"xi_standby_{self._device_id}"
        self._attr_is_on = False
        self._last_command_time = 0.0

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_is_on
        status = device.get("status") or {}
        db_is_on = status.get("power") is True or status.get("power") == "on"

        if time.time() - self._last_command_time < 5.0:
            if db_is_on == self._attr_is_on:
                self._last_command_time = 0.0
            return self._attr_is_on
        return db_is_on

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device = self.coordinator.data.get(self._device_id)
        if device:
            status = device.get("status") or {}
            db_is_on = status.get("power") is True or status.get("power") == "on"

            if time.time() - self._last_command_time < 5.0:
                if db_is_on == self._attr_is_on:
                    self._last_command_time = 0.0
            else:
                self._attr_is_on = db_is_on
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._last_command_time = time.time()
        self._attr_is_on = True
        self.async_write_ha_state()

        success = await self._client.send_command("standby", self._device_id, {"power": True})
        if success:
            await self.coordinator.async_request_refresh()
        else:
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._last_command_time = time.time()
        self._attr_is_on = False
        self.async_write_ha_state()

        success = await self._client.send_command("standby", self._device_id, {"power": False})
        if success:
            await self.coordinator.async_request_refresh()
        else:
            self._attr_is_on = True
            self.async_write_ha_state()
