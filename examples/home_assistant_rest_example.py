"""
Example for Home Assistant REST API integration with radbot.

This example demonstrates creating an agent with Home Assistant capabilities
using the REST API integration.
"""

import os
import uuid
import logging
from typing import Dict, Any

from dotenv import load_dotenv

from radbot.config.settings import ConfigManager
from radbot.tools.basic_tools import get_current_time, get_weather
from radbot.tools.ha_rest_client import HomeAssistantClient
from radbot.agent.agent import AgentFactory
# Import the factory directly
from radbot.agent.home_assistant_agent_factory import create_home_assistant_enabled_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_home_assistant_connection() -> Dict[str, Any]:
    """
    Test the connection to Home Assistant's REST API.
    
    Returns:
        Dictionary with connection test results
    """
    # Get Home Assistant configuration
    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")
    
    if not ha_url or not ha_token:
        return {
            "success": False,
            "error": "Missing HA_URL or HA_TOKEN environment variables"
        }
    
    try:
        # Create a client instance
        client = HomeAssistantClient(ha_url, ha_token)
        
        # Test API status
        if client.get_api_status():
            # Get some entity states
            entities = client.list_entities()
            if entities is None:
                return {
                    "success": False,
                    "error": "Failed to retrieve entities"
                }
            
            # Count entities by domain
            domains = {}
            for entity in entities:
                entity_id = entity.get('entity_id', '')
                if '.' in entity_id:
                    domain = entity_id.split('.')[0]
                    domains[domain] = domains.get(domain, 0) + 1
            
            return {
                "success": True,
                "entity_count": len(entities),
                "domains": domains
            }
        else:
            return {
                "success": False,
                "error": "Failed to connect to Home Assistant API"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Run the Home Assistant REST API integration example."""
    print("=" * 60)
    print("Home Assistant REST API Integration Example".center(60))
    print("=" * 60)
    
    # Test Home Assistant connection
    print("\nTesting Home Assistant connection...")
    test_result = test_home_assistant_connection()
    
    if test_result["success"]:
        print(f"✅ Connected to Home Assistant")
        print(f"Found {test_result['entity_count']} entities")
        print("Domains found:")
        for domain, count in test_result["domains"].items():
            print(f"  - {domain}: {count} entities")
    else:
        print(f"❌ Failed to connect to Home Assistant")
        print(f"Error: {test_result.get('error', 'Unknown error')}")
        print("\nPlease check your environment variables:")
        print("  - HA_URL: URL of your Home Assistant instance (e.g., http://your-ha-ip:8123)")
        print("  - HA_TOKEN: Long-lived access token for authentication")
        return
    
    # Create agent with Home Assistant integration
    print("\nCreating agent with Home Assistant REST API integration...")
    try:
        # Create the agent with Home Assistant capabilities
        agent = create_home_assistant_enabled_agent(
            agent_factory=AgentFactory.create_root_agent,
            base_tools=[get_current_time, get_weather]
        )
        
        print("✅ Agent created successfully")
        
        # Start interactive chat loop
        session_id = str(uuid.uuid4())
        print("\nInteractive chat session started. Type 'exit' to quit.")
        print("\nExample queries:")
        print("  - What devices do I have in the kitchen?")
        print("  - Turn on the living room light")
        print("  - What's the temperature in the bedroom?")
        print("  - Toggle the office lamp")
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() == "exit":
                break
            
            # Process the message
            try:
                print("\nProcessing...")
                response = agent.process_message(user_id=session_id, message=user_input)
                print(f"\nAgent: {response}")
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    except Exception as e:
        print(f"❌ Failed to create agent: {str(e)}")
        return
    
if __name__ == "__main__":
    main()