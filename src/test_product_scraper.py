"""
Test script for the Taurbull product scraper.

This script tests the functionality of the product scrapers by running 
them against the Taurbull website and saving the results to files.
"""
import json
import logging
import os
import sys
from pathlib import Path

from src.product_scraper import ProductCatalogScraper, ProductDetailScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path("test_output")

def setup_output_dir():
    """Create the output directory if it doesn't exist."""
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

def test_product_catalog_scraper():
    """Test the product catalog scraper."""
    logger.info("Testing product catalog scraper...")
    
    # Initialize the scraper
    catalog_scraper = ProductCatalogScraper()
    
    # Scrape the catalog (limit to 5 products for testing)
    products = catalog_scraper.scrape_catalog(max_pages=1)
    products = products[:min(5, len(products))]
    
    # Log results
    logger.info(f"Found {len(products)} products in the catalog")
    
    # Save results to files
    catalog_json_path = OUTPUT_DIR / "product_catalog.json"
    with open(catalog_json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved catalog JSON to {catalog_json_path}")
    
    # Save a voice-assistant-friendly text format
    catalog_txt_path = OUTPUT_DIR / "product_catalog.txt"
    with open(catalog_txt_path, "w", encoding="utf-8") as f:
        f.write("TAURBULL PRODUCT CATALOG\n")
        f.write("======================\n\n")
        for i, product in enumerate(products, 1):
            f.write(f"Product {i}: {product.get('name', 'N/A')}\n")
            if product.get('full_name') and product.get('full_name') != product.get('name'):
                f.write(f"Full name: {product.get('full_name')}\n")
            f.write(f"Price: {product.get('price', 'N/A')}\n")
            if product.get('price_per_kilo'):
                f.write(f"Price per kilo: {product.get('price_per_kilo')}\n")
            if product.get('price_per_unit'):
                f.write(f"Price per unit: {product.get('price_per_unit')}\n")
            if product.get('special_offer'):
                f.write(f"Special offer: {product.get('special_offer')}\n")
            if product.get('description'):
                f.write(f"Description: {product.get('description')}\n")
            f.write("\n")
    logger.info(f"Saved catalog text to {catalog_txt_path}")
    
    # Print sample products to console
    logger.info("Sample product information for voice assistant:")
    for i, product in enumerate(products, 1):
        print(f"\nProduct {i}: {product.get('name', 'N/A')}")
        print(f"Price: {product.get('price', 'N/A')}")
        if product.get('price_per_kilo'):
            print(f"Price per kilo: {product.get('price_per_kilo')}")
        if product.get('special_offer'):
            print(f"Special offer: {product.get('special_offer')}")
        
    return products

def test_product_detail_scraper():
    """Test the product detail scraper with a single product."""
    logger.info("Testing product detail scraper...")
    
    # Sample product URL (verified from catalog)
    product_url = "https://taurbull.com/products/ribeye-steak-black-angus-dry-aged"
    
    # Initialize the scraper
    detail_scraper = ProductDetailScraper()
    
    # Scrape the product details
    product_details = detail_scraper.scrape_product_details(product_url)
    
    # Log results
    logger.info(f"Scraped details for product: {product_details.get('name', 'Unknown')}")
    
    # Save results to file
    detail_json_path = OUTPUT_DIR / "product_detail_sample.json"
    with open(detail_json_path, "w", encoding="utf-8") as f:
        json.dump(product_details, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved product details to {detail_json_path}")
    
    # Save a voice-assistant-friendly version
    detail_txt_path = OUTPUT_DIR / "product_detail_sample.txt"
    with open(detail_txt_path, "w", encoding="utf-8") as f:
        f.write(f"PRODUCT: {product_details.get('name', 'Unknown')}\n")
        if product_details.get('full_name') and product_details.get('full_name') != product_details.get('name'):
            f.write(f"Full name: {product_details.get('full_name')}\n")
        f.write("=================================================\n\n")
        if product_details.get('price'):
            f.write(f"Price: {product_details.get('price')}\n")
        if product_details.get('price_per_kilo'):
            f.write(f"Price per kilo: {product_details.get('price_per_kilo')}\n")
        if product_details.get('price_per_unit'):
            f.write(f"Price per unit: {product_details.get('price_per_unit')}\n")
        if product_details.get('availability'):
            f.write(f"Availability: {product_details.get('availability')}\n")
        if product_details.get('categories'):
            f.write(f"Categories: {', '.join(product_details.get('categories'))}\n")
        if product_details.get('description'):
            f.write(f"\nDescription:\n{product_details.get('description')}\n")
        if product_details.get('features'):
            f.write("\nKey Features:\n")
            for feature in product_details.get('features'):
                f.write(f"- {feature}\n")
        if product_details.get('cooking_instructions'):
            f.write(f"\nCooking Instructions:\n{product_details.get('cooking_instructions')}\n")
        if product_details.get('ingredients'):
            f.write(f"\nIngredients:\n{product_details.get('ingredients')}\n")
    logger.info(f"Saved product details text to {detail_txt_path}")
    
    # Print product details to console in voice-assistant-friendly format
    logger.info("Product information for voice assistant:")
    print(f"\nProduct: {product_details.get('name', 'Unknown')}")
    print(f"Price: {product_details.get('price', 'Not specified')}")
    if product_details.get('price_per_kilo'):
        print(f"Price per kilo: {product_details.get('price_per_kilo')}")
    if product_details.get('description'):
        print(f"\nDescription: {product_details.get('description')}")
    
    return product_details

def test_full_product_details(max_products=5):
    """
    Test scraping full details for multiple products.
    
    Args:
        max_products: Maximum number of products to scrape details for
    """
    logger.info(f"Testing full product details scraping (max {max_products} products)...")
    
    # First, get the catalog
    catalog_scraper = ProductCatalogScraper()
    products = catalog_scraper.scrape_catalog(max_pages=1)
    
    if not products:
        logger.error("No products found in catalog")
        return []
    
    # Initialize the detail scraper
    detail_scraper = ProductDetailScraper()
    
    # Limit the number of products to scrape
    products_to_scrape = products[:min(max_products, len(products))]
    logger.info(f"Will scrape details for {len(products_to_scrape)} products")
    
    # Scrape details for each product
    all_product_details = []
    for i, product in enumerate(products_to_scrape, 1):
        url = product.get("url")
        if not url:
            logger.warning(f"Product {i} has no URL, skipping")
            continue
        
        logger.info(f"Scraping product {i}/{len(products_to_scrape)}: {product.get('name', 'Unknown')}")
        try:
            product_details = detail_scraper.scrape_product_details(url)
            
            # Create a voice-assistant-friendly version by removing the URL
            if "url" in product_details:
                del product_details["url"]
            
            # Transfer any data from catalog that might be missing in detail page
            if "special_offer" not in product_details and "special_offer" in product:
                product_details["special_offer"] = product["special_offer"]
                
            all_product_details.append(product_details)
        except Exception as e:
            logger.error(f"Error scraping details for product {i}: {e}")
    
    # Save all product details to a file
    all_details_json_path = OUTPUT_DIR / "all_product_details.json"
    with open(all_details_json_path, "w", encoding="utf-8") as f:
        json.dump(all_product_details, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved all product details to {all_details_json_path}")
    
    # Save a more readable text version for voice assistant
    all_details_txt_path = OUTPUT_DIR / "all_product_details.txt"
    with open(all_details_txt_path, "w", encoding="utf-8") as f:
        f.write("TAURBULL PRODUCT CATALOG - DETAILED\n")
        f.write("===================================\n\n")
        for i, details in enumerate(all_product_details, 1):
            f.write(f"PRODUCT {i}: {details.get('name', 'N/A')}\n")
            if details.get('full_name') and details.get('full_name') != details.get('name'):
                f.write(f"Full name: {details.get('full_name')}\n")
            f.write("-" * 50 + "\n")
            
            # Basic Product Information
            if details.get('price'):
                f.write(f"Price: {details.get('price')}\n")
            if details.get('price_per_kilo'):
                f.write(f"Price per kilo: {details.get('price_per_kilo')}\n")
            if details.get('price_per_unit'):
                f.write(f"Price per unit: {details.get('price_per_unit')}\n")
            if details.get('availability'):
                f.write(f"Availability: {details.get('availability')}\n")
            if details.get('special_offer'):
                f.write(f"Special offer: {details.get('special_offer')}\n")
            
            # Product Details
            if details.get('description'):
                f.write(f"\nDescription: {details.get('description')}\n")
            
            if details.get('features'):
                f.write("\nKey Features:\n")
                for feature in details.get('features'):
                    f.write(f"- {feature}\n")
            
            if details.get('cooking_instructions'):
                f.write(f"\nCooking Instructions: {details.get('cooking_instructions')}\n")
            
            if details.get('ingredients'):
                f.write(f"\nIngredients: {details.get('ingredients')}\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
    
    logger.info(f"Saved all product details text to {all_details_txt_path}")
    
    # Print sample of the data
    if all_product_details:
        logger.info("Sample product data for voice assistant:")
        for i, details in enumerate(all_product_details[:1], 1):
            print(f"\nProduct: {details.get('name', 'Unknown')}")
            if details.get('full_name') and details.get('full_name') != details.get('name'):
                print(f"Full name: {details.get('full_name')}")
            print(f"Price: {details.get('price', 'Not specified')}")
            if details.get('price_per_kilo'):
                print(f"Price per kilo: {details.get('price_per_kilo')}")
            if details.get('special_offer'):
                print(f"Special offer: {details.get('special_offer')}")
            
            if details.get('description'):
                description = details.get('description', '')
                print(f"\nDescription: {description[:150]}..." if len(description) > 150 else f"\nDescription: {description}")
    
    return all_product_details

def main():
    """Run the test functions."""
    logger.info("Starting product scraper tests")
    
    # Create output directory
    setup_output_dir()
    
    try:
        # Test catalog scraper
        catalog_products = test_product_catalog_scraper()
        logger.info(f"Successfully tested catalog scraper, found {len(catalog_products)} products")
        
        # Test detail scraper with a single product
        product_details = test_product_detail_scraper()
        logger.info(f"Successfully tested detail scraper for product: {product_details.get('name', 'Unknown')}")
        
        # Test full product details
        all_product_details = test_full_product_details(max_products=5)
        logger.info(f"Successfully tested full product details for {len(all_product_details)} products")
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 