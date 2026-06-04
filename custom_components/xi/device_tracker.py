"""Support for 자이 parking location device trackers."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
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
    """Set up the 자이 device tracker platform."""
    coordinator: XiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    try:
        parking_list = coordinator.parking_data.get("list") or []
        if parking_list:
            async_add_entities(
                XiCarDeviceTracker(coordinator, car)
                for car in parking_list
                if "carno" in car
            )
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Error setting up device trackers: %s", err)


class XiCarDeviceTracker(CoordinatorEntity[XiDataUpdateCoordinator], TrackerEntity):
    """Representation of a car device tracker based on parking location."""

    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: XiDataUpdateCoordinator,
        car_data: dict[str, Any],
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._carno = car_data["carno"]
        self._attr_name = f"차량 {self._carno}"

        # Unique ID based on household and car number
        apt_code = coordinator.client.apt_code or "unknown"
        dong = coordinator.client.dong_no or "unknown"
        ho = coordinator.client.ho_no or "unknown"
        self._attr_unique_id = f"xi_car_tracker_{apt_code}_{dong}_{ho}_{self._carno}"

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.ROUTER

    @property
    def location_name(self) -> str | None:
        """Return the location name of the device tracker."""
        parking_list = self.coordinator.parking_data.get("list") or []
        for car in parking_list:
            if car.get("carno") == self._carno:
                floor = car.get("floor")
                block = car.get("block")
                if floor or block:
                    label = car.get("label")
                    if label and label.strip():
                        return label
                    return f"{floor} {block}".strip()
                return "not_home"
        return "not_home"

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
