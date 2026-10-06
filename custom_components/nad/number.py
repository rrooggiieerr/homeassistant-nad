from datetime import timedelta
from typing import Any, override

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfFrequency,
    UnitOfLength,
    UnitOfSoundPressure,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity, handle_nad_action_errors

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1


_ENTITY_DESCRIPTIONS = [
    NumberEntityDescription(
        key="Main.Audyssey.Offset",
        translation_key="main_audyssey_offset",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Bass",
        translation_key="main_bass",
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
    ),
    NumberEntityDescription(
        key="Main.Brightness",
        translation_key="main_brightness",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.CenterDialog",
        translation_key="main_center_dialog",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.BackLeft",
        translation_key="main_distance_back_left",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.BackRight",
        translation_key="main_distance_back_right",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Center",
        translation_key="main_distance_center",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Left",
        translation_key="main_distance_left",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Right",
        translation_key="main_distance_right",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Sub",
        translation_key="main_distance_sub",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.SurroundLeft",
        translation_key="main_distance_surround_left",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.SurroundRight",
        translation_key="main_distance_surround_right",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Dolby.CenterWidth",
        translation_key="main_dolby_center_width",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Dolby.Dimension",
        translation_key="main_dolby_dimension",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Dolby.DRC",
        translation_key="main_dolby_drc",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.DTS.CenterGain",
        translation_key="main_dts_center_gain",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.DTS.DRC",
        translation_key="main_dts_drc",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="%",
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.IR.Channel",
        translation_key="main_ir_channel",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.BackLeft",
        translation_key="main_level_back_left",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.BackRight",
        translation_key="main_level_back_right",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Center",
        translation_key="main_level_center",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Left",
        translation_key="main_level_left",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Right",
        translation_key="main_level_right",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Sub",
        translation_key="main_level_sub",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.SurroundLeft",
        translation_key="main_level_surround_left",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.SurroundRight",
        translation_key="main_level_surround_right",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.LipSyncDelay",
        translation_key="main_lip_sync_delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Sleep",
        translation_key="main_sleep",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Back.Config1",
        translation_key="main_speaker_back_config1",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Back.Frequency",
        translation_key="main_speaker_back_frequency",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Center.Frequency",
        translation_key="main_speaker_center_frequency",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Front.Frequency",
        translation_key="main_speaker_front_frequency",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Surround.Frequency",
        translation_key="main_speaker_surround_frequency",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Treble",
        translation_key="main_treble",
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
    ),
    NumberEntityDescription(
        key="Main.Trigger1.Delay",
        translation_key="main_trigger1_delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Trigger2.Delay",
        translation_key="main_trigger2_delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Trigger3.Delay",
        translation_key="main_trigger3_delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Trim.Center",
        translation_key="main_trim_center",
    ),
    NumberEntityDescription(
        key="Main.Trim.Sub",
        translation_key="main_trim_sub",
    ),
    NumberEntityDescription(
        key="Main.Trim.Surround",
        translation_key="main_trim_surround",
    ),
    NumberEntityDescription(
        key="Main.VFD.TempLine",
        translation_key="main_vfd_temp_line",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Video.Brightness",
        translation_key="main_video_brightness",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Video.Contrast",
        translation_key="main_video_contrast",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Video.EdgeEnhancement.Level",
        translation_key="main_video_edge_enhancement_level",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Video.EdgeEnhancement.Treshold",
        translation_key="main_video_edge_enhancement_treshold",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Video.NoiseReduction",
        translation_key="main_video_noise_reduction",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Tuner.AM.Frequency",
        translation_key="tuner_am_frequency",
        device_class=NumberDeviceClass.FREQUENCY,
        # mode = NumberMode.SLIDER,
        native_unit_of_measurement=UnitOfFrequency.KILOHERTZ,
    ),
    NumberEntityDescription(
        key="Tuner.FM.Frequency",
        translation_key="tuner_fm_frequency",
        device_class=NumberDeviceClass.FREQUENCY,
        # mode = NumberMode.SLIDER,
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
    ),
    NumberEntityDescription(
        key="Tuner.Preset",
        translation_key="tuner_preset",
        # mode = NumberMode.BOX,
    ),
    NumberEntityDescription(
        key="Tuner.XM.Channel",
        translation_key="tuner_xm_channel",
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Receiver number."""
    coordinator: NADCoordinator = config_entry.runtime_data

    entities = []

    for entity_description in _ENTITY_DESCRIPTIONS:
        if (
            (config := coordinator.device.get_setting_config(entity_description.key))
            and config["type"] == "number"
            and "?" in config["operators"]
            and "=" in config["operators"]
        ):
            entities.append(NADNumber(coordinator, entity_description, config))

    async_add_entities(entities)


class NADNumber(NADEntity, NumberEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: NumberEntityDescription,
        config: dict[str, Any],
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id}-{entity_description.key.lower()}"
        )

        self.entity_description = entity_description

        self._attr_native_max_value = config.get("max", 0)
        self._attr_native_min_value = config.get("min", 0)
        self._attr_native_step = config.get("step", 1)

    @property
    @override
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        value = self._device.get_setting_value(self.entity_description.key)
        return float(value) if value is not None else None

    @override
    @handle_nad_action_errors
    async def async_set_native_value(self, value: float) -> None:
        await self._device.async_change_setting(self.entity_description.key, value)
