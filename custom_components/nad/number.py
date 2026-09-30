import logging
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
from .entity import NADEntity

_LOGGER = logging.getLogger(__name__)


_ENTITY_DESCRIPTIONS = [
    NumberEntityDescription(
        key="Main.Bass",
        name="Bass Tone Control",
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
    ),
    NumberEntityDescription(
        key="Main.Distance.BackLeft",
        name="Distance Back Left",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.BackRight",
        name="Distance Back Right",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Center",
        name="Distance Center",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Left",
        name="Distance Left",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Right",
        name="Distance Right",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.Sub",
        name="Distance Subwoofer",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.SurroundLeft",
        name="Distance Surround Left",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Distance.SurroundRight",
        name="Distance Surround Right",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Dolby.CenterWidth",
        name="Dolby Center Width",
        icon="mdi:dolby",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Dolby.Dimension",
        name="Dolby Dimension",
        icon="mdi:dolby",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Dolby.DRC",
        name="Dolby Dynamic Range Control",
        icon="mdi:dolby",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.DTS.CenterGain",
        name="DTS Center Gain",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.DTS.DRC",
        name="DTS Dynamic Range Control",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="%",
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.BackLeft",
        name="Speaker Level Back Left",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.BackRight",
        name="Speaker Level Back Right",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Center",
        name="Speaker Level Center",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Left",
        name="Speaker Level Left",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Right",
        name="Speaker Level Right",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.Sub",
        name="Speaker Level Subwoofer",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.SurroundLeft",
        name="Speaker Level Surround Left",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Level.SurroundRight",
        name="Speaker Level Surround Right",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.LipSyncDelay",
        name="Lip Sync Delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        entity_registry_enabled_default=False,
    ),
    # NumberEntityDescription(key = "Main.Sleep", name = "Time Before Sleep"),
    NumberEntityDescription(
        key="Main.Speaker.Back.Frequency",
        name="Speaker Crossover Back",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Center.Frequency",
        name="Speaker Crossover Center",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Front.Frequency",
        name="Speaker Crossover Front",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Speaker.Surround.Frequency",
        name="Speaker Crossover Surround",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Treble",
        name="Treble Tone Control",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
    ),
    NumberEntityDescription(
        key="Main.Trigger1.Delay",
        name="Trigger 1 Delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Trigger2.Delay",
        name="Trigger 2 Delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Trigger3.Delay",
        name="Trigger 3 Delay",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
    ),
    NumberEntityDescription(
        key="Main.Trim.Center",
        name="Trim Level Center",
    ),
    NumberEntityDescription(
        key="Main.Trim.Sub",
        name="Trim Level Subwoofer",
    ),
    NumberEntityDescription(
        key="Main.Trim.Surround",
        name="Trim Level Surround",
    ),
    NumberEntityDescription(
        key="Tuner.AM.Frequency",
        name="Tuner AM Frequency",
        device_class=NumberDeviceClass.FREQUENCY,
        # mode = NumberMode.SLIDER,
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
    ),
    NumberEntityDescription(
        key="Tuner.FM.Frequency",
        name="Tuner FM Frequency",
        device_class=NumberDeviceClass.FREQUENCY,
        # mode = NumberMode.SLIDER,
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
    ),
    NumberEntityDescription(
        key="Tuner.Preset",
        name="Tuner Preset",
        # mode = NumberMode.BOX,
    ),
    NumberEntityDescription(
        key="Tuner.XM.Channel",
        name="Tuner XM Channel",
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
        if config := coordinator.device.get_setting_config(entity_description.key):
            entities.append(NADNumber(coordinator, entity_description, config))

    async_add_entities(entities)


class NADNumber(NADEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_available = False

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
        return float(value) if value else None

    @override
    async def async_set_native_value(self, value: float) -> None:
        await self._device.async_change_setting(self.entity_description.key, value)
        self.async_write_ha_state()
