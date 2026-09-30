"""The NAD Device component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_PORT,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from nad_serial import NADDevice
from nad_serial.exceptions import NADConnectionError

from .const import CONF_SERIAL_PORT
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

    if CONF_SERIAL_PORT in entry.data:
        url = entry.data[CONF_SERIAL_PORT]
    elif CONF_HOST in entry.data and CONF_PORT in entry.data:
        url = f"socket://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
    else:
        raise ConfigEntryNotReady(
            "The binary protocol that some NAD devices, like the D-series, use on TCP port 50001 is currently not supported."
        )

    model = entry.data.get(CONF_MODEL)

    try:
        device = await NADDevice.async_connect(url)
    except NADConnectionError as ex:
        raise ConfigEntryNotReady(
            f"Unable to connect to NAD {model or 'device'} on {url}"
        ) from ex

    # if (
    #     device.serial_number and device.serial_number != entry.unique_id
    # ) or (model and device.model != model):
    #     await device.async_disconnect()
    #     raise ConfigEntryNotReady(
    #         f"Unable to connect to NAD {model or 'device'}, not the same device"
    #     )

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
