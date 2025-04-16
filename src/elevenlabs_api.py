"""
ElevenLabs API client for knowledge base management.
"""
import logging
import requests
import json
from pathlib import Path

# Import using try/except for flexibility
try:
    from src.config import ELEVENLABS_API_KEY, ELEVENLABS_API_URL, DEBUG
except ImportError:
    from config import ELEVENLABS_API_KEY, ELEVENLABS_API_URL, DEBUG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """
    Client for interacting with the ElevenLabs API.
    """
    
    def __init__(self, api_key=None, api_url=None):
        """
        Initialize the ElevenLabs API client.
        
        Args:
            api_key (str, optional): ElevenLabs API key
            api_url (str, optional): ElevenLabs API base URL
        """
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.api_url = api_url or ELEVENLABS_API_URL
        self.headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        if not self.api_key:
            logger.warning("No ElevenLabs API key provided. API calls will fail.")
        
        # Check if API key is the placeholder value
        if self.api_key == "your_api_key_here":
            logger.warning("Using placeholder API key. Please update the .env file with your actual ElevenLabs API key.")
    
    def get_knowledge_base_files(self):
        """
        Get list of files in the knowledge base.
        
        Returns:
            list: List of file information dictionaries
        """
        url = f"{self.api_url}/knowledge-base/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting knowledge base files: {e}")
            return []
    
    def delete_file(self, file_id):
        """
        Delete a file from the knowledge base.
        
        Args:
            file_id (str): ID of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.api_url}/knowledge-base/files/{file_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Successfully deleted file {file_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
    
    def upload_file(self, page_name, content):
        """
        Upload content as a file to the knowledge base.
        
        Args:
            page_name (str): Name of the page (used for filename)
            content (str): Content to upload
            
        Returns:
            dict or None: Response data if successful, None otherwise
        """
        url = f"{self.api_url}/knowledge-base/files"
        
        # Create a temporary file
        temp_file_path = Path(f"/tmp/{page_name}.txt")
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        try:
            files = {
                "file": (f"{page_name}.txt", open(temp_file_path, 'rb'), "text/plain")
            }
            
            # Use multipart/form-data format for file upload
            response = requests.post(
                url, 
                headers={"xi-api-key": self.api_key},  # Don't include Accept header for multipart
                files=files
            )
            response.raise_for_status()
            logger.info(f"Successfully uploaded {page_name}.txt to knowledge base")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error uploading file {page_name}.txt: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()
    
    def update_knowledge_base(self, page_name, content, force_update=False):
        """
        Update a file in the knowledge base, deleting any existing version first.
        
        Args:
            page_name (str): Name of the page
            content (str): Content to upload
            force_update (bool): Whether to force update even if file exists
            
        Returns:
            bool: True if successful, False otherwise
        """
        filename = f"{page_name}.txt"
        
        # Get existing files
        files = self.get_knowledge_base_files()
        existing_file = next((f for f in files if f.get("name") == filename), None)
        
        # Delete existing file if found
        if existing_file:
            logger.info(f"Found existing file {filename}, deleting first")
            file_id = existing_file.get("id")
            if not self.delete_file(file_id):
                logger.error(f"Failed to delete existing file {filename}")
                return False
        
        # Upload new file
        result = self.upload_file(page_name, content)
        return result is not None 