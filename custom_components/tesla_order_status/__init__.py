"""Tesla Order Status integration for Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import TeslaOrderStatusAPI
from .const import DOMAIN
from .coordinator import TeslaOrderStatusCoordinator
from .services import async_setup_services, async_unload_services

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Tesla Order Status integration."""
    # Set up services
    await async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tesla Order Status from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize paths in helpers/config.py
    from .helpers.config import init_paths
    integration_dir = Path(__file__).resolve().parent
    init_paths(Path(hass.config.config_dir), integration_dir)
    
    # Get tokens from config entry
    access_token = entry.data.get("access_token")
    refresh_token = entry.data.get("refresh_token")
    language = entry.data.get("language", "en")
    
    # Create API client
    api = TeslaOrderStatusAPI(
        hass,
        access_token,
        refresh_token,
        language,
    )
    
    # Create coordinator
    coordinator = TeslaOrderStatusCoordinator(hass, entry, api)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unload services if no more entries
        if not hass.data.get(DOMAIN):
            await async_unload_services(hass)

    return unload_ok

