#!/usr/bin/env python3
"""
Simple test script to directly test Crawl4AI API.
"""

import os
import requests
import json
from pprint import pprint

def test_crawl4ai_direct():
    """Test direct API call to Crawl4AI."""
    print("\n=== Testing Crawl4AI Direct API Call ===\n")
    
    # Define test URL - using the URL that's failing
    test_url = "https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/"
    
    # API configuration
    api_url = os.environ.get("CRAWL4AI_API_URL", "https://crawl4ai.demonsafe.com")
    api_token = os.environ.get("CRAWL4AI_API_TOKEN", "")
    
    print(f"Using API URL: {api_url}")
    print(f"Testing URL: {test_url}")
    
    # Setup request
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        print("Using API token for authentication")
    else:
        print("No API token provided")
    
    # Test base API connectivity
    try:
        print("\n--- Testing API connectivity ---")
        response = requests.get(f"{api_url}/", headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ API connection successful: {response.status_code}")
            try:
                print("API info:", response.json())
            except:
                print("Response not JSON:", response.text[:100])
        else:
            print(f"❌ API connection failed: {response.status_code}")
            print("Response:", response.text[:200])
    except Exception as e:
        print(f"❌ Error connecting to API: {str(e)}")
    
    # Try the markdown endpoint
    try:
        print("\n--- Testing markdown generation ---")
        
        # Prepare payload
        payload = {
            "url": test_url,
            "filter_type": "all",
            "markdown_flavor": "github"
        }
        
        print("Sending request with payload:")
        pprint(payload)
        
        # Make the request
        response = requests.post(f"{api_url}/md", headers=headers, json=payload, timeout=120)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Markdown request successful")
            
            try:
                result = response.json()
                print("Response keys:", list(result.keys()))
                
                if "content" in result:
                    content_length = len(result["content"])
                    print(f"Content found! Length: {content_length} characters")
                    
                    if content_length > 0:
                        print("\nContent preview (first 200 chars):")
                        print(result["content"][:200])
                        print("...")
                        
                        # Save to file for inspection
                        filename = "crawl4ai_response.md"
                        with open(filename, "w") as f:
                            f.write(result["content"])
                        print(f"\nFull content saved to {filename}")
                    else:
                        print("⚠️ Content is empty (zero length)")
                        print("\nFull response:")
                        pprint(result)
                else:
                    print("❌ No 'content' key in response")
                    print("\nFull response:")
                    pprint(result)
            except json.JSONDecodeError:
                print("❌ Invalid JSON response:")
                print(response.text[:500])
        else:
            print(f"❌ Markdown request failed: {response.status_code}")
            print("Response text:")
            print(response.text[:500])
    except Exception as e:
        print(f"❌ Error during markdown request: {str(e)}")

if __name__ == "__main__":
    test_crawl4ai_direct()