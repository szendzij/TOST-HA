# Tesla Order Status - Home Assistant Integration

This is a Home Assistant custom integration for tracking Tesla order status. It is based on the [Tesla Order Status Tracker](https://github.com/chrisi51/tesla-order-status) project.

## Features

- Track Tesla order status directly in Home Assistant
- Automatic updates every hour
- Sensors for each order with detailed information:
  - Order status
  - VIN (when available)
  - Model information
  - Delivery window
  - Delivery appointment date
  - ETA to delivery center
  - Timeline of order events
  - Change history
- Binary sensor to detect when order status changes
- Full integration with Home Assistant automations and notifications

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL
5. Search for "Tesla Order Status" and install it
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/tesla_order_status` folder to your Home Assistant `custom_components` directory
2. Copy the `app` folder to your Home Assistant config directory (alongside `custom_components`)
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Tesla Order Status**
4. Follow the authentication flow:
   - Click "Submit" to start
   - You will see an authorization URL
   - Open this URL in your browser
   - Log in to your Tesla account
   - After login, you will see a "Page Not Found" page - **this is CORRECT!**
   - Copy the full URL from your browser's address bar
   - Paste it into the "Redirect URL" field in Home Assistant
   - Click "Submit"

## Usage

After configuration, the integration will automatically create sensors for each of your Tesla orders:

- `sensor.tesla_order_[order_id]_status` - Current order status
- `sensor.tesla_order_[order_id]_vin` - Vehicle Identification Number
- `sensor.tesla_order_[order_id]_model` - Model information (e.g., "Model Y - AWD LR")
- `sensor.tesla_order_[order_id]_delivery_window` - Delivery window
- `sensor.tesla_order_[order_id]_delivery_appointment` - Delivery appointment date
- `sensor.tesla_order_[order_id]_eta_to_delivery_center` - ETA to delivery center
- `binary_sensor.tesla_order_[order_id]_has_changes` - Indicates if order status has changed

### Sensor Attributes

Each sensor includes additional attributes:
- `order_id` - Order reference number
- `model` - Vehicle model
- `vin` - Vehicle Identification Number
- `status` - Order status
- `delivery_window` - Delivery window
- `delivery_appointment` - Delivery appointment date
- `eta_to_delivery_center` - ETA to delivery center
- `options` - List of vehicle options
- `timeline` - Timeline of order events
- `history` - Change history
- `full_data` - Complete order data (JSON)

## Automations

You can create automations based on order status changes:

```yaml
automation:
  - alias: "Tesla Order Status Changed"
    trigger:
      - platform: state
        entity_id: binary_sensor.tesla_order_rn123456789_has_changes
        to: 'on'
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Tesla order status has changed!"
          data:
            actions:
              - action: "VIEW_ORDER"
                title: "View Order"
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:
1. Make sure you copied the complete URL from your browser
2. The URL should start with `https://auth.tesla.com/void/callback?code=...`
3. Try the authentication flow again

### No Sensors Created

If no sensors are created:
1. Check the logs for errors
2. Make sure you have active Tesla orders
3. Verify the integration is properly configured

### Token Refresh Issues

The integration automatically refreshes tokens when they expire. If you encounter token refresh errors:
1. Remove the integration
2. Re-add it with a fresh authentication

## Data Storage

The integration stores data in:
- `config/tesla_order_status/tokens.json` - Authentication tokens
- `config/tesla_order_status/orders.json` - Cached order data
- `config/tesla_order_status/history.json` - Change history

## Privacy

- All authentication happens directly between you and Tesla
- No data is sent to third-party servers
- All data is stored locally in your Home Assistant instance
- Tokens are stored securely in Home Assistant's config directory

## Support

For issues and questions:
- GitHub Issues: [https://github.com/chrisi51/tesla-order-status/issues](https://github.com/chrisi51/tesla-order-status/issues)
- Original Project: [https://github.com/chrisi51/tesla-order-status](https://github.com/chrisi51/tesla-order-status)

## License

This integration is based on the Tesla Order Status Tracker project. Please refer to the original project for license information.
