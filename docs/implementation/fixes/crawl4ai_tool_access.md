# Crawl4AI MCP Server Configuration

## Issue

The Crawl4AI MCP server at `https://crawl4ai.demonsafe.com/mcp/sse` is not working correctly with the SSE transport. When trying to invoke tools like `crawl4ai_crawl`, we get errors about failing to call the tool because all endpoints failed.

## Root Cause

After examining the Crawl4AI MCP bridge implementation at [mcp_bridge.py](https://github.com/unclecode/crawl4ai/blob/main/deploy/docker/mcp_bridge.py), we now understand how the server is designed to work:

1. The `/mcp/sse` endpoint is meant for establishing a Server-Sent Events (SSE) connection stream, not for direct tool invocation
2. Tool invocation happens by sending messages to a separate endpoint, typically `/mcp/messages/`
3. The standard MCP pattern expects clients to:
   - Connect to the SSE endpoint first
   - Wait for server initialization and tool discovery
   - Then send tool invocation requests to the messages endpoint
   - Receive tool responses through the SSE event stream

This explains why our previous attempts to POST directly to `/mcp/sse/invoke` and similar endpoints failed - that's not how the Crawl4AI MCP bridge is designed to work.

## Solution

Update our implementation to properly work with the Crawl4AI MCP server's architecture:

Changes made:

1. **Updated config.yaml to include the message endpoint:**
```yaml
mcp:
  servers:
  - id: crawl4ai
    name: Crawl4AI Server
    enabled: true
    transport: sse
    url: https://crawl4ai.demonsafe.com/mcp/sse
    message_endpoint: https://crawl4ai.demonsafe.com/mcp/messages
    auth_token: null
    tags:
    - web
    - search
```

2. **Enhanced MCPSSEClient to handle SSE properly:**
   - Modified to correctly handle SSE connection and messages
   - Added logic to find and use the correct message endpoint
   - Added fallback endpoint detection by inferring from SSE URL (replacing /sse with /messages)
   - Improved error handling and retry logic
   
3. **Created test script for async SSE communication:**
   - Implemented a proper async SSE client for testing
   - Added handling for SSE events and messages
   - Supports the correct message exchange pattern for MCP

## Testing

We've created a test script to validate our solution:

```python
# tools/test_crawl4ai_sse.py
async def main():
    # Get the URL from config.yaml
    from radbot.config.config_loader import config_loader
    server_config = config_loader.get_mcp_server("crawl4ai")
    
    # Create the SSE client
    client = AsyncSSEClient(server_config.get("url"))
    
    # Connect to SSE endpoint and process events
    connection_task = asyncio.create_task(client.connect())
    
    # Wait for connection with timeout
    # ...
    
    # If we have tools, try to invoke crawl4ai_crawl
    if client.tools:
        result = await client.invoke_tool(
            "crawl4ai_crawl", 
            {"url": "https://github.com/google/adk-samples"}
        )
```

The test will attempt to:
1. Establish an SSE connection to the server
2. Process incoming events to discover available tools
3. Send a tool invocation request to the messages endpoint
4. Process the tool response

## Next Steps

1. **Run the test script to verify the SSE communication works:**
   - If it works, update our client to use the same pattern
   - If it doesn't work, further investigate the server configuration

2. **Consider reaching out to the server administrator:**
   - Verify the correct URL and endpoint structure
   - Confirm authentication requirements
   - Get information about available tools and their parameters

3. **Update documentation:**
   - Document the correct usage pattern for MCP clients
   - Add examples for common tool invocations

## Conclusion

The issue was in our understanding of how the Crawl4AI MCP server works. After examining the server implementation, we now understand that it follows a specific message exchange pattern that's different from what we were trying. Our updated implementation should properly handle this pattern and allow successful tool invocation.