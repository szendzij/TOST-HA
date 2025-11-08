"""Sensor platform for Tesla Order Status."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DELIVERY_APPOINTMENT,
    ATTR_DELIVERY_WINDOW,
    ATTR_ETA_TO_DELIVERY_CENTER,
    ATTR_FULL_DATA,
    ATTR_HISTORY,
    ATTR_MODEL,
    ATTR_OPTIONS,
    ATTR_ORDER_ID,
    ATTR_STATUS,
    ATTR_TIMELINE,
    ATTR_VIN,
    DOMAIN,
)
from .coordinator import TeslaOrderStatusCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "status": SensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:car",
    ),
    "vin": SensorEntityDescription(
        key="vin",
        name="VIN",
        icon="mdi:identifier",
    ),
    "model": SensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:car-sports",
    ),
    "delivery_window": SensorEntityDescription(
        key="delivery_window",
        name="Delivery Window",
        icon="mdi:calendar-range",
    ),
    "delivery_appointment": SensorEntityDescription(
        key="delivery_appointment",
        name="Delivery Appointment",
        icon="mdi:calendar-clock",
    ),
    "eta_to_delivery_center": SensorEntityDescription(
        key="eta_to_delivery_center",
        name="ETA to Delivery Center",
        icon="mdi:map-marker-distance",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tesla Order Status sensors from a config entry."""
    coordinator: TeslaOrderStatusCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensors for each order
    sensors = []
    orders = coordinator.orders
    
    for order_data in orders:
        order_id = order_data.get("order_id", "")
        if not order_id:
            continue
        
        # Create sensors for this order
        for sensor_key, description in SENSOR_TYPES.items():
            sensors.append(
                TeslaOrderStatusSensor(
                    coordinator,
                    entry,
                    order_id,
                    sensor_key,
                    description,
                )
            )
    
    async_add_entities(sensors, update_before_add=True)


class TeslaOrderStatusSensor(
    CoordinatorEntity[TeslaOrderStatusCoordinator], SensorEntity
):
    """Representation of a Tesla Order Status sensor."""

    def __init__(
        self,
        coordinator: TeslaOrderStatusCoordinator,
        entry: ConfigEntry,
        order_id: str,
        sensor_key: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._order_id = order_id
        self._sensor_key = sensor_key
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{order_id}_{sensor_key}"
        self._attr_name = f"Tesla Order {order_id} {description.name}"

    @property
    def order_data(self) -> dict[str, Any] | None:
        """Get data for this order."""
        orders = self.coordinator.orders
        for order in orders:
            if order.get("order_id") == self._order_id:
                return order
        return None

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        order_data = self.order_data
        if not order_data:
            return None
        
        if self._sensor_key == "status":
            return order_data.get("status")
        elif self._sensor_key == "vin":
            return order_data.get("vin")
        elif self._sensor_key == "model":
            return order_data.get("model")
        elif self._sensor_key == "delivery_window":
            delivery_info = order_data.get("delivery_info", {})
            return delivery_info.get("delivery_window")
        elif self._sensor_key == "delivery_appointment":
            delivery_info = order_data.get("delivery_info", {})
            return delivery_info.get("delivery_appointment")
        elif self._sensor_key == "eta_to_delivery_center":
            delivery_info = order_data.get("delivery_info", {})
            return delivery_info.get("eta_to_delivery_center")
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        order_data = self.order_data
        if not order_data:
            return {}
        
        attrs = {
            ATTR_ORDER_ID: order_data.get("order_id"),
        }
        
        # Add model if available
        if order_data.get("model"):
            attrs[ATTR_MODEL] = order_data.get("model")
        
        # Add VIN if available
        if order_data.get("vin"):
            attrs[ATTR_VIN] = order_data.get("vin")
        
        # Add status
        if order_data.get("status"):
            attrs[ATTR_STATUS] = order_data.get("status")
        
        # Add delivery info
        delivery_info = order_data.get("delivery_info", {})
        if delivery_info.get("delivery_window"):
            attrs[ATTR_DELIVERY_WINDOW] = delivery_info.get("delivery_window")
        if delivery_info.get("delivery_appointment"):
            attrs[ATTR_DELIVERY_APPOINTMENT] = delivery_info.get("delivery_appointment")
        if delivery_info.get("eta_to_delivery_center"):
            attrs[ATTR_ETA_TO_DELIVERY_CENTER] = delivery_info.get("eta_to_delivery_center")
        
        # Add options
        if order_data.get("options"):
            attrs[ATTR_OPTIONS] = order_data.get("options")
        
        # Add timeline
        if order_data.get("timeline"):
            attrs[ATTR_TIMELINE] = order_data.get("timeline")
        
        # Add history
        if order_data.get("history"):
            attrs[ATTR_HISTORY] = order_data.get("history")
        
        # Add full data (for advanced use)
        if order_data.get("full_data"):
            attrs[ATTR_FULL_DATA] = order_data.get("full_data")
        
        return attrs

