"""Tesla orders data retrieval (non-interactive version for HA)."""

import json
import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.config import APP_VERSION, TESLA_STORES
from app.utils.helpers import decode_option_codes, get_date_from_timestamp, compare_dicts
from app.utils.history import load_history_from_file, save_history_to_file, get_history_of_order
from app.utils.timeline import get_timeline_from_order
from app.utils.option_codes import get_option_entry
from app.utils.connection import request_with_retry


def retrieve_orders(access_token: str, language: str = "en") -> List[Dict[str, Any]]:
    """Retrieve all orders from Tesla API.
    
    Args:
        access_token: Tesla API access token
        language: Language code for API requests
    
    Returns:
        List of order dictionaries
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    api_url = 'https://owner-api.teslamotors.com/api/1/users/orders'
    response = request_with_retry(api_url, headers, exit_on_error=False)
    if response is None:
        raise RuntimeError("Failed to retrieve orders from Tesla API")
    return response.json().get('response', [])


def retrieve_order_details(order_id: str, access_token: str, language: str = "en") -> Dict[str, Any]:
    """Retrieve detailed information for a specific order.
    
    Args:
        order_id: Order reference number
        access_token: Tesla API access token
        language: Language code for API requests
    
    Returns:
        Dictionary containing order details
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    api_url = f'https://akamai-apigateway-vfx.tesla.com/tasks?deviceLanguage={language}&deviceCountry=DE&referenceNumber={order_id}&appVersion={APP_VERSION}'
    response = request_with_retry(api_url, headers, exit_on_error=False)
    if response is None:
        raise RuntimeError(f"Failed to retrieve order details for {order_id}")
    return response.json()


def get_all_orders(access_token: str, language: str = "en") -> List[Dict[str, Any]]:
    """Get all orders with their details.
    
    Args:
        access_token: Tesla API access token
        language: Language code for API requests
    
    Returns:
        List of detailed order dictionaries
    """
    orders = retrieve_orders(access_token, language)
    
    detailed_orders = []
    for order in orders:
        order_id = order['referenceNumber']
        order_details = retrieve_order_details(order_id, access_token, language)
        
        if not order_details or not order_details.get('tasks'):
            continue  # Skip invalid orders
        
        detailed_order = {
            'order': order,
            'details': order_details
        }
        detailed_orders.append(detailed_order)
    
    return detailed_orders


def save_orders_to_file(orders: List[Dict[str, Any]], orders_file_path: Path) -> None:
    """Save orders to file.
    
    Args:
        orders: List of order dictionaries
        orders_file_path: Path to orders file
    """
    orders_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(orders_file_path, 'w') as f:
        json.dump(orders, f)


def load_orders_from_file(orders_file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Load orders from file.
    
    Args:
        orders_file_path: Path to orders file
    
    Returns:
        List of order dictionaries or None if file doesn't exist
    """
    if not orders_file_path.exists():
        return None
    try:
        with open(orders_file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def compare_orders(old_orders: List[Dict[str, Any]], new_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compare old and new orders to detect changes.
    
    Args:
        old_orders: Previous orders list
        new_orders: Current orders list
    
    Returns:
        List of difference dictionaries
    """
    differences = []
    for i, old_order in enumerate(old_orders):
        if i < len(new_orders):
            differences.extend(compare_dicts(old_order, new_orders[i], path=f'{i}.'))
        else:
            differences.append({'operation': 'removed', 'key': str(i)})
    for i in range(len(old_orders), len(new_orders)):
        differences.append({'operation': 'added', 'key': str(i)})
    return differences


def get_model_from_order(detailed_order: Dict[str, Any]) -> str:
    """Extract model information from order.
    
    Args:
        detailed_order: Detailed order dictionary
    
    Returns:
        Model string (e.g., "Model Y - AWD LR")
    """
    order = detailed_order.get('order', {})
    decoded_options = decode_option_codes(order.get('mktOptions', ''))
    model = "unknown"
    for _, description in decoded_options:
        if 'Model' in description and len(description) > 10:
            match = re.match(r'(Model [YSX3]).*?((AWD|RWD) (LR|SR|P)).*?$', description)
            if match:
                model_name = match.group(1)
                config_suffix = match.group(2)
                value = f"{model_name} - {config_suffix}"
                model = value.strip()
                break
    return model


def get_order_data(detailed_order: Dict[str, Any], order_index: int = 0) -> Dict[str, Any]:
    """Extract structured data from detailed order.
    
    Args:
        detailed_order: Detailed order dictionary
        order_index: Index of order (for history lookup)
    
    Returns:
        Dictionary with structured order data
    """
    order = detailed_order.get('order', {})
    order_details = detailed_order.get('details', {})
    tasks = order_details.get('tasks', {})
    scheduling = tasks.get('scheduling', {})
    registration_data = tasks.get('registration', {})
    order_info = registration_data.get('orderDetails', {})
    final_payment_data = tasks.get('finalPayment', {}).get('data', {})
    
    # Basic order info
    order_id = order.get('referenceNumber', '')
    status = order.get('orderStatus', '')
    vin = order.get('vin')
    
    # Model and options
    decoded_options = decode_option_codes(order.get('mktOptions', ''))
    model = get_model_from_order(detailed_order)
    options = []
    for code, description in decoded_options:
        entry = get_option_entry(code) or {}
        options.append({
            'code': code,
            'description': description,
            'category': entry.get('category')
        })
    
    # Delivery information
    location_id = order_info.get('vehicleRoutingLocation')
    store = TESLA_STORES.get(str(location_id) if location_id is not None else '', {})
    
    delivery_info = {
        'delivery_window': scheduling.get('deliveryWindowDisplay'),
        'delivery_appointment': get_date_from_timestamp(scheduling.get('deliveryAppointmentDate')) if scheduling.get('deliveryAppointmentDate') else None,
        'eta_to_delivery_center': final_payment_data.get('etaToDeliveryCenter'),
        'delivery_address_title': scheduling.get('deliveryAddressTitle'),
    }
    
    if store:
        delivery_info['routing_location'] = {
            'id': location_id,
            'name': store.get('display_name'),
            'address': store.get('address', {}),
            'phone': store.get('phone'),
            'email': store.get('store_email'),
        }
    
    # Vehicle status
    odometer = order_info.get('vehicleOdometer')
    odometer_type = order_info.get('vehicleOdometerType')
    vehicle_status = None
    if odometer is not None and odometer != 30 and odometer_type is not None:
        vehicle_status = {
            'odometer': odometer,
            'odometer_type': odometer_type
        }
    
    # Financing information
    financing_info = None
    financing_details = final_payment_data.get('financingDetails') or {}
    order_type = financing_details.get('orderType')
    tesla_finance_details = financing_details.get('teslaFinanceDetails') or {}
    
    if order_type == 'CASH' or not final_payment_data.get('financingIntent'):
        payment_details = final_payment_data.get('paymentDetails') or []
        financing_info = {
            'type': 'CASH',
            'payment_details': payment_details[0] if payment_details else None,
            'account_balance': final_payment_data.get('accountBalance'),
            'amount_due': final_payment_data.get('amountDue'),
        }
    else:
        financing_info = {
            'type': order_type,
            'product': financing_details.get('financialProductType'),
            'partner': tesla_finance_details.get('financePartnerName'),
            'monthly_payment': tesla_finance_details.get('monthlyPayment'),
            'term_months': tesla_finance_details.get('termsInMonths'),
            'interest_rate': tesla_finance_details.get('interestRate'),
            'mileage': tesla_finance_details.get('mileage'),
            'financed_amount': final_payment_data.get('amountDueFinancier'),
            'approved_amount': tesla_finance_details.get('approvedLoanAmount'),
        }
    
    # Timeline
    timeline = get_timeline_from_order(order_index, detailed_order)
    
    # History
    history = get_history_of_order(order_index)
    
    return {
        'order_id': order_id,
        'status': status,
        'vin': vin,
        'model': model,
        'options': options,
        'delivery_info': delivery_info,
        'vehicle_status': vehicle_status,
        'financing_info': financing_info,
        'timeline': timeline,
        'history': history,
        'full_data': detailed_order,  # Keep full data for advanced use
    }


def get_all_orders_data(access_token: str, language: str = "en") -> List[Dict[str, Any]]:
    """Get all orders with structured data.
    
    Args:
        access_token: Tesla API access token
        language: Language code for API requests
    
    Returns:
        List of structured order data dictionaries
    """
    detailed_orders = get_all_orders(access_token, language)
    return [get_order_data(order, idx) for idx, order in enumerate(detailed_orders)]

