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
    ATTR_AMOUNT_DUE,
    ATTR_DELIVERY_ADDRESS_TITLE,
    ATTR_DELIVERY_APPOINTMENT,
    ATTR_DELIVERY_WINDOW,
    ATTR_ETA_TO_DELIVERY_CENTER,
    ATTR_FINANCING_INFO,
    ATTR_FINANCING_TYPE,
    ATTR_FULL_DATA,
    ATTR_HISTORY,
    ATTR_MODEL,
    ATTR_MONTHLY_PAYMENT,
    ATTR_ODOMETER,
    ATTR_OPTIONS,
    ATTR_ORDER_ID,
    ATTR_ROUTING_LOCATION,
    ATTR_STATUS,
    ATTR_TIMELINE,
    ATTR_VEHICLE_STATUS,
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
    "delivery_address_title": SensorEntityDescription(
        key="delivery_address_title",
        name="Delivery Address Title",
        icon="mdi:map-marker",
    ),
    "routing_location_name": SensorEntityDescription(
        key="routing_location_name",
        name="Routing Location Name",
        icon="mdi:store",
    ),
    "odometer": SensorEntityDescription(
        key="odometer",
        name="Odometer",
        icon="mdi:counter",
    ),
    "financing_type": SensorEntityDescription(
        key="financing_type",
        name="Financing Type",
        icon="mdi:currency-usd",
    ),
    "monthly_payment": SensorEntityDescription(
        key="monthly_payment",
        name="Monthly Payment",
        icon="mdi:currency-usd",
    ),
    "amount_due": SensorEntityDescription(
        key="amount_due",
        name="Amount Due",
        icon="mdi:currency-usd",
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
    def native_value(self) -> str | int | float | None:
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
        elif self._sensor_key == "delivery_address_title":
            delivery_info = order_data.get("delivery_info", {})
            return delivery_info.get("delivery_address_title")
        elif self._sensor_key == "routing_location_name":
            delivery_info = order_data.get("delivery_info", {})
            routing_location = delivery_info.get("routing_location", {})
            return routing_location.get("name")
        elif self._sensor_key == "odometer":
            vehicle_status = order_data.get("vehicle_status")
            if vehicle_status:
                return vehicle_status.get("odometer")
            return None
        elif self._sensor_key == "financing_type":
            financing_info = order_data.get("financing_info")
            if financing_info:
                return financing_info.get("type")
            return None
        elif self._sensor_key == "monthly_payment":
            financing_info = order_data.get("financing_info")
            if financing_info:
                monthly_payment = financing_info.get("monthly_payment")
                if monthly_payment is not None:
                    try:
                        return float(monthly_payment)
                    except (ValueError, TypeError):
                        return None
            return None
        elif self._sensor_key == "amount_due":
            financing_info = order_data.get("financing_info")
            if financing_info:
                amount_due = financing_info.get("amount_due")
                if amount_due is not None:
                    try:
                        return float(amount_due)
                    except (ValueError, TypeError):
                        return None
            return None
        
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor."""
        if self._sensor_key == "odometer":
            order_data = self.order_data
            if order_data:
                vehicle_status = order_data.get("vehicle_status")
                if vehicle_status:
                    return vehicle_status.get("odometer_type")
        elif self._sensor_key in ("monthly_payment", "amount_due"):
            # Try to determine currency from order data
            # Default to EUR, but could be enhanced to detect from locale/region
            return "EUR"
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
        if delivery_info.get("delivery_address_title"):
            attrs[ATTR_DELIVERY_ADDRESS_TITLE] = delivery_info.get("delivery_address_title")
        if delivery_info.get("routing_location"):
            attrs[ATTR_ROUTING_LOCATION] = delivery_info.get("routing_location")
        
        # Add vehicle status
        if order_data.get("vehicle_status"):
            attrs[ATTR_VEHICLE_STATUS] = order_data.get("vehicle_status")
        
        # Add financing info
        if order_data.get("financing_info"):
            financing_info = order_data.get("financing_info")
            attrs[ATTR_FINANCING_INFO] = financing_info
            if financing_info.get("type"):
                attrs[ATTR_FINANCING_TYPE] = financing_info.get("type")
            if financing_info.get("monthly_payment") is not None:
                attrs[ATTR_MONTHLY_PAYMENT] = financing_info.get("monthly_payment")
            if financing_info.get("amount_due") is not None:
                attrs[ATTR_AMOUNT_DUE] = financing_info.get("amount_due")
        
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

