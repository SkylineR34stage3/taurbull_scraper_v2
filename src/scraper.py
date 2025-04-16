"""
Web scraper module for Taurbull website.
"""
import json
import logging
import requests
from bs4 import BeautifulSoup

# Import using try/except for flexibility
try:
    from src.config import DEBUG
except ImportError:
    from config import DEBUG

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