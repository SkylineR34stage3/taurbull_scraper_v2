from src.product_scraper import ProductDetailScraper
import json
import re
from bs4 import BeautifulSoup
import requests

def scrape_full_product_texts():
    scraper = ProductDetailScraper()
    urls = [
        'https://taurbull.com/products/dry-aged-burger-patties-black-angus-freiland',
        'https://taurbull.com/products/ribeye-steak-black-angus-dry-aged',
        'https://taurbull.com/products/short-ribs-black-angus-dry-aged'
    ]
    
    results = {}
    for url in urls:
        print(f'Scraping {url}...')
        # Use a direct request to get the HTML
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        response = session.get(url)
        html = response.text
        
        # Get all text content from the page using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get all text content, excluding scripts and styles
        for script in soup(['script', 'style']):
            script.extract()
            
        # Get text and clean it up
        text = soup.get_text(separator=' ').strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Store in results
        results[url] = {
            'basic_info': scraper.scrape_product_details(url),
            'full_text': text
        }
    
    # Output first 1000 chars of full text for preview
    for url, data in results.items():
        product_name = data['basic_info']['name']
        print(f'\n\n===== {product_name} =====')
        print(f'Full text (first 1000 chars):')
        print(data['full_text'][:1000])
    
    # Save complete results to file
    with open('product_texts.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print('\n\nComplete data saved to product_texts.json')

if __name__ == "__main__":
    scrape_full_product_texts() 