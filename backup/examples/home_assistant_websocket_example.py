"""
Example script showcasing the Home Assistant WebSocket integration.

This script demonstrates how to use the new WebSocket-based Home Assistant
integration by setting up a connection, querying entities, and controlling them.
"""

import asyncio
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from google import generativeai as genai
from google.generativeai.types import FunctionResponse

from radbot.tools.ha_websocket_client import HomeAssistantWebsocketClient
from radbot.tools.ha_state_cache import HomeAssistantStateCache
from radbot.tools.ha_tool_schemas import get_home_assistant_tool_schemas
from radbot.tools.ha_tools_impl import (
    get_home_assistant_entity_state,
    call_home_assistant_service,
    search_home_assistant_entities,
    get_home_assistant_entities_by_domain,
    get_home_assistant_domains,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global variables
state_cache = HomeAssistantStateCache()
ws_client = None

# Tool function mapping
tool_functions = {
    "get_home_assistant_entity_state": get_home_assistant_entity_state,
    "call_home_assistant_service": call_home_assistant_service,
    "search_home_assistant_entities": search_home_assistant_entities,
    "get_home_assistant_entities_by_domain": get_home_assistant_entities_by_domain,
    "get_home_assistant_domains": get_home_assistant_domains,
}

async def update_state_callback(event_data: Dict[str, Any]) -> None:
    """Callback function to update the state cache."""
    await state_cache.update_state(event_data)

async def setup_home_assistant():
    """Set up the Home Assistant WebSocket client and state cache."""
    global ws_client
    
    # Get configuration from environment variables
    ha_url = os.getenv("HA_WEBSOCKET_URL")
    ha_token = os.getenv("HA_WEBSOCKET_TOKEN")
    
    # Fall back to legacy environment variables if needed
    if not ha_url and os.getenv("HA_MCP_SSE_URL"):
        logger.info("Using derived WebSocket URL from MCP URL")
        mcp_url = os.getenv("HA_MCP_SSE_URL")
        base_url = mcp_url
        if "/mcp_server/sse" in base_url:
            base_url = base_url.split("/mcp_server/sse")[0]
        elif "/api/mcp_server/sse" in base_url:
            base_url = base_url.split("/api/mcp_server/sse")[0]
            
        # Convert http/https to ws/wss
        if base_url.startswith("http://"):
            base_url = base_url.replace("http://", "ws://")
        elif base_url.startswith("https://"):
            base_url = base_url.replace("https://", "wss://")
            
        ha_url = f"{base_url}/api/websocket"
        
    if not ha_token and os.getenv("HA_AUTH_TOKEN"):
        logger.info("Using token from HA_AUTH_TOKEN environment variable")
        ha_token = os.getenv("HA_AUTH_TOKEN")
    
    if not ha_url or not ha_token:
        raise ValueError(
            "Missing Home Assistant WebSocket configuration. "
            "Please set HA_WEBSOCKET_URL and HA_WEBSOCKET_TOKEN environment variables."
        )
    
    # Create and start the WebSocket client
    ws_client = HomeAssistantWebsocketClient(
        url=ha_url,
        token=ha_token,
        event_callback=update_state_callback
    )
    
    await ws_client.start()
    logger.info("Home Assistant WebSocket client started")
    
    # Give the client a moment to connect and receive initial states
    logger.info("Waiting for initial state updates...")
    await asyncio.sleep(5)
    
    # Check if we have received any states
    states = await state_cache.get_states()
    domain_count = len(await state_cache.get_domains())
    entity_count = await state_cache.count_entities()
    logger.info(f"Received {entity_count} entities in {domain_count} domains")
    
    return entity_count > 0

async def cleanup_home_assistant():
    """Clean up the Home Assistant WebSocket client."""
    global ws_client
    if ws_client:
        await ws_client.stop()
        logger.info("Home Assistant WebSocket client stopped")

async def run_interactive_agent():
    """Run an interactive agent that can control Home Assistant."""
    # Set up Google Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY environment variable")
    
    genai.configure(api_key=api_key)
    
    # Create the model with Home Assistant tools
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[get_home_assistant_tool_schemas()]
    )
    
    # Start a chat session
    chat = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": ["You are a helpful assistant that can control my smart home using Home Assistant."]
            },
            {
                "role": "model",
                "parts": ["I'm ready to help you control your smart home through Home Assistant! I can check on the status of your devices, turn things on or off, adjust settings, and more. What would you like to do with your smart home today?"]
            }
        ]
    )
    
    print("\n=== Home Assistant Assistant ===")
    print("Type 'exit' to quit.")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        print("Assistant is thinking...")
        
        # Send user input to model
        response = await chat.send_message_async(user_input)
        
        # Check if response contains a function call
        candidate = response.candidates[0]
        content = candidate.content
        
        # Process function calls until we get a text response
        while hasattr(content.parts[0], 'function_call'):
            function_call = content.parts[0].function_call
            function_name = function_call.name
            function_args = {k: v for k, v in function_call.args.items()}
            
            print(f"Calling function: {function_name}")
            
            if function_name in tool_functions:
                # Execute the function
                function_response = await tool_functions[function_name](**function_args)
                
                # Send the function response back to the model
                response = await chat.send_message_async(
                    FunctionResponse(name=function_name, response=function_response)
                )
                
                # Update for next iteration
                candidate = response.candidates[0]
                content = candidate.content
            else:
                print(f"Unknown function: {function_name}")
                break
        
        # Print the final text response
        print(f"\nAssistant: {content.parts[0].text}")

async def main():
    """Main entry point."""
    try:
        # Set up Home Assistant
        logger.info("Setting up Home Assistant...")
        success = await setup_home_assistant()
        
        if not success:
            logger.error("Failed to set up Home Assistant")
            return
        
        # Run the interactive agent
        await run_interactive_agent()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
    finally:
        # Clean up
        await cleanup_home_assistant()

if __name__ == "__main__":
    asyncio.run(main())