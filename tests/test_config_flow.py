"""Tests for the NAD config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from nad_serial.exceptions import NADConnectionError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nad.const import CONF_SERIAL_PORT, DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_ZEROCONF
from homeassistant.const import CONF_MAC, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import HOST, MAC_ADDRESS, MODEL, SERIAL_NUMBER, SERIAL_PORT, URL

NEW_HOST = "192.0.2.2"
NEW_URL = f"socket://{NEW_HOST}:23"

DHCP_SERVICE_INFO = DhcpServiceInfo(
    ip=HOST, hostname="nadaabbcc", macaddress="905682aabbcc"
)
NEW_DHCP_SERVICE_INFO = DhcpServiceInfo(
    ip=NEW_HOST, hostname="nadaabbcc", macaddress="905682aabbcc"
)
ZEROCONF_SERVICE_INFO = ZeroconfServiceInfo(
    ip_address=ip_address(HOST),
    ip_addresses=[ip_address(HOST)],
    port=23,
    hostname="nad.local.",
    type="_telnet._tcp.local.",
    name="NAD T757 (NAD905682aabbcc)._telnet._tcp.local.",
    properties={},
)


@pytest.mark.usefixtures("mock_setup_entry")
async def test_dhcp(hass: HomeAssistant, mock_connect: AsyncMock) -> None:
    """Test a DHCP discovery creates an entry with the MAC address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO
    )
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_SERIAL_PORT: URL,
        CONF_MODEL: MODEL,
        CONF_MAC: MAC_ADDRESS,
    }


@pytest.mark.usefixtures("mock_setup_entry")
async def test_dhcp_known_mac_updates_ip(
    hass: HomeAssistant,
    mock_network_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
) -> None:
    """Test a known MAC updates the IP address, and doesn't connect."""
    mock_network_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=NEW_DHCP_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert mock_network_config_entry.data[CONF_SERIAL_PORT] == NEW_URL
    mock_connect.assert_not_awaited()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_dhcp_known_mac_serial_entry(
    hass: HomeAssistant, mock_connect: AsyncMock
) -> None:
    """Test a known MAC doesn't change an RS232 entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=SERIAL_NUMBER,
        data={CONF_SERIAL_PORT: SERIAL_PORT, CONF_MODEL: MODEL, CONF_MAC: MAC_ADDRESS},
        version=2,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO
    )
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_SERIAL_PORT] == SERIAL_PORT
    mock_connect.assert_not_awaited()


@pytest.mark.usefixtures("mock_setup_entry", "mock_connect")
async def test_dhcp_unique_id_updates_host(hass: HomeAssistant) -> None:
    """Test a known serial number updates the host and adds the MAC."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=SERIAL_NUMBER,
        data={CONF_SERIAL_PORT: URL, CONF_MODEL: MODEL},
        version=2,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=NEW_DHCP_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    assert result["reason"] == "already_configured"
    assert entry.data == {
        CONF_SERIAL_PORT: NEW_URL,
        CONF_MODEL: MODEL,
        CONF_MAC: MAC_ADDRESS,
    }


async def test_zeroconf_already_configured_url(
    hass: HomeAssistant,
    mock_network_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
) -> None:
    """Test an entry with the same URL aborts without connecting."""
    mock_network_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_SERVICE_INFO
    )
    assert result["reason"] == "already_configured"
    mock_connect.assert_not_awaited()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_zeroconf(hass: HomeAssistant, mock_connect: AsyncMock) -> None:
    """Test a zeroconf discovery creates an entry without a MAC address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_SERVICE_INFO
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"NAD {MODEL}"
    assert result["data"] == {CONF_SERIAL_PORT: URL, CONF_MODEL: MODEL}
    assert result["result"].unique_id == SERIAL_NUMBER
    mock_connect.assert_awaited_once_with(URL)


async def test_zeroconf_cannot_connect(
    hass: HomeAssistant, mock_connect: AsyncMock
) -> None:
    """Test a connection error aborts discovery."""
    mock_connect.side_effect = NADConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_SERVICE_INFO
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure(
    hass: HomeAssistant,
    mock_rs232_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
) -> None:
    """Test reconfiguring the same device on another port."""
    mock_rs232_config_entry.add_to_hass(hass)

    result = await mock_rs232_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_rs232_config_entry.data == {CONF_SERIAL_PORT: URL, CONF_MODEL: MODEL}
    assert mock_rs232_config_entry.title == f"NAD {MODEL}"
    mock_connect.assert_awaited_once_with(URL)


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_not_same_device(
    hass: HomeAssistant,
    mock_rs232_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
    mock_nad_device: MagicMock,
) -> None:
    """Test that reconfiguring using another device is refused."""
    mock_rs232_config_entry.add_to_hass(hass)
    mock_nad_device.serial_number = "OTHER_SERIAL_NUMBER"

    result = await mock_rs232_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_same_device"}
    assert mock_rs232_config_entry.data[CONF_SERIAL_PORT] == SERIAL_PORT


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_cannot_connect_recovers(
    hass: HomeAssistant,
    mock_rs232_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
) -> None:
    """Test a connection error during reconfigure."""
    mock_rs232_config_entry.add_to_hass(hass)
    mock_connect.side_effect = NADConnectionError

    result = await mock_rs232_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: URL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert mock_rs232_config_entry.data[CONF_SERIAL_PORT] == SERIAL_PORT

    mock_connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_rs232_config_entry.data[CONF_SERIAL_PORT] == URL


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_without_serial_number(
    hass: HomeAssistant,
    mock_rs232_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
    mock_nad_device: MagicMock,
) -> None:
    """Test that the device check is skipped when the device has no serial number."""
    mock_rs232_config_entry.add_to_hass(hass)
    mock_nad_device.serial_number = None

    result = await mock_rs232_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: URL}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_rs232_config_entry.data[CONF_SERIAL_PORT] == URL
