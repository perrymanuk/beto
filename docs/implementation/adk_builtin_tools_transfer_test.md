# ADK Built-in Tools Transfer Test Guide

This document provides step-by-step instructions for testing agent transfers between the main agent and ADK built-in tool agents (Google Search and Code Execution).

## Prerequisites

- Ensure you have the latest version of the codebase
- Make sure all dependencies are installed (run `make setup`)
- Verify you have Google API credentials configured properly

## Test Setup

1. Run the test script to start the web application:

```bash
python tools/test_adk_builtin_transfers.py
```

This script:
- Enables the ADK built-in search and code execution tools
- Sets verbose logging for debugging
- Starts the web application

2. Open a browser and navigate to: http://localhost:8080

## Test Cases

### Test Case 1: Transfer to Google Search Agent

1. Enter the following message in the chat:
   ```
   What are the current trending AI news stories?
   ```

2. Observe the response. The main agent should:
   - Identify this requires current information
   - Transfer to the search agent
   - The search agent should respond with current AI news results

3. Check terminal logs for:
   - `PATCHED LLM _get_agent_to_run called for agent: 'search_agent'`
   - `LLM Flow patched lookup returning built-in agent 'search_agent'`

### Test Case 2: Transfer back from Google Search Agent

1. After receiving search results, enter:
   ```
   Thank you for the search results. Can you summarize them for me?
   ```

2. The search agent should:
   - Complete its task
   - Transfer back to the main beto agent
   - The main agent should provide a summary

3. Check terminal logs for:
   - `PATCHED LLM _get_agent_to_run called for agent: 'beto'`
   - `LLM Flow patched lookup returning root_agent for 'beto'`

### Test Case 3: Transfer to Code Execution Agent

1. Enter the following message:
   ```
   Can you write a Python function to calculate the Fibonacci sequence up to n terms?
   ```

2. Observe the response. The main agent should:
   - Identify this requires code execution
   - Transfer to the code execution agent
   - The code execution agent should write and run the requested code

3. Check terminal logs for:
   - `PATCHED LLM _get_agent_to_run called for agent: 'code_execution_agent'`
   - `LLM Flow patched lookup returning built-in agent 'code_execution_agent'`

### Test Case 4: Transfer back from Code Execution Agent

1. After receiving code execution results, enter:
   ```
   Thanks for the code. Can you explain how this algorithm works?
   ```

2. The code execution agent should:
   - Complete its explanation
   - Transfer back to the main beto agent
   - The main agent should provide additional explanation

3. Check terminal logs for:
   - `PATCHED LLM _get_agent_to_run called for agent: 'beto'`
   - `LLM Flow patched lookup returning root_agent for 'beto'`

## Expected Results

If the agent transfer fix is working correctly:

1. Each transfer should occur smoothly without errors in the logs
2. The correct agent should respond to each request
3. The logs should show our patched methods handling the agent lookups
4. Transfers in both directions should work (to built-in agents and back)

## Troubleshooting

If transfers fail:

1. **Check logs for errors**:
   - Look for error messages related to agent transfers
   - Verify that the patched methods are being called

2. **Verify agent registration**:
   - Check logs for sub-agent list at startup
   - Confirm both built-in agents are in the sub-agents list

3. **Check tool availability**:
   - Look for log messages about `transfer_to_agent` availability
   - Verify built-in agents have the required tools

4. **Test direct transfers**:
   - Try using explicit transfer commands like:
     ```
     transfer_to_agent(agent_name="search_agent")
     ```
     and
     ```
     transfer_to_agent(agent_name="beto")
     ```

## Recording Results

Document the test results for future reference, noting:

1. Whether each test case passed or failed
2. Any unexpected behavior or warnings
3. Relevant log messages that helped diagnose issues
4. Suggested improvements for future implementation