"""Tests for the NAD media player."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from nad_serial import NADAmplifier, NADMultiZoneAmplifier, NADZone
from nad_serial.exceptions import NADTimeoutError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nad.const import DOMAIN
from homeassistant.components.media_player import (
    ATTR_INPUT_SOURCE,
    ATTR_INPUT_SOURCE_LIST,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    ATTR_SOUND_MODE,
    ATTR_SOUND_MODE_LIST,
    DOMAIN as MEDIA_PLAYER_DOMAIN,
    SERVICE_SELECT_SOUND_MODE,
    SERVICE_SELECT_SOURCE,
    MediaPlayerEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
    SERVICE_VOLUME_UP,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from . import SERIAL_NUMBER, setup_integration

SOURCE_NAMES = {1: "CD", 2: "Tuner"}


@pytest.fixture(autouse=True)
def mock_media_player_platform() -> Generator[None]:
    """Only set up the media player platform."""
    with patch("custom_components.nad.PLATFORMS", [Platform.MEDIA_PLAYER]):
        yield


@pytest.fixture
def setting_configs() -> dict[str, dict[str, Any]]:
    """Return the setting configurations of the mocked device, by lowercase name."""
    return {
        "main.volume": {
            "max": 10,
            "min": -90,
            "operators": "=+-?",
            "step": 1,
            "type": "number",
        },
        "main.mute": {"operators": "=?", "type": "boolean"},
        "main.listeningmode": {
            "operators": "=+-?",
            "type": "enum",
            "values": ["Stereo", "Dolby"],
        },
    }


@pytest.fixture
def setting_values() -> dict[str, Any]:
    """Return the setting values of the mocked device, by lowercase name."""
    return {"main.listeningmode": "Stereo"}


def _configure_amplifier(
    device: MagicMock,
    setting_configs: dict[str, dict[str, Any]],
    setting_values: dict[str, Any],
) -> None:
    """Configure a mocked NAD amplifier or zone."""
    device.get_setting_config.side_effect = lambda setting: setting_configs.get(
        setting.lower()
    )
    device.supports_setting.side_effect = lambda setting: (
        setting.lower() in setting_configs
    )
    device.get_setting_value.side_effect = lambda setting: setting_values.get(
        setting.lower()
    )
    device.sends_updates = True
    device.is_on = True
    device.volume = -30
    device.muted = False
    device.source_names = SOURCE_NAMES
    device.source_name = "CD"
    for method in (
        "async_change_setting",
        "async_decrement",
        "async_increment",
        "async_mute",
        "async_request_is_on",
        "async_request_mute",
        "async_request_setting",
        "async_request_settings",
        "async_request_source_name",
        "async_request_volume",
        "async_set_source",
        "async_set_volume",
        "async_turn_off",
        "async_turn_on",
        "async_unmute",
    ):
        setattr(device, method, AsyncMock())


@pytest.fixture
def mock_amplifier(
    mock_nad_device: MagicMock,
    setting_configs: dict[str, dict[str, Any]],
    setting_values: dict[str, Any],
) -> MagicMock:
    """Return a mocked NAD amplifier."""
    mock_nad_device.__class__ = NADAmplifier
    _configure_amplifier(mock_nad_device, setting_configs, setting_values)
    return mock_nad_device


@pytest.fixture
async def entity_id(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_amplifier: MagicMock,
    mock_rs232_config_entry: MockConfigEntry,
) -> str:
    """Set up the integration and return the media player entity ID."""
    await setup_integration(hass, mock_rs232_config_entry)
    entity_id = er.async_get(hass).async_get_entity_id(
        MEDIA_PLAYER_DOMAIN, DOMAIN, SERIAL_NUMBER
    )
    assert entity_id
    return entity_id


async def _call(hass: HomeAssistant, service: str, entity_id: str, **data: Any) -> None:
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: entity_id, **data},
        blocking=True,
    )


async def _push_update(
    hass: HomeAssistant, device: MagicMock, setting: str, value: Any
) -> None:
    """Call the callback the entity registered with the device."""
    callback = device.add_callback.call_args[0][0]
    callback(setting, value)
    await hass.async_block_till_done()


async def test_state(hass: HomeAssistant, entity_id: str) -> None:
    """Test the media player state and attributes."""
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == pytest.approx(0.6)
    assert state.attributes[ATTR_MEDIA_VOLUME_MUTED] is False
    assert state.attributes[ATTR_INPUT_SOURCE] == "CD"
    assert state.attributes[ATTR_INPUT_SOURCE_LIST] == ["CD", "Tuner"]
    assert state.attributes[ATTR_SOUND_MODE] == "Stereo"
    assert state.attributes[ATTR_SOUND_MODE_LIST] == ["Stereo", "Dolby"]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )


async def test_state_off(
    hass: HomeAssistant, entity_id: str, mock_amplifier: MagicMock
) -> None:
    """Test the media player is off when the device is off."""
    mock_amplifier.is_on = False
    await _push_update(hass, mock_amplifier, "Main.Power", False)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


@pytest.mark.parametrize(
    ("volume", "expected"), [(-90, 0.0), (10, 1.0), (-100, 0.0), (19, 1.0)]
)
async def test_volume_level_clamped(
    hass: HomeAssistant,
    entity_id: str,
    mock_amplifier: MagicMock,
    volume: int,
    expected: float,
) -> None:
    """Test the volume level is clamped to 0..1."""
    mock_amplifier.volume = volume
    await _push_update(hass, mock_amplifier, "Main.Volume", volume)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == expected


@pytest.mark.parametrize(
    ("service", "data", "method", "args"),
    [
        (SERVICE_TURN_ON, {}, "async_turn_on", ()),
        (SERVICE_TURN_OFF, {}, "async_turn_off", ()),
        (
            SERVICE_VOLUME_SET,
            {ATTR_MEDIA_VOLUME_LEVEL: 0.5},
            "async_set_volume",
            (-40,),
        ),
        (SERVICE_VOLUME_UP, {}, "async_set_volume", (-29,)),
        (SERVICE_VOLUME_DOWN, {}, "async_set_volume", (-31,)),
        (SERVICE_VOLUME_MUTE, {ATTR_MEDIA_VOLUME_MUTED: True}, "async_mute", ()),
        (SERVICE_VOLUME_MUTE, {ATTR_MEDIA_VOLUME_MUTED: False}, "async_unmute", ()),
        (SERVICE_SELECT_SOURCE, {ATTR_INPUT_SOURCE: "Tuner"}, "async_set_source", (2,)),
        (
            SERVICE_SELECT_SOUND_MODE,
            {ATTR_SOUND_MODE: "Dolby"},
            "async_change_setting",
            ("Main.ListeningMode", "Dolby"),
        ),
    ],
)
async def test_actions(
    hass: HomeAssistant,
    entity_id: str,
    mock_amplifier: MagicMock,
    service: str,
    data: dict[str, Any],
    method: str,
    args: tuple[Any, ...],
) -> None:
    """Test the media player actions call the device."""
    await _call(hass, service, entity_id, **data)

    getattr(mock_amplifier, method).assert_awaited_once_with(*args)


async def test_select_unknown_source(
    hass: HomeAssistant, entity_id: str, mock_amplifier: MagicMock
) -> None:
    """Test selecting an unknown source raises."""
    with pytest.raises(HomeAssistantError):
        await _call(hass, SERVICE_SELECT_SOURCE, entity_id, source="Unknown")

    mock_amplifier.async_set_source.assert_not_awaited()


async def test_action_timeout(
    hass: HomeAssistant, entity_id: str, mock_amplifier: MagicMock
) -> None:
    """Test a device timeout is translated."""
    mock_amplifier.async_turn_on.side_effect = NADTimeoutError

    with pytest.raises(HomeAssistantError) as exc_info:
        await _call(hass, SERVICE_TURN_ON, entity_id)
    assert exc_info.value.translation_key == "timeout_error"


async def test_volume_range_changes_at_runtime(
    hass: HomeAssistant,
    entity_id: str,
    mock_amplifier: MagicMock,
    setting_configs: dict[str, dict[str, Any]],
) -> None:
    """Test the volume level and step follow a changed volume range."""
    setting_configs["main.volume"]["max"] = 0
    await _push_update(hass, mock_amplifier, "Main.Volume", -30)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == pytest.approx(60 / 90)

    await _call(hass, SERVICE_VOLUME_UP, entity_id)
    mock_amplifier.async_set_volume.assert_awaited_once_with(-29)

    mock_amplifier.async_set_volume.reset_mock()
    await _call(hass, SERVICE_VOLUME_SET, entity_id, volume_level=1.0)
    mock_amplifier.async_set_volume.assert_awaited_once_with(0)


@pytest.mark.parametrize(
    ("service", "method"),
    [(SERVICE_VOLUME_UP, "async_increment"), (SERVICE_VOLUME_DOWN, "async_decrement")],
)
async def test_volume_step_without_range(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_amplifier: MagicMock,
    mock_rs232_config_entry: MockConfigEntry,
    setting_configs: dict[str, dict[str, Any]],
    service: str,
    method: str,
) -> None:
    """Test volume up and down without a known volume range."""
    del setting_configs["main.volume"]["min"]
    del setting_configs["main.volume"]["max"]
    await setup_integration(hass, mock_rs232_config_entry)
    entity_id = er.async_get(hass).async_get_entity_id(
        MEDIA_PLAYER_DOMAIN, DOMAIN, SERIAL_NUMBER
    )
    assert entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    assert ATTR_MEDIA_VOLUME_LEVEL not in state.attributes
    features = state.attributes[ATTR_SUPPORTED_FEATURES]
    assert features & MediaPlayerEntityFeature.VOLUME_STEP
    assert not features & MediaPlayerEntityFeature.VOLUME_SET

    await _call(hass, service, entity_id)

    getattr(mock_amplifier, method).assert_awaited_once_with("Main.Volume")
    mock_amplifier.async_set_volume.assert_not_awaited()


async def test_zone_device_disabled_by_default(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_nad_device: MagicMock,
    mock_rs232_config_entry: MockConfigEntry,
    setting_configs: dict[str, dict[str, Any]],
) -> None:
    """Test zones get a child device that is disabled by default."""
    zone = MagicMock()
    zone.__class__ = NADZone
    zone.zone_number = 2
    zone.name = "Zone 2"
    _configure_amplifier(
        zone,
        {
            setting.replace("main.", "zone2."): config
            for setting, config in setting_configs.items()
        },
        {},
    )
    mock_nad_device.__class__ = NADMultiZoneAmplifier
    _configure_amplifier(mock_nad_device, setting_configs, {})
    mock_nad_device.zones = [zone]

    await setup_integration(hass, mock_rs232_config_entry)

    zone_device = dr.async_get(hass).async_get_child_device_by_identifier(
        (DOMAIN, f"{SERIAL_NUMBER}_zone2"), mock_rs232_config_entry.entry_id
    )
    assert zone_device is not None
    assert zone_device.disabled_by is dr.DeviceEntryDisabler.INTEGRATION

    entity_id = er.async_get(hass).async_get_entity_id(
        MEDIA_PLAYER_DOMAIN, DOMAIN, f"{SERIAL_NUMBER}_zone2"
    )
    assert entity_id is None or hass.states.get(entity_id) is None


VOLUME_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_STEP | MediaPlayerEntityFeature.VOLUME_SET
)


async def test_volume_control_fixed(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_amplifier: MagicMock,
    mock_rs232_config_entry: MockConfigEntry,
    setting_configs: dict[str, dict[str, Any]],
    setting_values: dict[str, Any],
) -> None:
    """Test volume control is disabled while the volume is fixed."""
    setting_configs["main.volumecontrol"] = {
        "operators": "=+-?",
        "type": "enum",
        "values": ["Variable", "Fixed"],
    }
    setting_values["main.volumecontrol"] = "Fixed"
    await setup_integration(hass, mock_rs232_config_entry)
    entity_id = er.async_get(hass).async_get_entity_id(
        MEDIA_PLAYER_DOMAIN, DOMAIN, SERIAL_NUMBER
    )
    assert entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    features = state.attributes[ATTR_SUPPORTED_FEATURES]
    assert not features & VOLUME_FEATURES
    assert features & MediaPlayerEntityFeature.VOLUME_MUTE

    with pytest.raises(HomeAssistantError):
        await _call(hass, SERVICE_VOLUME_SET, entity_id, volume_level=0.5)
    with pytest.raises(HomeAssistantError):
        await _call(hass, SERVICE_VOLUME_UP, entity_id)
    mock_amplifier.async_set_volume.assert_not_awaited()
    mock_amplifier.async_increment.assert_not_awaited()

    # The volume control is switched to variable on the device
    setting_values["main.volumecontrol"] = "Variable"
    await _push_update(hass, mock_amplifier, "Main.VolumeControl", "Variable")

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] & VOLUME_FEATURES == (
        VOLUME_FEATURES
    )

    await _call(hass, SERVICE_VOLUME_SET, entity_id, volume_level=0.5)
    mock_amplifier.async_set_volume.assert_awaited_once_with(-40)


async def test_volume_control_requested_when_added(
    hass: HomeAssistant, entity_id: str, mock_amplifier: MagicMock
) -> None:
    """Test the volume control is requested when the entity is added."""
    mock_amplifier.async_request_settings.assert_any_await(["Main.VolumeControl"])


async def test_update_requests_volume_settings(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    mock_amplifier: MagicMock,
    mock_rs232_config_entry: MockConfigEntry,
) -> None:
    """Test polling requests the volume control and volume range."""
    mock_amplifier.sends_updates = False
    await setup_integration(hass, mock_rs232_config_entry)
    assert await async_setup_component(hass, "homeassistant", {})
    entity_id = er.async_get(hass).async_get_entity_id(
        MEDIA_PLAYER_DOMAIN, DOMAIN, SERIAL_NUMBER
    )
    assert entity_id
    mock_amplifier.async_request_settings.reset_mock()

    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_amplifier.async_request_settings.assert_awaited_once_with(
        ["Main.VolumeControl", "Main.Volume.Min", "Main.Volume.Max"]
    )
    mock_amplifier.async_request_volume.assert_awaited_once()
