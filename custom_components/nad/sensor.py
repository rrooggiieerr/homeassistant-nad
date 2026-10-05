import logging
from datetime import timedelta
from typing import Any, override

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)
PARALLEL_UPDATES = 1

_ENTITY_DESCRIPTIONS = [
    SensorEntityDescription(
        key="DSP.Version",
        translation_key="dsp_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.DAB.DLS",
        translation_key="tuner_dab_dls",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.DAB.Service",
        translation_key="tuner_dab_service",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.FM.RDSName",
        translation_key="tuner_fm_rdsname",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.FM.RDSText",
        translation_key="tuner_fm_rdstext",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.XM.ChannelName",
        translation_key="tuner_xm_channel_name",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.XM.Name",
        translation_key="tuner_xm_name",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.XM.Title",
        translation_key="tuner_xm_title",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="UART.Version",
        translation_key="uart_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NAD Receiver sensor."""
    coordinator: NADCoordinator = config_entry.runtime_data

    entities = []

    for entity_description in _ENTITY_DESCRIPTIONS:
        if (
            (config := coordinator.device.get_setting_config(entity_description.key))
            and config["type"] in ("number", "string")
            and "?" in config["operators"]
            and "=" not in config["operators"]
        ):
            entities.append(NADSensor(coordinator, entity_description, config))

    async_add_entities(entities)


class NADSensor(NADEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_native_value = None

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: SensorEntityDescription,
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
    def native_value(self) -> Any:
        """Return the value reported by the sensor."""
        return self._device.get_setting_value(self.entity_description.key)
