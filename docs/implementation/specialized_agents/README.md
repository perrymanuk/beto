# Specialized Agents Documentation

This directory contains documentation related to the specialized agent architecture and implementation for RadBot.

## Overview

The specialized agent architecture divides agent functionality into focused domains, with each agent having access only to the tools it needs. This approach reduces token usage, improves performance, and allows for more specialized capabilities.

## Documents

1. [Agent Specialization](agent_specialization.md) - Overall architecture and categorization of specialized agents
2. [Multi-Agent Transfer Pattern](multi_agent_transfer_pattern.md) - Design patterns for agent communication and transfers
3. [Axel Agent](axel_agent.md) - Design of the Axel execution agent to complement Scout
4. [Axel Dynamic Worker System](axel_dynamic_worker_system.md) - Implementation of Axel's parallel task execution system

## Agent Categories

The specialized agent architecture includes the following agent types:

1. **File System Agent** - File operations and search
2. **Web Research Agent** - Web searches and content extraction
3. **Memory Agent** - Conversation history and knowledge management
4. **Todo Management Agent** - Task and project tracking
5. **Calendar Agent** - Event scheduling and management
6. **Home Assistant Agent** - Smart home device control
7. **Code Execution Agent** - Shell commands and code running
8. **Agentic Coder Agent** - Delegation to other models via prompt_claude
9. **Scout Agent** - Research and design planning
10. **Axel Agent** - Implementation and execution
11. **Core Utility Agent** - Common utilities needed across agents

## Implementation Approach

The specialized agent system uses a "Modified Hub-and-Spoke Pattern with Directed Transfers" where:

1. **Central Orchestrator (Beto)**: Can transfer to any specialized agent
2. **Specialized Agents**: Focus on specific domains with relevant toolsets
3. **Directed Transfers**: Specific allowed transfer paths (e.g., Scout ↔ Axel)
4. **Dynamic Workers**: Axel can create worker agents ("thing0", "thing1", etc.) for parallel execution

## Next Steps

Future implementation work includes:

1. Creating specialized tool modules for each agent category
2. Implementing the agent transfer mechanism
3. Updating configuration system to support specialized agents
4. Creating specialized instructions for each agent type
5. Testing and optimizing the system

## Related Files

- Configuration: `/Users/perry.manuk/git/perrymanuk/radbot/radbot/config/default_configs/instructions/axel.md`