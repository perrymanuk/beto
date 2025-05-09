# Crawl4AI Migration to MCP Server

This document describes the migration of the direct Crawl4AI integration to the MCP server-based approach.

## Overview

Previously, Radbot had two ways to connect to Crawl4AI:

1. A direct integration via the `radbot.tools.crawl4ai` package
2. An MCP server connection via the `integrations.mcp.servers` configuration

This migration consolidates these approaches by:

1. Removing the direct integration code
2. Providing backward compatibility through stub functions
3. Redirecting all Crawl4AI interactions through the MCP server

## Why MCP Server?

The MCP (Model Context Protocol) server approach offers several benefits:

1. **Standardized Interface**: Consistent interaction with various services
2. **Credential Management**: Simplified authentication via the MCP server
3. **Unified Configuration**: All external services configured through the MCP section
4. **Enhanced Capabilities**: MCP servers often provide additional functionality
5. **Reduced Maintenance**: Single integration point to maintain rather than multiple

## Configuration

To use Crawl4AI through the MCP server, configure it in your `config.yaml` file:

```yaml
integrations:
  mcp:
    servers:
    - id: crawl4ai
      name: Crawl4AI Server
      enabled: true
      transport: sse
      url: https://crawl4ai.demonsafe.com/mcp/sse
      auth_token: your_token_here_if_needed
      tags:
      - web
      - search
```

## Backward Compatibility

The migration includes backward compatibility through stub functions in the `radbot.tools.mcp.mcp_crawl4ai_client` module. These functions log warnings and return empty results or error messages.

The following APIs remain available but are now redirected to the MCP server or return stubs:

- `create_crawl4ai_toolset()`
- `test_crawl4ai_connection()`
- `handle_crawl4ai_tool_call()`

## Technical Implementation

The migration involved:

1. Removing the direct Crawl4AI code from `radbot.tools.crawl4ai`
2. Creating compatibility stubs for common functions
3. Updating imports across the codebase
4. Ensuring all Crawl4AI API calls go through the MCP server

## Future Considerations

In future releases, the stub compatibility layer may be removed completely. Applications should be updated to use the MCP server approach directly.

The environment variable `CRAWL4AI_API_TOKEN` is now deprecated. All authentication should be handled through the MCP server configuration.