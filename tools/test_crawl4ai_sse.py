#!/usr/bin/env python
"""
Test the Crawl4AI MCP server using SSE connection approach.

This script implements a proper SSE client connection to the Crawl4AI MCP server,
following the expected protocol patterns from the server implementation.
"""

import os
import sys
import json
import logging
import asyncio
import uuid
import time
from typing import Dict, Any, Optional, List
import aiohttp

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

class AsyncSSEClient:
    """A simple async SSE client for MCP."""
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize the SSE client."""
        self.url = url
        self.headers = headers or {}
        self.headers.update({
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        })
        self.session = None
        self.tools = []
        
    async def connect(self):
        """Connect to the SSE endpoint and process events."""
        self.session = aiohttp.ClientSession()
        try:
            logger.info(f"Connecting to SSE endpoint: {self.url}")
            
            # Connect to the SSE endpoint
            async with self.session.get(self.url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"SSE connection failed: {response.status}")
                    return False
                
                logger.info("SSE connection established, waiting for events...")
                
                # Process events as they arrive
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line:
                        continue
                        
                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:].strip())
                            await self._process_event(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in event: {line}")
                
            return True
        except Exception as e:
            logger.error(f"Error in SSE connection: {e}")
            return False
        finally:
            await self.close()
            
    async def _process_event(self, event_data: Dict[str, Any]):
        """Process an SSE event."""
        logger.info(f"Received event: {json.dumps(event_data, indent=2)[:100]}...")
        
        # Check for serverInfo event which would contain tools
        if event_data.get("type") == "serverInfo":
            if "tools" in event_data:
                self.tools = event_data["tools"]
                logger.info(f"Found {len(self.tools)} tools in server info")
                
        # You can handle other event types as needed
            
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Invoke a tool on the MCP server."""
        if not self.session:
            logger.error("Not connected to SSE endpoint")
            return None
            
        try:
            # The proper way to invoke a tool is to send a JSON-RPC request
            request_data = {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": str(uuid.uuid4())
            }
            
            # Based on the MCP bridge implementation, messages are sent to the /mcp/messages/ endpoint
            message_url = f"{self.url.replace('/sse', '/messages/')}"
            logger.info(f"Invoking tool {tool_name} via {message_url}")
            
            headers = {**self.headers, "Content-Type": "application/json"}
            async with self.session.post(message_url, json=request_data, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Tool invocation failed: {response.status}")
                    return None
                    
                result = await response.json()
                logger.info(f"Tool invocation result: {json.dumps(result, indent=2)[:100]}...")
                return result
                
        except Exception as e:
            logger.error(f"Error invoking tool: {e}")
            return None
            
    async def close(self):
        """Close the connection."""
        if self.session:
            await self.session.close()
            self.session = None

async def main():
    """Run the SSE client."""
    # Get the URL from config.yaml
    from radbot.config.config_loader import config_loader
    server_config = config_loader.get_mcp_server("crawl4ai")
    
    if not server_config:
        logger.error("Crawl4AI server not found in configuration")
        return
        
    url = server_config.get("url", "")
    if not url:
        logger.error("URL not specified in server configuration")
        return
    
    # Create the SSE client
    client = AsyncSSEClient(url)
    
    # Create a timeout task
    async def timeout_task():
        await asyncio.sleep(30)  # 30-second timeout
        logger.warning("Timeout reached, closing connection")
        await client.close()
    
    # Run connection in the background with timeout
    connection_task = asyncio.create_task(client.connect())
    timeout = asyncio.create_task(timeout_task())
    
    # Wait for either connection or timeout
    done, pending = await asyncio.wait(
        [connection_task, timeout],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # Cancel pending tasks
    for task in pending:
        task.cancel()
    
    # Check if we have tools
    if client.tools:
        logger.info(f"Tools discovered: {client.tools}")
        
        # Try to invoke the crawl4ai_crawl tool if it exists
        tool_names = [tool.get("name") for tool in client.tools]
        if "crawl4ai_crawl" in tool_names:
            result = await client.invoke_tool(
                "crawl4ai_crawl", 
                {"url": "https://github.com/google/adk-samples"}
            )
            logger.info(f"Crawl result: {json.dumps(result, indent=2)[:1000]}...")
        else:
            logger.warning(f"crawl4ai_crawl not found in available tools: {tool_names}")
    else:
        logger.warning("No tools discovered")

if __name__ == "__main__":
    asyncio.run(main())