"""
Content management module for handling caching and change detection.
"""
import hashlib
import logging
import os
from pathlib import Path

# Import using try/except for flexibility
try:
    from src.config import CACHE_DIR, DEBUG
except ImportError:
    from config import CACHE_DIR, DEBUG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentManager:
    """
    Manages content caching and change detection for website content.
    """
    
    @staticmethod
    def get_content_hash(content):
        """
        Generate MD5 hash for content.
        
        Args:
            content (str): The content to hash
            
        Returns:
            str: MD5 hash hexdigest
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def save_content(self, page_name, content):
        """
        Save content and its hash to cache.
        
        Args:
            page_name (str): Name of the page (used for filename)
            content (str): Content to save
            
        Returns:
            tuple: (content_path, hash_path)
        """
        # Ensure the cache directory exists
        CACHE_DIR.mkdir(exist_ok=True)
        
        content_path = CACHE_DIR / f"{page_name}.txt"
        hash_path = CACHE_DIR / f"{page_name}.md5"
        
        # Save content
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save hash
        content_hash = self.get_content_hash(content)
        with open(hash_path, 'w', encoding='utf-8') as f:
            f.write(content_hash)
        
        logger.debug(f"Saved content for {page_name} (hash: {content_hash})")
        return content_path, hash_path
    
    def has_content_changed(self, page_name, current_content):
        """
        Check if content has changed compared to the cached version.
        
        Args:
            page_name (str): Name of the page
            current_content (str): Current content to compare
            
        Returns:
            bool: True if content has changed or cache doesn't exist
        """
        hash_path = CACHE_DIR / f"{page_name}.md5"
        
        # If hash file doesn't exist, content is considered changed
        if not hash_path.exists():
            logger.info(f"No previous hash found for {page_name}, treating as new content")
            return True
        
        # Calculate current content hash
        current_hash = self.get_content_hash(current_content)
        
        # Read previous hash
        with open(hash_path, 'r', encoding='utf-8') as f:
            previous_hash = f.read().strip()
        
        # Compare hashes
        changed = current_hash != previous_hash
        if changed:
            logger.info(f"Content changed for {page_name} (old: {previous_hash}, new: {current_hash})")
        else:
            logger.info(f"No changes detected for {page_name}")
        
        return changed
    
    def get_cached_content(self, page_name):
        """
        Get the cached content for a page.
        
        Args:
            page_name (str): Name of the page
            
        Returns:
            str or None: Cached content if exists, None otherwise
        """
        content_path = CACHE_DIR / f"{page_name}.txt"
        
        if not content_path.exists():
            return None
        
        with open(content_path, 'r', encoding='utf-8') as f:
            return f.read() 