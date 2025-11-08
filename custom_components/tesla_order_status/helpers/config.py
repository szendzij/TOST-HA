"""Configuration module adapted for Home Assistant integration."""

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

# -------------------------
# Constants
# -------------------------
APP_VERSION = '9.99.9-9999'  # we can use a fake version here, as the API does not check it strictly
TODAY = time.strftime('%Y-%m-%d')
TELEMETRIC_URL = "https://www.tesla-order-status-tracker.de/push/telemetry.php"
VERSION = "p1.0.1"

# These will be initialized by the integration
_hass_config_dir: Optional[Path] = None
_integration_dir: Optional[Path] = None

def init_paths(hass_config_dir: Path, integration_dir: Path) -> None:
    """Initialize paths for Home Assistant integration.
    
    Args:
        hass_config_dir: Home Assistant config directory (hass.config.config_dir)
        integration_dir: Integration directory (where this file is located)
    """
    global _hass_config_dir, _integration_dir, BASE_DIR, APP_DIR, DATA_DIR, PUBLIC_DIR, PRIVATE_DIR
    global TOKEN_FILE, ORDERS_FILE, HISTORY_FILE, TESLA_STORES_FILE, SETTINGS_FILE, TESLA_STORES
    
    _hass_config_dir = hass_config_dir
    _integration_dir = integration_dir
    
    # Use integration directory as BASE_DIR for static files
    BASE_DIR = integration_dir.parent.parent.parent  # Go up to repo root for compatibility
    APP_DIR = integration_dir  # helpers directory
    DATA_DIR = hass_config_dir / "tesla_order_status"
    
    # Public data (static files bundled with integration)
    # For translations, use HA translations directory
    PUBLIC_DIR = integration_dir.parent / "translations"  # custom_components/tesla_order_status/translations
    PRIVATE_DIR = DATA_DIR / "private"
    
    # Files in HA config directory
    TOKEN_FILE = PRIVATE_DIR / 'tesla_tokens.json'
    ORDERS_FILE = PRIVATE_DIR / 'tesla_orders.json'
    HISTORY_FILE = PRIVATE_DIR / 'tesla_order_history.json'
    SETTINGS_FILE = PRIVATE_DIR / 'settings.json'
    
    # Static file bundled with integration
    TESLA_STORES_FILE = integration_dir.parent / 'tesla_locations.json'
    
    # Load TESLA_STORES from bundled file
    try:
        if TESLA_STORES_FILE.exists():
            with open(TESLA_STORES_FILE, encoding="utf-8") as f:
                TESLA_STORES = json.load(f)
        else:
            TESLA_STORES = {}
    except Exception:
        TESLA_STORES = {}

# Initialize with defaults (will be updated by integration)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PUBLIC_DIR = Path(__file__).resolve().parent.parent
PRIVATE_DIR = DATA_DIR / "private"

TOKEN_FILE = PRIVATE_DIR / 'tesla_tokens.json'
ORDERS_FILE = PRIVATE_DIR / 'tesla_orders.json'
HISTORY_FILE = PRIVATE_DIR / 'tesla_order_history.json'
TESLA_STORES_FILE = PUBLIC_DIR / 'tesla_locations.json'
SETTINGS_FILE = PRIVATE_DIR / 'settings.json'

TESLA_STORES = {}

class Config:
    def __init__(self, path: Path):
        self._path = path
        self._cfg: dict[str, Any] = {}
        self.load()  # gleich beim Init laden

    def load(self) -> None:
        if not self._path.exists():
            self._cfg = {}
            return
        try:
            with self._path.open(encoding="utf-8") as f:
                text = f.read()
                # remove trailing commas before } or ]
                text = re.sub(r",\s*([\]\}])", r"\1", text)
                self._cfg = json.loads(text)
        except json.JSONDecodeError as e:
            self._cfg = {}
            return

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(
            self._cfg,
            indent=2,
            sort_keys=True,
            ensure_ascii=False
        ) + "\n"
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self._path)

    def get(self, key: str, default: Any = None) -> Any:
        return self._cfg.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cfg[key] = value
        self.save()

    def has(self, key: str) -> bool:
        return key in self._cfg

    def delete(self, key: str) -> None:
        self._cfg.pop(key, None)
        self.save()

# This will be initialized after paths are set
cfg: Optional[Config] = None

def get_config() -> Config:
    """Get or create Config instance."""
    global cfg
    if cfg is None:
        cfg = Config(SETTINGS_FILE)
    return cfg

