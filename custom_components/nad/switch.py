import logging
from typing import override

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity

_LOGGER = logging.getLogger(__name__)


_ENTITY_DESCRIPTIONS = [
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Receiver switch."""
    coordinator: NADCoordinator = config_entry.runtime_data

    entities = []

    for entity_description in _ENTITY_DESCRIPTIONS:
        if coordinator.device.get_setting_config(entity_description.key):
            entities.append(NADSwitch(coordinator, entity_description))

    async_add_entities(entities)


class NADSwitch(NADEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_available = False

    _attr_is_on = None

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id}-{entity_description.key.lower()}"
        )

        self.entity_description = entity_description

    @property
    @override
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        value = self._device.get_setting_value(self.entity_description.key)
        return bool(value) if value is not None else None

    @override
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self._device.async_change_setting(self.entity_description.key, True)
        self.async_write_ha_state()

    @override
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self._device.async_change_setting(self.entity_description.key, False)
        self.async_write_ha_state()
