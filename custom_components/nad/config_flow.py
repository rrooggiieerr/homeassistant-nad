"""Config flow for the NAD Receiver integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import homeassistant.helpers.config_validation as cv
import serial
import serial.tools.list_ports
import voluptuous as vol
from aiodiscover.discovery import _LOGGER
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet

from . import NADReceiverCoordinator
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
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=CONF_DEFAULT_PORT): cv.port,
    }
)

STEP_SETUP_TCP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
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
            except CannotConnectError:
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
            raise vol.error.RequiredFieldInvalid("No serial port configured")

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
            assert model is not None, "Failed to retrieve receiver model"

            _LOGGER.info("Device %s available", serial_port)
        except serial.SerialException as ex:
            raise CannotConnectError(
                f"Unable to connect to the device {serial_port}: {ex}", ex
            ) from ex

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {CONF_TYPE: CONF_TYPE_SERIAL, CONF_SERIAL_PORT: serial_port},
            {
                CONF_MIN_VOLUME: CONF_DEFAULT_MIN_VOLUME,
                CONF_MAX_VOLUME: CONF_DEFAULT_MAX_VOLUME,
                CONF_VOLUME_STEP: CONF_DEFAULT_VOLUME_STEP,
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
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=title, data=data, options=options)

        return self.async_show_form(
            step_id="setup_telnet",
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
            raise CannotConnectError(
                f"Unable to connect to the device {host}: {ex}", ex
            ) from ex

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {CONF_TYPE: CONF_TYPE_TELNET, CONF_HOST: host, CONF_PORT: port},
            {
                CONF_MIN_VOLUME: CONF_DEFAULT_MIN_VOLUME,
                CONF_MAX_VOLUME: CONF_DEFAULT_MAX_VOLUME,
                CONF_VOLUME_STEP: CONF_DEFAULT_VOLUME_STEP,
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
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=title, data=data, options=options)

        return self.async_show_form(
            step_id="setup_tcp",
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
            raise CannotConnectError(
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return NADReceiverOptionsFlowHandler(config_entry)


class NADReceiverOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        _LOGGER.debug(config_entry.data)
        self.config_entry = config_entry
        self.updated_options = {}
        self.sources = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        STEP_CONFIG_VOLUME_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_MIN_VOLUME,
                    default=self.config_entry.options.get(
                        CONF_MIN_VOLUME, CONF_DEFAULT_MIN_VOLUME
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=-92, max=20)),
                vol.Required(
                    CONF_MAX_VOLUME,
                    default=self.config_entry.options.get(
                        CONF_MAX_VOLUME, CONF_DEFAULT_MAX_VOLUME
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=-92, max=20)),
                # vol.Required(
                #     CONF_VOLUME_STEP,
                #     default=self.config_entry.options.get(
                #         CONF_VOLUME_STEP, CONF_DEFAULT_VOLUME_STEP
                #     ),
                # ): cv.positive_int,
            }
        )

        if user_input is not None:
            STEP_CONFIG_VOLUME_SCHEMA(user_input)
            # self.updated_options[CONF_MIN_VOLUME] = user_input[CONF_MIN_VOLUME]
            # self.updated_options[CONF_MAX_VOLUME] = user_input[CONF_MAX_VOLUME]
            # self.updated_options[CONF_VOLUME_STEP] = user_input[CONF_VOLUME_STEP]
            # return await self.async_step_sources()
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init", data_schema=STEP_CONFIG_VOLUME_SCHEMA, errors=errors
        )

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if CONF_SOURCE_DICT in self.updated_options:
            sources = self.updated_options[CONF_SOURCE_DICT]
        else:
            sources = self.config_entry.options.get(CONF_SOURCE_DICT, {})

            coordinator: NADReceiverCoordinator = self.hass.data[DOMAIN][
                self.config_entry.entry_id
            ]
            sources = {**coordinator.get_sources(), **sources}
            self.updated_options[CONF_SOURCE_DICT] = sources

            self.STEP_CONFIG_SOURCES_SCHEMA = vol.Schema({})
            for source in sources:
                _LOGGER.debug(source)
                self.STEP_CONFIG_SOURCES_SCHEMA = (
                    self.STEP_CONFIG_SOURCES_SCHEMA.extend(
                        {
                            vol.Required(
                                str(source),
                                default=sources[source],
                            ): str
                        }
                    )
                )

        if user_input is not None:
            self.STEP_CONFIG_SOURCES_SCHEMA(user_input)
            for item in user_input:
                if item.isnumeric():
                    self.updated_options[CONF_SOURCE_DICT][int(item)] = user_input[item]
            _LOGGER.debug(self.updated_options)
            return self.async_create_entry(title="", data=self.updated_options)

        return self.async_show_form(
            step_id="sources",
            data_schema=self.STEP_CONFIG_SOURCES_SCHEMA,
            errors=errors,
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


class CannotConnectError(HomeAssistantError):
    """Error to indicate we cannot connect."""
