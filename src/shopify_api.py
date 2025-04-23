"""
Shopify API client module for fetching orders data.
"""
import logging
import requests
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Import using try/except for flexibility
try:
    from src.config import (
        SHOPIFY_API_KEY,
        SHOPIFY_API_SECRET,
        SHOPIFY_API_VERSION,
        SHOPIFY_SHOP_NAME,
        SHOPIFY_ACCESS_TOKEN,
        DEBUG
    )
except ImportError:
    from config import (
        SHOPIFY_API_KEY,
        SHOPIFY_API_SECRET,
        SHOPIFY_API_VERSION,
        SHOPIFY_SHOP_NAME,
        SHOPIFY_ACCESS_TOKEN,
        DEBUG
    )

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShopifyClient:
    """Client for interacting with the Shopify API to fetch orders."""

    def __init__(self):
        """Initialize the Shopify API client."""
        self.shop_url = f"https://{SHOPIFY_SHOP_NAME}"
        self.api_version = SHOPIFY_API_VERSION
        self.access_token = SHOPIFY_ACCESS_TOKEN
        
        # Check if we have the required credentials
        if not self.access_token:
            logger.warning("Shopify access token not set. API calls will fail.")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for Shopify API requests.
        
        Returns:
            Dict[str, str]: Headers dictionary
        """
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

    def get_orders(self, limit: int = 50, since_days: int = 30, status: str = "any") -> List[Dict[str, Any]]:
        """
        Fetch orders from Shopify.
        
        Args:
            limit (int): Maximum number of orders to fetch
            since_days (int): Fetch orders from the last n days
            status (str): Order status filter (any, open, closed, cancelled)
            
        Returns:
            List[Dict[str, Any]]: List of order dictionaries
        """
        logger.info(f"Fetching up to {limit} orders with status '{status}' from the last {since_days} days")
        
        # Calculate the date range
        created_at_min = (datetime.now() - timedelta(days=since_days)).isoformat()
        
        # Build the URL
        url = f"{self.shop_url}/admin/api/{self.api_version}/orders.json"
        
        # Parameters for the request
        params = {
            "limit": limit,
            "status": status,
            "created_at_min": created_at_min,
            "fields": "id,order_number,created_at,total_price,currency,customer,line_items,shipping_address,financial_status,fulfillment_status,shipping_lines,tags"
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            orders = response.json().get("orders", [])
            logger.info(f"Successfully fetched {len(orders)} orders")
            return orders
            
        except requests.RequestException as e:
            logger.error(f"Error fetching orders from Shopify: {e}")
            return []

    def get_order_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch details for a specific order.
        
        Args:
            order_id (int): The ID of the order to fetch
            
        Returns:
            Optional[Dict[str, Any]]: Order details or None if not found
        """
        logger.info(f"Fetching details for order {order_id}")
        
        url = f"{self.shop_url}/admin/api/{self.api_version}/orders/{order_id}.json"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            order = response.json().get("order", {})
            logger.info(f"Successfully fetched details for order {order_id}")
            return order
            
        except requests.RequestException as e:
            logger.error(f"Error fetching order {order_id} details: {e}")
            return None

    def format_orders_for_knowledge_base(self, orders: List[Dict[str, Any]]) -> str:
        """
        Format orders data for ElevenLabs knowledge base.
        
        Args:
            orders (List[Dict[str, Any]]): List of order dictionaries
            
        Returns:
            str: Formatted content for knowledge base
        """
        if not orders:
            return "No orders available."
        
        formatted_content = "# Taurbull Orders\n\n"
        
        for order in orders:
            # Extract basic order information
            order_number = order.get("order_number", "Unknown")
            order_id = order.get("id", "Unknown")
            created_at = order.get("created_at", "Unknown date")
            total_price = order.get("total_price", "0.00")
            currency = order.get("currency", "EUR")
            financial_status = order.get("financial_status", "Unknown")
            
            # Extract additional fields
            fulfillment_status = order.get("fulfillment_status", "unfulfilled")
            if not fulfillment_status:
                fulfillment_status = "unfulfilled"
            
            # Set delivery status based on fulfillment status
            delivery_status = "Not shipped yet"
            if fulfillment_status == "fulfilled":
                delivery_status = "Shipped"
            elif fulfillment_status == "partial":
                delivery_status = "Partially shipped"
                
            # Get shipping method/delivery method
            shipping_lines = order.get("shipping_lines", [])
            delivery_method = "Standard Shipping"
            if shipping_lines and len(shipping_lines) > 0:
                delivery_method = shipping_lines[0].get("title", "Standard Shipping")
            
            # Extract delivery date from tags
            tags = order.get("tags", "")
            delivery_date = "Not scheduled"
            
            # Look for a date pattern DD-MM-YYYY in tags
            date_pattern = r'(\d{2}-\d{2}-\d{4})'
            date_matches = re.findall(date_pattern, tags)
            if date_matches:
                delivery_date = date_matches[0]
            
            # Extract customer information
            customer = order.get("customer", {})
            customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            customer_email = customer.get("email", "No email provided")
            
            # Extract shipping address
            shipping_address = order.get("shipping_address", {})
            shipping_info = ""
            if shipping_address:
                address1 = shipping_address.get("address1", "")
                address2 = shipping_address.get("address2", "")
                city = shipping_address.get("city", "")
                zip_code = shipping_address.get("zip", "")
                country = shipping_address.get("country", "")
                
                shipping_info = f"""
SHIPPING ADDRESS:
{address1}
{address2}
{zip_code} {city}
{country}
"""
            
            # Extract line items (products)
            line_items = order.get("line_items", [])
            products_info = "PRODUCTS:\n"
            
            for item in line_items:
                title = item.get("title", "Unknown product")
                variant_title = item.get("variant_title", "")
                if variant_title:
                    product_name = f"{title} - {variant_title}"
                else:
                    product_name = title
                    
                quantity = item.get("quantity", 0)
                price = item.get("price", "0.00")
                
                products_info += f"- {quantity}x {product_name} ({price} {currency})\n"
            
            # Format the order entry with a clear separator
            order_entry = f"""
======================================
ORDER NUMBER: {order_number}
ID: {order_id}
DATE: {created_at}
CUSTOMER: {customer_name}
EMAIL: {customer_email}
PAYMENT STATUS: {financial_status}
FULFILLMENT STATUS: {fulfillment_status}
DELIVERY STATUS: {delivery_status}
DELIVERY METHOD: {delivery_method}
EXPECTED DELIVERY: {delivery_date}
TOTAL: {total_price} {currency}

{shipping_info}

{products_info}
======================================

"""
            formatted_content += order_entry
        
        logger.info(f"Formatted {len(orders)} orders with total {len(formatted_content.split())} words")
        return formatted_content 