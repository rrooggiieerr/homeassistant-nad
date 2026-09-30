import logging
from typing import Any, override

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NADCoordinator
from .entity import NADEntity

_LOGGER = logging.getLogger(__name__)

_ENTITY_DESCRIPTIONS = [
    SensorEntityDescription(
        key="DSP.Version", name="DSP Version", entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key="Tuner.DAB.DLS", name="DAB DLS", entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key="Tuner.DAB.Service",
        name="DAB Service",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.FM.RDSName",
        name="FM RDS Name",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.FM.RDSText",
        name="FM RDS Text",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.XM.ChannelName",
        name="XM Channel Name",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="Tuner.XM.Name", name="XM Name", entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key="Tuner.XM.Title", name="XM Title", entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key="UART.Version",
        name="UART Version",
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
        if config := coordinator.device.get_setting_config(entity_description.key):
            entities.append(NADSensor(coordinator, entity_description, config))

    async_add_entities(entities)


class NADSensor(NADEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_available = False
    _attr_native_value = None

    def __init__(
        self,
        coordinator: NADCoordinator,
        entity_description: SensorEntityDescription,
        config: dict[str, Any],
    ) -> None:
        """Initialize the number."""
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
