"""NAD Entity."""

from collections.abc import Callable, Coroutine
import functools
import logging
from typing import Any, Concatenate, override

from nad_serial import NADDevice
from nad_serial.exceptions import NADBaseError, NADConnectionError, NADTimeoutError

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NADCoordinator

_LOGGER = logging.getLogger(__name__)


def handle_nad_action_errors[EntityT: NADEntity, **P](
    func: Callable[Concatenate[EntityT, P], Coroutine[Any, Any, None]],
) -> Callable[Concatenate[EntityT, P], Coroutine[Any, Any, None]]:
    """Handles NAD errors for actions."""

    @functools.wraps(func)
    async def wrapper(self: EntityT, *args: P.args, **kwargs: P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
        except NADConnectionError as ex:
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"name": self._device.name},
            ) from ex
        except NADTimeoutError as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="timeout_error",
                translation_placeholders={"name": self._device.name},
            ) from ex
        except NADBaseError as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unknown_error",
                translation_placeholders={"error": str(ex)},
            ) from ex
        self.async_write_ha_state()

    return wrapper


def handle_nad_update_errors[EntityT: NADEntity](
    func: Callable[[EntityT], Coroutine[Any, Any, None]],
) -> Callable[[EntityT], Coroutine[Any, Any, None]]:
    """Handles NAD errors for updates."""

    @functools.wraps(func)
    async def wrapper(self: EntityT) -> None:
        try:
            await func(self)
            self._attr_available = True
        except NADConnectionError:
            await self.coordinator.async_request_refresh()
        except NADTimeoutError:
            self._attr_available = False
        except NADBaseError as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unknown_error",
                translation_placeholders={"error": str(ex)},
            ) from ex
        self.async_write_ha_state()

    return wrapper


class NADEntity(CoordinatorEntity[NADCoordinator]):
    """Base NAD entity."""

    _attr_available: bool = False

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

    @property
    @override
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available and self.coordinator.last_update_success

    @property
    @override
    def should_poll(self) -> bool:
        return not self.coordinator.device.sends_updates

    @override
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._device.add_callback(self._async_nad_callback))
        self._attr_available = True

    @callback
    def _async_nad_callback(self, setting: str, value: Any) -> None:
        """Handle settings pushed by the device."""
        if (
            not hasattr(self, "entity_description")
            or setting.lower() == self.entity_description.key.lower()
        ):
            _LOGGER.debug("%s changed to %s", setting, value)
            self.async_write_ha_state()

    @override
    @handle_nad_update_errors
    async def async_update(self) -> None:
        """Update the entity."""
        if (
            self._device.sends_updates
            or not self._device.is_on
            or not hasattr(self, "entity_description")
        ):
            return

        await self._device.async_request_setting(self.entity_description.key)
