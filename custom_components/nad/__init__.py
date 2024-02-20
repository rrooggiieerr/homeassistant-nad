"""The NAD Receiver component."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Callable

import homeassistant.helpers.config_validation as cv
import serial
import voluptuous as vol
from homeassistant.components.media_player.const import MediaPlayerState
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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
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
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.SENSOR,
]


class CommandNotSupportedError(Exception):
    """Error to indicate a command is not supported."""


class NADReceiverCoordinator(DataUpdateCoordinator):
    """NAD Receiver Data Update Coordinator."""

    unique_id = None
    model: str = None
    version: str = None
    device_info: DeviceInfo = None

    power_state = None

    _listener_commands = []

    def __init__(self, hass, entry: ConfigEntry):
        """Initialize NAD Receiver Data Update Coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=__name__,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=5),
        )

        self.config = entry.data
        self.options = entry.options
        self.receiver: NADReceiver = None

        config_type = self.config[CONF_TYPE]
        if config_type == CONF_TYPE_SERIAL:
            serial_port = self.config[CONF_SERIAL_PORT]
            self.receiver = NADReceiver(serial_port)
            self.unique_id = serial_port
        elif config_type == CONF_TYPE_TELNET:
            host = self.config[CONF_HOST]
            port = self.config[CONF_PORT]
            self.receiver = NADReceiverTelnet(host, port)
            self.unique_id = entry.entry_id
        elif config_type == CONF_TYPE_TCP:
            host = self.config[CONF_HOST]
            self.receiver = NADReceiverTCP(host)
            self.unique_id = entry.entry_id

    async def connect(self):
        if not self.model:
            # Open the connection by requesting the model
            try:
                self.model = self.exec_command("Main.Model", "?")
                self.version = self.exec_command("Main.Version", "?")
            except CommandNotSupportedError:
                raise ConfigEntryNotReady(f"Unable to connect to NAD receiver")

            self.device_info = DeviceInfo(
                identifiers={(DOMAIN, self.unique_id)},
                name=f"NAD {self.model}",
                model=self.model,
                manufacturer="NAD",
                sw_version=self.version,
            )

            self.sources = self.get_sources()

    async def disconnect(self):
        pass

    @callback
    def async_add_listener(
        self, update_callback: CALLBACK_TYPE, context: Any = None
    ) -> Callable[[], None]:
        remove_listener = super().async_add_listener(update_callback, context)

        _LOGGER.debug("Adding listener for %s", context)
        if context:
            self.add_listener_command(context)

        return remove_listener

    def add_listener_command(self, command):
        _LOGGER.debug("Adding command %s", command)
        if command not in self._listener_commands:
            self._listener_commands.append(command)

    def get_sources(self) -> {}:
        sources = {}

        for i in range(1, 13):
            try:
                response = self.exec_command(f"Source{i}.Enabled", "?")
                if response is not None and response.lower() == "yes":
                    response = self.exec_command(f"Source{i}.Name", "?")
                    sources[i] = response
            except CommandNotSupportedError:
                break

        return sources

    def supports_command(self, command: str):
        try:
            response = self.exec_command(command, "?")
        except CommandNotSupportedError:
            _LOGGER.debug("%s not supported", command)
            return False

        _LOGGER.debug("%s supported", command)
        if not self.data:
            self.data = {}
        self.data[command] = response

        return True

    def exec_command(self, command: str, operator: str, value: Optional = None):
        cmd = command + operator
        if value:
            cmd = f"{cmd}{value}"

        if self.config[CONF_TYPE] == CONF_TYPE_SERIAL:
            self.receiver.transport.ser.reset_input_buffer()

        try:
            msg = self.receiver.transport.communicate(cmd)
            _LOGGER.debug("sent: '%s' reply: '%s'", cmd, msg)

            if msg == "":
                raise CommandNotSupportedError()

            if msg.lower().startswith(command.lower() + "="):
                return msg.split("=")[1]
        except UnicodeDecodeError as ex:
            _LOGGER.error(ex)

        return None

    async def _async_update_data(self):
        """Fetch data from NAD Receiver."""
        try: 
            power_state = self.exec_command("Main.Power", "?")
        except CommandNotSupportedError:
            self.power_state = None
            raise UpdateFailed("Error communicating with NAD Receiver")

        _LOGGER.debug("power_state: %s", power_state)
        if not power_state:
            self.power_state = None
            raise UpdateFailed("Error communicating with NAD Receiver")

        if power_state.lower() == "on":
            self.power_state = MediaPlayerState.ON
        else:
            self.power_state = MediaPlayerState.OFF

        data = {}
        data["Main.Power"] = power_state

        for command in self._listener_commands:
            if command not in data:
                data[command] = self.exec_command(command, "?")

        return data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD Receiver from a config entry."""
    try:
        receiver_coordinator = NADReceiverCoordinator(hass, entry)

        # Open the connection.
        await receiver_coordinator.connect()

        _LOGGER.info("NAD receiver is available")
    except serial.SerialException as ex:
        raise ConfigEntryNotReady(f"Unable to connect to NAD receiver: {ex}") from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = receiver_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    receiver_coordinator: NADReceiverCoordinator = hass.data[DOMAIN][entry.entry_id]
    await receiver_coordinator.disconnect()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Configuration options updated, reloading NAD receiver integration")
    await hass.config_entries.async_reload(entry.entry_id)
