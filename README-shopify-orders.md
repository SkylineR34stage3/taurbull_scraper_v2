# Shopify Orders Integration for Taurbull Scraper

This feature adds the ability to retrieve order data from the Shopify API and upload it to the ElevenLabs knowledge base, making it available to your conversational AI agent.

## Setup

1. Add your Shopify API credentials to the `.env` file:

```
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_ACCESS_TOKEN=your_access_token
SHOPIFY_SHOP_NAME=your-shop.myshopify.com
```

You can obtain these credentials by:
- Creating a private app in your Shopify admin panel (Settings → Apps and sales channels → Develop apps)
- Setting permissions for orders, customers, and products (read access is sufficient)
- Copying the API key, secret, and access token to your `.env` file

## Usage

### Command Line Options

To fetch orders and update the knowledge base:

```
python -m src.main --once --orders
```

Additional parameters:
- `--force`: Force update the knowledge base even if content hasn't changed
- `--orders-days 30`: Fetch orders from the last 30 days (default)
- `--orders-limit 100`: Limit to 100 orders (default)

Example with all parameters:

```
python -m src.main --once --orders --force --orders-days 60 --orders-limit 200
```

### Running the Test Script

To test the Shopify orders integration without needing valid API credentials:

```
python -m src.test_shopify_format
```

This will:
1. Use mock order data
2. Format them for the knowledge base and save to `test_output/mock_orders_formatted.txt`
3. Display a sample of the formatting in the terminal

To test with real Shopify data:

```
python -m src.test_shopify_orders
```

This requires valid API credentials and will:
1. Fetch orders from your Shopify store
2. Save them to `test_output/shopify_orders_raw.json`
3. Format them for the knowledge base and save to `test_output/shopify_orders_formatted.txt`
4. Attempt to update the knowledge base with the formatted content

## Order Format

The system formats each order with the following structure:

```
======================================
ORDER NUMBER: 1025
ID: 6683975942490
DATE: 2025-04-22T00:18:09+02:00
CUSTOMER: Simon Fischer
EMAIL: simonchristianfischer@gmail.com
PAYMENT STATUS: paid
FULFILLMENT STATUS: unfulfilled
DELIVERY STATUS: Not shipped yet
DELIVERY METHOD: DPD Food Express
EXPECTED DELIVERY: 30-04-2025
TOTAL: 80.77 EUR

SHIPPING ADDRESS:
Bleichstrasse 13
None
65183 Wiesbaden
Germany

PRODUCTS:
- 1x Brisket - 1.900g (47.50 EUR)
- 1x Burger Patties - 2x200g (7.60 EUR)
- 1x Beef Ribs - 1.800g (45.00 EUR)
- 1x Burger Patties - 2x200g (7.60 EUR)
======================================
```

The system automatically:
- Extracts delivery dates from order tags (format: DD-MM-YYYY)
- Sets delivery status based on fulfillment status (Not shipped yet, Partially shipped, Shipped)
- Adds clear separators between orders for improved readability

## Implementation Details

- The `ShopifyClient` class in `src/shopify_api.py` handles the Shopify API interactions
- Orders are fetched using the Shopify REST API
- The system formats orders with customer information, products, shipping details, and delivery status
- The formatted content is uploaded to ElevenLabs and assigned to your agent

## Troubleshooting

If you encounter issues:

1. Check that your API credentials are correct
2. Ensure your Shopify app has the correct permissions
3. Check the logs for detailed error messages
4. Try running with `DEBUG=True` in your `.env` file for more verbose logging 