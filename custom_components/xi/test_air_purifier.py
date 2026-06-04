"""Tests for the 자이 Air Purifier platform."""
from unittest.mock import AsyncMock, patch

from homeassistant.components.xi.const import DOMAIN
from homeassistant.core import HomeAssistant
from tests.common import MockConfigEntry  # noqa: TID251


async def test_air_purifier_entities(hass: HomeAssistant) -> None:
    """Test air purifier sensor entities."""
    mock_devices = {
        "vent_device_id_123": {
            "device_id": "vent_device_id_123",
            "type": "acs2",
            "device_name": "시스클라인",
            "room_name": "거실",
            "status": {
                "power": True,
                "erv_runstate": "1",
                "erv_air_volume": "1",
                "erv_mode": "manual",
                "erv_reserve_time": "0",
                "erv_state": "0",
                "fau_runstate": "1",
                "fau_air_volume": "2",
                "fau_mode": "manual",
                "fau_reserve_time": "0",
                "fau_state": "0",
                "co2_value": "501",
                "smell_value": "1",
                "humidity_value": "55",
            },
            "status_custom": {
                "status_txt": "켜짐",
                "device_status_txt": "정상",
                "filter_status_txt": "정상",
                "erv_state_disp_txt": "정상(0)",
                "fau_state_disp_txt": "정상(0)",
                "smell_status_txt": "좋음",
                "fau_status": {
                    "text": "중풍",
                    "value": 2,
                },
                "erv_status": {
                    "text": "약풍",
                    "value": 1,
                },
            },
        }
    }

    with patch("homeassistant.components.xi.XiHomeClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.authenticate = AsyncMock(return_value={})
        mock_client.get_rooms = AsyncMock(return_value=[{"room_id": "1", "room_name": "거실"}])
        mock_client.get_devices_by_room = AsyncMock(return_value=list(mock_devices.values()))
        mock_client.send_command = AsyncMock(return_value=True)

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

        # Find entities from all states to be slugification-independent
        co2_entity = None

        for state in hass.states.async_all():
            entity_id = state.entity_id
            if entity_id.startswith("sensor."):
                if entity_id.endswith("_isanhwatanso"):
                    co2_entity = entity_id

        # Verify sensor entities
        assert co2_entity is not None
        co2_state = hass.states.get(co2_entity)
        assert co2_state is not None
        assert co2_state.state == "501.0"
