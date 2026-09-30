"""The NAD Data Update Coordinator"""

import logging
from datetime import timedelta
from typing import Final, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from nad_serial import NADDevice

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type NADConfigEntry = ConfigEntry[NADCoordinator]

UPDATE_INTERVAL = timedelta(seconds=5)


class NADCoordinator(DataUpdateCoordinator):
    """NAD Data Update Coordinator."""

    config_entry: NADConfigEntry

    device: Final[NADDevice]
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

    @override
    async def _async_update_data(self) -> None:
        """Fetch the latest data from the source."""
        if not self.device.sends_updates:
            # ToDo
            pass
