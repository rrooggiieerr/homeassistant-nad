from datetime import timedelta
from typing import Any, override

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity, handle_nad_action_errors

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1

_ENTITY_DESCRIPTIONS = [
    SelectEntityDescription(
        key="Main.AutoTrigger",
        translation_key="main_auto_trigger",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.Analog",
        translation_key="main_listening_mode_analog",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.Digital",
        translation_key="main_listening_mode_digital",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.DolbyDigital",
        translation_key="main_listening_mode_dolby_digital",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.DolbyDigital2ch",
        translation_key="main_listening_mode_dolby_digital2ch",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.DTS",
        translation_key="main_listening_mode_dts",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Back.Config2",
        translation_key="main_speaker_back_config2",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Center.Config",
        translation_key="main_speaker_center_config",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Front.Config",
        translation_key="main_speaker_front_config",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Surround.Config",
        translation_key="main_speaker_surround_config",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Trigger1.Out",
        translation_key="main_trigger1_out",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Trigger2.Out",
        translation_key="main_trigger2_out",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Trigger3.Out",
        translation_key="main_trigger3_out",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VFD.Display",
        translation_key="main_vfd_display",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VFD.Line1",
        translation_key="main_vfd_line1",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VFD.Line2",
        translation_key="main_vfd_line2",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Video.Aspect.Mode",
        translation_key="main_video_aspect_mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Video.Aspect.Ratio",
        translation_key="main_video_aspect_ratio",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Video.Rate",
        translation_key="main_video_rate",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Video.Resolution",
        translation_key="main_video_resolution",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VideoMode",
        translation_key="main_video_mode",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(key="Tuner.Band", translation_key="tuner_band"),
    SelectEntityDescription(
        key="Tuner.DigitalMode",
        translation_key="tuner_digital_mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Receiver select."""
    coordinator: NADCoordinator = config_entry.runtime_data

    entities = []

    for entity_description in _ENTITY_DESCRIPTIONS:
        if (
            (config := coordinator.device.get_setting_config(entity_description.key))
            and config["type"] == "enum"
            and "?" in config["operators"]
            and "=" in config["operators"]
        ):
            entities.append(NADSelect(coordinator, entity_description, config))

    async_add_entities(entities)


class NADSelect(NADEntity, SelectEntity):
    _attr_has_entity_name = True

    _attr_current_option = None

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: SelectEntityDescription,
        config: dict[str, Any],
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id}-{entity_description.key.lower()}"
        )

        self.entity_description = entity_description

        self._attr_options = config.get("values", [])

    @property
    @override
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        value = self._device.get_setting_value(self.entity_description.key)
        return str(value) if value else None

    @override
    @handle_nad_action_errors
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._device.async_change_setting(self.entity_description.key, option)
