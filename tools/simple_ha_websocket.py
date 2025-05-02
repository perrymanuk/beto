#!/usr/bin/env python3
"""
Simple standalone Home Assistant WebSocket client for testing and debugging.
This script connects directly to Home Assistant via WebSocket without using any other components.

Usage:
    python simple_ha_websocket.py [search_term]
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
import websockets

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple_ha_websocket")

class SimpleHAClient:
    """Simple Home Assistant WebSocket client for testing"""
    
    def __init__(self, url: str, token: str):
        """Initialize the client"""
        self.url = url
        self.token = token
        self.message_id = 1
        self.websocket = None
        
    async def connect(self) -> bool:
        """Connect to Home Assistant and authenticate"""
        try:
            logger.info(f"Connecting to {self.url}")
            self.websocket = await websockets.connect(self.url)
            logger.info("WebSocket connected, authenticating...")
            
            # Receive auth_required message
            auth_required = await self.websocket.recv()
            auth_data = json.loads(auth_required)
            if auth_data.get("type") != "auth_required":
                logger.error(f"Expected auth_required, got {auth_data.get('type')}")
                return False
                
            # Send authentication
            await self.websocket.send(json.dumps({"type": "auth", "access_token": self.token}))
            
            # Receive auth response
            auth_response = await self.websocket.recv()
            auth_result = json.loads(auth_response)
            if auth_result.get("type") != "auth_ok":
                logger.error(f"Authentication failed: {auth_result.get('message')}")
                return False
                
            logger.info(f"Authentication successful - HA version: {auth_result.get('ha_version')}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    async def get_states(self) -> List[Dict]:
        """Get all entity states"""
        if not self.websocket:
            logger.error("Not connected")
            return []
            
        try:
            # Send get_states command
            msg_id = self.message_id
            self.message_id += 1
            await self.websocket.send(json.dumps({
                "id": msg_id,
                "type": "get_states"
            }))
            logger.info(f"Sent get_states request with ID {msg_id}")
            
            # Wait for response
            while True:
                response = await self.websocket.recv()
                data = json.loads(response)
                
                # Check if this is our response
                if data.get("id") == msg_id and data.get("type") == "result":
                    if data.get("success"):
                        return data.get("result", [])
                    else:
                        logger.error(f"Error getting states: {data.get('error')}")
                        return []
        
        except Exception as e:
            logger.error(f"Error getting states: {e}")
            return []
    
    async def search_entities(self, search_term: str = "", domain: str = None) -> List[Dict]:
        """Search entities by term and/or domain"""
        all_states = await self.get_states()
        if not all_states:
            return []
            
        results = []
        search_term = search_term.lower()
        
        for entity in all_states:
            entity_id = entity.get("entity_id", "")
            entity_domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
            
            # Apply domain filter if specified
            if domain and entity_domain != domain:
                continue
                
            # If no search term, include all entities from filtered domain
            if not search_term and domain:
                results.append(entity)
                continue
                
            # Check for matches in entity ID
            if search_term in entity_id.lower():
                results.append(entity)
                continue
                
            # Check for matches in friendly name
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            if friendly_name and search_term in friendly_name:
                results.append(entity)
                continue
                
            # Check for matches in attributes
            for attr_name, attr_value in entity.get("attributes", {}).items():
                if isinstance(attr_value, str) and search_term in attr_value.lower():
                    results.append(entity)
                    break
        
        return results
    
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Connection closed")


async def main():
    """Main function"""
    # Load environment variables
    load_dotenv()
    
    # Get WebSocket URL and token
    ws_url = os.environ.get("HA_WEBSOCKET_URL")
    ws_token = os.environ.get("HA_WEBSOCKET_TOKEN")
    
    # Fall back to MCP variables if needed
    if not ws_url and os.environ.get("HA_MCP_SSE_URL"):
        mcp_url = os.environ.get("HA_MCP_SSE_URL")
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
            
        ws_url = f"{base_url}/api/websocket"
        logger.info(f"Derived WebSocket URL from MCP URL: {ws_url}")

    if not ws_token and os.environ.get("HA_AUTH_TOKEN"):
        ws_token = os.environ.get("HA_AUTH_TOKEN")
        logger.info("Using token from HA_AUTH_TOKEN environment variable")
        
    if not ws_url or not ws_token:
        logger.error("Missing HA_WEBSOCKET_URL or HA_WEBSOCKET_TOKEN environment variables")
        return 1
        
    # Create client and connect
    client = SimpleHAClient(ws_url, ws_token)
    if not await client.connect():
        logger.error("Failed to connect and authenticate")
        return 1
        
    try:
        # Get all states
        logger.info("Getting all states...")
        states = await client.get_states()
        logger.info(f"Received {len(states)} entities")
        
        # Count entities by domain
        domains = {}
        for state in states:
            entity_id = state.get("entity_id", "")
            if "." in entity_id:
                domain = entity_id.split(".", 1)[0]
                domains[domain] = domains.get(domain, 0) + 1
                
        logger.info(f"Found {len(domains)} domains: {domains}")
        
        # Get search term from command line or use default
        search_term = sys.argv[1] if len(sys.argv) > 1 else "light"
        logger.info(f"Searching for entities matching '{search_term}'...")
        
        # Search for entities
        results = await client.search_entities(search_term)
        logger.info(f"Found {len(results)} entities matching '{search_term}'")
        
        # Print results
        for i, entity in enumerate(results[:20]):  # Limit to 20 results
            entity_id = entity.get("entity_id", "")
            friendly_name = entity.get("attributes", {}).get("friendly_name", "")
            state = entity.get("state", "")
            logger.info(f"  {i+1}. {entity_id} - '{friendly_name}' [state: {state}]")
            
        # If more than 20 results, show a message
        if len(results) > 20:
            logger.info(f"... and {len(results) - 20} more.")
            
        # Now try domain-specific searches
        for domain in ["light", "switch", "sensor", "binary_sensor"]:
            domain_results = await client.search_entities(search_term, domain)
            logger.info(f"Found {len(domain_results)} {domain} entities matching '{search_term}'")
            
        # Also try domain-only searches
        for domain in ["light", "switch", "sensor", "binary_sensor"]:
            domain_only = await client.search_entities("", domain)
            logger.info(f"Total {domain} entities: {len(domain_only)}")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        
    finally:
        # Close connection
        await client.close()
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)