"""
Web scraper module for Taurbull website.
"""
import json
import logging
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Any

# Import using try/except for flexibility
try:
    from src.config import DEBUG
    from src.product_scraper import ProductDetailScraper
except ImportError:
    from config import DEBUG
    from product_scraper import ProductDetailScraper

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaurbullScraper:
    """Scraper for Taurbull website content."""

    @staticmethod
    def get_page_content(url):
        """
        Fetch HTML content from a URL.
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            str: HTML content of the page
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            logger.debug(f"Fetching content from {url}")
            response = requests.get(url, headers={
                'User-Agent': 'TaurbullContentScraper/1.0'
            })
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    def extract_faq_content(self, html):
        """
        Extract FAQ content from HTML using JSON-LD structured data.
        
        Args:
            html (str): HTML content of the FAQ page
            
        Returns:
            str: Formatted FAQ content as Q&A text
        """
        logger.debug("Extracting FAQ content from HTML")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find JSON-LD script tags
        script_tags = soup.find_all('script', type='application/ld+json')
        
        faq_content = ""
        faq_items_processed = 0
        
        for script in script_tags:
            try:
                data = json.loads(script.string)
                
                # Check for FAQPage type or FAQ items in mainEntity
                if '@type' in data:
                    if data['@type'] == 'FAQPage' and 'mainEntity' in data:
                        # Process FAQPage format
                        for item in data['mainEntity']:
                            if item.get('@type') == 'Question':
                                question = item.get('name', '')
                                answer_raw = item.get('acceptedAnswer', {}).get('text', '')
                                
                                # Clean HTML from answer
                                answer_soup = BeautifulSoup(answer_raw, 'html.parser')
                                clean_answer = answer_soup.get_text().strip()
                                
                                faq_content += f"Q: {question}\nA: {clean_answer}\n\n"
                                faq_items_processed += 1
                    
                    # Check for individual Question format
                    elif data['@type'] == 'Question':
                        question = data.get('name', '')
                        answer_raw = data.get('acceptedAnswer', {}).get('text', '')
                        
                        # Clean HTML from answer
                        answer_soup = BeautifulSoup(answer_raw, 'html.parser')
                        clean_answer = answer_soup.get_text().strip()
                        
                        faq_content += f"Q: {question}\nA: {clean_answer}\n\n"
                        faq_items_processed += 1
            
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Error parsing JSON-LD: {e}")
                continue
        
        logger.info(f"Extracted {faq_items_processed} FAQ items")
        return faq_content.strip()

    def extract_legal_page_content(self, html):
        """
        Extract legal page content from HTML.
        
        Args:
            html (str): HTML content of the legal page
            
        Returns:
            str: Formatted legal content as text
        """
        logger.debug("Extracting legal page content from HTML")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the main content container - usually this is within a specific div or section
        # For Taurbull's legal pages, the main content is typically in the main section
        content_container = soup.find('main')
        
        if not content_container:
            # If main tag is not found, try looking for content in article or specific div
            content_container = soup.find('article') or soup.find('div', {'class': 'page-content'})
            
        if not content_container:
            logger.warning("Could not find main content container. Using body content instead.")
            content_container = soup.body
            
        if not content_container:
            logger.error("Could not extract content from page")
            return ""
            
        # Extract all headings and paragraphs from the content
        headings = content_container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        paragraphs = content_container.find_all('p')
        
        # Format the content
        formatted_content = ""
        
        # Add major headings first
        for heading in headings:
            heading_text = heading.get_text().strip()
            if heading_text:
                tag = heading.name  # gets h1, h2, etc.
                # Format based on heading level
                if tag == 'h1':
                    formatted_content += f"# {heading_text}\n\n"
                elif tag == 'h2':
                    formatted_content += f"## {heading_text}\n\n"
                else:
                    formatted_content += f"### {heading_text}\n\n"
        
        # Add paragraphs
        for para in paragraphs:
            para_text = para.get_text().strip().replace('\n', ' ')
            if para_text:
                formatted_content += f"{para_text}\n\n"
        
        # If we didn't get any structured content, try to extract all text
        if not formatted_content.strip():
            logger.warning("No structured content found. Extracting all text.")
            formatted_content = content_container.get_text().strip()
            
        logger.info(f"Extracted {len(formatted_content.split())} words from legal page")
        return formatted_content.strip()

    def scrape_faq(self, url):
        """
        Scrape FAQ content from the specified URL.
        
        Args:
            url (str): URL of the FAQ page
            
        Returns:
            str: Formatted FAQ content
        """
        html = self.get_page_content(url)
        content = self.extract_faq_content(html)
        return content
        
    def scrape_legal_page(self, url):
        """
        Scrape legal page content from the specified URL.
        
        Args:
            url (str): URL of the legal page
            
        Returns:
            str: Formatted legal page content
        """
        html = self.get_page_content(url)
        content = self.extract_legal_page_content(html)
        return content
        
    def get_all_product_urls(self, catalog_url):
        """
        Get all product URLs from the catalog page, handling pagination.
        
        Args:
            catalog_url (str): URL of the product catalog page
            
        Returns:
            list: List of product URLs
        """
        logger.info(f"Getting product URLs from {catalog_url}")
        
        base_url = "https://taurbull.com"
        product_urls = []
        current_page = 1
        has_next_page = True
        
        while has_next_page:
            page_url = f"{catalog_url}?page={current_page}"
            logger.info(f"Scraping catalog page {current_page}: {page_url}")
            
            try:
                html = self.get_page_content(page_url)
                soup = BeautifulSoup(html, "html.parser")
                
                # Find product links
                product_links = []
                
                # Method 1: Look for a tags that contain product URLs
                for a_tag in soup.find_all('a', href=re.compile(r'/products/')):
                    href = a_tag.get('href')
                    if href and '/products/' in href and '?' not in href:  # Avoid duplicate links with query params
                        full_url = urljoin(base_url, href)
                        if full_url not in product_urls and full_url not in product_links:
                            product_links.append(full_url)
                
                # Method 2: Extract from product JSON data if available
                script_tags = soup.select("script:not([src])")
                for script in script_tags:
                    script_text = script.string
                    if script_text and "collection_viewed" in script_text and "productVariants" in script_text:
                        try:
                            # Find the section with product URLs
                            start_idx = script_text.find('"productVariants":[')
                            if start_idx > 0:
                                # Extract URLs from the JSON data
                                for match in re.finditer(r'"url":"(/products/[^"]+)"', script_text[start_idx:]):
                                    product_path = match.group(1)
                                    full_url = urljoin(base_url, product_path)
                                    if full_url not in product_urls and full_url not in product_links:
                                        product_links.append(full_url)
                        except Exception as e:
                            logger.error(f"Error parsing product data from script: {e}")
                
                if not product_links:
                    logger.warning(f"No products found on page {current_page}")
                    break
                
                # Add unique URLs to our list
                for url in product_links:
                    if url not in product_urls:
                        product_urls.append(url)
                
                # Check if there's a next page
                next_page_link = soup.select_one("a.pagination__item--next")
                if not next_page_link:
                    logger.info("No more pages available")
                    has_next_page = False
                else:
                    current_page += 1
                    
            except Exception as e:
                logger.error(f"Error scraping catalog page {current_page}: {e}")
                has_next_page = False
        
        logger.info(f"Found {len(product_urls)} product URLs")
        return product_urls
        
    def scrape_product_content(self, product_url):
        """
        Scrape detailed content for a single product.
        
        Args:
            product_url (str): URL of the product page
            
        Returns:
            dict: Product data including basic info and full text
        """
        logger.info(f"Scraping product content from {product_url}")
        
        try:
            html = self.get_page_content(product_url)
            
            # Parse the HTML and extract text content
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts and styles
            for script in soup(['script', 'style']):
                script.extract()
            
            # Get text and clean it up
            text = soup.get_text(separator=' ').strip()
            text = re.sub(r'\s+', ' ', text)
            
            # Get basic product info
            scraper = ProductDetailScraper()
            basic_info = scraper.scrape_product_details(product_url)
            
            return {
                "basic_info": basic_info,
                "full_text": text,
                "url": product_url
            }
        
        except Exception as e:
            logger.error(f"Error scraping product text from {product_url}: {e}")
            return {
                "basic_info": {},
                "full_text": "",
                "url": product_url,
                "error": str(e)
            }
            
    def format_product_for_knowledge_base(self, product_data):
        """
        Format product data for knowledge base document.
        
        Args:
            product_data (dict): Dictionary with product data
            
        Returns:
            str: Formatted text for knowledge base
        """
        basic_info = product_data.get("basic_info", {})
        full_text = product_data.get("full_text", "")
        url = product_data.get("url", "")
        
        name = basic_info.get("name", "Unknown Product")
        full_name = basic_info.get("full_name", name)
        price = basic_info.get("price", "Price not available")
        description = basic_info.get("description", "")
        
        # Create a structured text for the knowledge base
        formatted_text = f"""
PRODUCT: {full_name}
URL: {url}
PRICE: {price}
DESCRIPTION: {description}

FULL CONTENT:
{full_text}

"""
        return formatted_text
    
    def scrape_products(self, catalog_url):
        """
        Scrape all products from the catalog and format for knowledge base.
        
        Args:
            catalog_url (str): URL of the product catalog
            
        Returns:
            str: Formatted product content for knowledge base
        """
        logger.info(f"Scraping all products from {catalog_url}")
        
        # Get all product URLs
        product_urls = self.get_all_product_urls(catalog_url)
        
        if not product_urls:
            logger.warning("No product URLs found")
            return ""
        
        # Scrape product data from each URL
        all_product_data = []
        for i, url in enumerate(product_urls, 1):
            logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
            product_data = self.scrape_product_content(url)
            all_product_data.append(product_data)
        
        # Format data for ElevenLabs knowledge base
        formatted_content = "# Taurbull Product Catalog\n\n"
        for product_data in all_product_data:
            formatted_content += self.format_product_for_knowledge_base(product_data)
        
        logger.info(f"Scraped {len(all_product_data)} products with total {len(formatted_content.split())} words")
        return formatted_content 