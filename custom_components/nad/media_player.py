"""Support for interfacing with NAD receivers through RS-232."""
from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from nad_receiver import NADReceiver, NADReceiverTCP, NADReceiverTelnet

from . import NADReceiverCoordinator
from .const import (
    CONF_DEFAULT_MAX_VOLUME,
    CONF_DEFAULT_MIN_VOLUME,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_VOLUME_STEP,
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_SERIAL_PORT,
    CONF_SOURCE_DICT,
    CONF_VOLUME_STEP,
    DOMAIN,
)

CONF_DEFAULT_TYPE = "RS232"
CONF_DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
CONF_DEFAULT_NAME = "NAD Receiver"

_LOGGER = logging.getLogger(__name__)

SUPPORT_NAD = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.SELECT_SOURCE
)

# Max value based on a C658 with an MDC HDM-2 card installed
SOURCE_DICT_SCHEMA = vol.Schema({vol.Range(min=1, max=12): cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_TYPE, default=CONF_DEFAULT_TYPE): vol.In(
            ["RS232", "Telnet", "TCP"]
        ),
        vol.Optional(CONF_SERIAL_PORT, default=CONF_DEFAULT_SERIAL_PORT): cv.string,
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=CONF_DEFAULT_PORT): int,
        vol.Optional(CONF_NAME, default=CONF_DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MIN_VOLUME, default=CONF_DEFAULT_MIN_VOLUME): int,
        vol.Optional(CONF_MAX_VOLUME, default=CONF_DEFAULT_MAX_VOLUME): int,
        vol.Optional(CONF_SOURCE_DICT, default={}): SOURCE_DICT_SCHEMA,
        vol.Optional(CONF_VOLUME_STEP, default=CONF_DEFAULT_VOLUME_STEP): int,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the NAD platform."""
    if config.get(CONF_TYPE) in ("RS232", "Telnet"):
        add_entities(
            [NAD(None, config)],
            True,
        )
    else:
        add_entities(
            [NADtcp(None, config)],
            True,
        )


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
        async_add_entities([NAD(coordinator)])


class NAD(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a NAD Receiver."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_icon = "mdi:audio-video"
    _attr_supported_features = SUPPORT_NAD

    def __init__(self, coordinator: NADReceiverCoordinator):
        """Initialize the NAD Receiver device."""
        super().__init__(coordinator)

        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.unique_id}-mediaplayer"

        self._min_volume = coordinator.options[CONF_MIN_VOLUME]
        self._max_volume = coordinator.options[CONF_MAX_VOLUME]
        self._source_dict = coordinator.options[CONF_SOURCE_DICT]
        self._reverse_mapping = {value: key for key, value in self._source_dict.items()}

    async def async_added_to_hass(self) -> None:
        _LOGGER.debug("async_added_to_hass")
        await super().async_added_to_hass()

        if self.coordinator.receiver:
            self.async_write_ha_state()
        else:
            _LOGGER.debug("%s is not available", self.command)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("_handle_coordinator_update")
        self._attr_state = self.coordinator.power_state
        if self._attr_state == None:
            return

        if self._attr_state == MediaPlayerState.ON:
            self._attr_is_volume_muted = self.coordinator.muted
            volume = self.coordinator.volume
            # Some receivers cannot report the volume, e.g. C 356BEE,
            # instead they only support stepping the volume up or down
            self._attr_volume_level = (
                self.calc_volume(volume) if volume is not None else None
            )
            self._attr_source = self._source_dict.get(self.coordinator.source)

        self.async_write_ha_state()

    def turn_off(self) -> None:
        """Turn the media player off."""
        self.coordinator.receiver.main_power("=", "Off")

    def turn_on(self) -> None:
        """Turn the media player on."""
        self.coordinator.receiver.main_power("=", "On")

    def volume_up(self) -> None:
        """Volume up the media player."""
        self.coordinator.receiver.main_volume("+")

    def volume_down(self) -> None:
        """Volume down the media player."""
        self.coordinator.receiver.main_volume("-")

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        self.coordinator.receiver.main_volume("=", self.calc_db(volume))

    def mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        if mute:
            self.coordinator.receiver.main_mute("=", "On")
        else:
            self.coordinator.receiver.main_mute("=", "Off")

    def select_source(self, source: str) -> None:
        """Select input source."""
        self.coordinator.receiver.main_source("=", self._reverse_mapping.get(source))

    @property
    def source_list(self):
        """List of available input sources."""
        return sorted(self._reverse_mapping)

    @property
    def available(self) -> bool:
        """Return if device is available."""
        return self.state is not None

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


class NADtcp(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a NAD Digital amplifier."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_icon = "mdi:audio-video"
    _attr_supported_features = SUPPORT_NAD

    def __init__(self, coordinator: NADReceiverCoordinator):
        """Initialize the amplifier."""
        super().__init__(coordinator)

        self._min_vol = (
            coordinator.options[CONF_MIN_VOLUME] + 90
        ) * 2  # from dB to nad vol (0-200)
        self._max_vol = (
            coordinator.options[CONF_MAX_VOLUME] + 90
        ) * 2  # from dB to nad vol (0-200)
        self._volume_step = coordinator.options[CONF_VOLUME_STEP]
        self._nad_volume = None
        self._source_list = self.coordinator.receiver.available_sources()

        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.unique_id}-mediaplayer"

    def turn_off(self) -> None:
        """Turn the media player off."""
        self.coordinator.receiver.power_off()

    def turn_on(self) -> None:
        """Turn the media player on."""
        self.coordinator.receiver.power_on()

    def volume_up(self) -> None:
        """Step volume up in the configured increments."""
        self.coordinator.receiver.set_volume(self._nad_volume + 2 * self._volume_step)

    def volume_down(self) -> None:
        """Step volume down in the configured increments."""
        self.coordinator.receiver.set_volume(self._nad_volume - 2 * self._volume_step)

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        nad_volume_to_set = int(
            round(volume * (self._max_vol - self._min_vol) + self._min_vol)
        )
        self.coordinator.receiver.set_volume(nad_volume_to_set)

    def mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        if mute:
            self.coordinator.receiver.mute()
        else:
            self.coordinator.receiver.unmute()

    def select_source(self, source: str) -> None:
        """Select input source."""
        self.coordinator.receiver.select_source(source)

    @property
    def source_list(self):
        """List of available input sources."""
        return self.coordinator.receiver.available_sources()

    def update(self) -> None:
        """Get the latest details from the device."""
        try:
            nad_status = self.coordinator.receiver.status()
        except OSError:
            return
        if nad_status is None:
            return

        # Update on/off state
        if nad_status["power"]:
            self._attr_state = MediaPlayerState.ON
        else:
            self._attr_state = MediaPlayerState.OFF

        # Update current volume
        self._attr_volume_level = self.nad_vol_to_internal_vol(nad_status["volume"])
        self._nad_volume = nad_status["volume"]

        # Update muted state
        self._attr_is_volume_muted = nad_status["muted"]

        # Update current source
        self._attr_source = nad_status["source"]

    def nad_vol_to_internal_vol(self, nad_volume):
        """Convert nad volume range (0-200) to internal volume range.

        Takes into account configured min and max volume.
        """
        if nad_volume < self._min_vol:
            volume_internal = 0.0
        elif nad_volume > self._max_vol:
            volume_internal = 1.0
        else:
            volume_internal = (nad_volume - self._min_vol) / (
                self._max_vol - self._min_vol
            )
        return volume_internal
