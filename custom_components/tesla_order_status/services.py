"""Services for Tesla Order Status integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import TeslaOrderStatusCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_UPDATE = "update"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Tesla Order Status."""
    
    async def async_update_orders_service(call: ServiceCall) -> None:
        """Service to manually update Tesla orders."""
        _LOGGER.info("Manual update requested for Tesla Order Status")
        
        if DOMAIN not in hass.data:
            _LOGGER.warning("No Tesla Order Status integrations found")
            return
        
        coordinators = hass.data[DOMAIN]
        if not coordinators:
            _LOGGER.warning("No Tesla Order Status coordinators found")
            return
        
        # Update all coordinators
        updated_count = 0
        for entry_id, coordinator in coordinators.items():
            if isinstance(coordinator, TeslaOrderStatusCoordinator):
                try:
                    _LOGGER.debug("Requesting refresh for coordinator %s", entry_id)
                    await coordinator.async_request_refresh()
                    updated_count += 1
                except Exception as err:
                    _LOGGER.error(
                        "Error updating coordinator %s: %s",
                        entry_id,
                        err,
                        exc_info=True,
                    )
        
        if updated_count > 0:
            _LOGGER.info(
                "Successfully requested update for %d Tesla Order Status coordinator(s)",
                updated_count,
            )
        else:
            _LOGGER.warning("No coordinators were updated")
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE,
        async_update_orders_service,
    )
    _LOGGER.debug("Registered service %s.%s", DOMAIN, SERVICE_UPDATE)


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for Tesla Order Status."""
    if hass.services.has_service(DOMAIN, SERVICE_UPDATE):
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE)
        _LOGGER.debug("Unregistered service %s.%s", DOMAIN, SERVICE_UPDATE)

