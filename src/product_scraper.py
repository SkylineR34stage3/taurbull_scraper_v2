"""
Product scraper module for Taurbull website.

This module provides classes to scrape product catalog and product details
from the Taurbull website.
"""
import logging
import re
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class ProductCatalogScraper:
    """
    Scraper for the Taurbull product catalog.
    """
    
    BASE_URL = "https://taurbull.com"
    CATALOG_URL = "https://taurbull.com/collections/all"
    
    def __init__(self):
        """
        Initialize the product catalog scraper.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
    
    def scrape_catalog(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape the product catalog.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product dictionaries with basic information
        """
        products = []
        current_page = 1
        current_url = self.CATALOG_URL
        
        while current_page <= max_pages:
            logger.info(f"Scraping catalog page {current_page}: {current_url}")
            
            try:
                # Fetch the page
                response = self.session.get(current_url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find product elements - Updated selector
                product_elements = soup.select("loess-product-card.card")
                
                if not product_elements:
                    logger.warning(f"No products found on page {current_page}")
                    break
                
                # Extract product information
                for product_element in product_elements:
                    try:
                        product = self._extract_product_info(product_element)
                        if product:
                            # Fetch price for each product directly if needed
                            if "url" in product and (not product.get("price") or product["price"] == "Price information available upon request"):
                                try:
                                    detail_scraper = ProductDetailScraper()
                                    details = detail_scraper.scrape_product_details(product["url"])
                                    if "price" in details:
                                        product["price"] = details["price"]
                                    if "description" in details:
                                        product["description"] = details["description"]
                                except Exception as e:
                                    logger.error(f"Error fetching details for {product.get('name')}: {e}")
                            
                            # Clean up price format
                            if "price" in product:
                                product["price"] = self._clean_price(product["price"])
                                
                            products.append(product)
                    except Exception as e:
                        logger.error(f"Error extracting product info: {e}")
                
                # Check if there's a next page
                next_page_link = soup.select_one("a.pagination__item--next")
                if not next_page_link:
                    logger.info("No more pages available")
                    break
                
                # Get the next page URL
                next_page_url = next_page_link.get("href")
                if not next_page_url:
                    logger.info("No next page URL found")
                    break
                
                current_url = urljoin(self.BASE_URL, next_page_url)
                current_page += 1
                
                # Wait a moment to avoid overloading the server
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping catalog page {current_page}: {e}")
                break
        
        logger.info(f"Scraped {len(products)} products from {current_page} pages")
        return products
    
    def _clean_price(self, price_text: str) -> str:
        """Clean and format price text"""
        if not price_text:
            return "Price not available"
            
        # Remove extra whitespace
        price_text = re.sub(r'\s+', ' ', price_text).strip()
        
        # Try to extract the most meaningful price information
        if "Von " in price_text:
            # Extract the price after "Von "
            match = re.search(r'Von (€[\d,.]+)', price_text)
            if match:
                return match.group(1)
        
        # Look for a price pattern
        match = re.search(r'(€[\d,.]+)', price_text)
        if match:
            return match.group(1)
            
        return price_text
    
    def _extract_product_info(self, product_element) -> Optional[Dict[str, Any]]:
        """
        Extract product information from a product element.
        
        Args:
            product_element: BeautifulSoup element representing a product
            
        Returns:
            Dictionary with product information or None if extraction failed
        """
        try:
            # Extract URL (href attribute from modal-product's href attribute)
            modal_element = product_element.select_one("loess-modal-product")
            if not modal_element:
                return None
                
            relative_url = modal_element.get("href")
            if not relative_url:
                return None
            url = urljoin(self.BASE_URL, relative_url)
            url = url.replace("?view=quick-view", "")
            
            # Extract name from the URL (we'll clean it up later)
            full_name = relative_url.split("/")[-1].replace("?view=quick-view", "").replace("-", " ").title()
            
            # Extract base name
            detail_scraper = ProductDetailScraper()
            base_name = detail_scraper._extract_base_name(full_name)
            
            # Try to extract price from the card directly
            price = "Price information available upon request"
            price_element = product_element.select_one(".price")
            if price_element:
                price = price_element.text.strip()
            
            # Create product dictionary
            product = {
                "name": base_name,
                "full_name": full_name,
                "price": price,
                "url": url  # Keep URL for fetching details later
            }
            
            # Extract any badges (sale, new, etc)
            badge_element = product_element.select_one(".card-badges__badge")
            if badge_element:
                product["special_offer"] = badge_element.text.strip()
                
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
            return None


class ProductDetailScraper:
    """
    Scraper for Taurbull product details.
    """
    
    def __init__(self):
        """
        Initialize the product detail scraper.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
    
    def scrape_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape detailed information for a specific product.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with detailed product information
        """
        logger.info(f"Scraping product details: {product_url}")
        
        try:
            # Fetch the page
            response = self.session.get(product_url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract product details
            product_details = self._extract_product_details(soup, product_url)
            
            # Remove URL as it's not useful for voice assistant
            if "url" in product_details:
                del product_details["url"]
            
            return product_details
            
        except Exception as e:
            logger.error(f"Error scraping product details: {e}")
            return {"error": str(e)}
    
    def _clean_price(self, price_text: str) -> str:
        """Clean and format price text"""
        if not price_text:
            return "Price not available"
            
        # Remove extra whitespace
        price_text = re.sub(r'\s+', ' ', price_text).strip()
        
        # Try to extract the most meaningful price information
        if "Von " in price_text:
            # Extract the price after "Von "
            match = re.search(r'Von (€[\d,.]+)', price_text)
            if match:
                return match.group(1)
        
        # Look for a price pattern
        match = re.search(r'(€[\d,.]+)', price_text)
        if match:
            return match.group(1)
            
        return price_text
    
    def _extract_product_details(self, soup: BeautifulSoup, product_url: str) -> Dict[str, Any]:
        """
        Extract detailed product information from the product page.
        
        Args:
            soup: BeautifulSoup object of the product page
            product_url: URL of the product page
            
        Returns:
            Dictionary with detailed product information
        """
        # Initialize product details
        product_details = {}
        
        # Extract name
        # Try different selectors for the product title
        for selector in ["h1.product__title", "h1.product-single__title", "h1"]:
            name_element = soup.select_one(selector)
            if name_element:
                full_name = name_element.text.strip()
                # Extract the base name (e.g., "Ribeye Steak" from "Ribeye Steak Black Angus Dry Aged")
                base_name = self._extract_base_name(full_name)
                product_details["name"] = base_name
                product_details["full_name"] = full_name
                break
        
        # If no name was found, extract from URL
        if "name" not in product_details and product_url:
            full_name = product_url.split("/")[-1].replace("-", " ").title()
            base_name = self._extract_base_name(full_name)
            product_details["name"] = base_name
            product_details["full_name"] = full_name
        
        # Extract price from page metadata
        meta_price = self._extract_price_from_metadata(soup)
        if meta_price:
            product_details["price"] = meta_price
        else:
            # Extract price from visible elements
            price_element = soup.select_one(".product__price")
            if price_element:
                product_details["price"] = self._clean_price(price_element.text.strip())
        
        # Extract price per unit
        price_unit_element = soup.select_one(".product__unit-price")
        if price_unit_element:
            price_per_unit = price_unit_element.text.strip()
            # Clean up the price per unit text
            price_per_unit = re.sub(r'\s+', ' ', price_per_unit).strip()
            # Try to extract the price per kilo value
            match = re.search(r'€(\d+[\.,]\d+)\s*/\s*pro kg', price_per_unit)
            if match:
                product_details["price_per_kilo"] = f"€{match.group(1)}/kg"
            else:
                product_details["price_per_unit"] = price_per_unit
        
        # Try to find price per kilo from unit price information
        unit_price_element = soup.select_one("[data-unit-price]")
        if unit_price_element:
            unit_price = unit_price_element.get("data-unit-price")
            if unit_price and "price_per_kilo" not in product_details:
                try:
                    unit_price_float = float(unit_price) / 100  # Convert cents to euros
                    product_details["price_per_kilo"] = f"€{unit_price_float:.2f}/kg"
                except:
                    pass
        
        # Extract special offers/badges using multiple selectors
        for selector in [".product-badge", ".badge", ".sale-tag", ".card-badges__badge", ".discount-badge"]:
            special_offer_element = soup.select_one(selector)
            if special_offer_element:
                special_offer = special_offer_element.text.strip()
                if special_offer:
                    product_details["special_offer"] = special_offer
                    break
        
        # Look for sale price indicators
        compare_price_element = soup.select_one(".product__price--compare, .price--compare")
        if compare_price_element:
            compare_price = self._clean_price(compare_price_element.text.strip())
            if compare_price and compare_price != product_details.get("price", ""):
                if "special_offer" not in product_details:
                    current_price = product_details.get("price", "")
                    if current_price:
                        product_details["special_offer"] = f"Sale: Was {compare_price} now {current_price}"
        
        # Extract description from meta tags first
        meta_description = soup.select_one('meta[name="description"]')
        if meta_description:
            description = meta_description.get("content", "")
            if description:
                # Clean up the description (remove extra whitespace and HTML entities)
                description = re.sub(r'\s+', ' ', description).strip()
                description = description.replace("&amp;", "&")
                # Limit description length for voice assistant
                if len(description) > 500:
                    description = description[:497] + "..."
                product_details["description"] = description
        
        # If no description in meta tags, try other elements
        if "description" not in product_details:
            # Try different selectors for product description
            for selector in [".product__description", ".product-single__description", ".rte"]:
                description_element = soup.select_one(selector)
                if description_element:
                    description = description_element.text.strip()
                    # Clean up the description
                    description = re.sub(r'\s+', ' ', description).strip()
                    if len(description) > 500:
                        description = description[:497] + "..."
                    if description:
                        product_details["description"] = description
                        break
        
        # Extract cooking instructions and other content from collapsible sections
        collapsible_sections = soup.select(".collapsible-section")
        for section in collapsible_sections:
            title_element = section.select_one(".collapsible-title, .collapsible-header")
            content_element = section.select_one(".collapsible-content, .collapsible-body")
            
            if title_element and content_element:
                title = title_element.text.strip().lower()
                content = content_element.text.strip()
                content = re.sub(r'\s+', ' ', content).strip()
                
                if "zubereitung" in title or "cooking" in title:
                    product_details["cooking_instructions"] = content
                elif "zutaten" in title or "ingredients" in title:
                    product_details["ingredients"] = content
                elif "feature" in title or "merkmal" in title:
                    product_details["features"] = [li.text.strip() for li in content_element.select("li")]
        
        # Extract tab contents which may contain additional information
        tabs_content = soup.select(".tab-content, .product-info-tab")
        for tab in tabs_content:
            tab_title_element = tab.select_one(".tab-title, .tab-header")
            tab_content_element = tab.select_one(".tab-content__inner, .tab-body")
            
            if tab_title_element and tab_content_element:
                tab_title = tab_title_element.text.strip().lower()
                tab_content = tab_content_element.text.strip()
                
                # Summarize tab content for voice assistant
                tab_content = re.sub(r'\s+', ' ', tab_content).strip()
                if len(tab_content) > 300:
                    tab_content = tab_content[:297] + "..."
                
                if "ingredient" in tab_title or "zutaten" in tab_title:
                    product_details["ingredients"] = tab_content
                elif "cooking" in tab_title or "zubereitung" in tab_title:
                    product_details["cooking_instructions"] = tab_content
                elif "feature" in tab_title or "merkmal" in tab_title:
                    features = [li.text.strip() for li in tab_content_element.select("li")]
                    # Limit to top features for voice assistant
                    if len(features) > 5:
                        features = features[:5]
                    product_details["features"] = features
        
        # Extract product availability
        availability_element = soup.select_one(".product__availability, .product-availability")
        if availability_element:
            product_details["availability"] = availability_element.text.strip()
        
        # Extract product categories/tags
        categories = []
        category_elements = soup.select(".product__tags .tag, .product-tag")
        if category_elements:
            for category in category_elements:
                categories.append(category.text.strip())
            
            if categories:
                product_details["categories"] = categories
        
        return product_details
    
    def _extract_base_name(self, full_name: str) -> str:
        """
        Extract the base name of a product from the full name.
        
        For example:
        "Ribeye Steak Black Angus Dry Aged" -> "Ribeye Steak"
        "Dry Aged Burger Patties Black Angus Freiland" -> "Burger Patties"
        
        Args:
            full_name: Full product name
            
        Returns:
            Base product name
        """
        # Common qualifiers to remove
        qualifiers = [
            "black angus", "dry aged", "freiland", "premium", "mutterkuhaufzucht", 
            "farm direkt", "bbq", "beef", "steak", "premium"
        ]
        
        # Special cases for product types
        product_types = {
            "burger patties": "Burger Patties",
            "ribeye": "Ribeye Steak",
            "rump": "Rump Steak",
            "flank": "Flank Steak",
            "tomahawk": "Tomahawk Steak",
            "t-bone": "T-Bone Steak",
            "tbone": "T-Bone Steak",
            "filet": "Filet Steak",
            "sirloin": "Sirloin Steak",
            "short ribs": "Short Ribs",
            "tafelspitz": "Tafelspitz",
            "picanha": "Picanha",
            "porterhouse": "Porterhouse Steak",
            "flat iron": "Flat Iron Steak",
            "osso buco": "Osso Buco",
            "brisket": "Brisket",
            "rinderbrust": "Rinderbrust",
            "hackfleisch": "Hackfleisch",
            "smashburger": "Smashburger",
            "chuck eye": "Chuck Eye Steak",
            "chuckeye": "Chuck Eye Steak"
        }
        
        # Convert to lowercase for comparison
        name_lower = full_name.lower()
        
        # First try to match product types
        for product_type, name in product_types.items():
            if product_type in name_lower:
                return name
        
        # If no match, just return the first 2-3 words as the base name
        words = full_name.split()
        if len(words) <= 3:
            return full_name
        else:
            # Remove common qualifiers
            clean_words = []
            for word in words:
                if not any(qualifier in word.lower() for qualifier in qualifiers):
                    clean_words.append(word)
            
            # Return first 2-3 clean words
            if clean_words:
                return " ".join(clean_words[:min(3, len(clean_words))])
            else:
                return " ".join(words[:2])  # Fallback to first 2 words
    
    def _extract_price_from_metadata(self, soup) -> Optional[str]:
        """
        Extract price information from the page's metadata or JSON-LD.
        
        Args:
            soup: BeautifulSoup object of the product page
            
        Returns:
            Formatted price string or None if not found
        """
        # Try to find price in meta tags
        meta_price = soup.select_one('meta[property="og:price:amount"]')
        if meta_price:
            price_amount = meta_price.get("content", "")
            if price_amount:
                return f"€{price_amount}"
        
        # Try to find price in JSON-LD
        script_tags = soup.select("script[type='application/json']")
        for script in script_tags:
            try:
                script_content = script.string
                if script_content and '"price":' in script_content:
                    json_data = json.loads(script_content)
                    if isinstance(json_data, dict) and "price" in json_data:
                        price_cents = json_data.get("price")
                        if price_cents:
                            price_euros = float(price_cents) / 100
                            return f"€{price_euros:.2f}"
            except:
                continue
        
        # Try to find price in JavaScript variables
        script_tags = soup.select("script")
        for script in script_tags:
            try:
                script_content = script.string
                if script_content and '"price" :' in script_content:
                    match = re.search(r'"price"\s*:\s*(\d+[\.,]\d+)', script_content)
                    if match:
                        return f"€{match.group(1)}"
            except:
                continue
        
        return None 