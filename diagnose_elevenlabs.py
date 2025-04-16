#!/usr/bin/env python
"""
Diagnostic script to explore ElevenLabs API and find knowledge base information.
"""
import os
import json
import requests
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

print(f"Using API key: {API_KEY[:5]}...{API_KEY[-4:]}")

def print_response(title, response):
    """Print formatted API response"""
    print("\n" + "="*80)
    print(f"{title} - Status Code: {response.status_code}")
    print("="*80)
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
            return data
        except ValueError:
            print("Response is not JSON format:")
            print(response.text)
    else:
        print(f"Error: {response.text}")
    return None

# 1. Get User Information
print("\n🔍 Checking user information...")
user_response = requests.get("https://api.elevenlabs.io/v1/user", headers=headers)
print_response("USER INFO", user_response)

# 2. List Projects (if the API supports projects)
print("\n🔍 Checking for projects...")
projects_response = requests.get("https://api.elevenlabs.io/v1/projects", headers=headers)
projects = print_response("PROJECTS", projects_response)

# 3. Try accessing knowledge bases directly
print("\n🔍 Checking for knowledge bases...")
kb_response = requests.get("https://api.elevenlabs.io/v1/knowledge-bases", headers=headers)
knowledge_bases = print_response("KNOWLEDGE BASES", kb_response)

# 4. Try v2 API version if it exists
print("\n🔍 Trying v2 API for knowledge bases...")
kb_v2_response = requests.get("https://api.elevenlabs.io/v2/knowledge-bases", headers=headers)
print_response("V2 KNOWLEDGE BASES", kb_v2_response)

# 5. Exploring alternative endpoints
endpoints_to_try = [
    "https://api.elevenlabs.io/v1/knowledge-base",
    "https://api.elevenlabs.io/v1/knowledge-bases/files"
]

for endpoint in endpoints_to_try:
    print(f"\n🔍 Trying endpoint: {endpoint}")
    response = requests.get(endpoint, headers=headers)
    print_response(f"ENDPOINT: {endpoint}", response)

print("\n" + "="*80)
print("DIAGNOSTIC SUMMARY")
print("="*80)
print("Based on these results, look for:")
print("1. Project IDs (if projects were found)")
print("2. Knowledge Base IDs (if any were found)")
print("3. The correct API endpoint structure")
print("\nUse this information to update your scraper's API endpoints.") 