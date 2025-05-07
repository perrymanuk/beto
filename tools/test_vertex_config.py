#!/usr/bin/env python3
"""
Test script for Vertex AI configuration and integration.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radbot.config.config_loader import config_loader
from radbot.config.settings import ConfigManager
from radbot.config.adk_config import setup_vertex_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vertex_config():
    """Test Vertex AI configuration."""
    print("\n=== Testing Vertex AI Configuration ===")
    
    # Get the agent configuration
    agent_config = config_loader.get_agent_config()
    
    # Check Vertex AI settings
    use_vertex_ai = agent_config.get("use_vertex_ai", False)
    vertex_project = agent_config.get("vertex_project")
    vertex_location = agent_config.get("vertex_location", "us-central1")
    
    print(f"Use Vertex AI: {use_vertex_ai}")
    print(f"Vertex Project: {vertex_project}")
    print(f"Vertex Location: {vertex_location}")
    
    # Check using ConfigManager
    config = ConfigManager()
    print(f"\nConfigManager.is_using_vertex_ai(): {config.is_using_vertex_ai()}")
    print(f"ConfigManager.get_vertex_project(): {config.get_vertex_project()}")
    print(f"ConfigManager.get_vertex_location(): {config.get_vertex_location()}")
    
    # If Vertex AI is enabled, try to set up the environment
    if use_vertex_ai:
        print("\nTesting Vertex AI environment setup...")
        try:
            result = setup_vertex_environment()
            if result:
                print(f"✅ Successfully set up Vertex AI environment")
                print(f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
                print(f"GOOGLE_CLOUD_LOCATION: {os.environ.get('GOOGLE_CLOUD_LOCATION')}")
                print(f"GOOGLE_GENAI_USE_VERTEXAI: {os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')}")
                
                # Try to use the google-genai client directly
                try:
                    from google.genai.client import Client
                    client = Client(
                        vertexai=True,
                        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
                        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
                    )
                    print(f"✅ Successfully created Vertex AI client")
                    
                    # Check if client can get a model
                    try:
                        model = client.get_model("gemini-2.5-pro")
                        print(f"Model: {model.model_name}")
                        print("✅ Model access successful")
                    except Exception as e:
                        print(f"❌ Error accessing model: {str(e)}")
                except Exception as e:
                    print(f"❌ Error creating Vertex AI client: {str(e)}")
            else:
                print("❌ Failed to set up Vertex AI environment")
        except Exception as e:
            print(f"❌ Error setting up Vertex AI environment: {str(e)}")
    else:
        print("\nVertex AI is disabled, skipping environment setup test")

def main():
    print("Testing Vertex AI Configuration")
    print("===============================")
    
    try:
        test_vertex_config()
        print("\nAll tests completed!")
        return 0
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())