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
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, UnitOfSoundPressure
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet

from . import CommandNotSupportedError, NADReceiverCoordinator
from .const import (
    CONF_DEFAULT_MAX_VOLUME,
    CONF_DEFAULT_MIN_VOLUME,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_VOLUME_STEP,
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
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_PORT, default=CONF_DEFAULT_PORT): NumberSelector(
            NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
        ),
    }
)

STEP_SETUP_TCP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(),
    }
)

STEP_CONFIG_VOLUME_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_MIN_VOLUME,
            default=CONF_DEFAULT_MIN_VOLUME,
        ): NumberSelector(
            NumberSelectorConfig(
                min=-92,
                max=20,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement=UnitOfSoundPressure.DECIBEL,
            )
        ),
        vol.Required(
            CONF_MAX_VOLUME,
            default=CONF_DEFAULT_MAX_VOLUME,
        ): NumberSelector(
            NumberSelectorConfig(
                min=-92,
                max=20,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement=UnitOfSoundPressure.DECIBEL,
            )
        ),
        # vol.Required(
        #     CONF_VOLUME_STEP,
        #     default=self.config_entry.options.get(
        #         CONF_VOLUME_STEP, CONF_DEFAULT_VOLUME_STEP
        #     ),
        # ): cv.positive_int,
    }
)


class NADReceiverConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAD Receiver."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["setup_serial", "setup_telnet", "setup_tcp"],
        )

    async def async_step_setup_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the setup serial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            title, data, options = await self.validate_input_setup_serial(
                user_input, errors
            )

            if not errors:
                return self.async_create_entry(title=title, data=data, options=options)

        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        list_of_ports = {}
        for port in ports:
            list_of_ports[port.device] = (
                f"{port}, s/n: {port.serial_number or 'n/a'}"
                + (f" - {port.manufacturer}" if port.manufacturer else "")
            )

        self._step_setup_serial_schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_PORT, default=""): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in list_of_ports.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        sort=True,
                    )
                ),
            }
        )

        if user_input is not None:
            data_schema = self.add_suggested_values_to_schema(
                self._step_setup_serial_schema, user_input
            )
        else:
            data_schema = self._step_setup_serial_schema

        return self.async_show_form(
            step_id="setup_serial",
            data_schema=data_schema,
            errors=errors,
        )

    async def validate_input_setup_serial(
        self, data: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        """Validate the user input allows us to connect.

        Data has the keys from _step_setup_serial_schema with values provided by the user.
        """
        # Validate the data can be used to set up a connection.
        self._step_setup_serial_schema(data)

        serial_port = data.get(CONF_SERIAL_PORT)

        if serial_port is None:
            raise vol.error.RequiredFieldInvalid("No serial port configured")

        serial_port = await self.hass.async_add_executor_job(
            get_serial_by_id, serial_port
        )

        # Test if the device exists.
        if not os.path.exists(serial_port):
            errors[CONF_SERIAL_PORT] = "nonexisting_serial_port"

        await self.async_set_unique_id(serial_port)
        self._abort_if_unique_id_configured()

        if errors.get(CONF_SERIAL_PORT) is None:
            # Test if we can connect to the device and get model
            try:
                receiver = NADReceiver(serial_port)
                model = receiver.main_model("?")
            except (serial.SerialException, CommandNotSupportedError):
                errors["base"] = "cannot_connect"
            else:
                assert model is not None, "Failed to retrieve receiver model"

                _LOGGER.info("Device %s available", serial_port)

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {
                CONF_TYPE: CONF_TYPE_SERIAL,
                CONF_SERIAL_PORT: serial_port,
            },
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
            title, data, options = await self.validate_input_setup_telnet(
                user_input, errors
            )

            if not errors:
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
        port = int(data[CONF_PORT])

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        try:
            # Test if we can connect to the device and get model
            receiver = NADReceiverTelnet(host, port)
            model = receiver.main_model("?")

            _LOGGER.info("Device %s available", host)
        except CommandNotSupportedError as ex:
            errors["base"] = "cannot_connect"

        # Return info that you want to store in the config entry.
        return (
            f"NAD {model}",
            {CONF_TYPE: CONF_TYPE_TELNET, CONF_HOST: host, CONF_PORT: port},
            {
                CONF_MIN_VOLUME: CONF_DEFAULT_MIN_VOLUME,
                CONF_MAX_VOLUME: CONF_DEFAULT_MAX_VOLUME,
            },
        )

    async def async_step_setup_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the setup serial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            title, data, options = await self.validate_input_setup_tcp(
                user_input, errors
            )

            if not errors:
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
            # Test if we can connect to the device and get model
            receiver = NADReceiverTCP(host)
            model = receiver.main_model("?")

            _LOGGER.info("Device %s available", host)
        except CommandNotSupportedError as ex:
            errors["base"] = "cannot_connect"

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
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return NADReceiverOptionsFlowHandler()


class NADReceiverOptionsFlowHandler(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            STEP_CONFIG_VOLUME_SCHEMA(user_input)
            user_input[CONF_MIN_VOLUME] = int(user_input[CONF_MIN_VOLUME])
            user_input[CONF_MAX_VOLUME] = int(user_input[CONF_MAX_VOLUME])
            # user_input[CONF_VOLUME_STEP] = int(user_input[CONF_VOLUME_STEP])
            return self.async_create_entry(title="", data=user_input)

        if user_input is not None:
            data_schema = self.add_suggested_values_to_schema(
                STEP_CONFIG_VOLUME_SCHEMA, user_input
            )
        else:
            data_schema = self.add_suggested_values_to_schema(
                STEP_CONFIG_VOLUME_SCHEMA, self.config_entry.options
            )

        return self.async_show_form(
            step_id="init", data_schema=data_schema, errors=errors
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
