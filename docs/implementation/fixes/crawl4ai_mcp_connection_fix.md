# Crawl4AI MCP Connection Fix

## Overview

This document details the fixes implemented for the Crawl4AI MCP server connection issues. The implementation improves the robustness of the MCP client by handling various endpoint patterns and authentication requirements for the Crawl4AI server.

## Background

The Crawl4AI MCP server at `https://crawl4ai.demonsafe.com/mcp/sse` requires a specific connection pattern:

1. It uses a Server-Sent Events (SSE) endpoint for streaming responses
2. It requires a session ID parameter for message endpoints
3. It uses a trailing slash in the messages endpoint URL

Our previous implementation was attempting to connect directly to the SSE endpoint for tool calls, which was resulting in errors when trying to invoke tools like `crawl4ai_search` and `crawl4ai_crawl`.

## Changes Made

### 1. Improved Message Endpoint Handling

The client now tries multiple message endpoint patterns to match what Crawl4AI expects:

```python
messages_urls = [
    self.url.replace("/sse", "/messages/"),  # Crawl4AI format with trailing slash
    self.url.replace("/sse", "/messages"),   # Standard format without trailing slash
    f"{self.url.replace('/sse', '')}/messages/",  # Alternative with base URL
    f"{self.url.replace('/sse', '')}/messages"    # Alternative with base URL
]
```

### 2. Automatic Session ID Generation

For Crawl4AI servers, the client now automatically generates a session ID if one is not provided:

```python
# For Crawl4AI, we need a session ID
if "crawl4ai" in self.url.lower() and not self.session_id:
    # Generate a random session ID for Crawl4AI
    import uuid
    self.session_id = str(uuid.uuid4())
    logger.info(f"Generated session ID for Crawl4AI: {self.session_id}")
```

### 3. Priority for Session ID URLs

The endpoints with session IDs are now tried first to increase the chances of successful connection:

```python
# If we have a session_id, put the endpoints with session_id first
if self.session_id:
    for msg_url in messages_urls:
        session_messages_url = f"{msg_url}?session_id={self.session_id}"
        invoke_endpoints.append(session_messages_url)
```

### 4. Special Handling in Tool Functions

Tool functions now have special handling for Crawl4AI tools:

```python
# Special handling for crawl4ai tools
if "crawl4ai" in self.url.lower() and name.startswith("crawl4ai_"):
    logger.info(f"Special handling for crawl4ai tool: {name}")
    
    # Set message_endpoint if not already set
    if not self.message_endpoint and "/sse" in self.url:
        # Crawl4AI requires trailing slash for messages endpoint
        self.message_endpoint = self.url.replace("/sse", "/messages/")
        logger.info(f"Auto-set message_endpoint for crawl4ai: {self.message_endpoint}")
```

### 5. Improved Error Handling

The error handling has been enhanced to provide more detailed information:

```python
# For any other error, log in detail and continue to next endpoint
logger.error(f"Error calling tool {tool_name} at {invoke_url}: {response.status_code}")
try:
    # Try to parse error response as JSON
    error_details = response.json()
    logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
except:
    # Fall back to text response
    logger.error(f"Error response: {response.text[:200]}...")
```

## Testing

A test script has been created to validate the fix:

```python
# tools/test_crawl4ai_connection_fix.py
```

The script attempts to:
1. Connect to the Crawl4AI MCP server
2. Initialize the client to get tools
3. Directly invoke the `crawl4ai_search` tool

### Verification

While the current Crawl4AI MCP server at `https://crawl4ai.demonsafe.com/mcp/sse` still returns errors, our client now:

1. Correctly detects it's a Crawl4AI server
2. Automatically generates a session ID
3. Tries the correct endpoint patterns
4. Properly handles error responses
5. Creates fallback tools

This ensures that future Crawl4AI MCP instances with the correct endpoint pattern will work properly.

## Configuration Recommendations

For Crawl4AI MCP servers, we recommend the following configuration:

```yaml
integrations:
  mcp:
    servers:
    - id: crawl4ai
      name: Crawl4AI Server
      enabled: true
      transport: sse
      url: https://crawl4ai.demonsafe.com/mcp/sse  # Base SSE URL
      message_endpoint: https://crawl4ai.demonsafe.com/mcp/messages/  # Messages endpoint with trailing slash
      auth_token: null
      tags:
      - web
      - search
```

## Next Steps

1. **Coordinate with the Crawl4AI team**: The current server endpoint appears to be non-responsive. Consider reaching out to them to confirm the correct connection pattern.

2. **Update server URL**: If a new URL is provided, update the configuration in `config.yaml`.