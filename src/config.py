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

# Dictionary mapping page names to URLs
PAGES = {
    "faq": FAQ_URL,
    # Add more pages here as needed
} 