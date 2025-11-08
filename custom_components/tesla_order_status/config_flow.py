"""Config flow for Tesla Order Status integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

# Import auth utilities
import sys
from pathlib import Path

# Add app directory to path for imports
APP_DIR = Path(__file__).resolve().parent.parent.parent / "app"
sys.path.insert(0, str(APP_DIR.parent))

from app.utils.auth import (
    generate_code_verifier_and_challenge,
    get_auth_url,
    extract_auth_code_from_url,
    exchange_code_for_tokens,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # This will be called during config flow
    return {"title": "Tesla Order Status"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesla Order Status."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.code_verifier: str | None = None
        self.code_challenge: str | None = None
        self.state: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Generate OAuth2 parameters
            self.code_verifier, self.code_challenge = generate_code_verifier_and_challenge()
            
            # Generate auth URL
            import secrets
            self.state = secrets.token_hex(16)
            auth_url = get_auth_url(self.code_challenge, self.state)
            
            # Store in flow context
            self.hass.data.setdefault(DOMAIN, {})
            self.hass.data[DOMAIN]["auth_url"] = auth_url
            self.hass.data[DOMAIN]["code_verifier"] = self.code_verifier
            self.hass.data[DOMAIN]["state"] = self.state
            
            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the authentication step."""
        errors = {}
        
        if user_input is None:
            # Show instructions - generate auth URL if not already done
            if "auth_url" not in self.hass.data.get(DOMAIN, {}):
                self.code_verifier, self.code_challenge = generate_code_verifier_and_challenge()
                import secrets
                self.state = secrets.token_hex(16)
                auth_url = get_auth_url(self.code_challenge, self.state)
                self.hass.data.setdefault(DOMAIN, {})
                self.hass.data[DOMAIN]["auth_url"] = auth_url
                self.hass.data[DOMAIN]["code_verifier"] = self.code_verifier
                self.hass.data[DOMAIN]["state"] = self.state
            else:
                auth_url = self.hass.data[DOMAIN]["auth_url"]
            
            return self.async_show_form(
                step_id="auth",
                data_schema=vol.Schema({
                    vol.Required("redirect_url", description="Paste the full URL from Tesla redirect"): str,
                }),
                description_placeholders={
                    "auth_url": auth_url,
                },
                errors=errors,
            )
        
        redirect_url = user_input.get("redirect_url", "")
        
        if not redirect_url:
            errors["base"] = "missing_url"
            return self.async_show_form(
                step_id="auth",
                data_schema=vol.Schema({
                    vol.Required("redirect_url"): str,
                }),
                errors=errors,
            )
        
        try:
            # Extract auth code from URL
            auth_code = extract_auth_code_from_url(redirect_url)
            
            # Exchange code for tokens
            code_verifier = self.hass.data[DOMAIN].get("code_verifier")
            if not code_verifier:
                errors["base"] = "missing_verifier"
                return self.async_show_form(
                    step_id="auth",
                    data_schema=vol.Schema({
                        vol.Required("redirect_url"): str,
                    }),
                    errors=errors,
                )
            
            tokens = await self.hass.async_add_executor_job(
                exchange_code_for_tokens, auth_code, code_verifier
            )
            
            # Validate tokens
            if not tokens.get("access_token"):
                errors["base"] = "invalid_tokens"
                return self.async_show_form(
                    step_id="auth",
                    data_schema=vol.Schema({
                        vol.Required("redirect_url"): str,
                    }),
                    errors=errors,
                )
            
            # Create config entry
            return self.async_create_entry(
                title="Tesla Order Status",
                data={
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens.get("refresh_token"),
                    "expires_in": tokens.get("expires_in"),
                },
            )
            
        except ValueError as err:
            _LOGGER.exception("Error extracting auth code: %s", err)
            errors["base"] = "invalid_url"
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: %s", err)
            errors["base"] = "unknown"
        
        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema({
                vol.Required("redirect_url"): str,
            }),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

