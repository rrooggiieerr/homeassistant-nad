"""Nad Entity."""

import logging
from typing import Any, override

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from nad_serial import NADDevice

from .coordinator import NADCoordinator

_LOGGER = logging.getLogger(__name__)


class NADEntity(CoordinatorEntity):
    _device: NADDevice

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
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._device.add_callback(self._async_nad_callback))

    @callback
    def _async_nad_callback(self, setting: str, value: Any) -> None:
        _LOGGER.debug("%s changed to %s", setting, value)
        self.async_write_ha_state()

    # @property
    # def available(self) -> bool:
    #     """Return if entity is available."""
    #     if not self._attr_available:
    #         return self._attr_available
    #
    #     return self.coordinator.last_update_success
