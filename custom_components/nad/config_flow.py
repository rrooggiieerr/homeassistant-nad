"""Config flow for the NAD integration."""

import logging
from typing import Any, override

from nad_serial import NADDevice
from nad_serial.exceptions import NADBaseError
import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_MODEL, CONF_NAME, CONF_PORT, CONF_TYPE
from homeassistant.helpers.selector import SerialPortSelector

from .const import CONF_SERIAL_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_SERIAL_PORT): SerialPortSelector(),
    }
)


class NADConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAD."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate user input.
            url = user_input[CONF_SERIAL_PORT]
            self._async_abort_entries_match({CONF_SERIAL_PORT: url})

            device = None
            try:
                # Test if we can connect to the device
                device = await NADDevice.async_connect(url)

                if device.serial_number:
                    await self.async_set_unique_id(device.serial_number)
                    self._abort_if_unique_id_configured()

                _LOGGER.info("NAD %s available on %s", device.model, url)
            except NADBaseError:
                errors["base"] = "cannot_connect"
            finally:
                if device:
                    await device.async_disconnect()

            if device and not errors:
                return self.async_create_entry(
                    title=device.name,
                    data={CONF_SERIAL_PORT: url, CONF_MODEL: device.model},
                    options={},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import a YAML configuration."""
        if import_data[CONF_TYPE] == "Telnet":
            url = f"socket://{import_data[CONF_HOST]}:{import_data[CONF_PORT]}"
        else:
            url = import_data[CONF_SERIAL_PORT]

        self._async_abort_entries_match({CONF_SERIAL_PORT: url})

        device = None
        try:
            # Test if we can connect to the device
            device = await NADDevice.async_connect(url)

            if device.serial_number:
                await self.async_set_unique_id(device.serial_number)
                self._abort_if_unique_id_configured()

            _LOGGER.info("NAD %s available on %s", device.model, url)
        except NADBaseError:
            return self.async_abort(
                reason="cannot_connect", description_placeholders={"url": url}
            )
        finally:
            if device:
                await device.async_disconnect()

        return self.async_create_entry(
            title=import_data[CONF_NAME],
            data={
                CONF_SERIAL_PORT: url,
                CONF_MODEL: device.model,
                CONF_NAME: import_data[CONF_NAME],
            },
        )
