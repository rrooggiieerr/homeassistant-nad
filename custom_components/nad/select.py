from __future__ import annotations

import logging

from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    """Set up the NAD Receiver select."""
    coordinator: NADReceiverCoordinator = config_entry.runtime_data

    # Fetch initial data so we have data when entities subscribe
    # await coordinator.async_config_entry_first_refresh()

    entity_descriptions = [
        SelectEntityDescription(
            key="Main.AutoTrigger",
            name="Trigger Input",
            options=["Main", "Zone2", "Zone3", "Zone4", "All"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.ListeningMode.Analog",
            name="Analog Signal Listening Mode",
            options=[
                "None",
                "ProLogic",
                "PLIIMovie",
                "PLIIMusic",
                "NEO6Cinema",
                "NEO6Music",
                "EARS",
                "EnhancedStereo",
                "AnalogBypass",
            ],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.ListeningMode.Digital",
            name="Digital Signal Listening Mode",
            options=[
                "None",
                "ProLogic",
                "PLIIMovie",
                "PLIIMusic",
                "NEO6Cinema",
                "NEO6Music",
                "EARS",
                "EnhancedStereo",
                "StereoDownmix",
            ],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.ListeningMode.DolbyDigital",
            name="Dolby Digital Listening Mode",
            options=["None", "PLIIMovie", "PLIIMusic", "SurroundEX", "StereoDownmix"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.ListeningMode.DolbyDigital2ch",
            name="Dolby Digital 2 channel Listening Mode",
            options=["None", "ProLogic", "PLIIMovie", "PLIIMusic"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.ListeningMode.DTS",
            name="DTS Listening Mode",
            options=["None", "NEO6Music", "StereoDownmix"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Speaker.Back.Config2",
            name="Speaker Size Back",
            options=["Small", "Large"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Speaker.Center.Config",
            name="Speaker Size Center",
            options=["Off", "Small", "Large"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Speaker.Front.Config",
            name="Speaker Size Front",
            options=["Small", "Large"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Speaker.Surround.Config",
            name="Speaker Size Surround",
            options=["Off", "Small", "Large"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Trigger1.Out",
            name="Trigger 1",
            options=["Main", "Zone2", "Zone3", "Zone4", "Zone234", "Source"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Trigger2.Out",
            name="Trigger 2",
            options=["Main", "Zone2", "Zone3", "Zone4", "Zone234", "Source"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.Trigger3.Out",
            name="Trigger 3",
            options=["Main", "Zone2", "Zone3", "Zone4", "Zone234", "Source"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.VFD.Display",
            name="Main VFD Display",
            options=["On", "Temp"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="VFD Line1",
            name="VFD Line 1",
            options=[
                "MainSource",
                "Volume",
                "ListeningMode",
                "AudioSourceFormat",
                "Zone2Source",
                "Zone3Source",
                "Zone4Source",
                "Off",
            ],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.VFD.Line2",
            name="VFD Line 2",
            options=[
                "MainSource",
                "Volume",
                "ListeningMode",
                "AudioSourceFormat",
                "Zone2Source",
                "Zone3Source",
                "Zone4Source",
                "Off",
            ],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.VFD.TempLine",
            name="VFD Temp Line",
            options=["1", "2"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        SelectEntityDescription(
            key="Main.VideoMode",
            name="Video Mode",
            options=["NTSC", "PAL"],
            entity_category=EntityCategory.CONFIG,
        ),
        SelectEntityDescription(
            key="Tuner.Band", name="Tuner Band", options=["AM", "FM", "XM", "DAB"]
        ),
        SelectEntityDescription(
            key="Tuner.DigitalMode",
            name="Tuner Digital Mode",
            options=["XM", "DAB"],
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
    ]

    entities = []

    for entity_description in entity_descriptions:
        if coordinator.supports_command(entity_description.key):
            entities.append(NADReceiverSelect(coordinator, entity_description))

    async_add_entities(entities)


class NADReceiverSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_available = False

    _attr_current_option = None

    def __init__(
        self,
        coordinator: NADReceiverCoordinator,
        entity_description: SelectEntityDescription,
    ) -> None:
        """Initialize the select."""
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

        if self.coordinator.data and (
            new_state := self.coordinator.data.get(self.entity_description.key)
        ):
            self._attr_current_option = new_state
            self._attr_available = True
        else:
            _LOGGER.debug("%s is not available", self.entity_description.key)
            self._attr_available = False

        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self._attr_available:
            return self._attr_available

        return self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.coordinator.power_state == MediaPlayerState.ON:
            if self._attr_current_option == option:
                return

            response = self.coordinator.exec_command(
                self.entity_description.key, "=", option
            )
            if response is not None:
                self._attr_current_option = response
                self._attr_available = True
            else:
                _LOGGER.error("Failed to set %s to %s", self.name, option)
                self._attr_available = False
        else:
            self._attr_available = False

        self.async_write_ha_state()
        # await self.coordinator.async_request_refresh()
