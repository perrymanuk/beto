# Multi-Agent Transfer Pattern for Specialized Agents

<!-- Version: 0.4.0 | Last Updated: 2025-05-09 -->

## Overview

This document outlines the recommended design patterns for implementing multi-agent transfers within our specialized agent architecture. It focuses specifically on the constraints of using Vertex AI and addresses the challenge of organizing agents with specialized toolsets.

## Vertex AI Constraints

When working with Vertex AI and ADK, we face several important constraints that shape our multi-agent architecture:

1. **Single Tool Limitation**: When using Vertex AI, each agent can only use one built-in tool. This is a critical constraint expressed in the error message "At most one tool is supported."

2. **Parent-Child Relationship**: In ADK, each agent can only have one parent (the "Single Parent Rule"). This creates a tree structure where an agent instance can only be added as a sub-agent once.

3. **Agent Name Uniqueness**: Each agent in the hierarchy must have a unique name for proper routing and delegation.

## Multi-Agent Architecture Models

Based on these constraints, we can implement three main architectural patterns for our specialized agents:

### 1. Hub-and-Spoke Pattern

In this pattern, a central "hub" agent (the Main Orchestrator) connects to multiple "spoke" agents (specialized agents). The hub agent has no tools of its own but can transfer to any specialized agent.

```
                    ┌─────────────────┐
                    │                 │
                    │ Main Orchestrator │
                    │                 │
                    └─────────────────┘
                            │
                            │
        ┌───────────┬───────┴───────┬───────────┐
        │           │               │           │
        ▼           ▼               ▼           ▼
┌─────────────┐ ┌─────────┐   ┌─────────┐ ┌─────────────┐
│ File System │ │   Web   │   │  Home   │ │    Axel     │
│    Agent    │ │ Research│   │Assistant│ │  Execution  │
└─────────────┘ └─────────┘   └─────────┘ └─────────────┘
```

#### Advantages:
- Simple routing logic - the main agent can transfer to any specialized agent
- Specialized agents only need tools relevant to their domain
- Clear separation of concerns

#### Disadvantages:
- All transfers must go through the main agent
- No direct communication between specialized agents
- Main agent must understand and route all requests

### 2. Tree Hierarchy Pattern

This pattern organizes agents in a hierarchical tree structure, with domain-specific agents grouped under category managers.

```
                    ┌─────────────────┐
                    │                 │
                    │ Main Orchestrator │
                    │                 │
                    └─────────────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
        ┌─────────────────┐   ┌────────────────┐
        │                 │   │                │
        │  Data Services  │   │ Home Services  │
        │                 │   │                │
        └─────────────────┘   └────────────────┘
                 │                    │
        ┌────────┴─────────┐   ┌─────┴──────┐
        │                  │   │            │
        ▼                  ▼   ▼            ▼
┌─────────────┐    ┌─────────────┐ ┌─────────────┐
│ File System │    │   Memory    │ │    Home     │
│    Agent    │    │    Agent    │ │  Assistant  │
└─────────────┘    └─────────────┘ └─────────────┘
```

#### Advantages:
- Hierarchical organization reflects logical domains
- Mid-level managers can handle routing within their domain
- Reduces burden on main agent

#### Disadvantages:
- More complex to implement
- Longer transfer chains for cross-domain tasks
- Additional management overhead

### 3. Mesh Network Pattern with Restricted Transfers

This pattern allows certain specialized agents to transfer directly to other specialized agents based on common workflows, while still maintaining a central orchestrator.

```
                    ┌─────────────────┐
                    │                 │
                    │ Main Orchestrator │
                    │                 │
                    └─────────────────┘
                      ▲│            ▲│
                      │└────┐  ┌────┘│
                      │     │  │     │
                      │     ▼  │     ▼
              ┌───────┴───┐     ┌────────────┐
              │           │     │            │
              │   Scout   │◄────►    Axel    │
              │           │     │            │
              └───────────┘     └────────────┘
                │      ▲         ▲      │
                │      │         │      │
                ▼      │         │      ▼
           ┌─────────────┐     ┌─────────────┐
           │     Web     │     │    Code     │
           │   Research  │     │  Execution  │
           └─────────────┘     └─────────────┘
```

#### Advantages:
- Enables direct transfers for common workflows (e.g., Scout → Axel)
- Reduces latency for multi-step processes
- Still maintains central coordination when needed

#### Disadvantages:
- More complex transfer logic
- Potential for transfer cycles if not carefully designed
- Requires clear documentation of permitted transfers

## Recommended Transfer Pattern for Our Architecture

Based on our specialized agent design and the constraints of Vertex AI, we recommend implementing a **Modified Hub-and-Spoke Pattern with Directed Transfers**:

```
                    ┌─────────────────┐
                    │                 │
                    │ Main Orchestrator │
                    │     (Beto)      │
                    └─────────────────┘
                       ▲│          ▲│
                       │└──────────┘│
                       │            │
        ┌──────────────┼────────────┼──────────────┐
        │              │            │              │
        ▼              ▼            │              ▼
┌─────────────┐  ┌──────────┐       │        ┌──────────┐
│ File System │  │ Memory   │       │        │ Calendar │
│    Agent    │  │  Agent   │       │        │  Agent   │
└─────────────┘  └──────────┘       │        └──────────┘
                                    │
        ┌────────────────────────────┤
        │                            │
        ▼                            │
┌─────────────┐                      │
│  Agentic    │                      │
│   Coder     │                      │
└─────────────┘                      │
                                     │
        ┌─────────────────────────────┤
        │                             │
        ▼                             │
┌─────────────┐                       │
│    Home     │                       │
│  Assistant  │                       │
└─────────────┘                       │
                                      │
       ┌──────────────────────────────┤
       │                              │
       ▼                              │
┌─────────────┐                       │
│    Todo     │                       │
│    Agent    │                       │
└─────────────┘                       │
                                      │
       ┌──────────────────────────────┤
       │                              │
       ▼                              │
┌─────────────┐     ┌───────┐         │
│    Scout    │◄───►│ Axel  │─────────┘
└─────────────┘     └───────┘
       │
       ▼
┌─────────────┐
│    Web      │
│  Research   │
└─────────────┘
```

### Key Features:

1. **Central Orchestrator**: Beto serves as the main orchestrator, able to transfer to any specialized agent.

2. **Single-Tool Specialized Agents**: Each specialized agent focuses on one domain with its specific toolset.

3. **Directed Transfers**: Specific transfer paths are defined for common workflows:
   - Scout ↔ Axel: Research/design to implementation transfer
   - Scout → Web Research: For deeper research tasks
   - All agents → Beto: Return transfer to main agent

4. **Transfer Rules**:
   - The main agent (Beto) can transfer to any specialized agent
   - Specialized agents can transfer back to the main agent (Beto)
   - Scout can transfer to/from Axel (bidirectional)
   - Scout can transfer to Web Research (unidirectional)
   - All other transfers must go through the main agent

## Implementation Guidelines

To implement this pattern effectively:

### 1. Agent Creation

When creating specialized agents, ensure each has:
- A unique, descriptive name
- Clear purpose description for proper routing
- Single parent (except Scout/Axel which will have direct references to each other)
- Properly configured toolset specific to its domain

### 2. Transfer Mechanism

For each agent type, implement the transfer mechanism with appropriate constraints:

```python
# In the main agent (Beto)
def create_root_agent():
    # Create all specialized agents
    filesystem_agent = create_filesystem_agent()
    memory_agent = create_memory_agent()
    calendar_agent = create_calendar_agent()
    agentic_coder_agent = create_agentic_coder_agent()
    home_assistant_agent = create_home_assistant_agent()
    todo_agent = create_todo_agent()
    scout_agent = create_scout_agent()
    axel_agent = create_axel_agent()
    web_research_agent = create_web_research_agent()
    
    # Set up the special Scout-Axel bidirectional link
    scout_agent.add_specific_transfer_target(axel_agent)
    axel_agent.add_specific_transfer_target(scout_agent)
    
    # Set up Scout-Web Research link
    scout_agent.add_specific_transfer_target(web_research_agent)
    
    # Add all specialized agents as sub-agents of Beto
    root_agent = Agent(
        name="beto",
        # other parameters...
        sub_agents=[
            filesystem_agent,
            memory_agent,
            calendar_agent,
            agentic_coder_agent,
            home_assistant_agent,
            todo_agent,
            scout_agent,
            axel_agent,
            web_research_agent
        ]
    )
    
    return root_agent
```

### 3. Custom Transfer Method

Implement a custom transfer method for specialized agents that need to transfer to specific targets:

```python
class SpecializedAgent(Agent):
    def __init__(self, name, allowed_transfer_targets=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.allowed_transfer_targets = allowed_transfer_targets or []
    
    def add_specific_transfer_target(self, agent):
        """Add a specific agent that this agent can transfer to."""
        self.allowed_transfer_targets.append(agent)
    
    def can_transfer_to(self, agent_name):
        """Check if this agent can transfer to the specified agent."""
        # Can always transfer back to parent
        if self.parent_agent and self.parent_agent.name == agent_name:
            return True
        
        # Check specific allowed targets
        for agent in self.allowed_transfer_targets:
            if agent.name == agent_name:
                return True
        
        return False
```

### 4. Configuration

Update the configuration system to support specialized agent model configuration:

```yaml
model_config:
  main_model: "gemini-1.5-pro"
  sub_agent_model: "gemini-1.5-flash"
  specialized_agents:
    filesystem_agent_model: "gemini-1.5-flash"
    memory_agent_model: "gemini-1.5-flash"
    calendar_agent_model: "gemini-1.5-flash"
    agentic_coder_agent_model: "gemini-1.5-pro"
    home_assistant_agent_model: "gemini-1.5-flash"
    todo_agent_model: "gemini-1.5-flash"
    scout_agent_model: "gemini-1.5-pro"
    axel_agent_model: "gemini-1.5-pro"
    web_research_agent_model: "gemini-1.5-pro"
```

## Benefits

This transfer pattern offers several benefits:

1. **Compliance with Vertex AI Constraints**: By ensuring each specialized agent has only the tools it needs, we avoid the "At most one tool is supported" limitation.

2. **Clear Transfer Structure**: Agents know exactly which other agents they can transfer to, reducing confusion and errors.

3. **Optimized Workflows**: Direct transfers between Scout and Axel enable efficient design-to-implementation workflows.

4. **Scalability**: New specialized agents can be added without disrupting the existing structure.

5. **Maintainability**: Each agent has a clear, focused responsibility and set of tools.

## Conclusion

The Modified Hub-and-Spoke Pattern with Directed Transfers provides an effective architecture for our specialized agent system within the constraints of Vertex AI. By following these guidelines, we can create a system that balances flexibility with structure, enabling complex workflows while maintaining clear boundaries between agent responsibilities.

This architecture can be extended or modified as new requirements emerge, but the core principles of clear agent responsibilities, defined transfer paths, and toolset specialization should be maintained.