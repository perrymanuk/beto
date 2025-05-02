# Crawl4AI Integration for RadBot

This document describes the integration of Crawl4AI with the RadBot framework, providing a web crawling and knowledge retrieval capability using the Model Context Protocol (MCP).

## Overview

Crawl4AI is a specialized web crawler and knowledge retrieval system designed for LLM-friendly content extraction. The integration allows RadBot agents to:

1. Ingest web content from specified URLs, with configurable crawl depth
2. Query the ingested knowledge base using natural language
3. Utilize the retrieved information to enhance responses

This capability enables agents to access and leverage knowledge from specific websites, such as technical documentation, without requiring constant internet access for every query.

## Architecture

The integration follows RadBot's MCP pattern, implementing a client that exposes Crawl4AI's capabilities through MCP tools:

- `mcp_crawl4ai_client.py`: Core implementation providing:
  - Functions to create MCP-compatible toolsets
  - Factory function for easy agent creation with Crawl4AI capabilities
  - Connection testing and configuration utilities

### Key Components

1. **API Client**: Handles communication with the Crawl4AI service via REST API
2. **MCP Toolset**: Wraps API calls in MCP-compatible tool functions
3. **Agent Factory**: Simplifies the creation of agents with Crawl4AI capabilities

## Configuration

The integration requires the following environment variables:

- `CRAWL4AI_API_URL`: URL of the Crawl4AI service (default: https://crawl4ai.demonsafe.com)
- `CRAWL4AI_API_TOKEN`: Authentication token for the Crawl4AI API (required)

These can be set in the `.env` file or directly in the environment.

## Usage

### Basic Integration

To create an agent with Crawl4AI capabilities:

```python
from radbot.agent import create_agent
from radbot.tools import create_crawl4ai_enabled_agent

# Create an agent with Crawl4AI tools
agent = create_crawl4ai_enabled_agent(create_agent)
```

### Testing the Connection

To verify the connection to the Crawl4AI service:

```python
from radbot.tools import test_crawl4ai_connection

result = test_crawl4ai_connection()
print(f"Connection successful: {result['success']}")
if result['success']:
    print(f"API version: {result['api_version']}")
```

### Available Tools

The integration provides two main tools to the agent:

1. `crawl4ai_ingest_document`: Crawls and ingests content from a URL
   - Parameters:
     - `url`: Target URL to crawl (required)
     - `crawl_depth`: How many links to follow (default: 0, just the URL)
     - `content_selectors`: Optional CSS selectors to target specific content

2. `crawl4ai_query_knowledge`: Queries the ingested knowledge base
   - Parameters:
     - `search_query`: Search query or question (required)

These tools will be automatically used by the agent when appropriate, based on the user's request.

## Implementation Notes

- The integration uses the `requests` library for synchronous API calls, wrapped in async functions for MCP compatibility
- MCP tools are created using the ADK 0.3.0 `FunctionTool` approach for maximum compatibility
- JWT authentication is used for secure communication with the Crawl4AI service

## Examples

### Example: Ingesting and Querying Documentation

```python
# Sample conversation with an agent that has Crawl4AI capabilities

# User asks to ingest Python requests library documentation
user_query = "Please ingest the documentation from https://requests.readthedocs.io/en/latest/"
response = agent.process_message("user1", user_query)
# Agent uses crawl4ai_ingest_document and confirms success

# Later, user asks about the documentation
user_query = "How do I handle timeouts with the requests library?"
response = agent.process_message("user1", user_query)
# Agent uses crawl4ai_query_knowledge to retrieve relevant information
# and provides a well-informed response based on the documentation
```

## Future Enhancements

Potential improvements to the integration:

1. Async status tracking for long-running ingestion jobs
2. Bulk ingestion capabilities for multiple URLs
3. Enhanced error handling and recovery mechanisms
4. Query result caching for improved performance