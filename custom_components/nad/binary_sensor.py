"""Creates Binary Sensor entities for the NAD Home Assistant integration."""

from datetime import timedelta
from typing import Any, override

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1

_ENTITY_DESCRIPTIONS = [
    BinarySensorEntityDescription(
        key="Main.Audio.Lock",
        translation_key="main_audio_lock",
        entity_registry_enabled_default=False,
    ),
    BinarySensorEntityDescription(
        key="Main.Video.HDR",
        translation_key="main_video_hdr",
        entity_registry_enabled_default=False,
    ),
    BinarySensorEntityDescription(
        key="Main.Video.Lock",
        translation_key="main_video_lock",
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Sensor entities."""
    coordinator: NADCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            NADBinarySensor(coordinator, entity_description, config)
            for entity_description in _ENTITY_DESCRIPTIONS
            if (config := coordinator.device.get_setting_config(entity_description.key))
            and config["type"] == "boolean"
            and "?" in config["operators"]
            and "=" not in config["operators"]
        ]
    )


class NADBinarySensor(NADEntity, BinarySensorEntity):
    """NAD Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: BinarySensorEntityDescription,
        config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id}-{entity_description.key.lower()}"
        )

        self.entity_description = entity_description

    @property
    @override
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = self._device.get_setting_value(self.entity_description.key)
        return value if isinstance(value, bool) else None
