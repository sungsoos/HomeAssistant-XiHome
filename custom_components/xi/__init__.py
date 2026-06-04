"""The 자이 integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import XiHomeClient
from .const import DOMAIN
from .coordinator import XiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.LIGHT, Platform.CLIMATE, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 자이 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Instantiate API client
    client = XiHomeClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        device_model="Home Assistant",
        session=async_get_clientsession(hass),
    )

    # Use entry.data[CONF_HOST] to configure AUTH_URL and DEVICE_URL if needed
    host = entry.data[CONF_HOST]
    if host:
        if not host.startswith(("http://", "https://")):
            client.AUTH_URL = f"https://{host}:5451/api"
            client.DEVICE_URL = f"https://{host}:5452/api"
        else:
            client.AUTH_URL = f"{host}:5451/api"
            client.DEVICE_URL = f"{host}:5452/api"

    try:
        await client.authenticate()
    except Exception as err:
        raise ConfigEntryNotReady(f"Failed to authenticate with 자이: {err}") from err

    coordinator = XiDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
