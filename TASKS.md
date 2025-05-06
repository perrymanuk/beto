# Tasks

This file tracks development tasks for the radbot project.

## Setup & Infrastructure

- [x] Create initial directory structure
- [x] Set up Python packaging (pyproject.toml)
- [x] Create basic configuration files (.env.example, Makefile)
- [x] Set up Qdrant database (using homelab instance)
- [ ] Configure CI/CD pipeline

## Sequential Thinking for Scout

- [x] Add sequential thinking capability to the Scout agent triggered by "think" keyword
- [x] Implement structured thinking process inspired by MCP Sequential Thinking server
- [x] Create detection for thinking trigger keywords
- [x] Add step-by-step reasoning with conclusion support
- [x] Add documentation for sequential thinking feature
- [ ] Add unit tests for sequential thinking
- [ ] Enhance thinking with branch/revision UI
- [ ] Add visualization for thinking process

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
- [x] Fix memory_tools import path in agent.py (radbot.tools.memory.memory_tools instead of radbot.tools.memory_tools)
- [x] Fix Home Assistant MCP tools event loop errors by adding proper event loop handling in CLI
- [x] Fix Runner initialization in CLI to explicitly provide app_name parameter
- [x] Implement direct component creation in CLI to bypass factory functions with app_name issues
- [x] Fix MCP Fileserver client to handle event loop conflicts in async contexts
- [x] Fix function signature for search_home_assistant_entities to work with automatic function calling
- [x] Updated MCP implementation to work with ADK 0.3.0 without compatibility
- [x] Fixed MCP client import issues by updating to use ClientSession from mcp.client.session
- [x] Fixed MCP Tool import error by updating import path from mcp.server.lowlevel.tool to mcp.types
- [x] Upgrade ADK from 0.3.0 to 0.4.0

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

## Prompt Caching System

- [x] Create base PromptCache class for caching LLM responses
- [x] Implement cache key generation for LLM requests
- [x] Create before_model_callback for checking cache before LLM calls
- [x] Create after_model_callback for storing responses in cache
- [x] Implement CacheTelemetry class for tracking performance metrics
- [x] Create MultiLevelCache for session-specific and global caching
- [x] Add optional Redis integration for cross-session caching
- [x] Implement cache_status.py command-line utility
- [x] Add configuration options via environment variables
- [x] Integrate caching system with agent.py
- [x] Create unit tests for caching components
- [x] Add performance evaluation tools
- [x] Implement selective caching based on request content

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

## Google Calendar Integration

Phase 1: Setup and Authentication
- [x] Set up project dependencies for Google Calendar API
  - [x] Add google-api-python-client to pyproject.toml
  - [x] Add google-auth-httplib2 to pyproject.toml
  - [x] Add google-auth-oauthlib to pyproject.toml
  - [x] ~~Add gcsa (Google Calendar Simple API) for a more Pythonic interface~~ (Removed due to dependency conflict with ADK 0.4.0)
- [x] Create project structure
  - [x] Create radbot/tools/calendar/ directory
  - [x] Create __init__.py file with imports
  - [x] Create credentials/ directory with .gitignore
  - [x] Create initial module files (calendar_auth.py, calendar_manager.py, etc.)
- [ ] Create Google Cloud project with Calendar API enabled
  - [ ] Create project in Google Cloud Console
  - [ ] Enable Google Calendar API
  - [ ] Set up OAuth consent screen (internal or external)
  - [ ] Generate OAuth credentials (client ID and secret)
  - [ ] Download credentials.json to credentials/ directory
- [x] Implement authentication module (calendar_auth.py)
  - [x] Create get_calendar_service() for personal accounts
  - [x] Implement token refresh handling
  - [x] Create get_workspace_calendar_service() for Google Workspace
  - [x] Add scopes configuration (readonly, full access, freebusy)
  - [x] Create token persistence logic

Phase 2: Core Calendar Operations
- [x] Implement core calendar operations (calendar_operations.py)
  - [x] Create list_events() with filtering options
  - [x] Create format_time() utility for datetime handling
  - [x] Create create_event() with required and optional parameters
  - [x] Create update_event() for modifying existing events
  - [x] Create delete_event() for removing events
  - [x] Add check_calendar_access() for permissions checks
  - [x] Create get_calendar_availability() for free/busy info
  - [x] Implement execute_with_retry() for rate limiting
- [x] Create CalendarManager class (calendar_manager.py)
  - [x] Implement __init__ and instance variables
  - [x] Create authenticate_personal() method
  - [x] Create authenticate_workspace() method
  - [x] Add list_upcoming_events() wrapper
  - [x] Add create_new_event() wrapper
  - [x] Add update_existing_event() wrapper
  - [x] Add delete_existing_event() wrapper
  - [x] Create handle_calendar_request() dispatcher
  - [x] Add get_calendar_busy_times() wrapper
  - [x] Implement proper error handling throughout

Phase 3: Agent Integration
- [x] Create function tool interfaces (calendar_tools.py)
  - [x] Create list_calendar_events FunctionTool
  - [x] Create create_calendar_event FunctionTool
  - [x] Create update_calendar_event FunctionTool
  - [x] Create delete_calendar_event FunctionTool
  - [x] Create check_calendar_availability FunctionTool
  - [x] Add comprehensive documentation for each tool
- [x] Create Google Calendar agent factory
  - [x] Create calendar_agent_factory.py in radbot/agent/
  - [x] Add initialization for CalendarManager
  - [x] Configure function tools
  - [x] Set up appropriate agent instructions
  - [x] Create factory function for creating calendar-enabled agent
- [x] Add example implementation
  - [x] Create calendar_agent_example.py in examples/
  - [x] Add sample workflows for common calendar operations
  - [x] Show service account and OAuth2 authentication
  - [x] Fix module import error for FunctionTools in ADK 0.4.0
  - [x] Update calendar tool definitions to use ADK 0.4.0 API
  - [x] Add calendar tools to main agent
  - [x] Fix parameter parsing issue with ComplexTypes in function signatures
  - [x] Fix credential conflict by using separate env variables for Calendar and Vertex AI
  - [x] Fix "name 'get_credentials_from_env' is not defined" import error in calendar_manager.py
  - [x] Fix "Error 400: redirect_uri_mismatch" by adding flexible redirect URI options and configurable port
  - [x] Fix "Unable to submit request because function declaration response schema specified other fields alongside any_of" error by updating response types
  - [x] Fix unhandled exceptions in calendar wrapper functions to return error information instead of crashing

Phase 4: Security and Testing
- [x] Enhance security measures
  - [x] Implement secure token storage
  - [x] Add environment variable support for credentials
  - [x] Configure proper scopes for least privilege
  - [ ] Add option for keyring integration
  - [ ] Add option for cloud secret manager integration
- [x] Add appropriate .env.example entries
  - [x] GOOGLE_CLIENT_ID
  - [x] GOOGLE_CLIENT_SECRET
  - [x] GOOGLE_SERVICE_ACCOUNT_FILE
- [ ] Create unit tests for calendar components
  - [ ] Add test fixtures with mock responses
  - [ ] Test authentication flows
  - [ ] Test calendar operations
  - [ ] Test error handling and retries
  - [ ] Add integration test with real Google Calendar
- [x] Finalize documentation
  - [x] Create docs/implementation/google_calendar_integration.md
  - [x] Add screenshots and examples
  - [x] Document step-by-step setup process in google_calendar_setup.md
  - [x] Create troubleshooting guide in google_calendar_setup.md

## Testing & Documentation

- [x] Create unit tests for basic tools
- [x] Create integration tests for agent workflows
- [ ] Create ADK evaluation datasets
- [x] Write implementation documentation
- [x] Document agent configuration
- [x] Document memory system architecture
- [x] Add help target to Makefile
- [x] Document MCP fileserver implementation
- [x] Implement direct filesystem access to replace MCP fileserver
- [x] Deploy direct filesystem implementation and remove MCP fileserver dependency
- [x] Document enhanced memory system implementation
- [x] Implement scout agent sub-agent
- [x] Document scout agent implementation
- [x] Add scout.md custom prompt for our subagent "scout"
- [x] Document prompt caching implementation
- [x] Fix failing tests after code restructuring (updated import paths)
- [x] Fix scout agent transfer back to main agent
- [x] Fix scout agent (web search agent) transfer back to main agent by correcting agent name mismatch ('main' vs 'beto')
- [x] Fix app_name parameter in session.py to align with agent names for proper agent transfers
- [x] Fix self.app_name in RadBotAgent class to ensure consistency for agent transfers
- [x] Force agent name consistency by explicitly setting root_agent.name to 'beto' when initializing
- [x] Fix all remaining instances of "app_name=radbot" throughout the codebase (memory_tools.py, memory_agent_factory.py, cli/main.py)
- [x] Implement bidirectional parent-child relationship between main agent and scout agent to fix "Agent beto not found in the agent tree" error
- [x] Improve agent tree initialization with empty sub_agents list before adding sub-agents to ensure proper registration
- [x] Fix memory system tests to properly mock PayloadSchemaType.DATETIME enum from qdrant_client

## Documentation Cleanup

- [ ] Create subdirectory structure in docs/implementation/ (core, components, integrations, fixes, enhancements, migrations)
- [ ] Merge 15_agent_config_integration.md and agent_config_integration.md
- [ ] Merge crawl4ai.md and crawl4ai_integration.md
- [ ] Merge memory_system.md and 16_memory_implementation.md
- [ ] Consolidate home-assistant.md, home_assistant_integration.md, and 08_mcp_home_assistant.md
- [ ] Merge gui.md and custom_web_ui.md
- [ ] Consolidate google-calendar documentation files
- [ ] Consolidate MCP fix documentation files
- [ ] Consolidate todo tools documentation files
- [ ] Consolidate crawl4ai documentation files
- [ ] Create index.md files for each subdirectory
- [ ] Create master index.md for the implementation directory
- [ ] Update cross-references between documentation files
- [ ] Add version tags to relevant documentation sections

## CLI & Interfaces

- [x] Implement CLI interface
- [ ] Create scheduler for background tasks
- [x] Add logging system
- [ ] Create cache status command-line utility
- [x] Implement custom FastAPI web interface
- [x] Create WebSocket-based chat interface
- [x] Document FastAPI web implementation

## Voice & Audio

- [x] ~~Implement ElevenLabs TTS integration~~ (Removed due to implementation issues)
- [x] ~~Replace ElevenLabs with Google Cloud TTS implementation~~ (Removed due to implementation issues)
- [x] ~~Create TTS service for ADK web interface~~ (Removed due to implementation issues)
- [x] ~~Implement JavaScript extension for voice capabilities~~ (Removed due to implementation issues)
- [x] ~~Document voice implementation~~ (Removed due to implementation issues)
- [x] Remove broken voice implementation and related dependencies

## Web UI Improvements

- [x] Create task sorting by status (in progress first, backlog second, done last)
- [x] Fix project filter to allow selecting individual projects when "All Projects" is selected
- [x] Add task styling improvements for better readability
- [x] Enable responsive view for mobile devices
- [x] Add border and elevation effects to task panel
- [x] Prevent tasks and events panels from being open simultaneously
- [x] Fix agent transfer functionality (solve "Malformed function call: transfer_to_agent" error)
- [x] Fix tasks and events not loading issue
- [x] Connect tasks panel to task API at port 8001
- [x] Add settings panel for API endpoint configuration
- [x] Add dark mode toggle support
- [ ] Add notification system for agent status and tasks
- [ ] Implement event filtering by timestamp