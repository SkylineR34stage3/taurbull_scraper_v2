"""
Tests for the TaurbullScraper class.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

# Import using try/except for flexibility
try:
    from src.scraper import TaurbullScraper
except ImportError:
    from scraper import TaurbullScraper


@pytest.fixture
def sample_faq_html():
    """Sample HTML content with FAQ JSON-LD data."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FAQ - Taurbull</title>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "Sample Question 1?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "<p>Sample Answer 1</p>"
                    }
                },
                {
                    "@type": "Question",
                    "name": "Sample Question 2?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "<p>Sample Answer 2</p>"
                    }
                }
            ]
        }
        </script>
    </head>
    <body>
        <h1>FAQ</h1>
        <!-- Page content -->
    </body>
    </html>
    """


@pytest.fixture
def sample_individual_question_html():
    """Sample HTML content with individual Question JSON-LD data."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FAQ - Taurbull</title>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Question",
            "name": "Individual Question?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "<p>Individual Answer</p>"
            }
        }
        </script>
    </head>
    <body>
        <h1>FAQ</h1>
        <!-- Page content -->
    </body>
    </html>
    """


class TestTaurbullScraper:
    """Test suite for the TaurbullScraper class."""
    
    def test_get_page_content(self):
        """Test fetching page content."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "Sample content"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            scraper = TaurbullScraper()
            content = scraper.get_page_content("https://example.com")
            
            assert content == "Sample content"
            mock_get.assert_called_once()
    
    def test_extract_faq_content_faqpage(self, sample_faq_html):
        """Test extracting FAQ content from FAQPage format."""
        scraper = TaurbullScraper()
        content = scraper.extract_faq_content(sample_faq_html)
        
        # Check content includes both questions and answers
        assert "Q: Sample Question 1?" in content
        assert "A: Sample Answer 1" in content
        assert "Q: Sample Question 2?" in content
        assert "A: Sample Answer 2" in content
    
    def test_extract_faq_content_individual_question(self, sample_individual_question_html):
        """Test extracting FAQ content from individual Question format."""
        scraper = TaurbullScraper()
        content = scraper.extract_faq_content(sample_individual_question_html)
        
        # Check content includes the question and answer
        assert "Q: Individual Question?" in content
        assert "A: Individual Answer" in content
    
    def test_scrape_faq(self):
        """Test the full FAQ scraping process."""
        with patch.object(TaurbullScraper, 'get_page_content') as mock_get_content:
            with patch.object(TaurbullScraper, 'extract_faq_content') as mock_extract:
                mock_get_content.return_value = "Sample HTML"
                mock_extract.return_value = "Formatted FAQ Content"
                
                scraper = TaurbullScraper()
                result = scraper.scrape_faq("https://example.com/faq")
                
                assert result == "Formatted FAQ Content"
                mock_get_content.assert_called_once_with("https://example.com/faq")
                mock_extract.assert_called_once_with("Sample HTML") 