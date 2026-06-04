"""DataUpdateCoordinator for the 자이 integration."""
import asyncio
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import XiHomeClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class XiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching 자이 data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, client: XiHomeClient) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=3),
        )
        self.client = client
        self.room_names: dict[str, str] = {}
        self.parking_data: dict[str, Any] = {}
        self._last_parking_update = 0.0

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from API."""
        now = time.time()
        if now - self._last_parking_update >= 60.0:
            try:
                self.parking_data = await self.client.get_parking_location()
                self._last_parking_update = now
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Failed to fetch parking location: %s", err)


        try:
            # Fetch room IDs and names once if not already cached
            if not self.room_names:
                rooms = await self.client.get_rooms()
                for room in rooms:
                    room_id = room.get("room_id")
                    if room_id:
                        self.room_names[room_id] = room.get("room_name", f"Room {room_id}")

            all_devices: dict[str, dict[str, Any]] = {}
            room_ids = list(self.room_names.keys())

            # Fetch devices for all rooms concurrently
            results = await asyncio.gather(
                *(self.client.get_devices_by_room(room_id) for room_id in room_ids),
                return_exceptions=True
            )

            for room_id, result in zip(room_ids, results, strict=True):
                if isinstance(result, Exception):
                    _LOGGER.error("Failed to fetch devices for room %s: %s", room_id, result)
                    continue
                room_name = self.room_names[room_id]
                for device in result:
                    if "device_id" in device:
                        device["room_name"] = room_name
                        device["room_id"] = room_id
                        all_devices[device["device_id"]] = device
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        else:
            return all_devices

