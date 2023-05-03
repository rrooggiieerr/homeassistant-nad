"""Support for interfacing with NAD receivers through RS-232."""
from __future__ import annotations

import logging

from aiodiscover.discovery import _LOGGER
from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet

from . import NADReceiverCoordinator
from .const import (
    CONF_DEFAULT_MAX_VOLUME,
    CONF_DEFAULT_MIN_VOLUME,
    CONF_DEFAULT_VOLUME_STEP,
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_SOURCE_DICT,
    CONF_TYPE_SERIAL,
    CONF_TYPE_TELNET,
    CONF_VOLUME_STEP,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NAD Receiver media player."""
    coordinator: NADReceiverCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    if isinstance(coordinator.receiver, NADReceiverTCP):
        async_add_entities([NADtcp(coordinator)])
    elif isinstance(coordinator.receiver, NADReceiverTelnet) or isinstance(
        coordinator.receiver, NADReceiver
    ):
        async_add_entities([NADMain(coordinator), NADZone2(coordinator)])


class NAD(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a NAD Receiver."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    zone = "Main"

    def __init__(self, coordinator: NADReceiverCoordinator):
        """Initialize the NAD Receiver device."""
        super().__init__(coordinator, self.zone + ".Power")

        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = (
            f"{coordinator.unique_id}-mediaplayer-{self.zone.lower()}"
        )

        self._min_volume = coordinator.options.get(
            CONF_MIN_VOLUME, CONF_DEFAULT_MIN_VOLUME
        )
        self._max_volume = coordinator.options.get(
            CONF_MAX_VOLUME, CONF_DEFAULT_MAX_VOLUME
        )

        self._source_dict = coordinator.sources
        self._reverse_mapping = {value: key for key, value in self._source_dict.items()}

        coordinator.add_listener_command(self.zone + ".Mute")
        coordinator.add_listener_command(self.zone + ".Volume")
        coordinator.add_listener_command(self.zone + ".Source")

    async def async_added_to_hass(self) -> None:
        _LOGGER.debug("async_added_to_hass")
        await super().async_added_to_hass()

        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("_handle_coordinator_update")
        power_state = self.coordinator.data.get(self.zone + ".Power")
        if power_state is None:
            self._attr_state == None
            self._attr_available = False
        elif power_state.lower() == "off":
            self._attr_state = MediaPlayerState.OFF
            self._attr_available = True
        elif power_state.lower() == "on":
            self._attr_state = MediaPlayerState.ON
            self._attr_available = True

            self._attr_is_volume_muted = (
                self.coordinator.data.get(self.zone + ".Mute", "").lower() == "on"
            )

            volume = self.coordinator.data.get(self.zone + ".Volume")
            if volume.lstrip("-").isnumeric():
                volume = float(volume)
                self._attr_volume_level = self.calc_volume(volume)
            else:
                # Some receivers cannot report the volume, e.g. C 356BEE,
                # instead they only support stepping the volume up or down
                self._attr_volume_level = None

            source = int(self.coordinator.data.get(self.zone + ".Source"))
            self._attr_source = self._source_dict.get(source)

        self.async_write_ha_state()

    def turn_off(self) -> None:
        """Turn the media player off."""
        response = self.coordinator.exec_command(self.zone + ".Power", "=", "Off")
        if response.lower() == "off":
            self._attr_state = MediaPlayerState.OFF
            self.async_write_ha_state()

    def turn_on(self) -> None:
        """Turn the media player on."""
        response = self.coordinator.exec_command(self.zone + ".Power", "=", "On")
        if response.lower() == "on":
            self._attr_state = MediaPlayerState.ON
            self.async_write_ha_state()

    def volume_up(self) -> None:
        """Volume up the media player."""
        response = self.coordinator.exec_command(self.zone + ".Volume", "+")
        if response is not None and response.lstrip("-").isnumeric():
            self._attr_volume_level = self.calc_volume(float(response))
            self.async_write_ha_state()

    def volume_down(self) -> None:
        """Volume down the media player."""
        response = self.coordinator.exec_command(self.zone + ".Volume", "-")
        if response is not None and response.lstrip("-").isnumeric():
            self._attr_volume_level = self.calc_volume(float(response))
            self.async_write_ha_state()

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        response = self.coordinator.exec_command(
            self.zone + ".Volume", "=", int(self.calc_db(volume))
        )
        if response is not None and response.lstrip("-").isnumeric():
            self._attr_volume_level = self.calc_volume(float(response))
            self.async_write_ha_state()

    def mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        if mute:
            response = self.coordinator.exec_command(self.zone + ".Mute", "=", "On")
        else:
            response = self.coordinator.exec_command(self.zone + ".Mute", "=", "Off")

        if mute and response.lower() != "on":
            _LOGGER.error("Failed to mute volume")
        elif not mute and response.lower() != "off":
            _LOGGER.error("Failed to unmute volume")
        else:
            _LOGGER.debug("Volume %s", "muted" if mute else "unmuted")
            self._attr_is_volume_muted = mute
            self.async_write_ha_state()

    def select_source(self, source: str) -> None:
        """Select input source."""
        _LOGGER.debug("select_source(%s)", source)

        if source in self._reverse_mapping:
            source_id = self._reverse_mapping[source]
        elif source.isnumeric() and int(source) in self._source_dict:
            source_id = source
        else:
            raise HomeAssistantError(f"Source {source} invalid")

        _LOGGER.debug("Source ID: %s", source_id)

        response = self.coordinator.exec_command(self.zone + ".Source", "=", source_id)
        if response.isnumeric():
            self._attr_source = self._source_dict.get(int(response))
            self.async_write_ha_state()

    @property
    def source_list(self):
        """List of available input sources."""
        return list(self._reverse_mapping)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self._attr_available:
            return self._attr_available

        return self.coordinator.last_update_success

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


class NADMain(NAD):
    """Representation of a NAD Receiver - Zone 2."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )
    _attr_sound_mode_list = [
        "None",
        "ProLogic",
        "PLIIMovie",
        "PLIIMusic",
        "NEO6Cinema",
        "NEO6Music",
        "EARS",
        "EnhancedStereo",
        "AnalogBypass",
        "StereoDownmix",
        "SurroundEX",
    ]

    zone = "Main"

    def __init__(self, coordinator: NADReceiverCoordinator):
        """Initialize the NAD Receiver device."""
        super().__init__(coordinator)

        coordinator.add_listener_command(self.zone + ".ListeningMode")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()

        response = self.coordinator.data.get(self.zone + ".ListeningMode")
        if response is not None:
            self._attr_sound_mode = response
            self.async_write_ha_state()

    def select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        response = self.coordinator.exec_command(
            self.zone + ".ListeningMode", "=", sound_mode
        )
        if response is not None:
            self._attr_sound_mode = sound_mode
            self.async_write_ha_state()


class NADZone2(NAD):
    """Representation of a NAD Receiver - Zone 2."""

    _attr_name = "Zone 2"
    _attr_entity_registry_enabled_default = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    zone = "Zone2"
