# Crawl4AI MCP Integration Fix

This document describes the issues with the Crawl4AI MCP integration and provides solutions to resolve the "All endpoints failed" errors.

## Problem Description

The Radbot MCP client was unable to properly connect to the Crawl4AI MCP server, resulting in "All endpoints failed" errors. The key issues were:

1. **Session Registration:** The session ID must be properly registered with the SSE connection before it can be used for tool invocation.
2. **Message Endpoint Format:** The message endpoint URL was incorrectly formatted, particularly with trailing slashes.
3. **Tool Name Handling:** The client was using overly complex tool names rather than the simplified names expected by Crawl4AI.
4. **Retry Mechanism:** The client didn't properly retry on 404 errors, which can occur when a session is newly created.
5. **Error Diagnostics:** Error reporting lacked sufficient detail to diagnose connection issues.

## Key Discoveries

Through testing with the Crawl4AI server, we discovered the critical issue:

- **Session ID Registration:** The session ID must be included in the SSE connection URL **when establishing the connection**. It's not sufficient to generate a session ID and include it only in the message endpoint URL.
- **Error Message:** When attempting to use a tool with an unregistered session, the server returns a 404 error with the message "Could not find session".

## Implementation Details

### 1. Session Registration Process

The correct flow for Crawl4AI integration is:

1. Generate a session ID (UUID)
2. Connect to the SSE endpoint with the session ID included in the URL
   - Format: `https://crawl4ai.demonsafe.com/mcp/sse?session_id={session_id}`
3. Keep the SSE connection open briefly to allow the server to register the session
4. Use the same session ID for all tool invocations with the message endpoint
   - Format: `https://crawl4ai.demonsafe.com/mcp/messages?session_id={session_id}`

### 2. Message Endpoint Format

Crawl4AI expects the message endpoint URL in the format:

```
https://crawl4ai.demonsafe.com/mcp/messages?session_id=<SESSION_ID>
```

Key points:
- No trailing slash after "messages"
- Session ID as a query parameter with "session_id=" prefix
- Base URL derived from the SSE URL by replacing "/sse" with "/messages"

### 3. Tool Name Simplification

Crawl4AI uses simple tool names rather than prefixed ones:

| Simple Name | Used Instead Of           |
|-------------|-----------------------------|
| search      | crawl4ai_search, web_search |
| crawl       | crawl4ai_crawl, crawl_website |
| scrape      | crawl4ai_scrape, md        |
| extract     | crawl4ai_extract, ask      |
| md          | (markdown extraction)      |
| html        | (HTML extraction)          |
| screenshot  | (take screenshot)          |

### 4. Retry Logic

Implement proper retry logic with exponential backoff for:
- 404 errors (session not found) which can occur if the session registration was incomplete
- Server errors (5xx)
- Timeout errors
- Connection errors

## Fixed Implementation

### Session Registration Logic

The key implementation change is in the session registration:

```python
def _register_crawl4ai_session(self) -> bool:
    """
    Register a session with the Crawl4AI SSE connection.
    
    This is critical for Crawl4AI - the session ID must be registered with
    the SSE connection before it can be used for tool invocation.
    """
    logger.info("Registering session with Crawl4AI SSE connection")
    
    # Create the SSE URL with session ID
    sse_url = self.url
    if "?" not in sse_url:
        sse_url = f"{sse_url}?session_id={self.session_id}"
    elif "session_id=" not in sse_url:
        sse_url = f"{sse_url}&session_id={self.session_id}"
        
    logger.info(f"Connecting to SSE with session ID: {sse_url}")
    
    try:
        # Create a session for the SSE connection
        session = requests.Session()
        
        # Connect to the SSE endpoint with the session ID
        response = session.get(
            sse_url,
            headers=self.headers,
            stream=True,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to connect to SSE: {response.status_code}")
            return False
            
        logger.info("SSE connection established, waiting for server acknowledgment...")
        
        # Keep the connection open briefly to ensure the server registers the session
        start_time = time.time()
        max_wait = 5  # Wait up to 5 seconds
        
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
                
            logger.debug(f"SSE event: {line}")
            
            # Look for an acknowledgment or any message from the server
            if "ping" in str(line) or "data:" in str(line):
                logger.info(f"Received server message: {line}")
                # We've received some data, which indicates the connection is working
                
            if time.time() - start_time >= max_wait:
                # We've waited long enough
                break
                
        # Close the connection now that we've registered the session
        response.close()
        session.close()
        
        logger.info("Session registration complete")
        return True
    
    except Exception as e:
        logger.error(f"Error establishing SSE connection: {e}")
        return False
```

### Tool Invocation

The tool invocation code now includes proper handling of the registered session:

```python
def _call_crawl4ai_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
    """
    Special implementation for calling Crawl4AI tools.
    """
    # Map tool names to their simplest forms
    crawl4ai_tool_mapping = {
        "crawl4ai_search": "search",
        "crawl4ai_crawl": "crawl",
        "crawl4ai_scrape": "scrape",
        # ...
    }
    
    # Get the simplified tool name
    simple_tool_name = crawl4ai_tool_mapping.get(tool_name, tool_name)
    
    # Construct the message endpoint URL with session ID
    url = f"{self.message_endpoint}?session_id={self.session_id}"
    
    # Prepare the request data
    request_data = {
        "jsonrpc": "2.0",
        "method": "invoke",
        "params": {
            "name": simple_tool_name,
            "arguments": args
        },
        "id": str(uuid.uuid4())
    }
    
    # Make the request with retries
    # ...
```

## Configuration

The correct configuration in config.yaml for Crawl4AI:

```yaml
mcp:
  servers:
  - id: crawl4ai
    name: Crawl4AI Server
    enabled: true
    transport: sse
    url: https://crawl4ai.demonsafe.com/mcp/sse?session_id=<SESSION_ID>
    message_endpoint: https://crawl4ai.demonsafe.com/mcp/messages?session_id=<SESSION_ID>
    auth_token: null
    tags:
    - web
    - search
    - crawl
```

Note that:
1. The session ID is included in both the `url` and `message_endpoint`
2. No trailing slash in the message endpoint
3. The SSE URL and message endpoint share the same session ID

## Testing

A comprehensive test script `/tmp/crawl4ai/sse_session_register.py` validates the session registration process:

1. Connect to the SSE endpoint with the session ID in the URL
2. Keep the connection open briefly to ensure the server registers the session
3. Test the message endpoint with the registered session ID
4. Verify that tool invocation succeeds

## Conclusion

The Crawl4AI MCP integration has been fixed by:

1. Properly registering the session ID with the SSE connection
2. Using the correct message endpoint format without trailing slash
3. Using the same session ID for both the SSE connection and message endpoint
4. Using simple tool names rather than prefixed ones
5. Implementing proper retry logic for 404 errors

These changes ensure reliable connection to the Crawl4AI MCP server and successful tool invocation.