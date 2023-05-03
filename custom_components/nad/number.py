from __future__ import annotations

import logging

from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfFrequency, UnitOfLength, UnitOfTime
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
    """Set up the NAD Receiver number."""
    coordinator: NADReceiverCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Fetch initial data so we have data when entities subscribe
    # await coordinator.async_config_entry_first_refresh()

    entity_descriptions = [
        NumberEntityDescription(
            key="Main.Bass",
            name="Bass Tone Control",
            native_unit_of_measurement="db",
            native_min_value=-10,
            native_max_value=10,
        ),
        NumberEntityDescription(
            key="Main.Distance.BackLeft",
            name="Distance Back Left",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.BackRight",
            name="Distance Back Right",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.Center",
            name="Distance Center",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.Left",
            name="Distance Left",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.Right",
            name="Distance Right",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.Sub",
            name="Distance Subwoofer",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.SurroundLeft",
            name="Distance Surround Left",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Distance.SurroundRight",
            name="Distance Surround Right",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.FEET,
            native_min_value=0,
            native_max_value=30,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Dolby.CenterWidth",
            name="Dolby Center Width",
            icon="mdi:dolby",
            entity_category=EntityCategory.CONFIG,
            native_min_value=0,
            native_max_value=7,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Dolby.Dimension",
            name="Dolby Dimension",
            icon="mdi:dolby",
            entity_category=EntityCategory.CONFIG,
            native_min_value=-7,
            native_max_value=7,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Dolby.DRC",
            name="Dolby Dynamic Range Control",
            icon="mdi:dolby",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="%",
            native_min_value=25,
            native_max_value=100,
            native_step=25,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.DTS.CenterGain",
            name="DTS Center Gain",
            entity_category=EntityCategory.CONFIG,
            native_min_value=0,
            native_max_value=0.5,
            native_step=0.1,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.DTS.DRC",
            name="DTS Dynamic Range Control",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="%",
            native_min_value=25,
            native_max_value=100,
            native_step=25,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.BackLeft",
            name="Speaker Level Back Left",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.BackRight",
            name="Speaker Level Back Rigt",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.Center",
            name="Speaker Level Center",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.Left",
            name="Speaker Level Left",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.Right",
            name="Speaker Level Right",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.Sub",
            name="Speaker Level Subwoofer",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.SurroundLeft",
            name="Speaker Level Surround Left",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Level.SurroundRight",
            name="Speaker Level Surround Right",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement="db",
            native_min_value=-12,
            native_max_value=12,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.LipSyncDelay",
            name="Lip Sync Delay",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement=UnitOfTime.MILLISECONDS,
            native_min_value=0,
            native_max_value=120,
            entity_registry_enabled_default=False,
        ),
        # NumberEntityDescription(key = "Main.Sleep", name = "Time Before Sleep", native_min_value = 0, native_max_value = 90),
        NumberEntityDescription(
            key="Main.Speaker.Back.Frequency",
            name="Speaker Crossover Back",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.FREQUENCY,
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            native_min_value=40,
            native_max_value=200,
            native_step=10,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Speaker.Center.Frequency",
            name="Speaker Crossover Center",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.FREQUENCY,
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            native_min_value=40,
            native_max_value=200,
            native_step=10,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Speaker.Front.Frequency",
            name="Speaker Crossover Front",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.FREQUENCY,
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            native_min_value=40,
            native_max_value=200,
            native_step=10,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Speaker.Surround.Frequency",
            name="Speaker Crossover Surround",
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.FREQUENCY,
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            native_min_value=40,
            native_max_value=200,
            native_step=10,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Treble",
            name="Treble Tone Control",
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            native_min_value=-10,
            native_max_value=10,
            native_step=2,
        ),
        NumberEntityDescription(
            key="Main.Trigger1.Delay",
            name="Trigger 1 Delay",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            native_min_value=0,
            native_max_value=15,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Trigger2.Delay",
            name="Trigger 2 Delay",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            native_min_value=0,
            native_max_value=15,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Trigger3.Delay",
            name="Trigger 3 Delay",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            native_min_value=0,
            native_max_value=15,
            entity_registry_enabled_default=False,
        ),
        NumberEntityDescription(
            key="Main.Trim.Center",
            name="Trim Level Center",
            native_min_value=-6,
            native_max_value=6,
        ),
        NumberEntityDescription(
            key="Main.Trim.Sub",
            name="Trim Level Subwoofer",
            native_min_value=-6,
            native_max_value=6,
        ),
        NumberEntityDescription(
            key="Main.Trim.Surround",
            name="Trim Level Surround",
            native_min_value=-6,
            native_max_value=6,
        ),
        NumberEntityDescription(
            key="Tuner.AM.Frequency",
            name="Tuner AM Frequency",
            device_class=NumberDeviceClass.FREQUENCY,
            # mode = NumberMode.SLIDER,
            native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
            native_min_value=87.5,
            native_max_value=108.5,
            native_step=0.05,
        ),
        NumberEntityDescription(
            key="Tuner.FM.Frequency",
            name="Tuner FM Frequency",
            device_class=NumberDeviceClass.FREQUENCY,
            # mode = NumberMode.SLIDER,
            native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
            native_min_value=87.5,
            native_max_value=108.5,
            native_step=0.05,
        ),
        NumberEntityDescription(
            key="Tuner.Preset",
            name="Tuner Preset",
            # mode = NumberMode.BOX,
            native_min_value=1,
            native_max_value=40,
        ),
        NumberEntityDescription(
            key="Tuner.XM.Channel",
            name="Tuner XM Channel",
            native_min_value=0,
            native_max_value=255,
            entity_registry_enabled_default=False,
        ),
    ]

    entities = []

    for entity_description in entity_descriptions:
        if coordinator.supports_command(entity_description.key):
            entities.append(NADReceiverNumber(coordinator, entity_description))

    async_add_entities(entities)


class NADReceiverNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_available = False

    def __init__(
        self,
        coordinator: NADReceiverCoordinator,
        entity_description: NumberEntityDescription,
    ) -> None:
        """Initialize the number."""
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
            and (new_value := self.coordinator.data.get(self.entity_description.key))
            and new_value.lstrip("-").replace(".", "", 1).isnumeric()
        ):
            self._attr_native_value = float(new_value)
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

    async def async_set_native_value(self, value: float) -> None:
        _LOGGER.debug("async_set_native_value")
        if self.coordinator.power_state == MediaPlayerState.ON:
            if self._attr_native_value == value:
                return

            if self._attr_native_step < 1:
                response = self.coordinator.exec_command(
                    self.entity_description.key, "=", value
                )
            else:
                response = self.coordinator.exec_command(
                    self.entity_description.key, "=", int(value)
                )
            if response.lstrip("-").replace(".", "", 1).isnumeric():
                self._attr_native_value = float(response)
                self._attr_available = True
            else:
                _LOGGER.error("Failed to set %s to %s", self.name, value)
                self._attr_available = False
        else:
            self._attr_available = False

        self.async_write_ha_state()
        # await self.coordinator.async_request_refresh()
