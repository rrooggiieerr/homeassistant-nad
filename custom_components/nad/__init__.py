"""The NAD Device component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MODEL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
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

    url = entry.data[CONF_HOST]
    model = entry.data.get(CONF_MODEL)

    try:
        device = await NADDevice.async_connect(url)
    except NADConnectionError as ex:
        raise ConfigEntryNotReady(
            f"Unable to connect to NAD {model or 'device'} on {url}"
        ) from ex

    if (
        device.serial_number and device.serial_number != entry.unique_id
    ) or device.model != model:
        await device.async_disconnect()
        raise ConfigEntryNotReady(
            "Unable to connect to NAD {model or 'device'}, not the same device"
        )

    if not await device.async_ping():
        await device.async_disconnect()
        raise ConfigEntryNotReady(
            f"Unable to connect to NAD {model or 'device'} on {url}"
        )

    entry.runtime_data = NADCoordinator(hass, entry, device)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: NADCoordinator = entry.runtime_data
    await coordinator.device.async_disconnect()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
