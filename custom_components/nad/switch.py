"""Creates Switch entities for the NAD Home Assistant integration."""

from datetime import timedelta
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
from .entity import NADEntity, handle_nad_action_errors

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1


_ENTITY_DESCRIPTIONS = [
    SwitchEntityDescription(
        key="Main.AutoSense",
        translation_key="main_auto_sense",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.AutoStandby",
        translation_key="main_auto_standby",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.CEC.Audio",
        translation_key="main_cec_audio",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.CEC.Power",
        translation_key="main_cec_power",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.CEC.Switch",
        translation_key="main_cec_switch",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.ControlStandby",
        translation_key="main_control_standby",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.Dimmer",
        translation_key="main_dimmer",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.Dolby.Panorama",
        translation_key="main_dolby_panorama",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.EnhancedBass",
        translation_key="main_enhanced_bass",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.EnhancedStereo.Back",
        translation_key="main_enhanced_stereo_back",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.EnhancedStereo.Center",
        translation_key="main_enhanced_stereo_center",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.EnhancedStereo.Front",
        translation_key="main_enhanced_stereo_front",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.EnhancedStereo.Surround",
        translation_key="main_enhanced_stereo_surround",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.OSD.TempDisplay",
        translation_key="main_osd_temp_display",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.Speaker.Sub",
        translation_key="main_speaker_sub",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.SpeakerA",
        translation_key="main_speaker_a",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Main.SpeakerB",
        translation_key="main_speaker_b",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(key="Main.Tape1", translation_key="main_tape1"),
    SwitchEntityDescription(
        key="Main.ToneDefeat",
        translation_key="main_tone_defeat",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SwitchEntityDescription(
        key="Tuner.FM.Mute",
        translation_key="tuner_fm_mute",
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Switch entities."""
    coordinator: NADCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            NADSwitch(coordinator, entity_description)
            for entity_description in _ENTITY_DESCRIPTIONS
            if (config := coordinator.device.get_setting_config(entity_description.key))
            and config["type"] == "boolean"
            and "?" in config["operators"]
            and "=" in config["operators"]
        ]
    )


class NADSwitch(NADEntity, SwitchEntity):
    """NAD Switch."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

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
    @handle_nad_action_errors
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self._device.async_change_setting(self.entity_description.key, True)

    @override
    @handle_nad_action_errors
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self._device.async_change_setting(self.entity_description.key, False)
