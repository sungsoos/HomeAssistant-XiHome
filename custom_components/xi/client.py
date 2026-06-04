"""API client for XiHome integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class XiHomeClient:
    """Client for interacting with the camellia-back.xihome.kr API."""

    AUTH_URL = "https://camellia-back.xihome.kr:5451/api"
    DEVICE_URL = "https://camellia-back.xihome.kr:5452/api"

    def __init__(
        self,
        username: str,
        password: str,
        device_token: str | None = None,
        device_model: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        apt_code: str | None = None,
        dong_no: str | None = None,
        ho_no: str | None = None,
        session: aiohttp.ClientSession | None = None,
        on_tokens_updated: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Initialize."""
        import uuid

        self.username = username
        self.password = password
        self.device_token = device_token or str(uuid.uuid4())
        self.device_model = "Home Assistant"
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.apt_code = apt_code
        self.dong_no = dong_no
        self.ho_no = ho_no
        self.session = session
        self.on_tokens_updated = on_tokens_updated

    def _notify_tokens_updated(self) -> None:
        """Notify that tokens or connection details have been updated."""
        if self.on_tokens_updated:
            self.on_tokens_updated(
                {
                    "device_token": self.device_token,
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "apt_code": self.apt_code,
                    "dong_no": self.dong_no,
                    "ho_no": self.ho_no,
                }
            )

    async def authenticate(self) -> dict[str, Any]:
        """Log in to get access token and household details."""
        url = f"{self.AUTH_URL}/auth/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "device_token": self.device_token,
            "device_model_name": self.device_model,
        }

        session = self.session or aiohttp.ClientSession()
        try:
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status not in (200, 201):
                    text = await response.text()
                    raise Exception(f"Login failed: {response.status} - {text}")
                data = await response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                last_house = data.get("last_selected_household") or {}
                self.apt_code = last_house.get("last_selected_apt_code")
                self.dong_no = last_house.get("last_selected_dong_no")
                self.ho_no = last_house.get("last_selected_ho_no")
                self._notify_tokens_updated()
                return data
        finally:
            if not self.session:
                await session.close()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for device control API."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "device_token": self.device_token,
            "Origin": "https://camellia-front.xihome.kr",
            "User-Agent": "Mozilla/5.0 (Linux; Android 16; SM-A366N) AppleWebKit/537.36 XiHome/1.0.0 python-lib",
            "Host": "camellia-back.xihome.kr:5452",
        }

    def _get_base_params(self) -> dict[str, str]:
        """Get base query parameters."""
        dong = self.dong_no or ""
        ho = self.ho_no or ""
        return {
            "dong_no": dong.lstrip("0"),
            "ho_no": ho.lstrip("0"),
            "apt_code": self.apt_code or "",
        }

    async def refresh_tokens(self) -> dict[str, Any]:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            raise Exception("No refresh token available")

        url = f"{self.AUTH_URL}/auth/token"
        payload = {
            "refresh_token": self.refresh_token,
            "device_token": self.device_token,
            "device_model_name": self.device_model,
        }

        session = self.session or aiohttp.ClientSession()
        try:
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status not in (200, 201):
                    text = await response.text()
                    raise Exception(f"Token refresh failed: {response.status} - {text}")
                data = await response.json()
                result = data.get("result") or data
                self.access_token = result.get("access_token")
                if result.get("refresh_token"):
                    self.refresh_token = result.get("refresh_token")
                self._notify_tokens_updated()
                return result
        finally:
            if not self.session:
                await session.close()

    async def get_rooms(self) -> list[dict[str, Any]]:
        """Retrieve rooms."""
        url = f"{self.DEVICE_URL}/device/room"
        session = self.session or aiohttp.ClientSession()
        try:
            async with session.get(
                url,
                params=self._get_base_params(),
                headers=self._get_headers(),
                ssl=False,
            ) as response:
                if response.status == 401:
                    _LOGGER.info("Access token expired (401), attempting token refresh")
                    await self.refresh_tokens()
                    async with session.get(
                        url,
                        params=self._get_base_params(),
                        headers=self._get_headers(),
                        ssl=False,
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                        return data.get("result", {}).get("rooms", [])
                response.raise_for_status()
                data = await response.json()
                return data.get("result", {}).get("rooms", [])
        finally:
            if not self.session:
                await session.close()

    async def get_devices_by_room(self, room_id: str) -> list[dict[str, Any]]:
        """Retrieve devices in a specific room."""
        url = f"{self.DEVICE_URL}/device/list-redis/by_room_id"
        params = self._get_base_params()
        params["room_id"] = room_id
        session = self.session or aiohttp.ClientSession()
        try:
            async with session.get(
                url, params=params, headers=self._get_headers(), ssl=False
            ) as response:
                if response.status == 401:
                    _LOGGER.info("Access token expired (401), attempting token refresh")
                    await self.refresh_tokens()
                    async with session.get(
                        url, params=params, headers=self._get_headers(), ssl=False
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                        return data.get("result", {}).get("devices", [])
                response.raise_for_status()
                data = await response.json()
                return data.get("result", {}).get("devices", [])
        finally:
            if not self.session:
                await session.close()

    async def send_command(
        self, endpoint: str, device_id: str, status: dict[str, Any]
    ) -> bool:
        """Send device command."""
        url = f"{self.DEVICE_URL}/device/{endpoint}/command"
        payload = {
            "device_id": device_id,
            "status": status,
        }
        payload.update(self._get_base_params())
        session = self.session or aiohttp.ClientSession()
        try:
            async with session.post(
                url, json=payload, headers=self._get_headers(), ssl=False
            ) as response:
                if response.status == 401:
                    _LOGGER.info("Access token expired (401), attempting token refresh")
                    try:
                        await self.refresh_tokens()
                    except Exception as err:
                        _LOGGER.error(
                            "Failed to refresh tokens during command: %s", err
                        )
                        return False
                    async with session.post(
                        url, json=payload, headers=self._get_headers(), ssl=False
                    ) as retry_response:
                        if retry_response.status not in (200, 204):
                            text = await retry_response.text()
                            _LOGGER.error(
                                "Failed to send command to %s (retry): %s - %s - Payload: %s",
                                url,
                                retry_response.status,
                                text,
                                payload,
                            )
                        return retry_response.status in (200, 204)
                if response.status not in (200, 204):
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to send command to %s: %s - %s - Payload: %s",
                        url,
                        response.status,
                        text,
                        payload,
                    )
                return response.status in (200, 204)
        finally:
            if not self.session:
                await session.close()

    async def get_acs_dust(self, device_id: str, dust_unit: str) -> dict[str, Any]:
        """Retrieve specific dust concentration reading (PM1.0, PM2.5, PM10)."""
        url = f"{self.DEVICE_URL}/device/acs/dust"
        params = self._get_base_params()
        params["device_id"] = device_id
        params["dust_unit"] = dust_unit
        session = self.session or aiohttp.ClientSession()
        try:
            token_used = self.access_token
            async with session.get(
                url, params=params, headers=self._get_headers(), ssl=False
            ) as response:
                if response.status == 401:
                    _LOGGER.info("Access token expired (401), attempting token refresh")
                    await self.async_refresh_tokens(token_used)
                    async with session.get(
                        url, params=params, headers=self._get_headers(), ssl=False
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                        return data.get("result", {})
                response.raise_for_status()
                data = await response.json()
                return data.get("result", {})
        finally:
            if not self.session:
                await session.close()

    async def get_parking_location(self) -> dict[str, Any]:
        """Retrieve parking location of household registered cars."""
        url = f"{self.DEVICE_URL}/public/parking_location"
        session = self.session or aiohttp.ClientSession()
        try:
            token_used = self.access_token
            async with session.get(
                url, params=self._get_base_params(), headers=self._get_headers(), ssl=False
            ) as response:
                if response.status == 401:
                    _LOGGER.info("Access token expired (401), attempting token refresh")
                    await self.async_refresh_tokens(token_used)
                    async with session.get(
                        url, params=self._get_base_params(), headers=self._get_headers(), ssl=False
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                        return data.get("result", {})
                response.raise_for_status()
                data = await response.json()
                return data.get("result", {})
        finally:
            if not self.session:
                await session.close()
