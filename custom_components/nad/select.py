import logging
from typing import Any, override

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity

_LOGGER = logging.getLogger(__name__)


_ENTITY_DESCRIPTIONS = [
    SelectEntityDescription(
        key="Main.AutoTrigger",
        name="Trigger Input",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.Analog",
        name="Analog Signal Listening Mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.Digital",
        name="Digital Signal Listening Mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.DolbyDigital",
        name="Dolby Digital Listening Mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.DolbyDigital2ch",
        name="Dolby Digital 2 channel Listening Mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.ListeningMode.DTS",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Back.Config2",
        name="Speaker Size Back",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Center.Config",
        name="Speaker Size Center",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Front.Config",
        name="Speaker Size Front",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Speaker.Surround.Config",
        name="Speaker Size Surround",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Trigger1.Out",
        name="Trigger 1",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Trigger2.Out",
        name="Trigger 2",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.Trigger3.Out",
        name="Trigger 3",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VFD.Display",
        name="Main VFD Display",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="VFD Line1",
        name="VFD Line 1",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VFD.Line2",
        name="VFD Line 2",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VFD.TempLine",
        name="VFD Temp Line",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    SelectEntityDescription(
        key="Main.VideoMode",
        name="Video Mode",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(key="Tuner.Band", name="Tuner Band"),
    SelectEntityDescription(
        key="Tuner.DigitalMode",
        name="Tuner Digital Mode",
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
        if config := coordinator.device.get_setting_config(entity_description.key):
            entities.append(NADSelect(coordinator, entity_description, config))

    async_add_entities(entities)


class NADSelect(NADEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_available = False

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
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._device.async_change_setting(self.entity_description.key, option)
        self.async_write_ha_state()
