"""Support for 자이 parking binary sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the 자이 binary sensor platform."""
    coordinator: XiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    try:
        parking_list = coordinator.parking_data.get("list") or []
        if parking_list:
            async_add_entities(
                XiCarParkedBinarySensor(coordinator, car)
                for car in parking_list
                if "carno" in car
            )
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Error setting up binary sensors: %s", err)


class XiCarParkedBinarySensor(CoordinatorEntity[XiDataUpdateCoordinator], BinarySensorEntity):
    """Representation of a binary sensor that tracks if a car is parked."""

    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: XiDataUpdateCoordinator,
        car_data: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._carno = car_data["carno"]
        self._attr_name = f"주차 여부 {self._carno}"

        # Unique ID based on household and car number
        apt_code = coordinator.client.apt_code or "unknown"
        dong = coordinator.client.dong_no or "unknown"
        ho = coordinator.client.ho_no or "unknown"
        self._attr_unique_id = f"xi_parking_presence_{apt_code}_{dong}_{ho}_{self._carno}"

    @property
    def is_on(self) -> bool:
        """Return true if the car is parked."""
        parking_list = self.coordinator.parking_data.get("list") or []
        for car in parking_list:
            if car.get("carno") == self._carno:
                floor = car.get("floor")
                block = car.get("block")
                return bool(floor or block)
        return False

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
