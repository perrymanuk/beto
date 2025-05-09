# Axel Agent Implementation

<!-- Version: 0.5.0 | Last Updated: 2025-05-09 -->

## Overview

This document details the implementation of the "Axel" agent, a specialized execution agent designed to complement Scout's research and design capabilities. Axel is dedicated to precise execution and implementation of specifications, focusing on turning design documents into working code.

## Implementation Components

The Axel agent is implemented using a modular architecture with the following components:

1. **ExecutionAgent Class**: The main wrapper class that interfaces with ADK and manages execution capabilities
2. **Dynamic Worker System**: A system for parallel task execution using worker agents
3. **Task Models**: Pydantic models for structured communication between Axel and its workers
4. **Specialized Execution Tools**: A set of tools specifically designed for implementation tasks

### Directory Structure

```
radbot/agent/execution_agent/
├── __init__.py           # Package exports
├── agent.py              # ExecutionAgent and AxelExecutionAgent classes
├── factory.py            # create_execution_agent factory function
├── models.py             # TaskInstruction and TaskResult models
└── tools.py              # Specialized execution tools
```

## Core Components

### ExecutionAgent Class

The `ExecutionAgent` class serves as the main wrapper around the ADK agent, providing specialized capabilities for execution tasks:

```python
class ExecutionAgent:
    """Agent specialized in executing and implementing specifications."""

    def __init__(
        self,
        name: str = "axel",
        model: Optional[str] = None,
        instruction: Optional[str] = None,
        description: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        enable_code_execution: bool = True,
        app_name: str = "beto",
        agent_factory: Optional[Any] = None,
    ):
        # Implementation details...
```

The `ExecutionAgent` provides methods for:
- Creating an ADK agent for integration with the agent system
- Setting up bidirectional transfers with related agents (e.g., Scout)
- Managing specialized execution tools

### AxelExecutionAgent Class

The `AxelExecutionAgent` class is the ADK implementation of Axel, which handles the dynamic worker system:

```python
class AxelExecutionAgent(BaseAgent):
    """Axel agent that can dynamically spawn worker agents."""
    
    # Class constants
    MAX_WORKERS: ClassVar[int] = 3
    WORKER_TIMEOUT_MS: ClassVar[int] = 15 * 60 * 1000  # 15 minutes
```

The `AxelExecutionAgent` handles:
- Dividing a specification into domain-specific tasks
- Creating and managing worker agents
- Executing tasks in parallel using `ParallelAgent`
- Collecting and aggregating results

### Task Models

The task models provide structured communication between Axel and its worker agents:

```python
class TaskType(str, Enum):
    """Types of tasks that can be performed by worker agents."""
    
    CODE_IMPLEMENTATION = "code_implementation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"

class TaskInstruction(BaseModel):
    """Instructions from Axel to a worker agent."""
    
    task_id: str
    task_type: TaskType
    specification: str
    context: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)

class TaskStatus(str, Enum):
    """Status of a task execution."""
    
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class TaskResult(BaseModel):
    """Results from a worker agent back to Axel."""
    
    task_id: str
    task_type: TaskType
    status: TaskStatus
    summary: str
    details: str
    artifacts: Dict[str, str] = Field(default_factory=dict)
    error_message: Optional[str] = None
```

### Specialized Execution Tools

The specialized execution tools provide Axel with capabilities specific to implementation tasks:

```python
# Code execution tool
def code_execution_tool(code: str, description: str = "") -> Dict[str, Any]:
    """Execute Python code safely in a controlled environment."""
    # Implementation details...

# Test execution tool
def run_tests(test_file: str, test_pattern: Optional[str] = None) -> Dict[str, Any]:
    """Run tests using pytest."""
    # Implementation details...

# Code validation tool
def validate_code(file_path: str) -> Dict[str, Any]:
    """Validate Python code for syntax and style issues."""
    # Implementation details...

# Documentation generation tool
def generate_documentation(file_path: str, output_format: str = "markdown") -> Dict[str, Any]:
    """Generate documentation for a Python file."""
    # Implementation details...
```

## Integration with Agent System

The Axel agent is integrated into the existing agent system through the `specialized_agent_factory.py` module:

```python
def create_axel_agent(root_agent: Agent) -> Optional[Agent]:
    """Create the Axel agent for implementation tasks."""
    # Implementation details...

def create_specialized_agents(root_agent: Agent) -> List[Agent]:
    """Create all specialized agents and register them with the root agent."""
    specialized_agents = []
    
    # Create and register Axel agent
    axel_agent = create_axel_agent(root_agent)
    if axel_agent:
        specialized_agents.append(axel_agent)
    
    # Future specialized agents would be created here
    
    return specialized_agents
```

## Dual-Agent Workflow: Scout and Axel

The Scout and Axel agents work together to provide a complete research-to-implementation workflow:

1. **Research & Design (Scout)**:
   - Research topics and gather information
   - Analyze requirements and constraints
   - Create design specifications
   - Transfer to Axel for implementation

2. **Implementation & Execution (Axel)**:
   - Receive design specifications from Scout
   - Divide work into specialized tasks
   - Execute tasks in parallel using worker agents
   - Aggregate results into a comprehensive implementation
   - Transfer back to Scout for refinement if needed

### Scout-to-Axel Transfer

The bidirectional Scout-to-Axel transfer is implemented using the agent transfer mechanism:

```python
# In specialized_agent_factory.py

# Make Scout aware of Axel
scout_sub_agents = list(scout_agent.sub_agents) if hasattr(scout_agent, 'sub_agents') and scout_agent.sub_agents else []

# Check if Axel is already in Scout's sub_agents
axel_already_added = False
for agent in scout_sub_agents:
    if hasattr(agent, 'name') and agent.name == "axel":
        axel_already_added = True
        break
        
if not axel_already_added:
    # Add a weak reference to avoid strong circular refs
    scout_sub_agents.append(proxy(adk_agent))
    scout_agent.sub_agents = scout_sub_agents
    logger.info("Added Scout → Axel reference (using proxy)")
```

## Worker Agent System

The worker agent system allows Axel to delegate specific tasks to dynamically created worker agents:

```python
class WorkerAgent(BaseAgent):
    """Worker agent that executes a specific task."""
    
    def __init__(
        self, 
        *, 
        name: str, 
        task_id: str, 
        task_instruction: TaskInstruction
    ):
        """Initialize a worker agent."""
        # Implementation details...

    async def _execute_task(self, task_instruction: TaskInstruction) -> TaskResult:
        """Execute the specific task based on instruction type."""
        # Implementation details...
```

The worker agent system provides several key advantages:
1. **Parallel Execution**: Concurrent execution of multiple subtasks
2. **Domain Specialization**: Each worker focuses on a specific domain (code, docs, tests)
3. **Resource Isolation**: Each worker has its own execution context
4. **Robust Error Handling**: Failures in one worker don't affect others

## Configuration Integration

The Axel agent is integrated with the configuration system to allow customization:

```yaml
# In config.yaml
model_config:
  main_model: "gemini-1.5-pro"
  sub_agent_model: "gemini-1.5-flash"
  axel_agent_model: "gemini-1.5-pro"
```

The configuration is accessed through the `config_manager`:

```python
# Get the model from config
axel_model = config_manager.get_agent_model("axel_agent_model")
if not axel_model:
    # Fallback to other configurations...
```

## Testing

A test script is provided to validate the Axel agent functionality:

```python
# In tools/test_axel_agent.py
async def test_axel_agent():
    """Test the Axel agent functionality."""
    # Test implementation...

def test_code_execution():
    """Test the code execution functionality of Axel."""
    # Test implementation...
```

## Usage Examples

### Creating an Axel Agent

```python
from radbot.agent.execution_agent import create_execution_agent

# Create an Axel agent
axel_agent = create_execution_agent(
    name="axel",
    model="gemini-1.5-pro",
    enable_code_execution=True
)

# Create an ADK agent from the wrapper
adk_agent = axel_agent.create_adk_agent()
```

### Transferring from Scout to Axel

```python
# In Scout agent's implementation
def transfer_to_axel(specification):
    """Transfer control to Axel with a specification."""
    return transfer_to_agent("axel", specification)
```

## Future Extensions

1. **Enhanced Task Division**: Improve the task division logic to better split work based on specification content
2. **Additional Worker Types**: Add more specialized worker types beyond the current code/docs/tests
3. **Result Aggregation**: Enhance the result aggregation to combine artifacts from different workers
4. **Persistent Worker Pool**: Implement a pool of persistent workers for improved performance
5. **User Feedback Loop**: Add support for user feedback during the implementation process

## Conclusion

The Axel agent implementation provides a powerful execution-focused complement to the Scout agent, creating a complete research-to-implementation workflow. The dynamic worker system enables parallel execution of tasks, improving efficiency and enabling more complex implementations.

By separating research and design (Scout) from execution and implementation (Axel), each agent can specialize in its domain, leading to better overall results and a more natural workflow that matches how humans typically approach complex tasks.