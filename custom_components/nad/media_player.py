"""Creates Media Player entities for the NAD Home Assistant integration."""

from datetime import timedelta
import logging
from typing import Any, override

from nad_serial import NADAmplifier, NADMultiZoneAmplifier, NADZone
import probatio

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    issue_registry as ir,
)
from homeassistant.helpers.device_registry import ChildDeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_SERIAL_PORT, DOMAIN
from .coordinator import NADCoordinator
from .entity import NADEntity, handle_nad_action_errors, handle_nad_update_errors

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1

PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
    {
        probatio.Optional(CONF_TYPE, default="RS232"): probatio.In(
            ["RS232", "Telnet", "TCP"]
        ),
        probatio.Optional(CONF_SERIAL_PORT, default="/dev/ttyUSB0"): cv.string,
        probatio.Optional(CONF_HOST): cv.string,
        probatio.Optional(CONF_PORT, default=53): cv.port,
        probatio.Optional(CONF_NAME, default="NAD Receiver"): cv.string,
        # Accepted for backwards compatibility, ignored
        probatio.Optional("min_volume"): int,
        probatio.Optional("max_volume"): int,
        probatio.Optional("volume_step"): int,
        probatio.Optional("sources"): dict,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import the YAML configuration into a config entry."""
    if CONF_HOST not in config and config[CONF_TYPE] in ("Telnet", "TCP"):
        # This would have never worked in the first place...
        return

    if config[CONF_TYPE] == "TCP":
        ir.async_create_issue(
            hass,
            DOMAIN,
            "yaml_tcp_not_supported",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key="yaml_tcp_not_supported",
        )
        return

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(config)
    )
    if (
        result.get("type") is FlowResultType.ABORT
        and result.get("reason") != "already_configured"
    ):
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"deprecated_yaml_import_issue_{result.get('reason')}",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.WARNING,
            translation_key=f"deprecated_yaml_import_issue_{result.get('reason')}",
            translation_placeholders=dict(result.get("description_placeholders") or {}),
        )
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        is_fixable=False,
        issue_domain=DOMAIN,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Media Player entities."""
    coordinator: NADCoordinator = config_entry.runtime_data

    entities: list[NADMediaPlayer] = []

    if isinstance(coordinator.device, NADAmplifier):
        entities.append(NADMainMediaPlayer(coordinator))

    if (
        isinstance(coordinator.device, NADMultiZoneAmplifier)
        and coordinator.device.zones
    ):
        device_registry = dr.async_get(hass)
        parent_device_id = dr.async_get_device_id_by_identifier(
            hass, (DOMAIN, coordinator.unique_id), config_entry_id=config_entry.entry_id
        )
        for zone in coordinator.device.zones:
            device_info = ChildDeviceInfo(
                parent_device_id=parent_device_id,
                identifiers={
                    (DOMAIN, f"{coordinator.unique_id}_zone{zone.zone_number}")
                },
                name=zone.name,
            )
            device_registry.async_get_or_create_child(
                config_entry_id=config_entry.entry_id,
                disabled_by=dr.DeviceEntryDisabler.INTEGRATION,
                **device_info,
            )
            entities.append(NADZoneMediaPlayer(coordinator, zone, device_info))

    async_add_entities(entities)


class NADMediaPlayer(NADEntity, MediaPlayerEntity):
    """NAD Media Player."""

    _attr_has_entity_name = True
    _attr_name: str | None = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
    )

    _device: NADAmplifier
    _zone: str

    _min_db: int | None = None
    _max_db: int | None = None

    def __init__(self, coordinator: NADCoordinator, device: NADAmplifier | None = None):
        """Initialize the NAD media player."""
        super().__init__(coordinator, device)

        volume_config = self._device.get_setting_config(f"{self._zone}.Volume")
        if volume_config:
            self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_STEP
            min_db = volume_config.get("min")
            max_db = volume_config.get("max")
            if min_db is not None and max_db is not None:
                self._min_db = int(min_db)
                self._max_db = int(max_db)
                self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_SET
                step_db = volume_config.get("step", 1)
                self._attr_volume_step = step_db / abs(self._max_db - self._min_db)

        if self._device.supports_setting(f"{self._zone}.Mute"):
            self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_MUTE

        if self._device.source_names:
            self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOURCE

    @override
    @callback
    def _async_nad_callback(self, setting: str, value: Any) -> None:
        """Handle settings pushed by the device."""
        if setting.lower().startswith((f"{self._zone.lower()}.", "source")):
            _LOGGER.debug("%s changed to %s", setting, value)
            self.async_write_ha_state()

    @override
    @handle_nad_update_errors
    async def async_update(self) -> None:
        """Update the media player."""
        if self._device.sends_updates:
            return

        if self._zone != "Main":
            await self._device.async_request_is_on()
        if not self._device.is_on:
            return

        if self.supported_features & MediaPlayerEntityFeature.VOLUME_SET:
            await self._device.async_request_volume()

        if self.supported_features & MediaPlayerEntityFeature.VOLUME_MUTE:
            await self._device.async_request_mute()

        if self.supported_features & MediaPlayerEntityFeature.SELECT_SOURCE:
            await self._device.async_request_source_name()

        if self.supported_features & MediaPlayerEntityFeature.SELECT_SOUND_MODE:
            await self._device.async_request_setting(f"{self._zone}.ListeningMode")

    def calc_volume(self, decibel: int | None) -> float | None:
        """Calculate the volume given the decibel.

        Return the volume (0..1).
        """
        if decibel is None or self._min_db is None or self._max_db is None:
            return None

        level = (decibel - self._min_db) / (self._max_db - self._min_db)
        return max(0.0, min(1.0, level))

    def calc_db(self, volume: float) -> int:
        """Calculate the decibel given the volume.

        Return the dB.
        """
        assert self._min_db is not None
        assert self._max_db is not None
        return self._min_db + round(abs(self._min_db - self._max_db) * volume)

    @property
    @override
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        return MediaPlayerState.ON if self._device.is_on else MediaPlayerState.OFF

    @property
    @override
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        return self.calc_volume(self._device.volume)

    @property
    @override
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        return self._device.muted

    @property
    @override
    def source(self) -> str | None:
        """Name of the current input source."""
        return self._device.source_name

    @property
    @override
    def source_list(self) -> list[str] | None:
        """List of available input sources."""
        return (
            list(self._device.source_names.values())
            if self._device.source_names
            else None
        )

    @override
    @handle_nad_action_errors
    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self._device.async_turn_on()

    @override
    @handle_nad_action_errors
    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self._device.async_turn_off()

    @override
    @handle_nad_action_errors
    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if mute:
            await self._device.async_mute()
        else:
            await self._device.async_unmute()

    @override
    @handle_nad_action_errors
    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self._device.async_set_volume(self.calc_db(volume))

    @override
    @handle_nad_action_errors
    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        keys = (
            [key for key, value in self._device.source_names.items() if value == source]
            if self._device.source_names
            else []
        )
        if keys:
            await self._device.async_set_source(keys[0])
        else:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unknown_source",
                translation_placeholders={"source": source},
            )

    @override
    @handle_nad_action_errors
    async def async_volume_up(self) -> None:
        """Turn volume up for media player."""
        if None in [self._max_db, self._min_db]:
            await self._device.async_increment(f"{self._zone}.Volume")
        else:
            await super().async_volume_up()

    @override
    @handle_nad_action_errors
    async def async_volume_down(self) -> None:
        """Turn volume down for media player."""
        if None in [self._max_db, self._min_db]:
            await self._device.async_decrement(f"{self._zone}.Volume")
        else:
            await super().async_volume_down()


class NADMainMediaPlayer(NADMediaPlayer):
    """NAD Main Media Player."""

    def __init__(self, coordinator: NADCoordinator):
        """Initialize the NAD Receiver device."""
        self._zone = "Main"

        super().__init__(coordinator)

        self._attr_unique_id = coordinator.unique_id

        if self._device.get_setting_config(f"{self._zone}.ListeningMode"):
            self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE

    @property
    @override
    def sound_mode(self) -> str | None:
        """Name of the current sound mode."""
        value = self._device.get_setting_value(f"{self._zone}.ListeningMode")
        return str(value) if value else None

    @property
    @override
    def sound_mode_list(self) -> list[str] | None:
        """List of available sound modes."""
        listening_mode_config = self._device.get_setting_config(
            f"{self._zone}.ListeningMode"
        )
        return listening_mode_config.get("values") if listening_mode_config else None

    @override
    @handle_nad_action_errors
    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        await self._device.async_change_setting(
            f"{self._zone}.ListeningMode", sound_mode
        )


class NADZoneMediaPlayer(NADMediaPlayer):
    """NAD Zone Media Player."""

    _device: NADZone

    def __init__(
        self, coordinator: NADCoordinator, device: NADZone, device_info: ChildDeviceInfo
    ):
        """Initialize the NAD Receiver device."""
        self._zone = f"Zone{device.zone_number}"

        super().__init__(coordinator, device)

        self._attr_unique_id = f"{coordinator.unique_id}_zone{self._device.zone_number}"

        self._attr_device_info = device_info
