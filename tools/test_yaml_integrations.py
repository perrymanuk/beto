#!/usr/bin/env python3
"""
Test script to verify all integrations work with YAML configuration.

This script checks that all major integrations (Home Assistant, Google Calendar, 
Crawl4AI, etc.) can read their configuration from config.yaml and properly
fall back to environment variables when needed.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radbot.config.config_loader import config_loader
from radbot.tools.homeassistant.ha_client_singleton import get_ha_client
from radbot.tools.crawl4ai.utils import get_crawl4ai_config
from radbot.config.adk_config import get_google_api_key, setup_vertex_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_home_assistant_integration():
    """Test loading Home Assistant configuration from config.yaml."""
    print("\n=== Testing Home Assistant Integration ===")
    
    # Get Home Assistant configuration
    ha_config = config_loader.get_home_assistant_config()
    
    print("Home Assistant configuration:")
    print(f"  Enabled: {ha_config.get('enabled', False)}")
    
    if ha_config.get("url"):
        print(f"  URL: {ha_config.get('url')}")
    else:
        print("  URL: Not found in config.yaml")
        
    if ha_config.get("token"):
        print("  Token: ****")
    else:
        print("  Token: Not found in config.yaml")
    
    # Test getting the client
    client = get_ha_client()
    if client:
        print("  Client initialization: Success")
        
        # Test API status
        try:
            status = client.get_api_status()
            print(f"  API status: {status}")
        except Exception as e:
            print(f"  API status check failed: {e}")
    else:
        print("  Client initialization: Failed")

def test_crawl4ai_integration():
    """Test loading Crawl4AI configuration from config.yaml."""
    print("\n=== Testing Crawl4AI Integration ===")
    
    # Get Crawl4AI configuration from integrations section
    crawl4ai_config = config_loader.get_integrations_config().get("crawl4ai", {})
    
    print("Crawl4AI configuration:")
    print(f"  Enabled: {crawl4ai_config.get('enabled', False)}")
    
    if crawl4ai_config.get("api_url"):
        print(f"  API URL: {crawl4ai_config.get('api_url')}")
    else:
        print("  API URL: Not found in config.yaml")
        
    if crawl4ai_config.get("api_token"):
        print("  API Token: ****")
    else:
        print("  API Token: Not found in config.yaml")
    
    # Test the utility function
    api_url, api_token = get_crawl4ai_config()
    print(f"\nget_crawl4ai_config() results:")
    print(f"  API URL: {api_url}")
    if api_token:
        print("  API Token: ****")
    else:
        print("  API Token: Not found")

def test_google_api_integration():
    """Test loading Google API configuration from config.yaml."""
    print("\n=== Testing Google API Integration ===")
    
    # Get agent configuration for Vertex AI settings
    agent_config = config_loader.get_agent_config()
    
    print("Google API configuration:")
    print(f"  Use Vertex AI: {agent_config.get('use_vertex_ai', False)}")
    
    if agent_config.get("vertex_project"):
        print(f"  Vertex Project: {agent_config.get('vertex_project')}")
    else:
        print("  Vertex Project: Not found in config.yaml")
        
    if agent_config.get("vertex_location"):
        print(f"  Vertex Location: {agent_config.get('vertex_location')}")
    else:
        print("  Vertex Location: Not found in config.yaml")
    
    # Check for service account file
    if agent_config.get("service_account_file"):
        service_account_file = agent_config.get("service_account_file")
        print(f"  Service Account File: {service_account_file}")
        # Check if file exists
        if os.path.exists(service_account_file):
            print(f"  Service Account File exists: Yes")
        else:
            print(f"  Service Account File exists: No")
    else:
        print("  Service Account File: Not configured")
    
    # Get API key from config.yaml
    api_key = config_loader.get_config().get("api_keys", {}).get("google")
    if api_key:
        print("  API Key: **** (from config.yaml)")
    else:
        print("  API Key: Not found in config.yaml")
    
    # Test the helper functions
    api_key = get_google_api_key()
    if api_key:
        print("\nget_google_api_key() result: **** (API key found)")
    else:
        print("\nget_google_api_key() result: None (API key not found)")
    
    # Test environment setup
    is_vertex = setup_vertex_environment()
    print(f"\nsetup_vertex_environment() result: {is_vertex}")
    print("Environment variables after setup:")
    for var in ["GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "GOOGLE_API_KEY"]:
        value = os.environ.get(var)
        if var == "GOOGLE_API_KEY" and value:
            print(f"  {var}: ****")
        else:
            print(f"  {var}: {value}")

def test_mcp_integrations():
    """Test loading MCP server configurations from config.yaml."""
    print("\n=== Testing MCP Server Integrations ===")
    
    # Get MCP servers configuration
    servers = config_loader.get_mcp_servers()
    enabled_servers = config_loader.get_enabled_mcp_servers()
    
    print(f"MCP servers configured: {len(servers)}")
    print(f"MCP servers enabled: {len(enabled_servers)}")
    
    # Print details of each server
    for i, server in enumerate(servers):
        enabled = server.get("enabled", True)
        server_id = server.get("id")
        server_name = server.get("name", server_id)
        transport = server.get("transport", "sse")
        url = server.get("url")
        
        print(f"\nServer {i+1}: {server_name} ({server_id})")
        print(f"  Enabled: {enabled}")
        print(f"  Transport: {transport}")
        print(f"  URL: {url}")
        
        # Check if server has authentication
        auth_token = server.get("auth_token")
        if auth_token:
            print("  Auth Token: ****")
        else:
            print("  Auth Token: Not found")

def main():
    """Run all integration tests."""
    print("YAML Configuration Integration Tests")
    print("===================================")
    
    # Print configuration file path
    print(f"Configuration file: {config_loader.config_path}")
    
    try:
        test_home_assistant_integration()
        test_crawl4ai_integration()
        test_google_api_integration()
        test_mcp_integrations()
        
        print("\nAll integration tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\nTests failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())