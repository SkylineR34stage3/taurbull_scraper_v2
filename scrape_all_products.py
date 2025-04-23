from bs4 import BeautifulSoup
import requests
import json
import re
import os
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin
from src.product_scraper import ProductDetailScraper
from src.elevenlabs_api import ElevenLabsClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CATALOG_URL = "https://taurbull.com/collections/all"
BASE_URL = "https://taurbull.com"
OUTPUT_DIR = "product_data"
AGENT_ID = "2AmUavf0llkEhjBRMstL"  # Your agent ID

def get_all_product_urls() -> List[str]:
    """
    Scrape all product URLs from the catalog, handling pagination.
    
    Returns:
        List of product URLs
    """
    logger.info(f"Getting all product URLs from {CATALOG_URL}")
    
    product_urls = []
    current_page = 1
    has_next_page = True
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    
    while has_next_page:
        page_url = f"{CATALOG_URL}?page={current_page}"
        logger.info(f"Scraping catalog page {current_page}: {page_url}")
        
        try:
            response = session.get(page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find product links - Update for the actual HTML structure
            product_links = []
            
            # Method 1: Look for a tags that contain product URLs
            for a_tag in soup.find_all('a', href=re.compile(r'/products/')):
                href = a_tag.get('href')
                if href and '/products/' in href and '?' not in href:  # Avoid duplicate links with query params
                    full_url = urljoin(BASE_URL, href)
                    if full_url not in product_urls and full_url not in product_links:
                        product_links.append(full_url)
            
            # Method 2: Extract from product JSON data if available
            # Look for collection_viewed in the script section
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
                                full_url = urljoin(BASE_URL, product_path)
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

def scrape_product_text(url: str) -> Dict[str, Any]:
    """
    Scrape all text content from a product page.
    
    Args:
        url: URL of the product page
        
    Returns:
        Dictionary with basic info and full text of the product page
    """
    logger.info(f"Scraping product text from {url}")
    
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        
        response = session.get(url)
        response.raise_for_status()
        html = response.text
        
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
        basic_info = scraper.scrape_product_details(url)
        
        return {
            "basic_info": basic_info,
            "full_text": text,
            "url": url
        }
    
    except Exception as e:
        logger.error(f"Error scraping product text from {url}: {e}")
        return {
            "basic_info": {},
            "full_text": "",
            "url": url,
            "error": str(e)
        }

def format_product_for_knowledge_base(product_data: Dict[str, Any]) -> str:
    """
    Format product data for knowledge base document.
    
    Args:
        product_data: Dictionary with product data
        
    Returns:
        Formatted text for knowledge base
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

def main():
    """
    Main function to run the scraper.
    """
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get all product URLs
    product_urls = get_all_product_urls()
    
    # Scrape product data from each URL
    all_product_data = []
    for i, url in enumerate(product_urls, 1):
        logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
        product_data = scrape_product_text(url)
        all_product_data.append(product_data)
    
    # Save all product data to file
    with open(f"{OUTPUT_DIR}/all_products.json", "w", encoding="utf-8") as f:
        json.dump(all_product_data, f, ensure_ascii=False, indent=2)
    
    # Format data for ElevenLabs knowledge base
    formatted_content = ""
    for product_data in all_product_data:
        formatted_content += format_product_for_knowledge_base(product_data)
    
    # Save formatted content to file
    with open(f"{OUTPUT_DIR}/elevenlabs_knowledge_base.txt", "w", encoding="utf-8") as f:
        f.write(formatted_content)
    
    # Upload to ElevenLabs
    try:
        logger.info("Uploading content to ElevenLabs knowledge base")
        
        # Initialize the ElevenLabs client
        elevenlabs_client = ElevenLabsClient()
        
        # Check for existing documents
        existing_docs = elevenlabs_client.get_knowledge_base_docs()
        
        # Delete existing documents if needed
        for doc in existing_docs:
            doc_id = doc.get("id")
            if doc_id:
                logger.info(f"Deleting existing document: {doc_id}")
                elevenlabs_client.delete_knowledge_base_doc(doc_id)
        
        # Add new document to knowledge base
        file_path = f"{OUTPUT_DIR}/elevenlabs_knowledge_base.txt"
        doc_name = "Taurbull Product Information"
        metadata = {"source": "Taurbull Website", "type": "product_catalog"}
        
        result = elevenlabs_client.update_knowledge_base(file_path, doc_name, metadata, agent_id=AGENT_ID)
        
        logger.info(f"ElevenLabs knowledge base update result: {result}")
        
    except Exception as e:
        logger.error(f"Error uploading to ElevenLabs: {e}")
    
    logger.info("All tasks completed!")

if __name__ == "__main__":
    main() 