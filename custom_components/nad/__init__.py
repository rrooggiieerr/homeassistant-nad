"""The NAD Device component."""

from typing import Any

from nad_serial import NADDevice
from nad_serial.exceptions import NADBaseError

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_NAME,
    CONF_PORT,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.util import slugify

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


@callback
def _async_migrate_to_serial_number(
    hass: HomeAssistant, entry: NADConfigEntry, serial: str
) -> None:
    """Move an entry, its entities and devices from entry_id to the serial number."""
    if any(
        other.unique_id == serial
        for other in hass.config_entries.async_entries(DOMAIN)
        if other.entry_id != entry.entry_id
    ):
        return

    old = entry.entry_id

    entity_registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_registry, old):
        if entity.unique_id == old or entity.unique_id.startswith(
            (f"{old}-", f"{old}_")
        ):
            entity_registry.async_update_entity(
                entity.entity_id, new_unique_id=serial + entity.unique_id[len(old) :]
            )

    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, old):
        new_identifiers = {
            (domain, serial + ident[len(old) :])
            if domain == DOMAIN and ident.startswith(old)
            else (domain, ident)
            for domain, ident in device.identifiers
        }
        if new_identifiers != device.identifiers:
            device_registry.async_update_device(
                device.id, new_identifiers=new_identifiers
            )

    hass.config_entries.async_update_entry(entry, unique_id=serial)


async def async_setup_entry(hass: HomeAssistant, entry: NADConfigEntry) -> bool:
    """Set up NAD device from a config entry."""
    if entry.version == 1:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="binary_protocol_not_supported",
        )

    url = entry.data[CONF_SERIAL_PORT]
    model = entry.data.get(CONF_MODEL)

    try:
        device = await NADDevice.async_connect(url, model_hint=model)
    except NADBaseError as ex:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"url": url},
        ) from ex

    if (
        device.serial_number
        and entry.unique_id
        and device.serial_number != entry.unique_id
    ) or (model and device.model != model):
        await device.async_disconnect()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="not_same_device",
        )

    if not await device.async_ping():
        await device.async_disconnect()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"url": url},
        )

    if entry.unique_id is None and (serial := device.serial_number):
        _async_migrate_to_serial_number(hass, entry, serial)

    entry.runtime_data = NADCoordinator(hass, entry, device)

    if entry.source == SOURCE_IMPORT and (name := entry.data.get(CONF_NAME)):
        er.async_get(hass).async_get_or_create(
            Platform.MEDIA_PLAYER,
            DOMAIN,
            entry.runtime_data.unique_id,
            config_entry=entry,
            suggested_object_id=slugify(name),
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NADConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: NADConfigEntry) -> bool:
    """Migrate old config entries."""
    if entry.version > 2:
        # Downgrade from a future version
        return False

    if entry.version == 1:
        conf_type = entry.data.get(CONF_TYPE)

        if conf_type == "TCP":
            # Binary protocol, not supported
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"binary_protocol_not_supported_{entry.entry_id}",
                is_fixable=False,
                issue_domain=DOMAIN,
                severity=ir.IssueSeverity.ERROR,
                translation_key="binary_protocol_not_supported",
                translation_placeholders={"title": entry.title},
            )
            return True

        if conf_type is None:
            # Data is already in the current format
            hass.config_entries.async_update_entry(entry, version=2, minor_version=1)
            return True

        entry_id = entry.entry_id

        if conf_type == "Telnet":
            url = f"socket://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        else:
            url = entry.data[CONF_SERIAL_PORT]

        @callback
        def _migrate_entity(entity: er.RegistryEntry) -> dict[str, Any] | None:
            """Migrate the v1 media player unique ids."""
            if entity.unique_id == f"{entry_id}-mediaplayer-main":
                return {"new_unique_id": entry_id}
            if entity.unique_id.startswith(f"{entry_id}-mediaplayer-zone"):
                zone = entity.unique_id.removeprefix(f"{entry_id}-mediaplayer-zone")
                return {"new_unique_id": f"{entry_id}_zone{zone}"}
            # {entry_id}-{key} is unchanged
            return None

        await er.async_migrate_entries(hass, entry_id, _migrate_entity)

        # Drop the (nad, serial_port) identifier, keep (nad, entry_id)
        device_registry = dr.async_get(hass)
        if device := device_registry.async_get_device({(DOMAIN, entry_id)}):
            device_registry.async_update_device(
                device.id, new_identifiers={(DOMAIN, entry_id)}
            )

        hass.config_entries.async_update_entry(
            entry,
            data={CONF_SERIAL_PORT: url},
            options={},
            unique_id=None,
            version=2,
            minor_version=1,
        )

    return True


async def async_remove_entry(hass: HomeAssistant, entry: NADConfigEntry) -> None:
    """Clean up when a config entry is removed."""
    ir.async_delete_issue(
        hass, DOMAIN, f"binary_protocol_not_supported_{entry.entry_id}"
    )
