# Library-Based MCP Client Implementation

This document describes the implementation of the MCP client using the official MCP Python SDK with special handling for Crawl4AI and other MCP servers.

## Overview

The MCP (Model Context Protocol) client is responsible for connecting to MCP servers, discovering available tools, and invoking those tools on behalf of agents. Our implementation is based on the official MCP Python SDK with specific adaptations for Radbot's needs.

## Key Components

### `MCPSSEClient` Class

Located in `radbot/tools/mcp/client.py`, this class is the primary implementation of the MCP client. It handles:

- Connection establishment with MCP servers
- Session management
- Tool discovery and registration
- Tool invocation
- Server-Sent Events (SSE) handling
- Error management and fallback mechanisms

## Implementation Details

### Initialization Flow

The client initialization follows these steps:

1. Connection to the MCP server's SSE endpoint
2. Extraction of session ID and message endpoint from SSE events
3. Sending a proper initialization request with protocol version, capabilities, and client info
4. Requesting the list of available tools
5. Creating tool objects based on the server's response

### Special Handling for Crawl4AI

Crawl4AI servers have specific requirements and behaviors that require special handling:

- A persistent SSE connection is maintained in a background thread
- Events from the SSE stream are processed to extract session information
- Asynchronous tools return 202 Accepted responses immediately, with actual results coming through the SSE stream
- Session IDs must be maintained and included in all requests

### SSE Connection Management

For Crawl4AI servers, the client implements a robust SSE connection handling mechanism:

- A dedicated background thread listens for SSE events
- Events are parsed and processed based on their type (endpoint, result, etc.)
- Tool responses are stored in a thread-safe dictionary and associated with request IDs
- Threading.Event objects are used to synchronize waiting for asynchronous responses

### Tool Invocation Process

When a tool is invoked, the following happens:

1. The client formats a proper MCP request with the tool name and arguments
2. For Crawl4AI, it sets up an event to wait for an asynchronous response
3. The request is sent to the message endpoint with appropriate headers
4. For synchronous responses (200 OK), the result is processed immediately
5. For asynchronous responses (202 Accepted), the client waits for a response to arrive via the SSE stream
6. Results are extracted from the JSON-RPC format and returned

### Tool Discovery and Creation

The client supports several methods of tool discovery:

1. Retrieving tools via the MCP SDK's list_tools method
2. Fetching schema information from various common endpoints
3. Falling back to creating standard tools for well-known servers like Crawl4AI

### Error Handling and Fallbacks

To ensure robustness, the client implements multiple fallback mechanisms:

- If async initialization fails, it falls back to direct HTTP initialization
- If no session ID is provided by the server, it generates a UUID as fallback
- If no message endpoint is discovered, it constructs one based on common patterns
- If tool discovery fails, it can create standard tools for known server types

## Integration with Google ADK

Tools discovered from MCP servers are wrapped as Google ADK `FunctionTool` objects to make them compatible with the ADK framework. The client handles multiple versions of the ADK by adapting to different constructor signatures.

## Memory and Resource Management

The client properly cleans up resources when it's destroyed:

1. Closing the SSE connection by setting an active flag to false
2. Waiting for background threads to finish
3. Closing HTTP sessions
4. Cleaning up async context managers

## Common Challenges and Solutions

### Server-Sent Events Connection

**Challenge**: The Crawl4AI server would close SSE connections with "BrokenResourceError" when trying to send responses.

**Solution**: Maintain a persistent SSE connection in a background thread, properly parsing and handling all events, and using thread synchronization to wait for responses.

### Protocol Version Compliance

**Challenge**: Different MCP servers expect different initialization sequences.

**Solution**: Implement a standard initialization process using the 2025-03-26 protocol version with full compliant capabilities declaration.

### Tool Response Formats

**Challenge**: Different servers return results in different formats.

**Solution**: Handle multiple response formats including JSON-RPC result objects, custom output fields, and plain text responses.

### Session Management

**Challenge**: Maintaining the session across requests is critical, especially for Crawl4AI.

**Solution**: Extract and store session IDs from SSE events, and include them in all requests to maintain session continuity.

## Usage Example

```python
# Create a client
client = MCPSSEClient(url="https://crawl4ai.demonsafe.com/mcp/sse")

# Initialize the connection
client.initialize()

# Get available tools
tools = client.get_tools()

# Call a tool
result = client._call_tool("search", {"query": "What is the capital of France?"})
```

## Future Improvements

- Add support for authentication tokens and custom headers
- Implement caching of tool responses for better performance
- Add retry mechanisms for failed requests
- Support more complex tool schemas and parameter validation
- Add telemetry for monitoring and debugging
EOF < /dev/null