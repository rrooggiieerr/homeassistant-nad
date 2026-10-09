"""The NAD Data Update Coordinator."""

from datetime import timedelta
import logging
from typing import Final, override

from nad_serial import NADDevice
from nad_serial.exceptions import NADBaseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
            always_update=False,
        )

        self.device = device
        self.unique_id = config_entry.unique_id or config_entry.entry_id

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
    async def async_shutdown(self) -> None:
        """Disconnect from the NAD device."""
        await super().async_shutdown()
        await self.device.async_disconnect()

    @override
    async def _async_update_data(self) -> None:
        """Fetch the latest data from the source."""
        try:
            if not self.device.connected:
                await self.device.async_reconnect()
            else:
                await self.device.async_request_is_on()
        except NADBaseError as ex:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"name": self.device.name},
            ) from ex
