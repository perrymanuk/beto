# ADK Built-in Tools Transfer Testing

## Overview

This document describes how to test agent transfers between the main agent (beto), research agent (scout), and ADK built-in agents (search_agent, code_execution_agent). It outlines the available testing tools and approaches to validate that agent transfers work correctly.

## Testing Utilities

### 1. `test_adk_builtin_transfers.py` Script

We've created a dedicated test script to validate agent transfers:

```bash
# Path: tools/test_adk_builtin_transfers.py

# Run validation tests (programmatic validation)
python -m tools.test_adk_builtin_transfers --validate

# Run web application for manual testing
python -m tools.test_adk_builtin_transfers --web
```

#### Validation Mode

The validation mode (`--validate`) tests different configurations:

1. No built-in tools enabled
2. Only search enabled
3. Only code execution enabled
4. Both built-in tools enabled

For each configuration, it checks:
- If the source agent has the transfer_to_agent tool
- If the target agent is in the source agent's sub_agents list
- Whether transfers are expected to work based on these criteria

The validation reports a summary showing which transfers are valid and which have issues.

#### Web Mode

The web mode (`--web`) starts the web application with all built-in agents enabled, allowing you to manually test transfers by:

1. Starting a conversation
2. Asking the agent to search for something (triggers transfer to search_agent)
3. Asking the agent to execute code (triggers transfer to code_execution_agent)
4. Testing transfers from these agents back to beto

### 2. Environment Controls

You can control which built-in tools are enabled using environment variables:

```bash
# Enable/disable ADK built-in search
export RADBOT_ENABLE_ADK_SEARCH=true  # or false

# Enable/disable ADK built-in code execution
export RADBOT_ENABLE_ADK_CODE_EXEC=true  # or false

# Force enable code execution (useful for testing)
export RADBOT_FORCE_CODE_EXEC=true
```

### 3. Test Examples

#### Code Execution Transfer Test

The following code can be used to test the code execution agent transfer:

```python
# Run this in the web application 
# (Should trigger transfer to code_execution_agent)

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Calculate and print the 10th Fibonacci number
result = calculate_fibonacci(10)
print(f"The 10th Fibonacci number is: {result}")
```

After execution, the agent should transfer back to beto.

#### Search Transfer Test

Test the search agent with:

```
Please search for the latest news on quantum computing.
```

This should trigger a transfer to the search_agent, and after providing results, it should transfer back to beto.

#### Scout Transfer Test

Test the Scout agent with:

```
I need research on the environmental impact of electric vehicles.
```

This should trigger a transfer to Scout, which should be able to transfer back to beto when done.

## Debugging Transfer Issues

### Common Issues and Solutions

1. **Missing sub-agent relationships**
   - Ensure the target agent is in the source agent's sub_agents list
   - For bidirectional transfers, both agents need to have each other in their sub_agents lists

2. **Missing transfer_to_agent tool**
   - All agents must have the transfer_to_agent tool in their tools list

3. **Incorrect agent names**
   - Agent names must be consistent: "beto", "scout", "search_agent", "code_execution_agent"
   - Transfers won't work if the name doesn't match exactly

4. **LlmAgent config errors**
   - LlmAgent objects need proper configuration for Vertex AI 
   - Use proper error handling when configuring LlmAgent objects

### Checking Agent Configuration

Use these log statements to debug agent relationships:

```python
logger.info(f"Agent name: {agent.name if hasattr(agent, 'name') else 'unnamed'}")
logger.info(f"Sub-agents: {[sa.name for sa in agent.sub_agents if hasattr(sa, 'name')]}")
logger.info(f"Tools: {[getattr(t, 'name', str(t)) for t in agent.tools]}")
```

## What Makes Transfers Work

For transfers to work correctly between agents in ADK 0.4.0+:

1. The source agent must have the transfer_to_agent tool
2. The target agent must be in the source agent's sub_agents list
3. For bidirectional transfers, both agents must have each other in their sub_agents lists

Our implementation ensures these conditions are met by:

1. Adding the transfer_to_agent tool to all agents
2. Creating proxy agents when needed to establish parent-child relationships
3. Adding each agent to the other's sub_agents list for bidirectional navigation