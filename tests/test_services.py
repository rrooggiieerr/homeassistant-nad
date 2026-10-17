"""Tests for the NAD services."""

from unittest.mock import AsyncMock, MagicMock

from nad_serial.exceptions import NADCommandError, NADConnectionError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nad.const import DOMAIN
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import HomeAssistant, ServiceResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from . import setup_integration


async def _send(
    hass: HomeAssistant, entry: MockConfigEntry, **data: str
) -> ServiceResponse:
    return await hass.services.async_call(
        DOMAIN,
        "send_command",
        {ATTR_CONFIG_ENTRY_ID: entry.entry_id, **data},
        blocking=True,
        return_response=True,
    )


@pytest.mark.usefixtures("mock_connect", "mock_no_platforms")
@pytest.mark.parametrize(
    ("operator", "value", "expected_value"),
    [("?", None, None), ("=", "-30", "-30"), ("+", "5", None)],
)
async def test_send_command(
    hass: HomeAssistant,
    mock_rs232_config_entry: MockConfigEntry,
    mock_nad_device: MagicMock,
    operator: str,
    value: str | None,
    expected_value: str | None,
) -> None:
    """Test sending a command returns the device response."""
    await setup_integration(hass, mock_rs232_config_entry)

    mock_nad_device.async_request = AsyncMock(return_value=-30)
    data = {"setting": "Main.Volume", "operator": operator}
    if value is not None:
        data["value"] = value

    response = await _send(hass, mock_rs232_config_entry, **data)

    assert response == {"response": -30}
    mock_nad_device.async_request.assert_awaited_once_with(
        "Main.Volume", operator, expected_value
    )


@pytest.mark.usefixtures("mock_connect", "mock_no_platforms")
@pytest.mark.parametrize(
    ("side_effect", "expected", "translation_key"),
    [
        (NADCommandError("bad"), ServiceValidationError, "invalid_command"),
        (NADConnectionError("lost"), HomeAssistantError, "command_failed"),
    ],
)
async def test_send_command_errors(
    hass: HomeAssistant,
    mock_rs232_config_entry: MockConfigEntry,
    mock_nad_device: MagicMock,
    side_effect: Exception,
    expected: type[Exception],
    translation_key: str,
) -> None:
    """Test library errors are translated."""
    await setup_integration(hass, mock_rs232_config_entry)
    mock_nad_device.async_request = AsyncMock(side_effect=side_effect)

    with pytest.raises(expected) as exc_info:
        await _send(hass, mock_rs232_config_entry, setting="Main.Volume", operator="?")
    assert exc_info.value.translation_key == translation_key


@pytest.mark.usefixtures("mock_connect", "mock_no_platforms")
async def test_send_command_entry_not_loaded(
    hass: HomeAssistant, mock_rs232_config_entry: MockConfigEntry
) -> None:
    """Test the service refuses an entry that isn't loaded."""
    await setup_integration(hass, mock_rs232_config_entry)
    await hass.config_entries.async_unload(mock_rs232_config_entry.entry_id)

    with pytest.raises(ServiceValidationError) as exc_info:
        await _send(hass, mock_rs232_config_entry, setting="Main.Volume", operator="?")
    assert exc_info.value.translation_key == "service_config_entry_not_loaded"
