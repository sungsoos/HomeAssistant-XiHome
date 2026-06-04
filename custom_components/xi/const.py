"""Constants for the 자이 integration."""

DOMAIN = "xi"

import re
from typing import Any


def get_device_friendly_name(room_name: str, device_data: dict[str, Any]) -> str:
    """Generate a clean, friendly Korean name for a device."""
    raw_name = (
        device_data.get("device_name_by_room")
        or device_data.get("device_name")
        or device_data.get("name")
        or ""
    )

    # Check if raw_name matches "1.디밍조명" or "1.대기"
    match = re.match(r"^(\d+)\.(.+)$", raw_name)
    if match:
        num = match.group(1)
        base_name = match.group(2).strip()

        # Friendly translations
        if base_name == "디밍조명":
            base_name = "조명"
        elif base_name == "대기":
            base_name = "대기전력"
        elif base_name == "환기":
            base_name = "환기시스템"

        friendly_name = f"{base_name} {num}"
    # Simple cleanup if no prefix number
    elif raw_name == "디밍조명":
        friendly_name = "조명"
    elif raw_name == "대기":
        friendly_name = "대기전력"
    elif raw_name == "환기":
        friendly_name = "환기시스템"
    else:
        friendly_name = raw_name

    # If it's heating, map to "난방"
    device_id = device_data.get("device_id") or ""
    device_type = device_data.get("device_type") or device_data.get("type") or ""
    if "heating" in device_id.lower() or "heating" in device_type.lower():
        friendly_name = "난방"

    return f"{room_name} {friendly_name}".strip()


def is_air_purifier(device_data: dict[str, Any]) -> bool:
    """Check if device is an air purifier / ventilator."""
    device_id = device_data.get("device_id") or ""
    device_type = device_data.get("device_type") or device_data.get("type") or ""
    keywords = ["vent", "purifier", "sysclein", "air", "환기", "공기청정", "acs"]
    return any(kw in device_id.lower() or kw in device_type.lower() for kw in keywords)
