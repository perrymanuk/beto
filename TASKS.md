# Tasks

This file tracks development tasks for the radbot project.

## Setup & Infrastructure

- [x] Create initial directory structure
- [x] Set up Python packaging (pyproject.toml)
- [x] Create basic configuration files (.env.example, Makefile)
- [x] Set up Qdrant database (using homelab instance)
- [ ] Configure CI/CD pipeline

## Core Implementation

- [x] Implement base Agent structure using ADK
- [x] Set up configurable agent prompts
- [x] Configure model selection system
- [x] Implement ConfigManager for centralized configuration
- [x] Implement basic tools (time, weather)
- [x] Create Runner and Session service setup

## Memory System

- [x] Implement QdrantMemoryService
- [x] Create memory ingestion pipeline
- [x] Implement memory retrieval logic
- [x] Add memory tools (search_past_conversations, store_important_information)
- [x] Create memory-enabled agent factory
- [x] Integrate memory system with main CLI agent
- [x] Add memory status commands to CLI interface
- [x] Fix memory_tools.py to handle memory_type parameter
- [x] Add memory statistics retrieval functionality

## External Integration

- [x] Set up MCP client for Home Assistant
- [x] Integrate Home Assistant tools
- [x] Fix Home Assistant tool call implementation
- [x] Integrate MCP tools with main CLI agent
- [x] Create test script for Home Assistant entity state retrieval
- [x] Add entity search functionality to find real Home Assistant entities
- [x] Fix entity search tool malformed function call error
- [x] Add diagnostic tools to debug Home Assistant integration
- [x] Implement MCP fileserver integration
- [x] Create MCP fileserver server script
- [x] Implement MCP fileserver client integration
- [x] Add MCP fileserver tools to main agent
- [x] Create test script for MCP fileserver operations
- [ ] Implement additional MCP servers as needed

## Web Search Integration

- [x] Implement Tavily search tool in web_search_tools.py
- [x] Add necessary imports for Tavily search tool
- [x] Update tools/__init__.py to include the new Tavily search tool
- [x] Create a new file web_search_tools.py for the Tavily search functionality
- [x] Add function to create an agent with Tavily search capabilities
- [x] Update imports and references
- [x] Update pyproject.toml to include langchain-community dependency
- [x] Update .env.example with Tavily API environment variable
- [x] Create implementation for Tavily search agent factory  
- [x] Add web search agent factory to __init__.py
- [x] Update documentation in docs/implementation for web search feature
- [x] Create example script for web search agent
- [x] Update root_agent to include web search capabilities
- [ ] Test web search integration

## Testing & Documentation

- [x] Create unit tests for basic tools
- [x] Create integration tests for agent workflows
- [ ] Create ADK evaluation datasets
- [x] Write implementation documentation
- [x] Document agent configuration
- [x] Document memory system architecture
- [x] Add help target to Makefile
- [x] Document MCP fileserver implementation

## CLI & Interfaces

- [x] Implement CLI interface
- [ ] Create scheduler for background tasks
- [x] Add logging system