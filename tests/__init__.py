"""Tests for the NAD custom integration."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

SERIAL_NUMBER = "K25T757A12345"
BUILD = "T757_PG536M_DAB"
MODEL = "T757"
SERIAL_PORT = "/dev/ttyUSB1"
HOST = "192.0.2.1"
MAC_ADDRESS = "90:56:82:aa:bb:cc"
URL = f"socket://{HOST}:23"


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the NAD integration for testing."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
