"""Tesla Order Status API client for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

# Import helpers utilities
from .helpers.utils.auth import (
    is_token_valid,
    refresh_tokens,
    save_tokens_to_file,
    load_tokens_from_file,
)
from .helpers.utils.orders_data import (
    get_all_orders_data,
    save_orders_to_file,
    load_orders_from_file,
    compare_orders,
)
import time
TODAY = time.strftime('%Y-%m-%d')

from .const import (
    STORAGE_DIR_NAME,
    TOKEN_FILE_NAME,
    ORDERS_FILE_NAME,
    HISTORY_FILE_NAME,
)

_LOGGER = logging.getLogger(__name__)


class TeslaOrderStatusAPI:
    """Tesla Order Status API client."""

    def __init__(
        self,
        hass: HomeAssistant,
        access_token: str,
        refresh_token: str | None = None,
        language: str = "en",
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._language = language
        
        # Setup storage paths
        self._storage_dir = Path(hass.config.config_dir) / STORAGE_DIR_NAME
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._token_file = self._storage_dir / TOKEN_FILE_NAME
        self._orders_file = self._storage_dir / ORDERS_FILE_NAME
        self._history_file = self._storage_dir / HISTORY_FILE_NAME

    @property
    def access_token(self) -> str:
        """Get current access token, refreshing if needed."""
        if not is_token_valid(self._access_token):
            if self._refresh_token:
                _LOGGER.info("Access token expired, refreshing...")
                try:
                    tokens = refresh_tokens(self._refresh_token)
                    self._access_token = tokens["access_token"]
                    if "refresh_token" in tokens:
                        self._refresh_token = tokens["refresh_token"]
                    
                    # Save updated tokens
                    token_data = {
                        "access_token": self._access_token,
                        "refresh_token": self._refresh_token,
                    }
                    save_tokens_to_file(token_data, self._token_file)
                except Exception as err:
                    _LOGGER.error("Failed to refresh token: %s", err)
                    raise
            else:
                raise RuntimeError("Access token expired and no refresh token available")
        
        return self._access_token

    async def async_get_orders(self) -> list[dict[str, Any]]:
        """Get all orders with their details."""
        try:
            orders = await self.hass.async_add_executor_job(
                get_all_orders_data,
                self.access_token,
                self._language,
            )
            return orders
        except Exception as err:
            _LOGGER.error("Failed to retrieve orders: %s", err)
            raise

    async def async_update_orders(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Update orders and return (new_orders, changes).
        
        Returns:
            Tuple of (orders_data, changes_list)
        """
        # Load old orders
        old_orders = await self.hass.async_add_executor_job(
            load_orders_from_file,
            self._orders_file,
        )
        
        # Get new orders
        new_orders_data = await self.async_get_orders()
        
        # Convert to format for comparison (detailed orders)
        new_orders_detailed = []
        for order_data in new_orders_data:
            new_orders_detailed.append(order_data.get("full_data", {}))
        
        changes = []
        if old_orders:
            # Compare orders
            differences = await self.hass.async_add_executor_job(
                compare_orders,
                old_orders,
                new_orders_detailed,
            )
            
            if differences:
                # Save new orders
                await self.hass.async_add_executor_job(
                    save_orders_to_file,
                    new_orders_detailed,
                    self._orders_file,
                )
                
                # Update history
                import json
                # Load existing history from HA storage
                history = []
                if self._history_file.exists():
                    try:
                        with open(self._history_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        history = []
                
                # Append new changes
                history.append({
                    "timestamp": TODAY,
                    "changes": differences,
                })
                
                # Save to HA storage location
                await self.hass.async_add_executor_job(
                    lambda: json.dump(history, open(self._history_file, 'w', encoding='utf-8'), indent=2)
                )
                
                changes = differences
        else:
            # First time - save orders
            await self.hass.async_add_executor_job(
                save_orders_to_file,
                new_orders_detailed,
                self._orders_file,
            )
        
        return new_orders_data, changes

    async def async_get_cached_orders(self) -> list[dict[str, Any]] | None:
        """Get cached orders from file."""
        orders = await self.hass.async_add_executor_job(
            load_orders_from_file,
            self._orders_file,
        )
        if orders:
            # Convert back to structured format
            orders_data = []
            for idx, order in enumerate(orders):
                orders_data.append({
                    "order_id": order.get("order", {}).get("referenceNumber", ""),
                    "status": order.get("order", {}).get("orderStatus", ""),
                    "vin": order.get("order", {}).get("vin"),
                    "full_data": order,
                })
            return orders_data
        return None

