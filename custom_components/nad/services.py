"""Services for the NAD integration."""

from nad_serial.exceptions import NADBaseError, NADCommandError
import probatio

from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, service

from .const import DOMAIN
from .coordinator import NADConfigEntry

ATTR_SETTING = "setting"
ATTR_OPERATOR = "operator"
ATTR_VALUE = "value"

SERVICE_SEND_COMMAND = "send_command"

SEND_COMMAND_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        probatio.Required(ATTR_SETTING): cv.string,
        probatio.Required(ATTR_OPERATOR): probatio.In(["?", "=", "+", "-"]),
        probatio.Optional(ATTR_VALUE): cv.string,
    }
)


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
