"""Tests for the 자이 Parking Location platform."""
from unittest.mock import AsyncMock, patch

from homeassistant.components.xi.const import DOMAIN
from homeassistant.core import HomeAssistant
from tests.common import MockConfigEntry  # noqa: TID251


async def test_parking_location_entities(hass: HomeAssistant) -> None:
    """Test parking location sensor entities."""
    mock_parking_data = {
        "list": [
            {
                "tagid": "0",
                "carno": "12가3456",
                "floor": "B1_2",
                "block": "102-B",
                "label": "지하 1_2층 102-B",
                "in_parking_datetime_label": "2026-06-04 12:00:00",
                "image_filename": "car_image.jpg",
            },
            {
                "tagid": "1",
                "carno": "78나9012",
                "floor": "",
                "block": "",
                "label": "",
                "in_parking_datetime_label": "",
                "image_filename": "",
            },
        ],
        "status": {
            "parking_register_method": "camera",
            "FAVORITE_PARKING_yn": "Y",
        },
    }

    with patch("homeassistant.components.xi.XiHomeClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.authenticate = AsyncMock(return_value={})
        mock_client.get_rooms = AsyncMock(return_value=[])
        mock_client.get_devices_by_room = AsyncMock(return_value=[])
        mock_client.get_parking_location = AsyncMock(return_value=mock_parking_data)
        mock_client.apt_code = "APT123"
        mock_client.dong_no = "102"
        mock_client.ho_no = "503"

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
            },
        )
        config_entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Check entity for car 1 (parked)
        entity_id_1 = "sensor.ju_ca_wi_ci_12ga3456"
        state_1 = hass.states.get(entity_id_1)
        # Search dynamically if slugification varies
        if state_1 is None:
            for state in hass.states.async_all():
                if state.entity_id.startswith("sensor.") and "12ga3456" in state.entity_id:
                    entity_id_1 = state.entity_id
                    state_1 = state
                    break

        assert state_1 is not None
        assert state_1.state == "지하 1_2층 102-B"
        assert state_1.attributes["carno"] == "12가3456"
        assert state_1.attributes["floor"] == "B1_2"
        assert state_1.attributes["block"] == "102-B"
        assert state_1.attributes["in_parking_datetime_label"] == "2026-06-04 12:00:00"
        assert state_1.attributes["image_filename"] == "car_image.jpg"
        assert state_1.attributes["tagid"] == "0"
        assert state_1.attributes["parking_register_method"] == "camera"
        assert state_1.attributes["favorite_parking"] is True

        # Check binary sensor for car 1 (parked)
        bin_entity_id_1 = None
        for state in hass.states.async_all():
            if state.entity_id.startswith("binary_sensor.") and "12ga3456" in state.entity_id:
                bin_entity_id_1 = state.entity_id
                break
        assert bin_entity_id_1 is not None
        bin_state_1 = hass.states.get(bin_entity_id_1)
        assert bin_state_1 is not None
        assert bin_state_1.state == "on"
        assert bin_state_1.attributes["carno"] == "12가3456"

        # Check device tracker for car 1 (parked)
        tracker_entity_id_1 = None
        for state in hass.states.async_all():
            if state.entity_id.startswith("device_tracker.") and "12ga3456" in state.entity_id:
                tracker_entity_id_1 = state.entity_id
                break
        assert tracker_entity_id_1 is not None
        tracker_state_1 = hass.states.get(tracker_entity_id_1)
        assert tracker_state_1 is not None
        assert tracker_state_1.state == "지하 1_2층 102-B"
        assert tracker_state_1.attributes["carno"] == "12가3456"

        # Check entity for car 2 (not parked)
        entity_id_2 = "sensor.ju_ca_wi_ci_78na9012"
        state_2 = hass.states.get(entity_id_2)
        if state_2 is None:
            for state in hass.states.async_all():
                if state.entity_id.startswith("sensor.") and "78na9012" in state.entity_id:
                    entity_id_2 = state.entity_id
                    state_2 = state
                    break

        assert state_2 is not None
        assert state_2.state == "미주차"
        assert state_2.attributes["carno"] == "78나9012"
        assert state_2.attributes["floor"] == ""
        assert state_2.attributes["block"] == ""
        assert state_2.attributes["in_parking_datetime_label"] == ""
        assert state_2.attributes["image_filename"] == ""
        assert state_2.attributes["tagid"] == "1"
        assert state_2.attributes["parking_register_method"] == "camera"
        assert state_2.attributes["favorite_parking"] is True

        # Check binary sensor for car 2 (not parked)
        bin_entity_id_2 = None
        for state in hass.states.async_all():
            if state.entity_id.startswith("binary_sensor.") and "78na9012" in state.entity_id:
                bin_entity_id_2 = state.entity_id
                break
        assert bin_entity_id_2 is not None
        bin_state_2 = hass.states.get(bin_entity_id_2)
        assert bin_state_2 is not None
        assert bin_state_2.state == "off"
        assert bin_state_2.attributes["carno"] == "78나9012"

        # Check device tracker for car 2 (not parked)
        tracker_entity_id_2 = None
        for state in hass.states.async_all():
            if state.entity_id.startswith("device_tracker.") and "78na9012" in state.entity_id:
                tracker_entity_id_2 = state.entity_id
                break
        assert tracker_entity_id_2 is not None
        tracker_state_2 = hass.states.get(tracker_entity_id_2)
        assert tracker_state_2 is not None
        assert tracker_state_2.state == "not_home"
        assert tracker_state_2.attributes["carno"] == "78나9012"

