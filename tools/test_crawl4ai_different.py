#!/usr/bin/env python
"""
Test alternative approaches to connect to the Crawl4AI server.
This script tries different URL patterns and request formats.
"""

import os
import sys
import logging
import requests
import json
import uuid
from urllib.parse import urljoin, urlparse

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_server_endpoints():
    """Test different URL formats and request methods."""
    base_url = "https://crawl4ai.demonsafe.com"
    
    # Try to discover endpoints
    patterns = [
        "/mcp/sse",
        "/api/crawl",
        "/api/sse",
        "/api/mcp",
        "/api",
        "/v1",
        "",
    ]
    
    # Headers to try
    headers_options = [
        {"Content-Type": "application/json", "Accept": "application/json"},
        {"Content-Type": "application/json", "Accept": "*/*"},
        {"Content-Type": "application/json", "Accept": "text/event-stream"},
        {"X-Debug": "true", "Content-Type": "application/json"}
    ]
    
    # Different payload formats
    payload_options = [
        {  # Standard JSON-RPC
            "jsonrpc": "2.0",
            "method": "invoke",
            "params": {
                "name": "crawl4ai_crawl",
                "arguments": {"url": "https://github.com/google/adk-samples"}
            },
            "id": str(uuid.uuid4())
        },
        {  # Simplified format
            "name": "crawl4ai_crawl",
            "arguments": {"url": "https://github.com/google/adk-samples"}
        },
        {  # Alternative format
            "tool": "crawl4ai_crawl",
            "params": {"url": "https://github.com/google/adk-samples"}
        },
        # Direct query parameter approach will be tried separately
    ]
    
    # Try different methods
    methods = ["POST", "GET"]
    
    # First, try simple GET requests to discover endpoints
    logger.info("Discovering endpoints with GET requests...")
    for pattern in patterns:
        endpoint = urljoin(base_url, pattern)
        try:
            response = requests.get(endpoint, timeout=10)
            logger.info(f"GET {endpoint}: Status {response.status_code}, Headers: {dict(response.headers)}")
            logger.info(f"  Content: {response.text[:200]}...")
        except Exception as e:
            logger.error(f"Error with GET request to {endpoint}: {e}")
    
    # Test different combinations of methods, headers, and payload formats
    logger.info("\nTesting different request combinations...")
    for pattern in patterns:
        endpoint = urljoin(base_url, pattern)
        for method in methods:
            for headers in headers_options:
                if method == "GET":
                    # For GET, try with query parameters
                    query_params = {"tool": "crawl4ai_crawl", "url": "https://github.com/google/adk-samples"}
                    try:
                        response = requests.get(endpoint, params=query_params, headers=headers, timeout=10)
                        logger.info(f"GET {endpoint} (with query params): Status {response.status_code}")
                        if response.status_code < 400:
                            logger.info(f"  Headers: {dict(response.headers)}")
                            logger.info(f"  Content: {response.text[:200]}...")
                    except Exception as e:
                        logger.error(f"Error with GET request to {endpoint}: {e}")
                else:
                    # For POST, try different payload formats
                    for payload in payload_options:
                        try:
                            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                            logger.info(f"POST {endpoint}: Status {response.status_code}")
                            if response.status_code < 400:
                                logger.info(f"  Headers: {dict(response.headers)}")
                                logger.info(f"  Content: {response.text[:200]}...")
                        except Exception as e:
                            logger.error(f"Error with POST request to {endpoint}: {e}")
    
    # Try specific endpoints for the crawl4ai server based on common patterns
    specific_endpoints = [
        "/mcp/sse/crawl",
        "/api/crawl",
        "/api/firecrawl/crawl",
        "/firecrawl/crawl"
    ]
    
    logger.info("\nTesting crawl-specific endpoints...")
    for endpoint_path in specific_endpoints:
        endpoint = urljoin(base_url, endpoint_path)
        try:
            # Try basic GET request
            response = requests.get(endpoint, timeout=10)
            logger.info(f"GET {endpoint}: Status {response.status_code}")
            if response.status_code < 400:
                logger.info(f"  Headers: {dict(response.headers)}")
                logger.info(f"  Content: {response.text[:200]}...")
            
            # Try GET with query params
            query_params = {"url": "https://github.com/google/adk-samples"}
            response = requests.get(endpoint, params=query_params, timeout=10)
            logger.info(f"GET {endpoint} (with URL param): Status {response.status_code}")
            if response.status_code < 400:
                logger.info(f"  Headers: {dict(response.headers)}")
                logger.info(f"  Content: {response.text[:200]}...")
            
            # Try POST with minimal JSON
            response = requests.post(
                endpoint, 
                json={"url": "https://github.com/google/adk-samples"}, 
                headers={"Content-Type": "application/json"}, 
                timeout=10
            )
            logger.info(f"POST {endpoint} (simple JSON): Status {response.status_code}")
            if response.status_code < 400:
                logger.info(f"  Headers: {dict(response.headers)}")
                logger.info(f"  Content: {response.text[:200]}...")
        except Exception as e:
            logger.error(f"Error with requests to {endpoint}: {e}")

if __name__ == "__main__":
    test_server_endpoints()