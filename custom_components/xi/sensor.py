"""Sensor platform for 자이 integration."""
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_friendly_name, is_air_purifier
from .coordinator import XiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: XiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = []
    try:
        for device in coordinator.data.values():
            if is_air_purifier(device):
                room_name = device.get("room_name", "Room")

                # Numeric measurement sensors (CO2 only)
                sensors.append(
                    XiAirPurifierMeasurementSensor(
                        coordinator,
                        device,
                        room_name,
                        "co2",
                        "이산화탄소",
                        SensorDeviceClass.CO2,
                        SensorStateClass.MEASUREMENT,
                        CONCENTRATION_PARTS_PER_MILLION,
                        ["co2", "co2_value", "co2_level", "carbon_dioxide"],
                    )
                )
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Error setting up sensors: %s", err)

    async_add_entities(sensors, update_before_add=True)


class XiAirPurifierMeasurementSensor(CoordinatorEntity[XiDataUpdateCoordinator], SensorEntity):
    """Representation of a 자이 Air Purifier Numeric Sensor."""

    def __init__(
        self,
        coordinator: XiDataUpdateCoordinator,
        device_data: dict[str, Any],
        room_name: str,
        sensor_key: str,
        sensor_label: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
        unit: str,
        lookup_keys: list[str],
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._device_id = device_data["device_id"]
        self._sensor_key = sensor_key
        self._lookup_keys = lookup_keys

        self._attr_name = f"{get_device_friendly_name(room_name, device_data)} {sensor_label}"
        self._attr_unique_id = f"xi_sensor_{sensor_key}_{self._device_id}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return None
        status = device.get("status") or {}

        # General lookup keys
        for key in self._lookup_keys:
            val = status.get(key)
            if val is not None and str(val).strip() != "":
                try:
                    return float(val)
                except ValueError:
                    pass
        return None
