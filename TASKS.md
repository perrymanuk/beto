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
- [x] Implement shell command execution with security controls
- [x] Fix import error for basic_tools module
- [x] Fix class name and import path errors in CLI
- [x] Update agent's process_message method to be compatible with ADK 0.3.0+
- [x] Fix session management and parameter errors in Runner.run()
- [x] Fix syntax error in process_message method's try/except structure
- [x] Fix session management method signatures to match ADK 0.3.0+ API
- [x] Fix InMemorySessionService parameter mismatch in get_session and create_session calls
- [x] Fix function signature for search_home_assistant_entities to work with automatic function calling

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
- [x] Implement Enhanced Memory System with multi-layered approach
- [x] Create memory detector for keyword-triggered storage
- [x] Implement custom tagging with beto_ prefix
- [x] Create enhanced memory agent with automatic memory detection

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
- [x] Fix MCP fileserver import error after code restructuring
- [x] Fix MCP missing functions error after code restructuring
- [x] Fix MCP relative import paths after code restructuring
- [x] Fix MCP parent package re-exports after code restructuring

## Home Assistant Integration

- [x] Set up MCP client for Home Assistant (native integration)
- [x] Create documentation for using Home Assistant's native MCP endpoint
- [x] Update configuration to use MCP integration exclusively
- [x] Create entity search functionality for MCP integration
- [x] Implement robust error handling for MCP connection
- [x] Create examples demonstrating MCP integration
- [x] Update documentation for MCP integration
- [x] Integrate Home Assistant tools with radbot_web agent
- [x] Remove WebSocket implementation in favor of native MCP approach
- [x] Fix entity search issues with MCP integration
- [x] Improve error handling for unsupported domains in MCP
- [x] Add documentation about MCP limitations
- [ ] Create integration tests for MCP integration

## Web Search & Content Integration

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
- [x] Test web search integration
- [x] Fix Tavily search tool not being attached or loaded correctly in the agent
- [x] Add better error handling and debugging for Tavily search tool
- [x] Create diagnostic script for testing Tavily search tool functionality
- [x] Document Tavily search tool fix implementation

## Crawl4AI & Vector Search

- [x] Implement Crawl4AI vector store using Qdrant
- [x] Fix issue with web_query errors (400 Bad Request)
- [x] Create document chunking strategy for better search results
- [x] Update Crawl4AI client to store extracted content in vector DB
- [x] Fix read_url_as_markdown_directly function to store content
- [x] Fix ingest_url_to_knowledge_base function to use vector store
- [x] Update web_query function to use vector search instead of direct API call
- [x] Write implementation documentation in docs/implementation/crawl4ai.md
- [x] Create test script for Crawl4AI vector search functionality
- [x] Update TASKS.md to track implementation progress
- [x] Fix Qdrant compatibility issues with count_documents method
- [x] Fix crawl4ai_ingest_url to extract content from "markdown" field
- [x] Pin qdrant-client version for better compatibility
- [x] Create validation scripts for crawl4ai and Qdrant fixes
- [x] Fix recursive depth crawling to properly follow links at each level
- [x] Create DeepCrawl class for efficient breadth-first recursive crawling
- [x] Update crawl4ai_ingest_url.py to use proper depth handling
- [x] Add crawl4ai dependency to pyproject.toml
- [x] Document improved crawl4ai depth implementation
- [x] Create test script for validating depth crawling functionality
- [x] Implement staged crawling for more efficient web content processing
- [x] Add depth limiting as default strategy for crawl4ai
- [x] Document staged crawling implementation
- [x] Document depth limiting implementation
- [x] Implement two-step crawling to avoid Playwright dependency
- [x] Create documentation for two-step crawling approach
- [x] Revert crawl4ai_ingest_url tool to basic URL ingestion without link crawling
- [x] Fix crawl4ai_two_step_crawl and crawl4ai_ingest_and_read to match the reverted crawl4ai_ingest_url

## Shell Command Execution

- [x] Implement secure shell command execution function with subprocess
- [x] Create dual-mode system (strict and allow-all modes)
- [x] Implement command allow-listing for strict mode
- [x] Add basic argument validation to prevent command injection
- [x] Create Google Agent SDK tool registration
- [x] Implement comprehensive error handling and logging
- [x] Create unit tests for shell command execution
- [x] Document implementation in docs/implementation
- [ ] Integrate with agent factories for CLI and web interfaces
- [ ] Create additional command-specific argument validation rules

## PostgreSQL Todo List Feature

- [x] Create Pydantic models for todo list data validation and serialization
- [x] Implement PostgreSQL database connection with psycopg2 and connection pooling
- [x] Create database schema with UUID primary keys and enum type for task status
- [x] Implement database interaction layer for CRUD operations
- [x] Create ADK FunctionTools with consistent error handling
- [x] Update environment configuration for PostgreSQL connection
- [x] Add todo agent factory for easy integration
- [x] Create example script demonstrating the todo agent
- [x] Improve user experience by supporting project names instead of requiring UUIDs
- [x] Fix UUID handling issues in todo_tools with proper psycopg2 adapter registration
- [x] Fix task removal functionality with improved error handling
- [x] Document UUID handling fix for todo tools
- [x] Add enhanced filtering to hide completed tasks by default
- [x] Document todo list filtering enhancements
- [x] Restructure todo tools into modular components (db, models, api)
- [x] Add list_all_tasks tool to show tasks across all projects
- [x] Document todo tools restructuring
- [x] Add update_task and update_project tools for modifying existing entries
- [x] Document todo update functionality
- [x] Fix JSON serialization issue with datetime objects in todo tools
- [x] Fix dictionary serialization issue in update_task and add_task functions
- [ ] Implement unit tests for todo tools
- [ ] Create integration tests with test database

## Testing & Documentation

- [x] Create unit tests for basic tools
- [x] Create integration tests for agent workflows
- [ ] Create ADK evaluation datasets
- [x] Write implementation documentation
- [x] Document agent configuration
- [x] Document memory system architecture
- [x] Add help target to Makefile
- [x] Document MCP fileserver implementation
- [x] Document enhanced memory system implementation

## CLI & Interfaces

- [x] Implement CLI interface
- [ ] Create scheduler for background tasks
- [x] Add logging system

## Voice & Audio

- [x] ~~Implement ElevenLabs TTS integration~~ (Removed due to implementation issues)
- [x] ~~Replace ElevenLabs with Google Cloud TTS implementation~~ (Removed due to implementation issues)
- [x] ~~Create TTS service for ADK web interface~~ (Removed due to implementation issues)
- [x] ~~Implement JavaScript extension for voice capabilities~~ (Removed due to implementation issues)
- [x] ~~Document voice implementation~~ (Removed due to implementation issues)
- [x] Remove broken voice implementation and related dependencies