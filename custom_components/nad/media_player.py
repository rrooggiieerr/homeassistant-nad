"""Support for interfacing with NAD receivers through RS-232."""

import logging
from typing import override

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import ChildDeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from nad_serial import NADAmplifier, NADMultiZoneAmplifier, NADZone

from .const import DOMAIN
from .coordinator import NADCoordinator
from .entity import NADEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Receiver media player."""
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
    """Representation of a NAD media player."""

    _attr_has_entity_name = True
    _attr_name: str | None = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    _device: NADAmplifier
    _zone: str

    def __init__(self, coordinator: NADCoordinator, device: NADAmplifier | None = None):
        """Initialize the NAD media player."""
        super().__init__(coordinator, device)

        volume_config = self._device.get_setting_config(f"{self._zone}.Volume")
        if volume_config:
            self._min_volume = volume_config.get("min")
            self._max_volume = volume_config.get("max")
            step_db = volume_config.get("step", 1)
            if self._min_volume is not None and self._max_volume is not None:
                self._attr_volume_step = step_db / abs(self._max_volume - self._min_volume)

    def calc_volume(self, decibel):
        """Calculate the volume given the decibel.

        Return the volume (0..1).
        """
        return abs(self._min_volume - decibel) / abs(
            self._min_volume - self._max_volume
        )

    def calc_db(self, volume):
        """Calculate the decibel given the volume.

        Return the dB.
        """
        return self._min_volume + round(
            abs(self._min_volume - self._max_volume) * volume
        )

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
    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self._device.async_turn_on()
        self.async_write_ha_state()

    @override
    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self._device.async_turn_off()
        self.async_write_ha_state()

    @override
    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if mute:
            await self._device.async_mute()
        else:
            await self._device.async_unmute()
        self.async_write_ha_state()

    @override
    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self._device.async_set_volume(self.calc_db(volume))
        self.async_write_ha_state()

    @override
    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        keys = (
            [key for key, value in self._device.source_names.items() if value == source]
            if self._device.source_names
            else []
        )
        if keys:
            await self._device.async_set_source(keys[0])
            self.async_write_ha_state()
        else:
            raise HomeAssistantError("Unknown source")


class NADMainMediaPlayer(NADMediaPlayer):
    """Representation of a NAD zone."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )

    def __init__(self, coordinator: NADCoordinator):
        """Initialize the NAD Receiver device."""
        self._zone = "Main"

        super().__init__(coordinator)

        self._attr_unique_id = coordinator.unique_id

    @property
    def sound_mode(self) -> str | None:
        """Name of the current sound mode."""
        value = self._device.get_setting_value(f"{self._zone}.ListeningMode")
        return str(value) if value else None

    @property
    def sound_mode_list(self) -> list[str] | None:
        """List of available sound modes."""
        listening_mode_config = self._device.get_setting_config(
            f"{self._zone}.ListeningMode"
        )
        return listening_mode_config.get("values") if listening_mode_config else None

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        await self._device.async_change_setting(
            f"{self._zone}.ListeningMode", sound_mode
        )
        self.async_write_ha_state()


class NADZoneMediaPlayer(NADMediaPlayer):
    """Representation of a NAD zone."""

    _device: NADZone

    def __init__(
        self, coordinator: NADCoordinator, device: NADZone, device_info: ChildDeviceInfo
    ):
        """Initialize the NAD Receiver device."""
        self._zone = f"Zone{device.zone_number}"

        super().__init__(coordinator, device)

        self._attr_unique_id = f"{coordinator.unique_id}_zone{self._device.zone_number}"

        self._attr_device_info = device_info
