# Tavily Integration via MCP

This document describes how to integrate Tavily search capabilities with RadBot using the Model Context Protocol (MCP).

## Overview

Tavily provides powerful web search capabilities through their API. Instead of using the LangChain-based integration, we've switched to using the Tavily MCP server approach for a cleaner integration that doesn't require additional dependencies.

## Configuration

To enable Tavily web search capabilities, you need to:

1. Get a Tavily API key from https://app.tavily.com/home
2. Add the Tavily MCP server configuration to your `config.yaml`

### Adding Tavily to config.yaml

Add the following to your `config.yaml` file:

```yaml
integrations:
  mcp:
    enabled: true
    servers:
      # Tavily MCP server
      - id: tavily-mcp
        enabled: true
        transport: stdio
        command: "npx"
        args: ["-y", "tavily-mcp@0.1.3"]
        env:
          TAVILY_API_KEY: "tvly-YOUR_API_KEY_HERE"
        description: "Tavily search and research tools"
```

Alternatively, you can also run the Tavily MCP server directly:

1. Install the Tavily MCP server:
   ```bash
   npx -y tavily-mcp@0.1.3
   ```

2. Configure with your API key in `config.yaml`:
   ```yaml
   integrations:
     mcp:
       enabled: true
       servers:
         - id: tavily-mcp
           enabled: true
           transport: stdio
           command: "npx"
           args: ["-y", "tavily-mcp@0.1.3"]
           env:
             TAVILY_API_KEY: "tvly-YOUR_API_KEY_HERE"
           description: "Tavily search and research tools"
   ```

## Usage

The Tavily MCP server provides the following tools:

- `tavily-search`: Perform web searches with customizable parameters
- `tavily-extract`: Extract information from specified URLs

These tools will be automatically available to your agent when the MCP server is configured correctly.

## Troubleshooting

If you encounter issues with the Tavily integration:

1. Check that your API key is valid
2. Ensure the MCP server configuration is correct in `config.yaml`
3. Check the logs for any connection errors
4. Verify that the Tavily MCP server is accessible (if using a proxy service)

For more information, refer to the [Tavily MCP documentation](https://docs.tavily.com/documentation/mcp).