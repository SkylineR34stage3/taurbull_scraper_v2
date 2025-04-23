"""
Test script for the Shopify orders formatting.
Uses mock data to test the formatting without needing API credentials.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the ShopifyClient
try:
    from src.shopify_api import ShopifyClient
except ImportError:
    from shopify_api import ShopifyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up output directory
OUTPUT_DIR = Path("test_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Mock Shopify orders data
MOCK_ORDERS = [
    {
        "id": 6685435953498,
        "order_number": 1026,
        "created_at": "2025-04-22T23:14:49+02:00",
        "total_price": "49.99",
        "currency": "EUR",
        "customer": {
            "first_name": "Matthias",
            "last_name": "Proksch",
            "email": "heimlinch32@aol.com"
        },
        "financial_status": "paid",
        "fulfillment_status": None,
        "shipping_lines": [
            {
                "title": "DPD Food Express"
            }
        ],
        "tags": "",
        "shipping_address": {
            "address1": "Sperlingsberg 12",
            "address2": None,
            "city": "Querfurt/OT Oberschmon",
            "zip": "06268",
            "country": "Germany"
        },
        "line_items": [
            {
                "title": "Beef Ribs",
                "variant_title": "1.800g",
                "quantity": 1,
                "price": "45.00"
            }
        ]
    },
    {
        "id": 6683975942490,
        "order_number": 1025,
        "created_at": "2025-04-22T00:18:09+02:00",
        "total_price": "80.77",
        "currency": "EUR",
        "customer": {
            "first_name": "Simon",
            "last_name": "Fischer",
            "email": "simonchristianfischer@gmail.com"
        },
        "financial_status": "paid",
        "fulfillment_status": None,
        "shipping_lines": [
            {
                "title": "DPD Food Express"
            }
        ],
        "tags": "30-04-2025, qikify-boosterkit-first-sell",
        "shipping_address": {
            "address1": "Bleichstrasse 13",
            "address2": None,
            "city": "Wiesbaden",
            "zip": "65183",
            "country": "Germany"
        },
        "line_items": [
            {
                "title": "Brisket",
                "variant_title": "1.900g",
                "quantity": 1,
                "price": "47.50"
            },
            {
                "title": "Burger Patties",
                "variant_title": "2x200g",
                "quantity": 1,
                "price": "7.60"
            },
            {
                "title": "Beef Ribs",
                "variant_title": "1.800g",
                "quantity": 1,
                "price": "45.00"
            },
            {
                "title": "Burger Patties",
                "variant_title": "2x200g",
                "quantity": 1,
                "price": "7.60"
            }
        ]
    },
    {
        "id": 6683253899610,
        "order_number": 1024,
        "created_at": "2025-04-21T15:24:28+02:00",
        "total_price": "31.59",
        "currency": "EUR",
        "customer": {
            "first_name": "Hauser",
            "last_name": "Ramona",
            "email": "ramonahauser119@gmail.com"
        },
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "shipping_lines": [
            {
                "title": "DPD Food Express"
            }
        ],
        "tags": "23-04-2025",
        "shipping_address": {
            "address1": "Buchenweg 6",
            "address2": None,
            "city": "Bodenwöhr",
            "zip": "92439",
            "country": "Germany"
        },
        "line_items": [
            {
                "title": "Picanha",
                "variant_title": "350g",
                "quantity": 2,
                "price": "13.30"
            }
        ]
    }
]

def test_format_orders():
    """
    Test the order formatting with mock data.
    """
    logger.info("Testing order formatting with mock data")
    
    # Initialize ShopifyClient
    client = ShopifyClient()
    
    # Format orders
    formatted_orders = client.format_orders_for_knowledge_base(MOCK_ORDERS)
    
    # Save the formatted orders to a file
    output_file = OUTPUT_DIR / "mock_orders_formatted.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_orders)
    
    logger.info(f"Saved formatted mock orders to {output_file}")
    
    # Also save the mock data as JSON for reference
    json_file = OUTPUT_DIR / "mock_orders_raw.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(MOCK_ORDERS, f, indent=2)
    
    logger.info(f"Saved raw mock orders to {json_file}")
    
    return formatted_orders

if __name__ == "__main__":
    formatted = test_format_orders()
    print("\nFormatted Orders Sample:\n")
    print(formatted[:800] + "...")  # Print the beginning of the formatted text 