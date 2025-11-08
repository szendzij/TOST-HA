"""Constants for Tesla Order Status integration."""

DOMAIN = "tesla_order_status"

# Tesla API constants
CLIENT_ID = "ownerapi"
REDIRECT_URI = "https://auth.tesla.com/void/callback"
AUTH_URL = "https://auth.tesla.com/oauth2/v3/authorize"
TOKEN_URL = "https://auth.tesla.com/oauth2/v3/token"
SCOPE = "openid email offline_access"
CODE_CHALLENGE_METHOD = "S256"
APP_VERSION = "9.99.9-9999"

# API endpoints
API_ORDERS_URL = "https://owner-api.teslamotors.com/api/1/users/orders"
API_TASKS_BASE_URL = "https://akamai-apigateway-vfx.tesla.com/tasks"

# Update interval (default: 1 hour)
DEFAULT_UPDATE_INTERVAL = 3600  # seconds

# Storage paths (will be set by integration)
STORAGE_DIR_NAME = "tesla_order_status"
TOKEN_FILE_NAME = "tokens.json"
ORDERS_FILE_NAME = "orders.json"
HISTORY_FILE_NAME = "history.json"
SETTINGS_FILE_NAME = "settings.json"

# Sensor attributes
ATTR_ORDER_ID = "order_id"
ATTR_VIN = "vin"
ATTR_MODEL = "model"
ATTR_STATUS = "status"
ATTR_DELIVERY_WINDOW = "delivery_window"
ATTR_DELIVERY_APPOINTMENT = "delivery_appointment"
ATTR_ETA_TO_DELIVERY_CENTER = "eta_to_delivery_center"
ATTR_TIMELINE = "timeline"
ATTR_HISTORY = "history"
ATTR_OPTIONS = "options"
ATTR_FULL_DATA = "full_data"

# Binary sensor attributes
ATTR_CHANGES = "changes"
ATTR_LAST_UPDATE = "last_update"

