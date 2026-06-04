"""Light platform for 자이 integration."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
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
    """Set up the light platform."""
    coordinator: XiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    lights = []
    try:
        for device_id, device in coordinator.data.items():
            device_type = device.get("type") or device.get("device_type") or ""
            # Exclude master switches like "alllight"
            if "alllight" in device_type.lower() or "alllight" in device_id.lower():
                continue
            room_name = device.get("room_name", "Room")
            if "dimming" in device_type.lower() or "dimming" in device_id.lower():
                lights.append(XiDimmingLight(coordinator, device, room_name))
            elif "light" in device_type.lower() or "light" in device_id.lower():
                lights.append(XiLight(coordinator, device, room_name))
    except Exception as err:
        _LOGGER.error("Error setting up lights: %s", err)

    async_add_entities(lights, update_before_add=True)


class XiLight(CoordinatorEntity[XiDataUpdateCoordinator], LightEntity):
    """Representation of a 자이 Standard Light."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator: XiDataUpdateCoordinator, device_data: dict[str, Any], room_name: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._client = coordinator.client
        self._device_data = device_data
        self._device_id = device_data["device_id"]
        self._room_name = room_name
        self._attr_name = get_device_friendly_name(room_name, device_data)
        self._attr_unique_id = f"xi_light_{self._device_id}"
        self._attr_is_on = False
        self._last_command_time = 0.0

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if time.time() - self._last_command_time < 1.0:
            return self._attr_is_on
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_is_on
        status = device.get("status") or {}
        return status.get("power") is True or status.get("power") == "on"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if time.time() - self._last_command_time >= 1.0:
            device = self.coordinator.data.get(self._device_id)
            if device:
                status = device.get("status") or {}
                self._attr_is_on = status.get("power") is True or status.get("power") == "on"
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        self._last_command_time = time.time()
        self._attr_is_on = True
        self.async_write_ha_state()
        success = await self._client.send_command("light", self._device_id, {"power": True})
        if success:
            if (device := self.coordinator.data.get(self._device_id)) is not None:
                if "status" not in device:
                    device["status"] = {}
                device["status"]["power"] = True
            self.coordinator.async_set_updated_data(self.coordinator.data)
            await self.coordinator.async_request_refresh()
        else:
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._last_command_time = time.time()
        self._attr_is_on = False
        self.async_write_ha_state()
        success = await self._client.send_command("light", self._device_id, {"power": False})
        if success:
            if (device := self.coordinator.data.get(self._device_id)) is not None:
                if "status" not in device:
                    device["status"] = {}
                device["status"]["power"] = False
            self.coordinator.async_set_updated_data(self.coordinator.data)
            await self.coordinator.async_request_refresh()
        else:
            self._attr_is_on = True
            self.async_write_ha_state()


class XiDimmingLight(CoordinatorEntity[XiDataUpdateCoordinator], LightEntity):
    """Representation of a 자이 Dimming Light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: XiDataUpdateCoordinator, device_data: dict[str, Any], room_name: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._client = coordinator.client
        self._device_data = device_data
        self._device_id = device_data["device_id"]
        self._room_name = room_name
        self._attr_name = get_device_friendly_name(room_name, device_data)
        self._attr_unique_id = f"xi_dimming_light_{self._device_id}"
        self._attr_is_on = False
        self._attr_brightness = 255
        self._last_command_time = 0.0

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if time.time() - self._last_command_time < 1.0:
            return self._attr_is_on
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_is_on
        status = device.get("status") or {}
        return status.get("power") is True or status.get("power") == "on"

    @property
    def brightness(self) -> int:
        """Return the brightness of this light."""
        if time.time() - self._last_command_time < 1.0:
            return self._attr_brightness
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_brightness
        status = device.get("status") or {}
        dimming = status.get("dimming")
        if dimming is not None:
            try:
                d_val = int(dimming)
                if 1 <= d_val <= 4:
                    return int((d_val / 4.0) * 255.0)
            except ValueError:
                pass
        return self._attr_brightness

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if time.time() - self._last_command_time >= 1.0:
            device = self.coordinator.data.get(self._device_id)
            if device:
                status = device.get("status") or {}
                self._attr_is_on = status.get("power") is True or status.get("power") == "on"
                dimming = status.get("dimming")
                if dimming is not None:
                    try:
                        d_val = int(dimming)
                        if 1 <= d_val <= 4:
                            self._attr_brightness = int((d_val / 4.0) * 255.0)
                    except ValueError:
                        pass
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        self._last_command_time = time.time()

        # Fall back to previous brightness, or default to max (255)
        brightness = kwargs.get("brightness") or self.brightness or 255

        # 4-Step mapping brackets:
        # Step 1: 0 - 64
        # Step 2: 65 - 128
        # Step 3: 129 - 191
        # Step 4: 192 - 255
        if brightness <= 64:
            dimming = 1
        elif brightness <= 128:
            dimming = 2
        elif brightness <= 191:
            dimming = 3
        else:
            dimming = 4

        # Optimistic update
        old_is_on = self._attr_is_on
        old_brightness = self._attr_brightness
        self._attr_is_on = True
        self._attr_brightness = int((dimming / 4.0) * 255.0)
        self.async_write_ha_state()

        status = {"power": True, "dimming": dimming}

        success = await self._client.send_command("dimming", self._device_id, status)
        if success:
            if (device := self.coordinator.data.get(self._device_id)) is not None:
                if "status" not in device:
                    device["status"] = {}
                device["status"]["power"] = True
                device["status"]["dimming"] = dimming
            self.coordinator.async_set_updated_data(self.coordinator.data)
            await self.coordinator.async_request_refresh()
        else:
            self._attr_is_on = old_is_on
            self._attr_brightness = old_brightness
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._last_command_time = time.time()
        old_is_on = self._attr_is_on
        self._attr_is_on = False
        self.async_write_ha_state()

        success = await self._client.send_command("dimming", self._device_id, {"power": False, "dimming": 0})
        if success:
            if (device := self.coordinator.data.get(self._device_id)) is not None:
                if "status" not in device:
                    device["status"] = {}
                device["status"]["power"] = False
                device["status"]["dimming"] = 0
            self.coordinator.async_set_updated_data(self.coordinator.data)
            await self.coordinator.async_request_refresh()
        else:
            self._attr_is_on = old_is_on
            self.async_write_ha_state()
