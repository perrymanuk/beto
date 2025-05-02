"""
Example of specialized Home Assistant domain interactions.

This example demonstrates how to work with specific Home Assistant domains
through the Model Context Protocol (MCP), focusing on common domains like
lights, sensors, climate devices, and media players.
"""

import os
import uuid
import logging
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from radbot.tools.mcp_tools import create_home_assistant_toolset, create_ha_mcp_enabled_agent
from radbot.tools.mcp_utils import (
    test_home_assistant_connection, 
    list_home_assistant_domains,
    check_home_assistant_entity
)
from radbot.agent.agent import AgentFactory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class HomeAssistantDomainExamples:
    """
    Class containing examples of interactions with different Home Assistant domains.
    """
    
    def __init__(self):
        """Initialize the Home Assistant connection and tools."""
        # Test Home Assistant connection
        self.ha_connection = test_home_assistant_connection()
        
        if not self.ha_connection["success"]:
            print(f"❌ Failed to connect to Home Assistant: {self.ha_connection.get('error', 'Unknown error')}")
            self.ha_toolset = None
            return
            
        # Create Home Assistant MCP toolset
        self.ha_toolset = create_home_assistant_toolset()
        
        if not self.ha_toolset:
            print("❌ Failed to create Home Assistant toolset")
            return
            
        print("✅ Successfully connected to Home Assistant MCP")
        
        # Get available domains
        domains_result = list_home_assistant_domains()
        if domains_result["success"]:
            self.available_domains = domains_result["domains"]
            print(f"Available domains: {', '.join(self.available_domains)}")
        else:
            self.available_domains = []
            print("❌ Failed to retrieve available domains")
    
    def is_connected(self) -> bool:
        """Check if Home Assistant is connected."""
        return self.ha_toolset is not None and self.ha_connection["success"]
    
    def check_domain(self, domain: str) -> bool:
        """Check if a specific domain is available."""
        return domain in self.available_domains
    
    def list_domain_entities(self, domain: str) -> List[str]:
        """
        List all entities for a specific domain.
        
        Args:
            domain: The Home Assistant domain (e.g., 'light', 'switch')
            
        Returns:
            List of entity IDs belonging to the domain
        """
        if not self.is_connected():
            print("❌ Home Assistant not connected")
            return []
            
        if not self.check_domain(domain):
            print(f"❌ Domain '{domain}' not available")
            return []
            
        # List entities for the domain by examining tool structure
        # In a real implementation, we would use a dedicated API for this
        entities = []
        try:
            # Assume entities are stored in the toolset or can be queried
            # This is a simplified approach - in real use, you would query HA directly
            # through the MCP, which may involve examining the API exposed by
            # the Home Assistant MCP server
            
            tool_names = []
            if hasattr(self.ha_toolset, 'list_tools') and callable(getattr(self.ha_toolset, 'list_tools')):
                tool_names = self.ha_toolset.list_tools()
            elif hasattr(self.ha_toolset, '_tools') and self.ha_toolset._tools:
                tool_names = list(self.ha_toolset._tools.keys())
            
            # For demonstration purposes, we're assuming entities are exposed in the API
            # In a real implementation, you'd use the appropriate API method
            
            print(f"Found {len(tool_names)} tools for domain '{domain}'")
            return tool_names
            
        except Exception as e:
            logger.error(f"Error listing entities for domain {domain}: {str(e)}")
            return []
    
    def light_domain_examples(self):
        """Examples of interacting with the light domain."""
        if not self.check_domain("light"):
            print("❌ Light domain not available")
            return
        
        print("\n=== Light Domain Examples ===")
        
        # Example 1: List lights
        print("\n1. Listing lights...")
        agent = create_agent_for_domain("light")
        if agent:
            response = agent.process_message(
                user_id="domain_examples",
                message="What lights do I have available?"
            )
            print(f"Agent: {response}")
            
            # Example 2: Get light state
            print("\n2. Getting light state...")
            response = agent.process_message(
                user_id="domain_examples",
                message="Is the living room light on?"
            )
            print(f"Agent: {response}")
            
            # Example 3: Control lights
            print("\n3. Controlling lights...")
            response = agent.process_message(
                user_id="domain_examples",
                message="Turn on the kitchen light at 50% brightness with a warm white color"
            )
            print(f"Agent: {response}")
            
            # Allow time to see the effect
            time.sleep(2)
            
            print("\n4. Creating a light scene...")
            response = agent.process_message(
                user_id="domain_examples",
                message="Set all living room lights to a relaxing evening scene"
            )
            print(f"Agent: {response}")
    
    def climate_domain_examples(self):
        """Examples of interacting with the climate domain."""
        if not self.check_domain("climate"):
            print("❌ Climate domain not available")
            return
        
        print("\n=== Climate Domain Examples ===")
        
        # Example 1: List climate devices
        print("\n1. Listing climate devices...")
        agent = create_agent_for_domain("climate")
        if agent:
            response = agent.process_message(
                user_id="domain_examples",
                message="What climate devices do I have?"
            )
            print(f"Agent: {response}")
            
            # Example 2: Get current temperature
            print("\n2. Getting current temperature...")
            response = agent.process_message(
                user_id="domain_examples",
                message="What's the current temperature in the bedroom?"
            )
            print(f"Agent: {response}")
            
            # Example 3: Set temperature
            print("\n3. Setting temperature...")
            response = agent.process_message(
                user_id="domain_examples",
                message="Set the living room thermostat to 22 degrees"
            )
            print(f"Agent: {response}")
    
    def sensor_domain_examples(self):
        """Examples of interacting with the sensor domain."""
        if not self.check_domain("sensor"):
            print("❌ Sensor domain not available")
            return
        
        print("\n=== Sensor Domain Examples ===")
        
        # Example 1: List sensors
        print("\n1. Listing sensors...")
        agent = create_agent_for_domain("sensor")
        if agent:
            response = agent.process_message(
                user_id="domain_examples",
                message="What sensors do I have in my home?"
            )
            print(f"Agent: {response}")
            
            # Example 2: Get sensor readings
            print("\n2. Getting sensor readings...")
            response = agent.process_message(
                user_id="domain_examples",
                message="What's the humidity level in the bathroom?"
            )
            print(f"Agent: {response}")
            
            print("\n3. Getting energy consumption...")
            response = agent.process_message(
                user_id="domain_examples",
                message="How much power is my home using right now?"
            )
            print(f"Agent: {response}")
    
    def media_player_domain_examples(self):
        """Examples of interacting with the media_player domain."""
        if not self.check_domain("media_player"):
            print("❌ Media player domain not available")
            return
        
        print("\n=== Media Player Domain Examples ===")
        
        # Example 1: List media players
        print("\n1. Listing media players...")
        agent = create_agent_for_domain("media_player")
        if agent:
            response = agent.process_message(
                user_id="domain_examples",
                message="What media players do I have available?"
            )
            print(f"Agent: {response}")
            
            # Example 2: Control media player
            print("\n2. Controlling media player...")
            response = agent.process_message(
                user_id="domain_examples",
                message="Play some jazz music in the living room"
            )
            print(f"Agent: {response}")
            
            # Allow time to see the effect
            time.sleep(2)
            
            print("\n3. Getting media player state...")
            response = agent.process_message(
                user_id="domain_examples",
                message="What's currently playing on the TV?"
            )
            print(f"Agent: {response}")
    
    def run_all_examples(self):
        """Run examples for all available domains."""
        if not self.is_connected():
            print("❌ Home Assistant not connected, cannot run examples")
            return
        
        # Run examples for each domain if available
        if self.check_domain("light"):
            self.light_domain_examples()
        
        if self.check_domain("climate"):
            self.climate_domain_examples()
        
        if self.check_domain("sensor"):
            self.sensor_domain_examples()
        
        if self.check_domain("media_player"):
            self.media_player_domain_examples()
        
        print("\n=== Additional Domains ===")
        for domain in self.available_domains:
            if domain not in ["light", "climate", "sensor", "media_player"]:
                print(f"- {domain}")

def create_agent_for_domain(target_domain=None):
    """
    Create an agent with focus on a specific Home Assistant domain.
    
    Args:
        target_domain: Optional domain to focus on (e.g., 'light', 'climate')
        
    Returns:
        An agent with Home Assistant capabilities
    """
    try:
        # Create Home Assistant toolset
        ha_toolset = create_home_assistant_toolset()
        if not ha_toolset:
            print("❌ Failed to create Home Assistant toolset")
            return None
        
        # Create the agent
        print(f"Creating agent{' for ' + target_domain + ' domain' if target_domain else ''}")
        agent = AgentFactory.create_root_agent(tools=[ha_toolset])
        
        if not agent:
            print("❌ Failed to create agent")
            return None
            
        return agent
        
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return None

def interactive_domain_explorer():
    """Interactive explorer for Home Assistant domains."""
    # Initialize example class
    examples = HomeAssistantDomainExamples()
    
    if not examples.is_connected():
        print("\nRunning in simulated mode since Home Assistant connection failed.")
    
    print("\n=== Home Assistant Domain Explorer ===")
    print("This tool lets you explore and test different Home Assistant domains")
    
    # Main loop
    while True:
        print("\nOptions:")
        print("1. List available domains")
        print("2. Explore a specific domain")
        print("3. Run examples for all domains")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ")
        
        if choice == "1":
            if examples.available_domains:
                print("\nAvailable domains:")
                for domain in examples.available_domains:
                    print(f"- {domain}")
            else:
                print("\nNo domains available or Home Assistant not connected.")
                
        elif choice == "2":
            domain = input("\nEnter domain name (e.g., light, sensor): ")
            if examples.check_domain(domain):
                print(f"\nExploring {domain} domain...")
                
                if domain == "light":
                    examples.light_domain_examples()
                elif domain == "climate":
                    examples.climate_domain_examples()
                elif domain == "sensor":
                    examples.sensor_domain_examples()
                elif domain == "media_player":
                    examples.media_player_domain_examples()
                else:
                    print(f"Domain '{domain}' is available but no specific examples are defined.")
                    # Create a generic agent for testing this domain
                    agent = create_agent_for_domain()
                    if agent:
                        print("\nCreated a generic agent. You can interact with it below.")
                        print("Type 'exit' to return to the main menu.")
                        
                        # Mini session with the agent
                        session_id = str(uuid.uuid4())
                        while True:
                            user_input = input("\nYou: ")
                            if user_input.lower() == "exit":
                                break
                                
                            try:
                                response = agent.process_message(
                                    user_id=session_id,
                                    message=user_input
                                )
                                print(f"Agent: {response}")
                            except Exception as e:
                                print(f"Error: {str(e)}")
            else:
                print(f"\nDomain '{domain}' is not available.")
                
        elif choice == "3":
            examples.run_all_examples()
            
        elif choice == "4":
            print("\nExiting domain explorer.")
            break
            
        else:
            print("\nInvalid choice. Please enter a number between 1 and 4.")

def main():
    """Run the Home Assistant domain examples."""
    print("=" * 60)
    print("Home Assistant Domain Examples".center(60))
    print("=" * 60)
    
    # Run the interactive explorer
    interactive_domain_explorer()

if __name__ == "__main__":
    main()