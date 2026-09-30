"""The NAD Data Update Coordinator"""

import logging
from datetime import timedelta
from typing import Final, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from nad_serial import NADDevice

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type NADConfigEntry = ConfigEntry[NADCoordinator]

UPDATE_INTERVAL = timedelta(seconds=5)


class NADCoordinator(DataUpdateCoordinator[None]):
    """NAD Data Update Coordinator."""

    config_entry: NADConfigEntry

    device: Final[NADDevice]
    unique_id: str
    device_info: Final[DeviceInfo]

    def __init__(self, hass, config_entry: NADConfigEntry, device: NADDevice):
        """Initialize NAD Data Update Coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=True,
        )

        self.device = device
        self.unique_id = self.device.serial_number or config_entry.entry_id

        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer="NAD",
            model=device.model,
            name=device.name,
            serial_number=device.serial_number,
            sw_version=device.firmware_version,
        )

        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            **self.device_info,
        )

    @override
    async def _async_update_data(self) -> None:
        """Fetch the latest data from the source."""
        if self.device.sends_updates and not await self.device.async_ping():
            raise UpdateFailed(f"Error communicating with NAD {self.device.name}")
