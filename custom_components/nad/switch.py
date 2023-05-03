from __future__ import annotations

import logging

from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NADReceiverCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NAD Receiver switch."""
    coordinator: NADReceiverCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Fetch initial data so we have data when entities subscribe
    # await coordinator.async_config_entry_first_refresh()

    entity_descriptions = [
        SwitchEntityDescription(
            key="Main.Dimmer",
            name="Front VFD Dimmer",
            icon="mdi:text-short",
            entity_category=EntityCategory.CONFIG,
        ),
        SwitchEntityDescription(
            key="Main.Dolby.Panorama",
            name="Dolby Panorama",
            icon="mdi:dolby",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SwitchEntityDescription(
            key="Main.EnhancedBass",
            name="Enhanced Bass",
            entity_category=EntityCategory.CONFIG,
        ),
        SwitchEntityDescription(
            key="Main.EnhancedStereo.Back",
            name="Enhanced Stereo Back",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SwitchEntityDescription(
            key="Main.EnhancedStereo.Center",
            name="Enhanced Stereo Center",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SwitchEntityDescription(
            key="Main.EnhancedStereo.Front",
            name="Enhanced Stereo Front",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SwitchEntityDescription(
            key="Main.EnhancedStereo.Surround",
            name="Enhanced Stereo Surround",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SwitchEntityDescription(
            key="Main.OSD.TempDisplay",
            name="OSD Temp Display",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SwitchEntityDescription(key="Main.Speaker.Sub", name="Subwoofer"),
        SwitchEntityDescription(
            key="Main.SpeakerA", name="Speakers A", icon="mdi:speaker-multiple"
        ),
        SwitchEntityDescription(
            key="Main.SpeakerB", name="Speakers B", icon="mdi:speaker-multiple"
        ),
        SwitchEntityDescription(key="Main.ToneDefeat", name="Tone Defeat"),
        SwitchEntityDescription(
            key="Tuner.FM.Mute",
            name="Tuner FM Mute",
            icon="mdi:radio-fm",
            entity_registry_enabled_default=False,
        ),
    ]

    entities = []

    for entity_description in entity_descriptions:
        if coordinator.supports_command(entity_description.key):
            entities.append(NADReceiverSwitch(coordinator, entity_description))

    async_add_entities(entities)


class NADReceiverSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_available = False

    _attr_is_on = None

    def __init__(
        self,
        coordinator: NADReceiverCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, entity_description.key)

        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = (
            f"{coordinator.unique_id}-{entity_description.key.lower()}"
        )

        self.entity_description = entity_description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if (
            self.coordinator.data
            and (new_state := self.coordinator.data.get(self.entity_description.key))
            and (new_state := new_state.lower())
            and new_state in ["on", "off"]
        ):
            self._attr_is_on = new_state == "on"
            self._attr_available = True
        else:
            self._attr_available = False

        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self._attr_available:
            return self._attr_available

        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        _LOGGER.debug("Turning on %s", self.name)
        response = self.coordinator.exec_command(self.entity_description.key, "=", "On")
        if response.lower() == "on":
            self._attr_is_on = True
            self._attr_available = True
        else:
            _LOGGER.error("Failed to switch on %s", self.name)
            self._attr_available = False

        self.async_write_ha_state()
        # await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        _LOGGER.debug("Turning off %s", self.name)
        response = self.coordinator.exec_command(
            self.entity_description.key, "=", "Off"
        )
        if response.lower() == "off":
            self._attr_is_on = False
            self._attr_available = True
        else:
            _LOGGER.error("Failed to switch off %s", self.name)
            self._attr_available = False

        self.async_write_ha_state()
        # await self.coordinator.async_request_refresh()
