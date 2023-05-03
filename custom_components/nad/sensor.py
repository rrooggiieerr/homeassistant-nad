from __future__ import annotations

import logging

from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
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
    """Set up the NAD Receiver sensor."""
    coordinator: NADReceiverCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Fetch initial data so we have data when entities subscribe
    # await coordinator.async_config_entry_first_refresh()

    entity_descriptions = [
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

    entities = []

    for entity_description in entity_descriptions:
        if coordinator.supports_command(entity_description.key):
            entities.append(NADReceiverSensor(coordinator, entity_description))

    async_add_entities(entities)


class NADReceiverSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_available = False
    _attr_native_value = None

    def __init__(
        self,
        coordinator: NADReceiverCoordinator,
        entity_description: SensorEntityDescription,
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

        if self.coordinator.data and (
            new_value := self.coordinator.data.get(self.entity_description.key)
        ):
            self._attr_native_value = new_value
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
