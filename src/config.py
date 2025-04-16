"""
Configuration module for the Taurbull scraper.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# API Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# Scraping Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))

# URLs
FAQ_URL = os.getenv("FAQ_URL", "https://taurbull.com/pages/faq")
LEGAL_NOTICE_URL = os.getenv("LEGAL_NOTICE_URL", "https://taurbull.com/policies/legal-notice")
PRIVACY_POLICY_URL = os.getenv("PRIVACY_POLICY_URL", "https://taurbull.com/policies/privacy-policy")
TERMS_OF_SERVICE_URL = os.getenv("TERMS_OF_SERVICE_URL", "https://taurbull.com/policies/terms-of-service")

# Dictionary mapping page names to URLs
PAGES = {
    "faq": FAQ_URL,
    "legal_notice": LEGAL_NOTICE_URL,
    "privacy_policy": PRIVACY_POLICY_URL,
    "terms_of_service": TERMS_OF_SERVICE_URL,
    # Add more pages here as needed
} 