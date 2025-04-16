"""
Test script for the legal pages scraper functionality.
"""
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

# Import scraper modules
from src.scraper import TaurbullScraper
from src.config import LEGAL_NOTICE_URL, PRIVACY_POLICY_URL, TERMS_OF_SERVICE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_legal_page_scraper(url, page_name):
    """
    Test the legal page scraper on a specific URL.
    
    Args:
        url (str): URL to scrape
        page_name (str): Name of the page for logging
    """
    logger.info(f"Testing legal page scraper on {page_name}: {url}")
    
    try:
        # Create scraper
        scraper = TaurbullScraper()
        
        # Scrape the page
        content = scraper.scrape_legal_page(url)
        
        # Log results
        word_count = len(content.split())
        logger.info(f"Successfully scraped {page_name}. Content length: {len(content)} chars, {word_count} words")
        
        # Save to file for inspection
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{page_name}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"Saved content to {output_file}")
        
    except Exception as e:
        logger.error(f"Error scraping {page_name}: {e}")
        raise


def main():
    """
    Main test function.
    """
    logger.info("Starting legal pages scraper test")
    
    # Create test output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Test each legal page
    test_legal_page_scraper(LEGAL_NOTICE_URL, "legal_notice")
    test_legal_page_scraper(PRIVACY_POLICY_URL, "privacy_policy")
    test_legal_page_scraper(TERMS_OF_SERVICE_URL, "terms_of_service")
    
    logger.info("Legal pages scraper test completed")


if __name__ == "__main__":
    main() 