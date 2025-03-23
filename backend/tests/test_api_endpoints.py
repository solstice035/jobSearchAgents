#!/usr/bin/env python3
"""
Test script for the API endpoints.

This script tests the Career Coach API endpoints by making HTTP requests to the local server.
"""

import sys
import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API base URL
BASE_URL = "http://localhost:5001/api"

def test_api_endpoints():
    """Test the Career Coach API endpoints."""
    try:
        print("Testing API endpoints...")
        
        # 1. Health check
        print("\nTesting health check endpoint...")
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"Error: Health check failed with status code {response.status_code}")
            print(response.text)
            return
        
        print("Health check succeeded:")
        print(json.dumps(response.json(), indent=2))
        
        # 2. Create session
        print("\nCreating a coaching session...")
        response = requests.post(f"{BASE_URL}/career-coach/sessions", json={"user_id": "test_user_api"})
        if response.status_code != 201:
            print(f"Error: Create session failed with status code {response.status_code}")
            print(response.text)
            return
        
        print("Session created:")
        print(json.dumps(response.json(), indent=2))
        
        # Extract session ID
        session_id = response.json()["session_id"]
        
        # 3. Send a message
        print("\nSending a message...")
        message = "Hi, I'm a software developer with 5 years of experience. I'm looking to advance my career and possibly move into a leadership role."
        response = requests.post(f"{BASE_URL}/career-coach/sessions/{session_id}/messages", json={"message": message})
        if response.status_code != 200:
            print(f"Error: Send message failed with status code {response.status_code}")
            print(response.text)
            return
        
        print("Message sent:")
        print(f"Response: {response.json()['response'][:200]}...")
        
        # 4. Get session summary
        print("\nGetting session summary...")
        response = requests.get(f"{BASE_URL}/career-coach/sessions/{session_id}")
        if response.status_code != 200:
            print(f"Error: Get session summary failed with status code {response.status_code}")
            print(response.text)
            return
        
        print("Session summary:")
        print(json.dumps(response.json()["summary"], indent=2))
        
        print("\nAPI endpoint tests completed successfully!")
    
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the API server at {BASE_URL}")
        print("Make sure the Flask server is running.")
    except Exception as e:
        print(f"Error testing API endpoints: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()
