"""Config flow for the NAD integration."""

import logging
from typing import Any, override
from urllib.parse import urlsplit

from nad_serial import NADDevice
from nad_serial.exceptions import NADBaseError
import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
    CONF_PORT,
    CONF_TYPE,
)
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.selector import SerialPortSelector
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import CONF_SERIAL_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_SERIAL_PORT): SerialPortSelector(),
    }
)
RECONFIGURE_SCHEMA = USER_SCHEMA


class NADConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAD."""

    VERSION = 2

    _host: str
    _device: NADDevice
    _mac: str | None = None

    @override
    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Zeroconf discovery: %s", discovery_info)

        if discovery_info.ip_address.version == 6:
            self._host = f"[{discovery_info.ip_address}]"
        else:
            self._host = str(discovery_info.ip_address)

        return await self.async_step_discovery_confirm()

    @override
    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle DHCP discovery."""
        mac = format_mac(discovery_info.macaddress)
        _LOGGER.debug("DHCP discovery: %s", discovery_info)

        for entry in self._async_current_entries():
            if entry.data.get(CONF_MAC) != mac:
                continue

            current = urlsplit(entry.data[CONF_SERIAL_PORT])
            if current.scheme == "socket" and current.hostname != discovery_info.ip:
                # Update the url with the new IP address
                url = f"socket://{discovery_info.ip}:23"
                _LOGGER.debug("Updating %s to %s", entry.title, url)
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_SERIAL_PORT: url}
                )
                self.hass.config_entries.async_schedule_reload(entry.entry_id)

            return self.async_abort(reason="already_configured")

        self._host = discovery_info.ip
        self._mac = mac

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle discovery confirmation."""
        if user_input is not None:
            title = self._device.name
            data = {
                CONF_SERIAL_PORT: f"socket://{self._host}:23",
                CONF_MODEL: self._device.model,
            }
            if self._mac:
                data[CONF_MAC] = self._mac

            return self.async_create_entry(title=title, data=data)

        url = f"socket://{self._host}:23"
        self._async_abort_entries_match({CONF_SERIAL_PORT: url})

        device = None
        try:
            # Test if we can connect to the device
            device = await NADDevice.async_connect(url)

            if device.serial_number:
                await self.async_set_unique_id(device.serial_number)

                updates: dict[str, str] = {}
                if self._mac:
                    updates[CONF_MAC] = self._mac

                if (
                    entry := self.hass.config_entries.async_entry_for_domain_unique_id(
                        DOMAIN, device.serial_number
                    )
                ) and entry.data[CONF_SERIAL_PORT].startswith("socket://"):
                    # Update the url with the new IP address
                    _LOGGER.debug("Updating %s to %s", entry.title, url)
                    updates[CONF_SERIAL_PORT] = url

                self._abort_if_unique_id_configured(updates=updates)

            self._device = device

            _LOGGER.info("%s available on %s", device.name, url)
        except NADBaseError:
            return self.async_abort(reason="cannot_connect")
        finally:
            if device:
                await device.async_disconnect()

        _LOGGER.debug("%s on %s is not yet configured", device.name, self._host)
        self.context.update(
            {
                "title_placeholders": {
                    "name": device.name,
                }
            }
        )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

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

                _LOGGER.info("%s available on %s", device.name, url)
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

            _LOGGER.info("%s available on %s", device.name, url)
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
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfigure flow."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            url = user_input[CONF_SERIAL_PORT]

            device = None
            try:
                # Test if we can connect to the device
                device = await NADDevice.async_connect(url)

                if (
                    reconfigure_entry.unique_id
                    and device.serial_number
                    and reconfigure_entry.unique_id != device.serial_number
                ):
                    errors["base"] = "not_same_device"

                _LOGGER.info("%s available on %s", device.name, url)
            except NADBaseError:
                errors["base"] = "cannot_connect"
            finally:
                if device:
                    await device.async_disconnect()

            if not errors:
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={CONF_SERIAL_PORT: url},
                )

        # Combine the current entry data with schema.
        data_schema = self.add_suggested_values_to_schema(
            RECONFIGURE_SCHEMA,
            user_input or reconfigure_entry.data,
        )

        return self.async_show_form(
            step_id="reconfigure",
            description_placeholders={"title": reconfigure_entry.title},
            data_schema=data_schema,
            errors=errors,
        )
