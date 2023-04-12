"""The NAD Receiver component."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Callable

import homeassistant.helpers.config_validation as cv
import serial
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet

from .const import (
    CONF_SERIAL_PORT,
    CONF_TYPE_SERIAL,
    CONF_TYPE_TCP,
    CONF_TYPE_TELNET,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD Receiver from a config entry."""
    try:
        receiver = None

        config_type = entry.data[CONF_TYPE]
        if config_type == CONF_TYPE_SERIAL:
            serial_port = entry.data[CONF_SERIAL_PORT]
            receiver = NADReceiver(serial_port)
        elif config_type == CONF_TYPE_TELNET:
            host = entry.data(CONF_HOST)
            port = entry.data[CONF_PORT]
            receiver = NADReceiverTelnet(host, port)
        elif config_type == CONF_TYPE_TCP:
            host = entry.data(CONF_HOST)
            receiver = NADReceiverTCP(host)

        # Open the connection by requesting the model
        receiver.main_model("?")

        _LOGGER.info("NAD receiver is available")
    except serial.SerialException as ex:
        raise ConfigEntryNotReady(f"Unable to connect to NAD receiver: {ex}") from ex

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = receiver

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # It should not be necessary to close the serial port because we close
    # it after every use in cover.py, i.e. no need to do entry["client"].close()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
