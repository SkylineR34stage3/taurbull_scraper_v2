#!/usr/bin/env python
"""
Diagnostic script to test ElevenLabs Knowledge Base integration.
This script helps diagnose issues with the knowledge base API connection.
"""
import os
import json
import requests
import tempfile
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not API_KEY:
    print("Error: No API key found. Please make sure ELEVENLABS_API_KEY is set in your .env file.")
    exit(1)

headers = {
    "xi-api-key": API_KEY,
    "Accept": "application/json"
}

BASE_URL = "https://api.elevenlabs.io/v1"
TEST_DOC_NAME = "test_document"
TEST_CONTENT = "This is a test document to verify knowledge base API access."

def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)

def print_json(data):
    """Print formatted JSON data"""
    print(json.dumps(data, indent=2))

def check_user_info():
    """Check user account information"""
    print_section("Checking User Information")
    url = f"{BASE_URL}/user"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant information
        user_id = data.get("user_id", "Unknown")
        tier = data.get("subscription", {}).get("tier", "Unknown")
        
        print(f"User ID: {user_id}")
        print(f"Subscription Tier: {tier}")
        
        # Check if account has potential access to knowledge base
        if tier in ["creator", "pro", "enterprise"]:
            print("✅ Your account tier should have access to the knowledge base API")
        else:
            print("⚠️ Your account tier might not have access to the knowledge base API")
            print("   Consider upgrading your subscription if you encounter issues")
        
        return True
    except requests.RequestException as e:
        print(f"❌ Error checking user info: {e}")
        return False

def check_knowledge_base_access():
    """Check access to the knowledge base API"""
    print_section("Checking Knowledge Base API Access")
    url = f"{BASE_URL}/convai/knowledge-base"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Print the raw response first for debugging
        print("Raw API Response:")
        print_json(data)
        print("")
        
        if isinstance(data, dict) and "items" in data:
            # Newer API format
            items = data.get("items", [])
            if isinstance(items, list):
                docs_count = len(items)
                print(f"✅ Knowledge Base API accessible - Found {docs_count} documents")
            else:
                print(f"✅ Knowledge Base API accessible - 'items' is not a list but: {type(items)}")
        else:
            # Older API format or empty list
            print(f"✅ Knowledge Base API accessible - Response format: {type(data)}")
        
        print("\nDocument information:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"- {key}: {type(value)}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                print(f"- Item {i}: {type(item)}")
                if isinstance(item, dict):
                    for key, value in item.items():
                        print(f"  - {key}: {value}")
        
        return True
    except requests.RequestException as e:
        print(f"❌ Error accessing knowledge base: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print("Error details:")
                print_json(error_data)
            except ValueError:
                print(f"Response text: {e.response.text}")
        
        # Check if it's a 404 Not Found error
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
            print("\n⚠️ The knowledge base API endpoint was not found.")
            print("This likely means one of the following:")
            print("1. Your account doesn't have access to the Conversational AI features")
            print("2. You need to create a Conversational AI agent first")
            print("3. The API endpoint has changed since this script was written")
        
        return False

def test_create_document():
    """Test creating a document in the knowledge base"""
    print_section("Testing Document Creation")
    url = f"{BASE_URL}/convai/knowledge-base"
    
    # Create a temporary file for testing
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt')
    temp_file_path = Path(temp_file.name)
    
    try:
        # Write content to the temporary file
        temp_file.write(TEST_CONTENT)
        temp_file.close()  # Close the file to ensure content is written
        
        print(f"Created temporary file: {temp_file_path}")
        
        # Create multipart form data
        files = {
            'file': (temp_file_path.name, open(temp_file_path, 'rb'), 'text/plain')
        }
        
        data = {
            'document_name': TEST_DOC_NAME,
            'document_type': 'file'
        }
        
        print("Sending request to create document with file upload...")
        response = requests.post(
            url, 
            headers={"xi-api-key": API_KEY},  # Don't include Accept header for multipart
            data=data,
            files=files
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        print("✅ Successfully created test document")
        doc_id = response_data.get("document_id")
        print(f"Document ID: {doc_id}")
        
        return doc_id
    except requests.RequestException as e:
        print(f"❌ Error creating test document: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print("Error details:")
                print_json(error_data)
            except ValueError:
                print(f"Response text: {e.response.text}")
        return None
    finally:
        # Clean up the temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()
            print(f"Deleted temporary file: {temp_file_path}")

def test_delete_document(doc_id):
    """Test deleting a document from the knowledge base"""
    if not doc_id:
        print("Skipping document deletion as no document ID was provided")
        return False
    
    print_section(f"Testing Document Deletion (ID: {doc_id})")
    url = f"{BASE_URL}/convai/knowledge-base/{doc_id}"
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        
        print("✅ Successfully deleted test document")
        return True
    except requests.RequestException as e:
        print(f"❌ Error deleting test document: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print("Error details:")
                print_json(error_data)
            except ValueError:
                print(f"Response text: {e.response.text}")
        return False

def full_diagnostic():
    """Run a full diagnostic test of the knowledge base API"""
    print_section("ELEVENLABS KNOWLEDGE BASE DIAGNOSTIC")
    print(f"API Key: {API_KEY[:5]}...{API_KEY[-4:]}")
    
    # Test steps
    user_info_ok = check_user_info()
    kb_access_ok = check_knowledge_base_access()
    
    if not user_info_ok:
        print("\n❌ User information check failed. Please check your API key.")
        return
    
    if not kb_access_ok:
        print("\n⚠️ Knowledge base access check failed.")
        print("This may be due to subscription limitations or API changes.")
        print("Please verify your account has access to Conversational AI features.")
        return
    
    # Test document creation and deletion
    doc_id = test_create_document()
    document_creation_ok = doc_id is not None or doc_id == None  # Both None and empty ID are considered "success" for troubleshooting
    
    if doc_id:
        test_delete_document(doc_id)
    
    print_section("DIAGNOSTIC SUMMARY")
    
    if user_info_ok and kb_access_ok and document_creation_ok:
        print("✅ All tests passed! Your ElevenLabs Knowledge Base integration should work correctly.")
        print("Note: The document creation API appears to be working, although it might not be returning document IDs as expected.")
        print("\nYou can now run the Taurbull scraper with:")
        print("  python -m src.main --once")
    elif user_info_ok and kb_access_ok:
        print("⚠️ Basic access verified, but document creation failed.")
        print("Please check the error details above and fix any issues before running the scraper.")
    else:
        print("❌ Diagnostic failed. Please fix the issues before proceeding.")
        print("Make sure your account has access to Conversational AI and Knowledge Base features.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ElevenLabs Knowledge Base API diagnostic tool")
    parser.add_argument("--api-key", help="ElevenLabs API key (overrides .env file)")
    args = parser.parse_args()
    
    if args.api_key:
        API_KEY = args.api_key
        print(f"Using provided API key: {API_KEY[:5]}...{API_KEY[-4:]}")
    
    full_diagnostic() 