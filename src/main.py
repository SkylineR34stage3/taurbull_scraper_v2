"""
Main module for the Taurbull Website Scraper application.
"""
import logging
import time
import schedule
import sys
from pathlib import Path

# Import modules using relative imports
try:
    # When running as a module (python -m src.main)
    from src.config import PAGES, SCRAPE_INTERVAL_HOURS, DEBUG
    from src.scraper import TaurbullScraper
    from src.content_manager import ContentManager
    from src.elevenlabs_api import ElevenLabsClient
except ImportError:
    # When running directly from src directory (python main.py)
    from config import PAGES, SCRAPE_INTERVAL_HOURS, DEBUG
    from scraper import TaurbullScraper
    from content_manager import ContentManager
    from elevenlabs_api import ElevenLabsClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("taurbull_scraper.log")
    ]
)
logger = logging.getLogger(__name__)


def process_page(page_name, url):
    """
    Process a single page - scrape, check for changes, and update knowledge base if needed.
    
    Args:
        page_name (str): Name of the page
        url (str): URL of the page
        
    Returns:
        bool: True if page was updated, False otherwise
    """
    logger.info(f"Processing page: {page_name} from {url}")
    
    scraper = TaurbullScraper()
    content_manager = ContentManager()
    elevenlabs = ElevenLabsClient()
    
    try:
        # Scrape the page content
        if page_name == "faq":
            content = scraper.scrape_faq(url)
        else:
            # For future implementation of other page types
            logger.warning(f"Scraping for page type '{page_name}' not implemented yet")
            return False
        
        # Check if content has changed
        if content_manager.has_content_changed(page_name, content):
            # Update the knowledge base
            logger.info(f"Updating knowledge base for {page_name}")
            success = elevenlabs.update_knowledge_base(page_name, content)
            
            if success:
                # Save the new content
                content_manager.save_content(page_name, content)
                logger.info(f"Successfully updated {page_name} in knowledge base")
                return True
            else:
                logger.error(f"Failed to update {page_name} in knowledge base")
                return False
        else:
            logger.info(f"No changes detected for {page_name}, skipping update")
            return False
            
    except Exception as e:
        logger.error(f"Error processing page {page_name}: {e}", exc_info=True)
        return False


def run_scraper():
    """
    Run the scraper for all configured pages.
    """
    logger.info("Starting scraper run")
    
    # Process each page
    updated_pages = 0
    for page_name, url in PAGES.items():
        if process_page(page_name, url):
            updated_pages += 1
    
    logger.info(f"Scraper run completed. Updated {updated_pages} of {len(PAGES)} pages")


def schedule_scraper():
    """
    Schedule the scraper to run at regular intervals.
    """
    # Schedule the job
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(run_scraper)
    logger.info(f"Scheduled scraper to run every {SCRAPE_INTERVAL_HOURS} hours")
    
    # Run immediately on startup
    run_scraper()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    """
    Main entry point for the application.
    """
    logger.info("Taurbull Website Scraper starting")
    
    # Check if running as a one-time job or scheduled service
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_scraper()
    else:
        schedule_scraper()
    
    return 0


if __name__ == "__main__":
    main() 