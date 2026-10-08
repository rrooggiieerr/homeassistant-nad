"""Creates Text entities for the NAD Home Assistant integration."""

from datetime import timedelta
from typing import override

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity, handle_nad_action_errors

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1

_ENTITY_DESCRIPTIONS = [
    TextEntityDescription(
        key="Main.BT.Name",
        translation_key="main_bt_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source1.Name",
        translation_key="source1_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source2.Name",
        translation_key="source2_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source3.Name",
        translation_key="source3_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source4.Name",
        translation_key="source4_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source5.Name",
        translation_key="source5_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source6.Name",
        translation_key="source6_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source7.Name",
        translation_key="source7_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source8.Name",
        translation_key="source8_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source9.Name",
        translation_key="source9_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    TextEntityDescription(
        key="Source10.Name",
        translation_key="source10_name",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Text entities."""
    coordinator: NADCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            NADText(coordinator, entity_description)
            for entity_description in _ENTITY_DESCRIPTIONS
            if (config := coordinator.device.get_setting_config(entity_description.key))
            and config["type"] == "string"
            and "?" in config["operators"]
            and "=" in config["operators"]
        ]
    )


class NADText(NADEntity, TextEntity):
    """NAD Text."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: TextEntityDescription,
    ) -> None:
        """Initialize the text."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id}-{entity_description.key.lower()}"
        )

        self.entity_description = entity_description

    @property
    @override
    def native_value(self) -> str | None:
        """Return the value reported by the text."""
        value = self._device.get_setting_value(self.entity_description.key)
        return str(value) if value is not None else None

    @override
    @handle_nad_action_errors
    async def async_set_value(self, value: str) -> None:
        """Change the value."""
        await self._device.async_change_setting(self.entity_description.key, value)
