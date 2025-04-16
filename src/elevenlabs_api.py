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
                
                # Parse response
                result = response.json()
                
                # Log the response structure to help debug
                logger.debug(f"Knowledge base upload response: {json.dumps(result)}")
                
                # The API may return different formats, try to extract document_id
                if isinstance(result, dict):
                    # Check various potential keys where document_id might be
                    if "document_id" in result:
                        logger.info(f"Found document_id in response: {result['document_id']}")
                    elif "id" in result:
                        # Create a standardized return format
                        result = {"document_id": result["id"]}
                        logger.info(f"Found id in response, normalized to document_id: {result['document_id']}")
                    
                return result
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
            
            # Log the response structure to help debug
            logger.debug(f"Knowledge base listing response: {json.dumps(data)}")
            
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
            
            # Check response status
            if response.status_code == 404:
                # Document not found is considered a success (already deleted)
                logger.warning(f"Document {doc_id} not found (404). Considering it already deleted.")
                return True
            elif response.status_code == 400:
                # Bad request might be due to document already being deleted or other API constraints
                logger.warning(f"Bad request (400) when deleting document {doc_id}. This may happen if the document is already deleted or in use.")
                # Check if there's additional error information in the response
                try:
                    error_data = response.json()
                    logger.warning(f"Error details: {error_data}")
                except ValueError:
                    logger.warning(f"Response text: {response.text}")
                return False
            else:
                # For any other status code, raise for status to catch other errors
                response.raise_for_status()
                logger.info(f"Successfully deleted document {doc_id}")
                return True
            
        except requests.RequestException as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def get_agent(self, agent_id):
        """
        Get agent configuration.
        
        Args:
            agent_id (str): ID of the agent
            
        Returns:
            dict or None: Agent configuration if successful, None otherwise
        """
        url = f"{self.api_url}/convai/agents/{agent_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Successfully retrieved agent configuration for {agent_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting agent configuration: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    logger.error(f"Error details: {error_data}")
                except ValueError:
                    logger.error(f"Response text: {e.response.text}")
            return None
    
    def update_agent_knowledge_base(self, agent_id, knowledge_base_ids):
        """
        Update agent's knowledge base configuration.
        
        Args:
            agent_id (str): ID of the agent
            knowledge_base_ids (list): List of knowledge base document IDs
            
        Returns:
            bool: True if successful, False otherwise
        """
        # First get the current agent configuration
        agent_config = self.get_agent(agent_id)
        if not agent_config:
            logger.error(f"Could not retrieve agent configuration for {agent_id}")
            return False
        
        # Update the agent's knowledge base configuration
        url = f"{self.api_url}/convai/agents/{agent_id}"
        
        # Get knowledge base documents to get names
        existing_docs = self.get_knowledge_base_docs()
        
        # Create knowledge base items in the format needed for the agent config
        knowledge_base_items = []
        for doc_id in knowledge_base_ids:
            # Find doc name from the existing docs
            doc_name = None
            for doc in existing_docs:
                if doc.get("id") == doc_id:
                    doc_name = doc.get("name")
                    break
            
            # Add knowledge base item with required fields
            kb_item = {
                "type": "file",
                "id": doc_id,
                "usage_mode": "auto"
            }
            
            # Add name if available
            if doc_name:
                kb_item["name"] = doc_name
            else:
                # Use a default name if not found
                kb_item["name"] = f"Document {doc_id}"
                
            knowledge_base_items.append(kb_item)
            
        # Prepare update payload
        try:
            # Extract conversation_config from agent_config
            conversation_config = agent_config.get("conversation_config", {})
            
            # Update the knowledge_base field in the prompt section
            if "agent" not in conversation_config:
                conversation_config["agent"] = {}
            if "prompt" not in conversation_config["agent"]:
                conversation_config["agent"]["prompt"] = {}
            
            # Set the knowledge_base field to our new list
            conversation_config["agent"]["prompt"]["knowledge_base"] = knowledge_base_items
            
            # Create the update payload
            payload = {
                "conversation_config": conversation_config
            }
            
            # Log payload for debugging
            logger.debug(f"Agent update payload: {json.dumps(payload)}")
            
            # Make the update request
            response = requests.patch(
                url,
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            logger.info(f"Successfully updated agent {agent_id} with knowledge base documents")
            return True
        except KeyError as e:
            logger.error(f"Error preparing agent update payload: {e}")
            return False
        except requests.RequestException as e:
            logger.error(f"Error updating agent: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    logger.error(f"Error details: {error_data}")
                except ValueError:
                    logger.error(f"Response text: {e.response.text}")
            return False
    
    def update_knowledge_base(self, page_name, content, force_update=False, agent_id=None):
        """
        Update the knowledge base with new content, deleting any existing version first.
        
        Args:
            page_name (str): Name of the page
            content (str): Content to upload
            force_update (bool): Whether to force update even if file exists
            agent_id (str, optional): Agent ID to assign the document to
            
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
                    delete_success = self.delete_knowledge_base_doc(doc_id)
                    if not delete_success:
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
            
            if success and agent_id:
                # Check if the result has a document_id or id
                doc_id = None
                if isinstance(result, dict):
                    if "document_id" in result:
                        doc_id = result["document_id"]
                    elif "id" in result:
                        doc_id = result["id"]
                
                if doc_id:
                    logger.info(f"Successfully added document with ID {doc_id}")
                    
                    # If a document was previously assigned to the agent, we want to keep it in the list
                    # Get the current agent configuration and collect current knowledge base docs
                    agent_config = self.get_agent(agent_id)
                    existing_kb_ids = []
                    
                    if agent_config and "conversation_config" in agent_config:
                        try:
                            # Extract existing knowledge base items
                            knowledge_base_items = agent_config["conversation_config"]["agent"]["prompt"].get("knowledge_base", [])
                            
                            # Collect IDs of existing documents (except any with the same name as we're updating)
                            for item in knowledge_base_items:
                                if isinstance(item, dict) and "id" in item:
                                    kb_item_id = item["id"]
                                    # Check if this document is not the one we're replacing
                                    kb_doc = next((d for d in existing_docs if d.get("id") == kb_item_id), None)
                                    if kb_doc and kb_doc.get("name") != f"{page_name}.txt" and kb_doc.get("name") != page_name:
                                        existing_kb_ids.append(kb_item_id)
                        except (KeyError, TypeError) as e:
                            logger.warning(f"Error extracting existing knowledge base IDs: {e}")
                    
                    # Add our new document ID to the list
                    existing_kb_ids.append(doc_id)
                    
                    # Update the agent with all knowledge base document IDs
                    if self.update_agent_knowledge_base(agent_id, existing_kb_ids):
                        logger.info(f"Successfully assigned document {doc_id} to agent {agent_id}")
                    else:
                        logger.error(f"Failed to assign document {doc_id} to agent {agent_id}")
                else:
                    # Log the result for debugging
                    logger.error(f"Document was added but couldn't determine document ID. Response: {json.dumps(result)}")
                    
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
                success = result is not None
                
                if success and agent_id and isinstance(result, dict):
                    # Check for either document_id or id in the response
                    if "document_id" in result:
                        doc_id = result["document_id"]
                    elif "id" in result:
                        doc_id = result["id"]
                    else:
                        logger.error(f"Couldn't extract document ID from result: {json.dumps(result)}")
                        return success
                        
                    if self.update_agent_knowledge_base(agent_id, [doc_id]):
                        logger.info(f"Successfully assigned document {doc_id} to agent {agent_id}")
                    else:
                        logger.error(f"Failed to assign document {doc_id} to agent {agent_id}")
                
                return success
            return False 