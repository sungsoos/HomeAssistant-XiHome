"""Climate platform for 자이 integration."""

from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
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
    """Set up the climate platform."""
    coordinator: XiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    heaters = []
    try:
        for device_id, device in coordinator.data.items():
            device_type = device.get("type") or device.get("device_type") or ""
            # Detect heating devices
            if (
                "heating" in device_type.lower()
                or "heating" in device_id.lower()
                or "thermostat" in device_type.lower()
            ):
                room_name = device.get("room_name", "Room")
                heaters.append(XiHeatingThermostat(coordinator, device, room_name))
    except Exception as err:
        _LOGGER.error("Error setting up heating: %s", err)

    async_add_entities(heaters, update_before_add=True)


class XiHeatingThermostat(CoordinatorEntity[XiDataUpdateCoordinator], ClimateEntity):
    """Representation of a 자이 Heating Thermostat."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: XiDataUpdateCoordinator,
        device_data: dict[str, Any],
        room_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._client = coordinator.client
        self._device_data = device_data
        self._device_id = device_data["device_id"]
        self._room_name = room_name
        self._attr_name = get_device_friendly_name(room_name, device_data)
        self._attr_unique_id = f"xi_heating_{self._device_id}"
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = 22.0
        self._attr_target_temperature = 22.0
        self._last_command_time = 0.0

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_hvac_mode
        status = device.get("status") or {}
        power_on = status.get("power") is True or status.get("power") == "on"
        db_hvac_mode = HVACMode.HEAT if power_on else HVACMode.OFF

        if time.time() - self._last_command_time < 5.0:
            target_temp = (
                status.get("temperature")
                or status.get("target_temperature")
                or status.get("target_temp")
                or status.get("user_change")
                or status.get("user_load")
                or status.get("userChange")
                or status.get("userLoad")
            )
            db_target_temp = (
                float(target_temp)
                if target_temp is not None
                else self._attr_target_temperature
            )

            if (
                db_hvac_mode == self._attr_hvac_mode
                and db_target_temp == self._attr_target_temperature
            ):
                self._last_command_time = 0.0
            return self._attr_hvac_mode
        return db_hvac_mode

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_current_temperature
        status = device.get("status") or {}
        current_temp = status.get("current_temperature") or status.get("current_temp")
        if current_temp is not None:
            return float(current_temp)
        return self._attr_current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return self._attr_target_temperature
        status = device.get("status") or {}
        target_temp = (
            status.get("temperature")
            or status.get("target_temperature")
            or status.get("target_temp")
            or status.get("user_change")
            or status.get("user_load")
            or status.get("userChange")
            or status.get("userLoad")
        )
        db_target_temp = (
            float(target_temp)
            if target_temp is not None
            else self._attr_target_temperature
        )

        if time.time() - self._last_command_time < 5.0:
            power_on = status.get("power") is True or status.get("power") == "on"
            db_hvac_mode = HVACMode.HEAT if power_on else HVACMode.OFF
            if (
                db_hvac_mode == self._attr_hvac_mode
                and db_target_temp == self._attr_target_temperature
            ):
                self._last_command_time = 0.0
            return self._attr_target_temperature
        return db_target_temp

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device = self.coordinator.data.get(self._device_id)
        if device:
            status = device.get("status") or {}
            power_on = status.get("power") is True or status.get("power") == "on"
            db_hvac_mode = HVACMode.HEAT if power_on else HVACMode.OFF

            target_temp = (
                status.get("temperature")
                or status.get("target_temperature")
                or status.get("target_temp")
                or status.get("user_change")
                or status.get("user_load")
                or status.get("userChange")
                or status.get("userLoad")
            )
            db_target_temp = (
                float(target_temp)
                if target_temp is not None
                else self._attr_target_temperature
            )

            if time.time() - self._last_command_time < 5.0:
                if (
                    db_hvac_mode == self._attr_hvac_mode
                    and db_target_temp == self._attr_target_temperature
                ):
                    self._last_command_time = 0.0
            else:
                self._attr_hvac_mode = db_hvac_mode
                self._attr_target_temperature = db_target_temp

            # Always update current temperature
            current_temp = status.get("current_temperature") or status.get(
                "current_temp"
            )
            if current_temp is not None:
                self._attr_current_temperature = float(current_temp)

        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        self._last_command_time = time.time()
        old_hvac_mode = self._attr_hvac_mode
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

        power_on = hvac_mode == HVACMode.HEAT
        success = await self._client.send_command(
            "heating", self._device_id, {"power": power_on}
        )
        if success:
            await self.coordinator.async_request_refresh()
        else:
            self._attr_hvac_mode = old_hvac_mode
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        self._last_command_time = time.time()
        if (target_temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        old_target_temperature = self._attr_target_temperature
        self._attr_target_temperature = target_temp
        self.async_write_ha_state()

        status = {"temperature": int(target_temp)}
        # Ensure it remains/turns on
        if self.hvac_mode == HVACMode.HEAT:
            status["power"] = True

        success = await self._client.send_command("heating", self._device_id, status)
        if success:
            await self.coordinator.async_request_refresh()
        else:
            self._attr_target_temperature = old_target_temperature
            self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the heating on."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the heating off."""
        await self.async_set_hvac_mode(HVACMode.OFF)
