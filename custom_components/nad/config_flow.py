"""Config flow for the NAD Receiver integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import homeassistant.helpers.config_validation as cv
import serial
import serial.tools.list_ports
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet

from .const import (
    CONF_DEFAULT_MAX_VOLUME,
    CONF_DEFAULT_MIN_VOLUME,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_VOLUME_STEP,
    CONF_MANUAL_PATH,
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_SERIAL_PORT,
    CONF_SOURCE_DICT,
    CONF_TYPE_SERIAL,
    CONF_TYPE_TCP,
    CONF_TYPE_TELNET,
    CONF_VOLUME_STEP,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_SETUP_TELNET_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=CONF_DEFAULT_PORT): int,
    }
)

STEP_SETUP_TCP_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HOST): cv.string,
    }
)


class NADReceiverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAD Receiver."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            user_selection = user_input[CONF_TYPE]
            if user_selection == CONF_TYPE_SERIAL:
                return await self.async_step_setup_serial()

            if user_selection == CONF_TYPE_TELNET:
                return await self.async_step_setup_telnet()

            if user_selection == CONF_TYPE_TCP:
                return await self.async_step_setup_tcp()

        list_of_types = [CONF_TYPE_SERIAL, CONF_TYPE_TELNET, CONF_TYPE_TCP]

        schema = vol.Schema({vol.Required(CONF_TYPE): vol.In(list_of_types)})
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_setup_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the setup serial step."""
        errors: dict[str, str] = {}

        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        list_of_ports = {}
        for port in ports:
            list_of_ports[
                port.device
            ] = f"{port}, s/n: {port.serial_number or 'n/a'}" + (
                f" - {port.manufacturer}" if port.manufacturer else ""
            )

        self.STEP_SETUP_SERIAL_SCHEMA = vol.Schema(
            {
                vol.Exclusive(CONF_SERIAL_PORT, CONF_SERIAL_PORT): vol.In(
                    list_of_ports
                ),
                vol.Exclusive(
                    CONF_MANUAL_PATH, CONF_SERIAL_PORT, CONF_MANUAL_PATH
                ): cv.string,
            }
        )

        if user_input is not None:
            try:
                title, data, options = await self.validate_input_setup_serial(
                    user_input, errors
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=title, data=data, options=options)

        return self.async_show_form(
            step_id="setup_serial",
            data_schema=self.STEP_SETUP_SERIAL_SCHEMA,
            errors=errors,
        )

    async def validate_input_setup_serial(
        self, data: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        """Validate the user input allows us to connect.

        Data has the keys from STEP_SETUP_SERIAL_SCHEMA with values provided by the user.
        """
        # Validate the data can be used to set up a connection.
        self.STEP_SETUP_SERIAL_SCHEMA(data)

        serial_port = None
        if CONF_MANUAL_PATH in data:
            serial_port = data[CONF_MANUAL_PATH]
        elif CONF_SERIAL_PORT in data:
            serial_port = data[CONF_SERIAL_PORT]

        if serial_port is None:
            raise vol.error.RequiredFieldInvalid(CONF_SERIAL_PORT)

        serial_port = await self.hass.async_add_executor_job(
            get_serial_by_id, serial_port
        )

        # Test if the device exists
        if not os.path.exists(serial_port):
            raise vol.error.PathInvalid(f"Device {serial_port} does not exists")

        await self.async_set_unique_id(serial_port)
        self._abort_if_unique_id_configured()

        # Test if we can connect to the device
        try:
            # Get model from the device
            receiver = NADReceiver(serial_port)
            model = receiver.main_model("?")

            _LOGGER.info("Device %s available", serial_port)
        except serial.SerialException as ex:
            raise CannotConnect(
                f"Unable to connect to the device {serial_port}: {ex}", ex
            ) from ex

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {CONF_TYPE: CONF_TYPE_SERIAL, CONF_SERIAL_PORT: serial_port},
            {
                CONF_MIN_VOLUME: CONF_DEFAULT_MIN_VOLUME,
                CONF_MAX_VOLUME: CONF_DEFAULT_MAX_VOLUME,
                CONF_SOURCE_DICT: {},
            },
        )

    async def async_step_setup_telnet(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the setup serial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                title, data, options = await self.validate_input_setup_telnet(
                    user_input, errors
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=title, data=data, options=options)

        return self.async_show_form(
            step_id="setup_serial",
            data_schema=STEP_SETUP_TELNET_SCHEMA,
            errors=errors,
        )

    async def validate_input_setup_telnet(
        self, data: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        # Validate the data can be used to set up a connection.
        STEP_SETUP_TELNET_SCHEMA(data)

        host = data[CONF_HOST]
        port = data[CONF_PORT]

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        try:
            # Test if we can connect to the device
            receiver = NADReceiverTelnet(host, port)
            # Get model from the device
            model = receiver.main_model("?")

            _LOGGER.info("Device %s available", host)
        except Exception as ex:
            raise CannotConnect(
                f"Unable to connect to the device {host}: {ex}", ex
            ) from ex

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {CONF_TYPE: CONF_TYPE_TELNET, CONF_HOST: host, CONF_PORT: port},
            {
                CONF_MIN_VOLUME: CONF_DEFAULT_MIN_VOLUME,
                CONF_MAX_VOLUME: CONF_DEFAULT_MAX_VOLUME,
                CONF_SOURCE_DICT: {},
            },
        )

    async def async_step_setup_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the setup serial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                title, data, options = await self.validate_input_setup_tcp(
                    user_input, errors
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=title, data=data, options=options)

        return self.async_show_form(
            step_id="setup_serial",
            data_schema=STEP_SETUP_TCP_SCHEMA,
            errors=errors,
        )

    async def validate_input_setup_tcp(
        self, data: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        # Validate the data can be used to set up a connection.
        STEP_SETUP_TCP_SCHEMA(data)

        host = data[CONF_HOST]

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        try:
            # Test if we can connect to the device
            receiver = NADReceiverTCP(host)
            # Get model from the device
            model = receiver.main_model("?")

            _LOGGER.info("Device %s available", host)
        except Exception as ex:
            raise CannotConnect(
                f"Unable to connect to the device {host}: {ex}", ex
            ) from ex

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {CONF_TYPE: CONF_TYPE_TCP, CONF_HOST: host},
            {
                CONF_MIN_VOLUME: CONF_DEFAULT_MIN_VOLUME,
                CONF_MAX_VOLUME: CONF_DEFAULT_MAX_VOLUME,
                CONF_VOLUME_STEP: CONF_DEFAULT_VOLUME_STEP,
            },
        )


def get_serial_by_id(dev_path: str) -> str:
    """Return a /dev/serial/by-id match for given device if available."""
    by_id = "/dev/serial/by-id"
    if not os.path.isdir(by_id):
        return dev_path

    for path in (entry.path for entry in os.scandir(by_id) if entry.is_symlink()):
        if os.path.realpath(path) == dev_path:
            return path
    return dev_path


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
