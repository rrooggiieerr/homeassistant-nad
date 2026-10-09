"""Tests for the NAD config entry migration."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nad.const import CONF_SERIAL_PORT, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)

from . import HOST, MODEL, SERIAL_NUMBER, SERIAL_PORT


def _add_v1_config_entry(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    data: dict,
    unique_id: str,
) -> tuple[MockConfigEntry, str, str]:
    """Add a v1 config entry with a device and entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        title=f"NAD {MODEL}",
        unique_id=unique_id,
        data=data,
        options={"min_volume": -92, "max_volume": -20, "volume_step": 4},
    )
    entry.add_to_hass(hass)

    identifiers = {(DOMAIN, entry.entry_id)}
    if CONF_SERIAL_PORT in data:
        identifiers.add((DOMAIN, data[CONF_SERIAL_PORT]))
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers=identifiers
    )

    media_player = entity_registry.async_get_or_create(
        "media_player",
        DOMAIN,
        f"{entry.entry_id}-mediaplayer-main",
        config_entry=entry,
    )
    switch = entity_registry.async_get_or_create(
        "switch", DOMAIN, f"{entry.entry_id}-main.speakera", config_entry=entry
    )
    return entry, media_player.entity_id, switch.entity_id


@pytest.mark.usefixtures("mock_connect", "mock_no_platforms")
@pytest.mark.parametrize(
    ("data", "old_unique_id", "expected_url"),
    [
        ({"type": "RS232", "serial_port": SERIAL_PORT}, SERIAL_PORT, SERIAL_PORT),
        (
            {"type": "Telnet", "host": HOST, "port": 23},
            HOST,
            f"socket://{HOST}:23",
        ),
    ],
)
async def test_migrate_v1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    data: dict,
    old_unique_id: str,
    expected_url: str,
) -> None:
    """Test migrating a v1 config entry for a device with serial number."""
    entry, media_player_id, switch_id = _add_v1_config_entry(
        hass, device_registry, entity_registry, data, old_unique_id
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == 2
    assert entry.minor_version == 1
    assert entry.unique_id == SERIAL_NUMBER
    assert entry.data == {CONF_SERIAL_PORT: expected_url}
    assert entry.options == {}

    # Same entity_ids, new unique ids
    assert entity_registry.async_get(media_player_id).unique_id == SERIAL_NUMBER
    assert (
        entity_registry.async_get(switch_id).unique_id
        == f"{SERIAL_NUMBER}-main.speakera"
    )

    # One device, identified by the serial number
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert len(devices) == 1
    assert devices[0].identifiers == {(DOMAIN, SERIAL_NUMBER)}


@pytest.mark.usefixtures("mock_connect", "mock_no_platforms")
async def test_migrate_v1_no_serial_number(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_nad_device: MagicMock,
) -> None:
    """Test migrating a v1 config entry for a device without a serial number."""
    mock_nad_device.serial_number = None
    entry, media_player_id, switch_id = _add_v1_config_entry(
        hass,
        device_registry,
        entity_registry,
        {"type": "RS232", "serial_port": SERIAL_PORT},
        SERIAL_PORT,
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 2
    assert entry.minor_version == 1
    assert entry.unique_id is None
    assert entity_registry.async_get(media_player_id).unique_id == entry.entry_id
    assert (
        entity_registry.async_get(switch_id).unique_id
        == f"{entry.entry_id}-main.speakera"
    )
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert devices[0].identifiers == {(DOMAIN, entry.entry_id)}


@pytest.mark.usefixtures("mock_no_platforms")
async def test_migrate_v1_tcp(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    mock_connect: AsyncMock,
) -> None:
    """Test that a v1 config entry stays at v1 and raises an issue when type is TCP."""
    data = {"type": "TCP", "host": HOST}
    entry = MockConfigEntry(
        domain=DOMAIN, version=1, minor_version=1, unique_id=HOST, data=data
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.version == 1
    assert entry.data == data
    mock_connect.assert_not_awaited()

    issue_id = f"binary_protocol_not_supported_{entry.entry_id}"
    assert issue_registry.async_get_issue(DOMAIN, issue_id)

    # Removing the entry removes the issue
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)


async def test_migrate_future_version(hass: HomeAssistant) -> None:
    """Test that a configuration entry from a future version is not set up."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data={CONF_SERIAL_PORT: SERIAL_PORT}
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.MIGRATION_ERROR
