## 📋 Current Tasks

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