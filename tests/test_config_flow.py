"""Tests for the NAD reconfigure flow."""

from unittest.mock import AsyncMock, MagicMock

from nad_serial.exceptions import NADConnectionError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nad.const import CONF_SERIAL_PORT
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import HOST, MODEL, SERIAL_PORT

NEW_URL = f"socket://{HOST}:23"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_connect: AsyncMock
) -> None:
    """Test reconfiguring the same device on another port."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: NEW_URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {CONF_SERIAL_PORT: NEW_URL, CONF_MODEL: MODEL}
    assert mock_config_entry.title == f"NAD {MODEL}"
    mock_connect.assert_awaited_once_with(NEW_URL)


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_not_same_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
    mock_nad_device: MagicMock,
) -> None:
    """Test that reconfiguring using another device is refused."""
    mock_config_entry.add_to_hass(hass)
    mock_nad_device.serial_number = "OTHER_SERIAL_NUMBER"

    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: NEW_URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_same_device"}
    assert mock_config_entry.data[CONF_SERIAL_PORT] == SERIAL_PORT


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_cannot_connect_recovers(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_connect: AsyncMock
) -> None:
    """Test a connection error during reconfigure."""
    mock_config_entry.add_to_hass(hass)
    mock_connect.side_effect = NADConnectionError

    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: NEW_URL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert mock_config_entry.data[CONF_SERIAL_PORT] == SERIAL_PORT

    mock_connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: NEW_URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_SERIAL_PORT] == NEW_URL


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_without_serial_number(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
    mock_nad_device: MagicMock,
) -> None:
    """Test that the device check is skipped when the device has no serial number."""
    mock_config_entry.add_to_hass(hass)
    mock_nad_device.serial_number = None

    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: NEW_URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_SERIAL_PORT] == NEW_URL
