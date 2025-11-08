"""Binary sensor platform for Tesla Order Status changes."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_CHANGES, ATTR_LAST_UPDATE, DOMAIN
from .coordinator import TeslaOrderStatusCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTION = BinarySensorEntityDescription(
    key="has_changes",
    name="Has Changes",
    icon="mdi:alert-circle",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tesla Order Status binary sensors from a config entry."""
    coordinator: TeslaOrderStatusCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create binary sensors for each order
    sensors = []
    orders = coordinator.orders
    
    for order_data in orders:
        order_id = order_data.get("order_id", "")
        if not order_id:
            continue
        
        sensors.append(
            TeslaOrderStatusBinarySensor(
                coordinator,
                entry,
                order_id,
            )
        )
    
    async_add_entities(sensors, update_before_add=True)


class TeslaOrderStatusBinarySensor(
    CoordinatorEntity[TeslaOrderStatusCoordinator], BinarySensorEntity
):
    """Representation of a Tesla Order Status binary sensor for changes."""

    def __init__(
        self,
        coordinator: TeslaOrderStatusCoordinator,
        entry: ConfigEntry,
        order_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._order_id = order_id
        self.entity_description = BINARY_SENSOR_DESCRIPTION
        self._attr_unique_id = f"{entry.entry_id}_{order_id}_has_changes"
        self._attr_name = f"Tesla Order {order_id} Has Changes"

    @property
    def is_on(self) -> bool:
        """Return True if changes detected."""
        changes = self.coordinator.changes
        if not changes:
            return False
        
        # Find order index for this order_id
        orders = self.coordinator.orders
        order_index = None
        for idx, order in enumerate(orders):
            if order.get("order_id") == self._order_id:
                order_index = idx
                break
        
        if order_index is None:
            return False
        
        # Check if any change is related to this order (changes use index prefix)
        for change in changes:
            key = change.get("key", "")
            # Changes are stored with order index prefix (e.g., "0.order.referenceNumber")
            if str(key).startswith(f"{order_index}."):
                return True
        
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        changes = self.coordinator.changes
        order_changes = []
        
        # Find order index for this order_id
        orders = self.coordinator.orders
        order_index = None
        for idx, order in enumerate(orders):
            if order.get("order_id") == self._order_id:
                order_index = idx
                break
        
        if order_index is not None and changes:
            # Filter changes for this order (changes use index prefix)
            for change in changes:
                key = change.get("key", "")
                if str(key).startswith(f"{order_index}."):
                    order_changes.append(change)
        
        attrs = {
            ATTR_CHANGES: order_changes,
            ATTR_LAST_UPDATE: self.coordinator.last_update_success_time.isoformat() if self.coordinator.last_update_success_time else None,
        }
        
        return attrs

