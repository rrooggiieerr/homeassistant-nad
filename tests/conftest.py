"""Fixtures for the NAD integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations."""


@pytest.fixture(autouse=True)
def mock_usb(hass: HomeAssistant) -> None:
    """Mock the USB component to prevent setup failures."""
    hass.config.components.add("usb")


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Prevent the config entry from being set up."""
    with patch(
        "custom_components.nad.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_nad_device() -> MagicMock:
    """Return a mocked NAD device."""
    device = MagicMock()
    device.model = "T755"
    device.name = "NAD T755"
    device.serial_number = "K25T757A12345"
    device.async_disconnect = AsyncMock()
    return device


@pytest.fixture
def mock_connect(mock_nad_device: MagicMock) -> Generator[AsyncMock]:
    """Patch NADDevice.async_connect in the config flow."""
    with patch(
        "custom_components.nad.config_flow.NADDevice.async_connect",
        return_value=mock_nad_device,
    ) as mock:
        yield mock
