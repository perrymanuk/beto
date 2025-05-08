# Context7 Integration

This document describes the integration of Context7 with Radbot, enabling access to up-to-date library documentation directly within the agent framework.

## Overview

Context7 is a tool that provides current, comprehensive documentation for libraries and frameworks. It helps AI coding assistants provide accurate and relevant information by retrieving official documentation for specific library versions. This integration allows Radbot agents to access Context7's documentation retrieval capabilities.

## Architecture

The Context7 integration uses a stdio-based MCP server architecture similar to the Claude CLI integration:

1. The Context7 MCP server is launched using NPX when needed
2. Communication with the server happens over standard input/output
3. Radbot interfaces with Context7 via our `MCPSSEClient` and tool infrastructure
4. Tools for library ID resolution and documentation retrieval are exposed to agents

## Configuration

The Context7 integration is configured in the main `config.yaml` file. A template configuration can be found in `config/context7.yaml.example`.

```yaml
integrations:
  mcp:
    enabled: true
    servers:
      # Context7 MCP server configuration
      - id: context7
        enabled: true
        transport: stdio
        command: npx
        args:
          - -y
          - "@upstash/context7-mcp@latest"
        timeout: 30
        tags:
          - documentation
          - library
          - reference
```

### Configuration Parameters

- `id`: The identifier for the Context7 service in Radbot (must be "context7")
- `enabled`: Whether the service is active
- `transport`: Must be "stdio" for Context7
- `command`: The command to run Context7 ("npx")
- `args`: Arguments to pass to the command
- `timeout`: Optional timeout in seconds (default: 30)
- `tags`: Optional tags for categorizing the service

## Tools and Functionality

The Context7 integration provides two main functions:

1. **Library ID Resolution**: Converts a library name (e.g., "react") to a Context7-compatible library ID
2. **Documentation Retrieval**: Fetches up-to-date documentation for a specific library

### Tool: `context7_resolve_library`

Resolves a library name to a Context7-compatible library ID.

**Parameters:**
- `library_name`: String, the name of the library to resolve

**Returns:**
- Dictionary containing:
  - `success`: Boolean, whether the resolution was successful
  - `library_id`: String, the resolved library ID
  - `matches`: List of potential matches if multiple libraries match the name
  - `message`: String, additional information

### Tool: `context7_get_docs`

Retrieves documentation for a specific library.

**Parameters:**
- `library_id`: String, the Context7-compatible library ID
- `topic`: Optional string, a specific topic to focus on
- `tokens`: Optional integer, maximum number of tokens to return

**Returns:**
- Dictionary containing:
  - `success`: Boolean, whether the documentation retrieval was successful
  - `documentation`: String, the retrieved documentation
  - `library_id`: String, the library ID used
  - `message`: String, additional information

## Usage Examples

### Basic Usage

```python
from radbot.tools.mcp.context7_client import resolve_library_id, get_library_docs

# Resolve a library ID
result = resolve_library_id("react")
if result["success"]:
    library_id = result["library_id"]
    
    # Fetch documentation
    docs = get_library_docs(library_id)
    if docs["success"]:
        print(docs["documentation"])
```

### Focused Topic Example

```python
# Resolve a library ID
result = resolve_library_id("python")
if result["success"]:
    # Fetch documentation about a specific topic
    docs = get_library_docs(
        library_id=result["library_id"],
        topic="asyncio",
        tokens=5000
    )
    if docs["success"]:
        print(docs["documentation"])
```

## Implementation Notes

- The Context7 MCP server is launched as a subprocess when needed
- Documentation is retrieved directly from the official sources
- Context7 ensures that documentation is up-to-date and version-specific
- Library ID resolution handles fuzzy matching for library names

## Troubleshooting

Common issues:

1. **Server Launch Failures**: Ensure NPX is installed and that you have internet access
2. **Library Resolution Failures**: Check that you're using a commonly known library name
3. **No Documentation**: Some libraries may not have documentation available in Context7's database
4. **Performance Issues**: Large documentation requests can take time to process

## References

- [Context7 GitHub Repository](https://github.com/upstash/context7)
- [NPM Package: @upstash/context7-mcp](https://www.npmjs.com/package/@upstash/context7-mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification/2025-03-26)