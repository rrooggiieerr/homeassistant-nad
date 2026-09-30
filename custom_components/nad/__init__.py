"""The NAD Device component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from nad_serial import NADDevice
from nad_serial.exceptions import NADConnectionError

from .coordinator import NADConfigEntry, NADCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: NADConfigEntry) -> bool:
    """Set up NAD device from a config entry."""

    try:
        device = await NADDevice.async_connect(entry.data[CONF_HOST])
    except NADConnectionError as ex:
        raise ConfigEntryNotReady("Unable to connect to NAD device") from ex

    coordinator = NADCoordinator(hass, entry, device)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady, ConfigEntryAuthFailed:
        await coordinator.device.async_disconnect()
        raise

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: NADCoordinator = entry.runtime_data
    await coordinator.device.async_disconnect()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
