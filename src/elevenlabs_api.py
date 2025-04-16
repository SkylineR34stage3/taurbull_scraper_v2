"""
ElevenLabs API client for knowledge base management.
"""
import logging
import requests
import json
import tempfile
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
    
    def get_user_info(self):
        """
        Get user account information.
        
        Returns:
            dict or None: User info if successful, None otherwise
        """
        url = f"{self.api_url}/user"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def add_to_knowledge_base(self, name, content, document_type="text"):
        """
        Add content to the knowledge base.
        
        Args:
            name (str): Name for the knowledge base document
            content (str): Text content to add
            document_type (str): Type of document ('file', 'url', 'text')
            
        Returns:
            dict or None: Response data if successful, None otherwise
        """
        url = f"{self.api_url}/convai/knowledge-base"
        
        if document_type == "file":
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
                temp_file_path = Path(temp_file.name)
                temp_file.write(content)
            
            try:
                # Create multipart form data
                files = {
                    'file': (f"{name}.txt", open(temp_file_path, 'rb'), 'text/plain')
                }
                
                data = {
                    'document_name': name,
                    'document_type': 'file'
                }
                
                # Use multipart/form-data format for file upload
                response = requests.post(
                    url, 
                    headers={"xi-api-key": self.api_key},  # Don't include Accept header for multipart
                    data=data,
                    files=files
                )
                
                response.raise_for_status()
                logger.info(f"Successfully added {name} to knowledge base")
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Error adding content to knowledge base: {e}")
                return None
            finally:
                # Clean up temporary file
                if temp_file_path.exists():
                    temp_file_path.unlink()
        
        elif document_type == "url":
            # Create request payload for URL
            payload = {
                "document_name": name,
                "document_type": "url",
                "url": content  # In this case, content should be a URL
            }
            
            try:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                logger.info(f"Successfully added URL {name} to knowledge base")
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Error adding URL to knowledge base: {e}")
                return None
        
        else:
            # Handle text content (this approach may not be supported by the API anymore)
            logger.warning("Text document type might not be supported directly. Converting to file upload.")
            return self.add_to_knowledge_base(name, content, document_type="file")
    
    def get_knowledge_base_docs(self):
        """
        Get list of documents in the knowledge base.
        
        Returns:
            list: List of document information dictionaries
        """
        url = f"{self.api_url}/convai/knowledge-base"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Check if the response has the expected structure
            if isinstance(data, dict) and "documents" in data:
                return data["documents"]
            
            # For backwards compatibility with older API versions or unexpected response formats
            logger.warning(f"Unexpected knowledge base response format: {type(data)}")
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            elif isinstance(data, list):
                return data
            else:
                logger.error("Unable to extract documents from knowledge base response")
                return []
            
        except requests.RequestException as e:
            logger.error(f"Error getting knowledge base documents: {e}")
            return []
    
    def delete_knowledge_base_doc(self, doc_id):
        """
        Delete a document from the knowledge base.
        
        Args:
            doc_id (str): ID of the document to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.api_url}/convai/knowledge-base/{doc_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Successfully deleted document {doc_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def update_knowledge_base(self, page_name, content, force_update=False):
        """
        Update the knowledge base with new content, deleting any existing version first.
        
        Args:
            page_name (str): Name of the page
            content (str): Content to upload
            force_update (bool): Whether to force update even if file exists
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Updating knowledge base for {page_name}")
        
        try:
            # Get existing documents
            existing_docs = self.get_knowledge_base_docs()
            
            # Find existing document with same name
            existing_doc = next((d for d in existing_docs if isinstance(d, dict) and d.get("name") == f"{page_name}.txt"), None)
            if not existing_doc:
                # Try without .txt extension
                existing_doc = next((d for d in existing_docs if isinstance(d, dict) and d.get("name") == page_name), None)
            
            # Delete existing document if found
            if existing_doc:
                doc_id = existing_doc.get("id")
                logger.info(f"Found existing document '{existing_doc.get('name')}' with ID {doc_id}, deleting first")
                
                try:
                    if not self.delete_knowledge_base_doc(doc_id):
                        logger.warning(f"Failed to delete existing document {existing_doc.get('name')}")
                        # If force_update is true, continue anyway
                        if not force_update:
                            logger.info("Skipping update due to deletion failure. Use force_update=True to override.")
                            return False
                        logger.info("Proceeding with update despite deletion failure (force_update=True)")
                except Exception as e:
                    logger.warning(f"Exception deleting document: {e}")
                    # If force_update is true, continue anyway
                    if not force_update:
                        logger.info("Skipping update due to deletion error. Use force_update=True to override.")
                        return False
                    logger.info("Proceeding with update despite deletion error (force_update=True)")
            
            # Add new document as a file upload
            result = self.add_to_knowledge_base(page_name, content, document_type="file")
            success = result is not None
            
            if success:
                logger.info(f"Successfully updated knowledge base with {page_name}")
            else:
                logger.error(f"Failed to update knowledge base with {page_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            # Try direct upload without deletion if force_update is True
            if force_update:
                logger.info(f"Attempting direct upload with force_update=True")
                result = self.add_to_knowledge_base(page_name, content, document_type="file")
                return result is not None
            return False 