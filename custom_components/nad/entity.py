"""Nad Entity."""

import logging
from datetime import timedelta
from typing import Any, override

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed
from nad_serial import NADConnectionError, NADDevice, NADTimeoutError

from .coordinator import NADCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


class NADEntity(CoordinatorEntity[NADCoordinator]):
    _device: NADDevice

    coordinator: NADCoordinator

    def __init__(
        self,
        coordinator: NADCoordinator,
        device: NADDevice | None = None,
    ) -> None:
        """Initialize the NAD entity."""
        super().__init__(coordinator)

        if device:
            self._device = device
        else:
            self._device = coordinator.device
            self._attr_device_info = coordinator.device_info

    @override
    @property
    def should_poll(self) -> bool:
        return not self.coordinator.device.sends_updates

    @override
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._device.add_callback(self._async_nad_callback))

    @callback
    def _async_nad_callback(self, setting: str, value: Any) -> None:
        _LOGGER.debug("%s changed to %s", setting, value)
        self.async_write_ha_state()

    @override
    async def async_update(self) -> None:
        """Update the entity."""
        if not self._device.sends_updates and hasattr(self, "entity_description"):
            try:
                await self._device.async_request_setting(self.entity_description.key)
            except NADTimeoutError, NADConnectionError:
                raise UpdateFailed(f"Error communicating with NAD {self._device.name}")
            self.async_write_ha_state()
