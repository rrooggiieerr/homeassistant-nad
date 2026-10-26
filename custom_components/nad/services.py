"""Services for the NAD integration."""

import re

from nad_serial.exceptions import NADBaseError, NADCommandError
import probatio

from homeassistant.const import ATTR_CONFIG_ENTRY_ID, ATTR_DEVICE_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    service,
)

from .const import DOMAIN
from .coordinator import NADConfigEntry

ATTR_SETTING = "setting"
ATTR_OPERATOR = "operator"
ATTR_VALUE = "value"
ATTR_CODE = "code"
ATTR_CHANNEL = "channel"

SERVICE_SEND_COMMAND = "send_command"
SERVICE_SEND_IR = "send_ir"

SEND_COMMAND_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        probatio.Required(ATTR_SETTING): cv.string,
        probatio.Required(ATTR_OPERATOR): probatio.In(["?", "=", "+", "-"]),
        probatio.Optional(ATTR_VALUE): cv.string,
    }
)

SEND_IR_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_DEVICE_ID): cv.string,
        probatio.Required(ATTR_CODE): probatio.All(
            probatio.Coerce(int), probatio.Range(min=0, max=255)
        ),
        probatio.Optional(ATTR_CHANNEL): probatio.All(
            probatio.Coerce(int), probatio.In([0, 1])
        ),
    }
)

ZONE_IDENTIFIER_RE = re.compile(r"_zone(\d+)$")


async def _async_send_command(call: ServiceCall) -> ServiceResponse:
    """Send a command to a NAD device and return its response."""
    entry: NADConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY_ID]
    )
    setting = call.data[ATTR_SETTING]
    operator = call.data[ATTR_OPERATOR]
    value = call.data.get(ATTR_VALUE) if operator == "=" else None
    try:
        response = await entry.runtime_data.device.async_request(
            setting, operator, value
        )
    except NADCommandError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_command",
            translation_placeholders={"error": str(err)},
        ) from err
    except NADBaseError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"error": str(err)},
        ) from err

    if operator != "?":
        entry.runtime_data.async_update_listeners()

    return {"response": response}


async def _async_send_ir(call: ServiceCall) -> None:
    """Send an IR code to a NAD device or zone."""
    device_id = call.data[ATTR_DEVICE_ID]
    if not (device_entry := dr.async_get(call.hass).async_get(device_id)):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="device_not_found",
            translation_placeholders={"device_id": device_id},
        )
    entry: NADConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, device_entry.config_entry_id
    )

    zone = "Main"
    for domain, identifier in device_entry.identifiers:
        if domain == DOMAIN and (match := ZONE_IDENTIFIER_RE.search(identifier)):
            zone = f"Zone{match.group(1)}"

    device = entry.runtime_data.device
    name = device_entry.name_by_user or device_entry.name or device.name
    channel = call.data.get(ATTR_CHANNEL)
    setting = f"{zone}.IR" if channel is None else f"{zone}.IR{channel + 1}"
    if not device.supports_setting(setting):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="ir_not_supported",
            translation_placeholders={"name": name, "setting": setting},
        )

    try:
        await device.async_change_setting(setting, call.data[ATTR_CODE])
    except NADCommandError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_command",
            translation_placeholders={"error": str(err)},
        ) from err
    except NADBaseError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"error": str(err)},
        ) from err


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the NAD services."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        _async_send_command,
        schema=SEND_COMMAND_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_IR, _async_send_ir, schema=SEND_IR_SCHEMA
    )
