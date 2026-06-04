"""Config flow for 자이 integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="camellia-back.xihome.kr"): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

class PlaceholderHub:
    """Placeholder class to make a simple connection class."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize."""
        self.host = host
        self.username = username
        self.password = password

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        host = self.host
        if not host.startswith(("http://", "https://")):
            url = f"https://{host}:5451/api/auth/login"
        else:
            url = f"{host}/auth/login"

        payload = {
            "username": self.username,
            "password": self.password,
            "device_token": "SAMPLE_FCM_DEVICE_TOKEN_STRING",
            "device_model_name": "Home Assistant"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, ssl=False, timeout=10) as response:
                    if response.status in (200, 201):
                        return True
                    if response.status == 400:
                        raise InvalidAuth
                    raise CannotConnect
        except Exception as err:
            raise CannotConnect from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 자이."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                hub = PlaceholderHub(
                    user_input[CONF_HOST],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                await hub.authenticate()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Name of the device", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
