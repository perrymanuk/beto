## 📋 Current Tasks

### Agent Specialization and Multi-Agent System Implementation

This project aims to restructure our agent architecture into specialized agents with focused toolsets, reducing token usage and improving performance. It includes the implementation of Axel, a specialized execution agent that complements Scout's research capabilities, along with a dynamic worker system for parallel task execution.

#### Completed (Planning & Design Phase)
✅ Analyze current tools and their functions
✅ Group tools into logical categories based on functionality
✅ Define specialized agent roles based on tool categories
✅ Document agent specialization structure and configuration approach
✅ Add Agentic Coder agent type for prompt_claude and similar tools
✅ Design and document Axel agent for execution of Scout's design specs
✅ Research and document multi-agent transfer patterns for ADK with Vertex AI constraints
✅ Design and document Axel's dynamic worker system for parallel task execution
✅ Organize specialized agent documentation in a shared folder (`docs/implementation/specialized_agents/`)

#### Implementation Phase 1: Core Architecture
✅ Create specialized tool modules for each agent category
✅ Update AgentFactory to support specialized agent creation
✅ Implement "Modified Hub-and-Spoke Pattern with Directed Transfers" architecture
✅ Create custom transfer method for agents that need specific transfer targets
✅ Update configuration system to support specialized agents
✅ Create specialized instructions for each agent type

#### Implementation Phase 2: Axel Agent System
✅ Create Axel execution agent module structure
✅ Implement Axel agent with specialized execution capabilities
✅ Implement Axel's dynamic worker system with ParallelAgent
✅ Implement structured communication using Pydantic models
✅ Create domain-specific task division (code/docs/testing)
✅ Implement worker agent creation and management

#### Implementation Phase 3: Testing & Integration
✅ Modify main agent to detect specialization needs and perform transfers
✅ Test individual specialized agents with their specific toolsets
✅ Test Scout-to-Axel workflow for design-to-implementation tasks
✅ Test Axel's parallel worker system with various task types
⏱️ Optimize token usage and performance metrics
✅ Document final implementation details and usage examples

### MCP-Proxy Integration

#### Completed

✅ Research MCP-Proxy architecture and endpoints from documentation
✅ Design integration approach for MCP-Proxy similar to crawl4ai and claude-cli
✅ Create configuration template for MCP-Proxy integration in config.yaml
✅ Determine that existing MCPSSEClient supports the proxy connection pattern without modifications
✅ Verify that MCPClientFactory can properly handle these connections
✅ Create comprehensive documentation in docs/implementation/integrations/mcp_proxy.md
✅ Create test script to verify connections to all proxy endpoints
✅ Update config.yaml with all MCP-Proxy endpoints

#### To Do

⏱️ Test integration with each proxy endpoint (firecrawl-proxy, tavily-proxy, context7-proxy, webresearch-proxy, nomad-proxy)
⏱️ Create example agent that uses multiple proxy tools together
⏱️ Document common use cases and examples for the proxy integration

### Web UI Enhancements

#### Completed

✅ Add `/claude` command feature for templated prompts
✅ Create config schema for claude_templates
✅ Implement variable substitution for template arguments
✅ Create API endpoint for accessing claude_templates from config
✅ Add documentation for `/claude` command usage
✅ Add default behavior to send text directly to Claude when no template is specified
✅ Fix chat persistence message duplication issue
✅ Implement message sync tracking to prevent database bloat
✅ Reduce automatic sync frequency to improve performance 
✅ Implement context size limiting to reduce LLM token usage
✅ Implement dynamic context sizing based on message length
✅ Optimize token usage for simple queries like "hi"
✅ Document web chat persistence fix implementation
✅ Optimize system prompts to reduce token usage by ~80%
✅ Document prompt optimization implementation
✅ Split session.py into smaller modules for better maintainability

#### To Do

⏱️ Add TypeScript typing for claude_templates
⏱️ Add UI interface for managing/creating templates
⏱️ Add validation for template variables
⏱️ Implement full two-way sync for chat messages
⏱️ Add database cleanup for duplicate messages

### MCP Client Implementation Replacement with Standard SDK

Based on the analysis and migration plan in `docs/implementation/mcp/library_based_clients.md`, we have replaced our custom MCP client with a standardized implementation based on the MCP Python SDK.

#### Completed

✅ Add MCP SDK dependencies to pyproject.toml
✅ Create test script to validate the new MCP client with Crawl4AI
✅ Identify all code dependencies on the current MCP client
✅ Replace MCPSSEClient in client.py with the new implementation
✅ Update mcp_core.py for tool creation logic with new client
✅ Test with Crawl4AI servers
✅ Update documentation with detailed implementation notes
✅ Fix SSE connection issues for Crawl4AI servers
✅ Implement robust event handling for asynchronous tools
✅ Add persistent background thread for SSE connection

#### To Do

⏱️ Update MCPClientFactory to work better with the new client implementation
⏱️ Update/clean up server-specific implementations (e.g., Home Assistant)
⏱️ Update unit tests for MCP tools and utilities
⏱️ Test with Home Assistant and other MCP servers
⏱️ Validate proper ADK integration with all agent types
⏱️ Update examples that use MCP tools
⏱️ Clean up deprecated code and ensure consistent style

### Improved MCP SSE Client Implementation

The MCPSSEClient implementation has been improved to fix freezing issues during application startup and provide better reliability for MCP server connections.

#### Completed

✅ Created a more robust MCPSSEClient implementation in `radbot/tools/mcp/client.py`
✅ Implemented a multi-level approach to connecting to MCP servers and acquiring tools
✅ Added proper timeout handling and fallback mechanisms
✅ Added documentation for the implementation in `docs/implementation/fixes/mcp_sse_client_fix.md`

#### To Do

⏱️ Add a simple test script to verify the improved client works correctly
⏱️ Extend error handling for different MCP server implementations

### Migration of Crawl4AI to MCP Server Integration

The direct Crawl4AI integration has been deprecated in favor of using the MCP server approach exclusively. This change simplifies the codebase and provides a more consistent integration pattern.

#### Completed

✅ Created compatibility stubs for backward compatibility
✅ Updated imports in all affected files
✅ Updated agent.py to use the MCP server approach
✅ Added documentation for the migration
✅ Fixed MCP SSE client implementation to avoid freezing during startup

#### To Do

⏱️ Remove the entire `radbot/tools/crawl4ai` directory
⏱️ Update affected examples and tests

Note: The `radbot/tools/crawl4ai` directory should be completely removed after verifying that all functionality works correctly through the MCP server integration. This includes:

```
radbot/tools/crawl4ai/__init__.py
radbot/tools/crawl4ai/crawl4ai_extract_links.py
radbot/tools/crawl4ai/crawl4ai_ingest_and_read.py
radbot/tools/crawl4ai/crawl4ai_ingest_url.py
radbot/tools/crawl4ai/crawl4ai_query.py
radbot/tools/crawl4ai/crawl4ai_scan_links.py
radbot/tools/crawl4ai/crawl4ai_two_step_crawl.py
radbot/tools/crawl4ai/crawl4ai_vector_store.py
radbot/tools/crawl4ai/mcp_crawl4ai_client.py
radbot/tools/crawl4ai/utils.py
```

After removing this directory, you may need to update examples and test files that import directly from these modules.

See the migration doc at `docs/implementation/fixes/crawl4ai_mcp_migration.md` for more details.

### ADK 0.4.0 FunctionTool Parameter Fix

#### Completed

✅ Identified the issue with FunctionTool parameter mismatch in ADK 0.4.0
✅ Created test script to verify correct parameters for FunctionTool
✅ Fixed claude_prompt.py to use the correct 'func' parameter instead of 'function'
✅ Updated web/api/session.py to handle FunctionTool name resolution more robustly
✅ Added documentation in docs/implementation/fixes/adk_functiontool_parameter_fix.md
✅ Tested the fix by verifying Claude prompt tool creation works correctly

### Agent Context Separation Fix

#### Completed

✅ Identified the issue with context preservation between agents in transfers
✅ Modified agent_transfer.py to prevent forwarding prompts between agents
✅ Updated transfer_controller.py to use a neutral initialization message
✅ Implemented frontend context tracking for each agent
✅ Added explicit agent targeting in messages with AGENT:NAME:message format
✅ Implemented direct agent access for Scout in the websocket handler
✅ Enhanced _get_event_type in utils.py to properly detect transfer_to_agent tool calls
✅ Added special handling for transfer_to_agent in function_call and tool_call formats
✅ Fixed JavaScript syntax error in socket.js causing agent transfers to fail
✅ Fixed null reference in app_main.js breaking the application initialization
✅ Added proper error handling for DOM elements in JavaScript modules
✅ Updated socket.js to use ADK 0.4.0 style transfer detection via actions.transfer_to_agent
✅ Created comprehensive documentation in docs/implementation/fixes/agent_context_separation_fix.md
✅ Tested agent transfers between all specialized agents
✅ Verified proper transfer event recording in the web interface
✅ Verified no JavaScript errors appear in the browser console
✅ Fixed issue where agent transfers don't persist after the first message
✅ Fixed context tracking in chat.js to properly maintain agent targeting in messages
✅ Enhanced switchAgentContext function to ensure proper state persistence
✅ Added REST API fallback improvements for agent targeting
✅ Created documentation in docs/implementation/fixes/agent_transfer_persistence_fix.md

### Async Crawl4AI Client Fix

#### Completed

✅ Identified syntax error in async_crawl4ai_client.py causing high token usage
✅ Fixed function indentation to properly nest functions within async context manager
✅ Added proper cleanup in finally blocks for async methods
✅ Created documentation in docs/implementation/fixes/async_crawl4ai_client_fix.md
✅ Verified the fix corrected the "expected 'except' or 'finally' block" error
✅ Fixed indentation issues with nested functions in the implementation
✅ Fixed "coroutine 'AsyncCrawl4AIClient.initialize' was never awaited" warning
✅ Implemented proper async client handling in dynamic_tools_loader.py
✅ Added proper event loop management for async clients
✅ Fixed "Cannot run the event loop while another loop is running" error
✅ Implemented thread-based approach for isolating async operations

#### To Do

⏱️ Add test for the async client to validate correct functionality
⏱️ Update imports in related modules to use the fixed implementation

## 📋 Previously Completed Tasks

✅ Fix ADK built-in tools transfer issues
✅ Verify the fixes implemented in search_tool.py and code_execution_tool.py
✅ Create a test script to validate agent transfers between beto, scout, search_agent, and code_execution_agent
✅ Test bidirectional transfers between all agents
✅ Update documentation to reflect the fixes and transfer mechanism
✅ Fix the error with 'ToolGoogleSearch' import in search_test.py
✅ Fix the error with 'ToolCodeExecution' import in code_execution_test.py
✅ Add import compatibility fixes to search_tool.py and code_execution_tool.py
✅ Fix 'At most one tool is supported' error in test scripts
✅ Simplify agent.py to remove conditional logic (similar to ADK examples)
✅ Implement cleaner AgentTool-based approach in agent.py
✅ Test simplifications with search_test.py, code_execution_test.py, and test_adk_builtin_transfers.py
✅ Fix agent sub-agent creation in simplified implementation
✅ Fix artifact service initialization error in session.py
✅ Fix 'At most one tool is supported' error with Vertex AI for specialized agents
✅ Update code_execution_tool.py to use only one tool with Vertex AI
✅ Update search_tool.py to use only one tool with Vertex AI
✅ Add documentation for Vertex AI single-tool limitation fix
✅ Extend test_adk_builtin_transfers.py to validate Vertex AI compatibility
✅ Implement agent-specific model configuration in settings.py
✅ Update ConfigManager with get_agent_model method and fallback logic
✅ Add agent-specific model configuration to config schema
✅ Update specialized agent creation code to use agent-specific models
✅ Add tests for agent-specific model configuration