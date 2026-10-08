"""The NAD Device component."""

from nad_serial import NADDevice
from nad_serial.exceptions import NADBaseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MODEL, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady

from .const import CONF_SERIAL_PORT, DOMAIN
from .coordinator import NADConfigEntry, NADCoordinator

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, entry: NADConfigEntry) -> bool:
    """Set up NAD device from a config entry."""

    if CONF_SERIAL_PORT in entry.data:
        url = entry.data[CONF_SERIAL_PORT]
    elif CONF_HOST in entry.data and CONF_PORT in entry.data:
        url = f"socket://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
    else:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="binary_protocol_not_supported",
        )

    model = entry.data.get(CONF_MODEL)

    try:
        device = await NADDevice.async_connect(url, model_hint=model)
    except NADBaseError as ex:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"url": url},
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
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"url": url},
        )

    entry.runtime_data = NADCoordinator(hass, entry, device)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
