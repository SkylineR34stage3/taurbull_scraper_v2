"""
Main module for the Taurbull Website Scraper application.
"""
import logging
import time
import schedule
import sys
import os
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

# ElevenLabs agent ID to assign knowledge base documents to
AGENT_ID = "2AmUavf0llkEhjBRMstL"


def check_api_connectivity():
    """
    Check connectivity to the ElevenLabs API and show user information.
    
    Returns:
        bool: True if connectivity check passes
    """
    elevenlabs = ElevenLabsClient()
    
    # Try to get user info to test API key
    user_info = elevenlabs.get_user_info()
    
    if not user_info:
        logger.error("Failed to connect to ElevenLabs API. Please check your API key and connection.")
        return False
    
    # Log user information
    tier = user_info.get("subscription", {}).get("tier", "unknown")
    logger.info(f"Connected to ElevenLabs API. Account tier: {tier}")
    
    # Check if user has conversational AI access
    # Note: This is just a basic check - actual access might depend on the specific tier details
    if tier not in ["creator", "pro", "enterprise"]:
        logger.warning("Your ElevenLabs account might not have access to the Knowledge Base API.")
        logger.warning("Please ensure you have an appropriate subscription tier.")
    
    return True


def process_page(page_name, url, force_scrape=False, max_products=None):
    """
    Process a single page - scrape, check for changes, and update knowledge base if needed.
    
    Args:
        page_name (str): Name of the page
        url (str): URL of the page
        force_scrape (bool): Whether to force update regardless of content changes
        max_products (int, optional): Maximum number of products to scrape (for products page only)
        
    Returns:
        bool: True if page was updated, False otherwise
    """
    logger.info(f"Processing page: {page_name} from {url}")
    
    scraper = TaurbullScraper()
    content_manager = ContentManager()
    elevenlabs = ElevenLabsClient()
    
    # Check if running on Heroku (for special handling)
    is_heroku = 'DYNO' in os.environ
    
    try:
        # Scrape the page content
        if page_name == "faq":
            content = scraper.scrape_faq(url)
        elif page_name in ["legal_notice", "privacy_policy", "terms_of_service"]:
            # Handle legal pages using the legal page scraper
            content = scraper.scrape_legal_page(url)
        elif page_name == "products":
            # Handle product pages using the product scraper
            if max_products:
                logger.info(f"Limiting product scraping to {max_products} products")
            content = scraper.scrape_products(url)
        else:
            # For future implementation of other page types
            logger.warning(f"Scraping for page type '{page_name}' not implemented yet")
            return False
        
        if not content:
            logger.error(f"Failed to extract content from {page_name}")
            return False
            
        logger.info(f"Extracted {len(content.split())} words from {page_name}")
        
        # Check if content has changed or force_scrape is enabled
        if force_scrape or content_manager.has_content_changed(page_name, content):
            # Update the knowledge base
            if force_scrape:
                logger.info(f"Force scrape enabled, updating knowledge base for {page_name}")
            else:
                logger.info(f"Content changed for {page_name}, updating knowledge base")
            
            # Use force_update=True when running on Heroku to handle API issues or when force_scrape is enabled
            force_update = is_heroku or force_scrape
            if force_update:
                log_reason = "running on Heroku" if is_heroku else "force scrape enabled"
                logger.info(f"Using force_update=True ({log_reason})")
            
            # Update the knowledge base and assign to the agent
            logger.info(f"Assigning document to agent {AGENT_ID}")
            success = elevenlabs.update_knowledge_base(page_name, content, force_update=force_update, agent_id=AGENT_ID)
            
            if success:
                # Save the new content
                content_manager.save_content(page_name, content)
                logger.info(f"Successfully updated {page_name} in knowledge base and assigned to agent")
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


def run_scraper(force_scrape=False, max_products=None):
    """
    Run the scraper for all configured pages.
    
    Args:
        force_scrape (bool): Whether to force scrape all pages regardless of content changes
        max_products (int, optional): Maximum number of products to scrape
    """
    logger.info(f"Starting scraper run (force_scrape={force_scrape})")
    
    # First check API connectivity
    if not check_api_connectivity():
        logger.error("API connectivity check failed. Scraper run aborted.")
        return
    
    # Process each page
    updated_pages = 0
    for page_name, url in PAGES.items():
        # For products page, pass the max_products parameter
        if page_name == "products":
            if process_page(page_name, url, force_scrape, max_products):
                updated_pages += 1
        else:
            if process_page(page_name, url, force_scrape):
                updated_pages += 1
    
    logger.info(f"Scraper run completed. Updated {updated_pages} of {len(PAGES)} pages")


def schedule_scraper(force_scrape=False, max_products=None):
    """
    Schedule the scraper to run at regular intervals.
    
    Args:
        force_scrape (bool): Whether to force scrape all pages regardless of content changes
        max_products (int, optional): Maximum number of products to scrape
    """
    # Schedule the job
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(run_scraper, force_scrape=force_scrape, max_products=max_products)
    logger.info(f"Scheduled scraper to run every {SCRAPE_INTERVAL_HOURS} hours")
    
    # Run immediately on startup
    run_scraper(force_scrape=force_scrape, max_products=max_products)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    """
    Main entry point for the application.
    """
    logger.info("Taurbull Website Scraper starting")
    
    # Check if ELEVENLABS_API_KEY is set
    if not os.environ.get("ELEVENLABS_API_KEY"):
        logger.error("ELEVENLABS_API_KEY environment variable is not set.")
        logger.error("Please set your API key in the .env file or as an environment variable.")
        return 1
    
    # Parse command line arguments
    force_scrape = False
    run_once = False
    max_products = None
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--once":
            run_once = True
        elif arg == "--force":
            force_scrape = True
            logger.info("Force scrape enabled - will update all pages regardless of content changes")
        elif arg == "--max-products" and i+1 < len(sys.argv[1:]):
            try:
                max_products = int(sys.argv[i+2])
                logger.info(f"Maximum product limit set to {max_products}")
            except (ValueError, IndexError):
                logger.warning("Invalid max-products value, using unlimited")
    
    # Check if running as a one-time job or scheduled service
    if run_once:
        run_scraper(force_scrape=force_scrape, max_products=max_products)
    else:
        schedule_scraper(force_scrape=force_scrape, max_products=max_products)
    
    return 0


if __name__ == "__main__":
    main() 