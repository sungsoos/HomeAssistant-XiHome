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

        # Add parking location sensors
        parking_list = coordinator.parking_data.get("list") or []
        if parking_list:
            sensors.extend(
                XiParkingLocationSensor(coordinator, car)
                for car in parking_list
                if "carno" in car
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


class XiParkingLocationSensor(CoordinatorEntity[XiDataUpdateCoordinator], SensorEntity):
    """Representation of a 자이 Parking Location Sensor."""

    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: XiDataUpdateCoordinator,
        car_data: dict[str, Any],
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._carno = car_data["carno"]
        self._attr_name = f"주차 위치 {self._carno}"

        # Unique ID based on household and car number
        apt_code = coordinator.client.apt_code or "unknown"
        dong = coordinator.client.dong_no or "unknown"
        ho = coordinator.client.ho_no or "unknown"
        self._attr_unique_id = f"xi_parking_{apt_code}_{dong}_{ho}_{self._carno}"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        parking_list = self.coordinator.parking_data.get("list") or []
        for car in parking_list:
            if car.get("carno") == self._carno:
                label = car.get("label")
                if label and label.strip():
                    return label
                floor = car.get("floor")
                block = car.get("block")
                if floor or block:
                    return f"{floor} {block}".strip()
                return "미주차"
        return "미주차"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device state attributes."""
        parking_list = self.coordinator.parking_data.get("list") or []
        status = self.coordinator.parking_data.get("status") or {}
        for car in parking_list:
            if car.get("carno") == self._carno:
                return {
                    "carno": car.get("carno"),
                    "floor": car.get("floor"),
                    "block": car.get("block"),
                    "in_parking_datetime_label": car.get("in_parking_datetime_label"),
                    "image_filename": car.get("image_filename"),
                    "tagid": car.get("tagid"),
                    "parking_register_method": status.get("parking_register_method"),
                    "favorite_parking": status.get("FAVORITE_PARKING_yn") == "Y",
                }
        return {}


