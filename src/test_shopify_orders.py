"""
Test script for the Shopify orders feature.
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
    from src.elevenlabs_api import ElevenLabsClient
except ImportError:
    from shopify_api import ShopifyClient
    from elevenlabs_api import ElevenLabsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up output directory
OUTPUT_DIR = Path("test_output")

# ElevenLabs agent ID to assign knowledge base documents to
AGENT_ID = "2AmUavf0llkEhjBRMstL"  # Use the same agent ID as in main.py


def setup_output_dir():
    """
    Set up the output directory for test results.
    """
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        logger.info(f"Created output directory at {OUTPUT_DIR}")
    else:
        logger.info(f"Using existing output directory at {OUTPUT_DIR}")


def test_fetch_orders(limit=10, days=30):
    """
    Test fetching orders from Shopify.
    
    Args:
        limit (int): Maximum number of orders to fetch
        days (int): Fetch orders from the last n days
    """
    logger.info(f"Testing Shopify orders API with limit={limit}, days={days}")
    
    # Initialize the ShopifyClient
    client = ShopifyClient()
    
    # Fetch orders
    orders = client.get_orders(limit=limit, since_days=days)
    
    # Save the raw orders data
    orders_file = OUTPUT_DIR / "shopify_orders_raw.json"
    with open(orders_file, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2)
    logger.info(f"Saved raw orders data to {orders_file}")
    
    # Format orders for knowledge base
    formatted_orders = client.format_orders_for_knowledge_base(orders)
    
    # Save the formatted orders
    formatted_file = OUTPUT_DIR / "shopify_orders_formatted.txt"
    with open(formatted_file, 'w', encoding='utf-8') as f:
        f.write(formatted_orders)
    logger.info(f"Saved formatted orders to {formatted_file}")
    
    return orders, formatted_orders


def test_update_knowledge_base(formatted_orders):
    """
    Test updating the ElevenLabs knowledge base with orders.
    
    Args:
        formatted_orders (str): Formatted orders content
    """
    logger.info("Testing update of ElevenLabs knowledge base with orders")
    
    # Initialize the ElevenLabsClient
    client = ElevenLabsClient()
    
    # Update the knowledge base
    success = client.update_knowledge_base(
        "orders", 
        formatted_orders, 
        force_update=True,
        agent_id=AGENT_ID
    )
    
    if success:
        logger.info(f"Successfully updated 'orders' in knowledge base and assigned to agent {AGENT_ID}")
    else:
        logger.error("Failed to update knowledge base with orders")
    
    return success


def main():
    """
    Main entry point for the test script.
    """
    logger.info("Starting Shopify orders test script")
    
    # Set up the output directory
    setup_output_dir()
    
    try:
        # Test fetching orders
        orders, formatted_orders = test_fetch_orders(limit=10, days=30)
        
        if orders:
            logger.info(f"Successfully fetched {len(orders)} orders")
            
            # Test updating knowledge base
            if formatted_orders:
                success = test_update_knowledge_base(formatted_orders)
                if success:
                    logger.info("All tests completed successfully")
                else:
                    logger.error("Knowledge base update test failed")
            else:
                logger.error("No formatted orders to update knowledge base")
        else:
            logger.error("Failed to fetch any orders")
    
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)


if __name__ == "__main__":
    main() 