"""Tests for importing the NAD YAML configuration."""

from unittest.mock import AsyncMock

from nad_serial.exceptions import NADConnectionError
import pytest

from custom_components.nad.const import CONF_SERIAL_PORT, DOMAIN
from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component


async def _setup_yaml(hass: HomeAssistant, platform_config: dict) -> None:
    assert await async_setup_component(
        hass,
        MEDIA_PLAYER_DOMAIN,
        {MEDIA_PLAYER_DOMAIN: [{"platform": DOMAIN, **platform_config}]},
    )
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_setup_entry")
@pytest.mark.parametrize(
    ("platform_config", "expected_url", "expected_title"),
    [
        ({}, "/dev/ttyUSB0", "NAD Receiver"),
        (
            {"type": "RS232", "serial_port": "/dev/ttyUSB1"},
            "/dev/ttyUSB1",
            "NAD Receiver",
        ),
        (
            {"type": "Telnet", "host": "192.0.2.1", "port": 23, "name": "Living room"},
            "socket://192.0.2.1:23",
            "Living room",
        ),
    ],
)
async def test_import(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    mock_connect: AsyncMock,
    platform_config: dict,
    expected_url: str,
    expected_title: str,
) -> None:
    """Test a successful YAML import."""
    await _setup_yaml(hass, platform_config)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.source == SOURCE_IMPORT
    assert entry.title == expected_title
    assert entry.unique_id == "K25T757A12345"
    assert entry.data[CONF_SERIAL_PORT] == expected_url
    mock_connect.assert_awaited_once_with(expected_url)

    assert issue_registry.async_get_issue(DOMAIN, "deprecated_yaml")


async def test_import_tcp(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry, mock_connect: AsyncMock
) -> None:
    """Test that TCP is not imported but raises the not supported issue."""
    await _setup_yaml(hass, {"type": "TCP", "host": "192.0.2.1"})

    assert not hass.config_entries.async_entries(DOMAIN)
    mock_connect.assert_not_awaited()
    issue = issue_registry.async_get_issue(DOMAIN, "yaml_tcp_not_supported")
    assert issue
    assert issue.severity is ir.IssueSeverity.ERROR


@pytest.mark.parametrize("conf_type", ["Telnet", "TCP"])
async def test_import_without_host(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    mock_connect: AsyncMock,
    conf_type: str,
) -> None:
    """Test that a config without host is silently ignored."""
    await _setup_yaml(hass, {"type": conf_type})

    assert not hass.config_entries.async_entries(DOMAIN)
    mock_connect.assert_not_awaited()
    assert not issue_registry.issues


@pytest.mark.usefixtures("mock_setup_entry")
async def test_import_cannot_connect(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry, mock_connect: AsyncMock
) -> None:
    """Test the import when the device can't be reached."""
    mock_connect.side_effect = NADConnectionError

    await _setup_yaml(hass, {"type": "RS232", "serial_port": "/dev/ttyUSB1"})

    assert not hass.config_entries.async_entries(DOMAIN)
    issue = issue_registry.async_get_issue(
        DOMAIN, "deprecated_yaml_import_issue_cannot_connect"
    )
    assert issue
    assert issue.translation_placeholders["url"] == "/dev/ttyUSB1"
    assert not issue_registry.async_get_issue(DOMAIN, "deprecated_yaml")


@pytest.mark.usefixtures("mock_setup_entry")
async def test_import_already_configured(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry, mock_connect: AsyncMock
) -> None:
    """Test that a second import fails, but still shows the YAML issue."""
    config = {"type": "RS232", "serial_port": "/dev/ttyUSB1"}
    await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={**config, "name": "NAD"}
    )
    await hass.async_block_till_done()
    mock_connect.reset_mock()

    await _setup_yaml(hass, config)

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    mock_connect.assert_not_awaited()
    assert issue_registry.async_get_issue(DOMAIN, "deprecated_yaml")
