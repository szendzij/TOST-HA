"""DataUpdateCoordinator for Tesla Order Status."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TeslaOrderStatusAPI
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TeslaOrderStatusCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tesla Order Status data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: TeslaOrderStatusAPI,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.api = api
        self.entry = entry
        self._orders: list[dict[str, Any]] = []
        self._changes: list[dict[str, Any]] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            orders, changes = await self.api.async_update_orders()
            self._orders = orders
            self._changes = changes
            
            # Send notification if changes detected
            if changes:
                _LOGGER.info("Changes detected in Tesla orders: %d changes", len(changes))
                # Trigger notification (will be handled by binary sensor)
            
            return {
                "orders": orders,
                "changes": changes,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    @property
    def orders(self) -> list[dict[str, Any]]:
        """Get current orders."""
        return self._orders

    @property
    def changes(self) -> list[dict[str, Any]]:
        """Get latest changes."""
        return self._changes

