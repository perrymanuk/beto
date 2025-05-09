# Axel Dynamic Worker System

<!-- Version: 0.4.0 | Last Updated: 2025-05-09 -->

## Overview

This document details the implementation of Axel's dynamic worker system, which enables parallel execution of tasks using dynamically created worker agents. This system allows Axel to efficiently distribute and process complex implementation tasks by dividing them into smaller, parallel workloads.

## Design Goals

1. **Parallel Execution**: Enable concurrent execution of multiple subtasks to improve efficiency
2. **Dynamic Scaling**: Create exactly the number of worker agents needed for a specific execution
3. **Structured Communication**: Use well-defined data formats for task instructions and results
4. **Resource Management**: Control resource usage through worker limits and timeouts
5. **Task Isolation**: Ensure each worker has a clean execution context
6. **Robust Error Handling**: Gracefully handle worker failures without disrupting the entire execution
7. **Progress Tracking**: Provide visibility into task execution progress

## System Architecture

The dynamic worker system follows a "create and destroy" pattern, where Axel dynamically generates worker agents for each execution:

```
┌───────────────────────────────────────┐
│                                       │
│               Axel Agent              │
│         (Execution Coordinator)       │
│                                       │
└─────────────────┬─────────────────────┘
                  │
                  │ Creates dynamically
                  │
┌─────────────────┼─────────────────────┐
│                 │                     │
▼                 ▼                     ▼
┌───────────┐ ┌───────────┐       ┌───────────┐
│           │ │           │  ...  │           │
│  thing0   │ │  thing1   │       │  thing2   │
│           │ │           │       │           │
└───────────┘ └───────────┘       └───────────┘
```

### Components

1. **Axel Agent**: The main coordinator that receives the implementation specification, divides it into tasks, creates worker agents, and aggregates results.

2. **Worker Agents (thing0, thing1, thing2)**: Dynamically created agents that execute specific tasks based on the instructions from Axel. Each worker has a unique name and a fresh execution context.

3. **ParallelAgent**: An ADK workflow agent created by Axel to execute multiple worker agents concurrently.

4. **Task Instructions**: Pydantic models defining the structure of tasks sent from Axel to workers.

5. **Task Results**: Pydantic models defining the structure of results returned from workers to Axel.

## Data Models

### Task Instructions

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum

class TaskType(str, Enum):
    CODE_IMPLEMENTATION = "code_implementation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"

class TaskInstruction(BaseModel):
    """Instructions from Axel to a worker agent"""
    task_id: str = Field(..., description="Unique identifier for this task")
    task_type: TaskType = Field(..., description="Type of task to perform")
    specification: str = Field(..., description="Markdown documentation with task details")
    context: Dict[str, str] = Field(default_factory=dict, description="Additional context needed for task")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks this depends on")
```

### Task Results

```python
class TaskStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class TaskResult(BaseModel):
    """Results from a worker agent back to Axel"""
    task_id: str = Field(..., description="ID of the completed task")
    status: TaskStatus = Field(..., description="Completion status of the task")
    summary: str = Field(..., description="Brief summary of what was accomplished")
    details: str = Field(..., description="Detailed markdown description of work done")
    artifacts: Dict[str, str] = Field(default_factory=dict, description="Produced artifacts (code, docs, etc.)")
    error_message: Optional[str] = Field(None, description="Error details if status is FAILED")
```

## Implementation

### Axel Agent Implementation

```python
import asyncio
import secrets
from typing import ClassVar, List, Dict, Any, Optional
from pydantic import BaseModel, Field

from google.adk.agents import BaseAgent, ParallelAgent
from google.adk.events import Event, EventActions
from google.genai import types

# Import the TaskInstruction and TaskResult models defined above

class AxelExecutionAgent(BaseAgent):
    """Axel agent that can dynamically spawn worker agents."""
    
    # Class constants
    MAX_WORKERS: ClassVar[int] = 3
    WORKER_TIMEOUT_MS: ClassVar[int] = 15 * 60 * 1000  # 15 minutes
    
    async def _run_async_impl(self, ctx):
        # Extract the specification from the request
        specification = self._extract_specification(ctx.request)
        
        # Create an execution ID for this run
        execution_id = secrets.token_hex(4)
        
        # Divide the work into tasks
        tasks = await self._divide_work(specification)
        
        # Limit to MAX_WORKERS
        if len(tasks) > self.MAX_WORKERS:
            tasks = self._prioritize_tasks(tasks)[:self.MAX_WORKERS]
        
        # Create worker agents
        workers = []
        for i, task in enumerate(tasks):
            worker = WorkerAgent(
                name=f"thing{i}",
                task_id=task.task_id,
                task_instruction=task
            )
            workers.append(worker)
        
        # Yield initial event
        yield Event(
            author=self.name,
            content=types.Content(
                role="assistant",
                parts=[types.Part(text=f"Starting execution with {len(workers)} workers")]
            )
        )
        
        # Create a ParallelAgent with these workers
        parallel_executor = ParallelAgent(
            name=f"axel_executor_{execution_id}",
            sub_agents=workers
        )
        
        # Execute all workers in parallel with progress tracking
        completed = 0
        failed_tasks = []
        
        # Run the parallel executor
        async for event in parallel_executor.run_async(ctx):
            # Forward events
            yield Event(
                author=self.name,
                content=types.Content(
                    role="assistant", 
                    parts=[types.Part(text=f"Worker progress: {event.content}")]
                )
            )
            
            # Check for completion events
            if "task_completed" in event.actions.state_delta:
                completed += 1
                yield Event(
                    author=self.name,
                    content=types.Content(
                        role="assistant",
                        parts=[types.Part(text=f"Progress: {completed}/{len(workers)} tasks completed")]
                    )
                )
        
        # Collect results
        results = []
        for worker in workers:
            result_key = f"result:{worker.task_id}"
            if result_key in ctx.session.state:
                result = ctx.session.state[result_key]
                results.append(result)
                if result.status == TaskStatus.FAILED:
                    failed_tasks.append(result)
        
        # Handle failures if any
        if failed_tasks:
            failure_report = await self._handle_failures(failed_tasks)
            yield Event(
                author=self.name,
                content=types.Content(
                    role="assistant",
                    parts=[types.Part(text=failure_report)]
                )
            )
        
        # Aggregate results
        final_summary = await self._aggregate_results(results)
        
        # Return final summary
        yield Event(
            author=self.name,
            content=types.Content(
                role="assistant",
                parts=[types.Part(text=final_summary)]
            )
        )
    
    async def _divide_work(self, specification: str) -> List[TaskInstruction]:
        """Divide work from specification into 3 domain-specific tasks"""
        tasks = []
        
        # Create implementation task
        tasks.append(TaskInstruction(
            task_id=f"impl_{secrets.token_hex(4)}",
            task_type=TaskType.CODE_IMPLEMENTATION,
            specification=self._extract_implementation_specs(specification),
            context={}
        ))
        
        # Create documentation task
        tasks.append(TaskInstruction(
            task_id=f"docs_{secrets.token_hex(4)}",
            task_type=TaskType.DOCUMENTATION,
            specification=self._extract_documentation_specs(specification),
            context={}
        ))
        
        # Create testing task
        tasks.append(TaskInstruction(
            task_id=f"test_{secrets.token_hex(4)}",
            task_type=TaskType.TESTING,
            specification=self._extract_testing_specs(specification),
            context={}
        ))
        
        return tasks
    
    def _prioritize_tasks(self, tasks: List[TaskInstruction]) -> List[TaskInstruction]:
        """Prioritize tasks if we exceed MAX_WORKERS"""
        # For now, just return the first MAX_WORKERS tasks
        # This could be extended with more sophisticated prioritization
        return tasks[:self.MAX_WORKERS]
    
    def _extract_specification(self, request) -> str:
        """Extract the specification from the user request"""
        # Implementation depends on request format
        # Return the markdown specification text
        return request.content.text
        
    def _extract_implementation_specs(self, specification: str) -> str:
        """Extract implementation-specific parts of the specification"""
        # Implementation-specific logic to extract relevant parts
        # Could use LLM to intelligently divide the spec
        return specification
        
    def _extract_documentation_specs(self, specification: str) -> str:
        """Extract documentation-specific parts of the specification"""
        # Documentation-specific logic to extract relevant parts
        return specification
        
    def _extract_testing_specs(self, specification: str) -> str:
        """Extract testing-specific parts of the specification"""
        # Testing-specific logic to extract relevant parts
        return specification
    
    async def _handle_failures(self, failed_tasks: List[TaskResult]) -> str:
        """Handle and report failed tasks"""
        failure_report = "## Task Execution Failures\n\n"
        
        for task in failed_tasks:
            failure_report += f"### Failed Task: {task.task_id}\n"
            failure_report += f"**Type:** {task.task_type}\n"
            failure_report += f"**Error:** {task.error_message}\n\n"
            failure_report += "**Instructions that failed:**\n```\n"
            failure_report += task.details + "\n```\n\n"
        
        return failure_report
    
    async def _aggregate_results(self, results: List[TaskResult]) -> str:
        """Aggregate results from all workers into a comprehensive summary"""
        summary = "# Execution Summary\n\n"
        
        # Group results by task type
        by_type = {}
        for result in results:
            if result.task_type not in by_type:
                by_type[result.task_type] = []
            by_type[result.task_type].append(result)
        
        # Summarize each task type
        for task_type, type_results in by_type.items():
            summary += f"## {task_type.value.title()} Results\n\n"
            
            for result in type_results:
                summary += f"### {result.task_id}\n"
                summary += f"{result.summary}\n\n"
            
            # Add overall summary for this type
            summary += f"**Overall {task_type.value} progress:** "
            summary += f"{len([r for r in type_results if r.status == TaskStatus.COMPLETED])} completed, "
            summary += f"{len([r for r in type_results if r.status == TaskStatus.FAILED])} failed, "
            summary += f"{len([r for r in type_results if r.status == TaskStatus.PARTIAL])} partial\n\n"
        
        return summary
```

### Worker Agent Implementation

```python
class WorkerAgent(BaseAgent):
    """Worker agent that executes a specific task."""
    
    def __init__(self, *, name: str, task_id: str, task_instruction: TaskInstruction):
        super().__init__(name=name)
        self._task_id = task_id
        self._task_instruction = task_instruction
        
    async def _run_async_impl(self, ctx):
        # Initialize
        yield Event(
            author=self.name,
            content=types.Content(
                role=self.name, 
                parts=[types.Part(text=f"Starting task {self._task_id} of type {self._task_instruction.task_type}")]
            )
        )
        
        # Execute with timeout protection
        try:
            result = await asyncio.wait_for(
                self._execute_task(self._task_instruction),
                timeout=15 * 60  # 15 minutes
            )
        except asyncio.TimeoutError:
            result = TaskResult(
                task_id=self._task_id,
                status=TaskStatus.FAILED,
                summary="Task execution timed out after 15 minutes",
                details="The worker agent did not complete within the allocated time limit.",
                error_message="Execution timeout (15 minutes)"
            )
        except Exception as e:
            result = TaskResult(
                task_id=self._task_id,
                status=TaskStatus.FAILED,
                summary=f"Task execution failed with error: {str(e)}",
                details=f"Error details: {str(e)}",
                error_message=str(e)
            )
        
        # Store result in state
        result_key = f"result:{self._task_id}"
        
        # Return completion event
        yield Event(
            author=self.name,
            content=types.Content(
                role=self.name, 
                parts=[types.Part(text=f"Completed task {self._task_id} with status: {result.status}")]
            ),
            actions=EventActions(
                state_delta={
                    result_key: result,
                    "task_completed": True
                }
            )
        )

    async def _execute_task(self, task_instruction: TaskInstruction) -> TaskResult:
        """Execute the specific task based on instruction type"""
        if task_instruction.task_type == TaskType.CODE_IMPLEMENTATION:
            return await self._execute_implementation_task(task_instruction)
        elif task_instruction.task_type == TaskType.DOCUMENTATION:
            return await self._execute_documentation_task(task_instruction)
        elif task_instruction.task_type == TaskType.TESTING:
            return await self._execute_testing_task(task_instruction)
        else:
            raise ValueError(f"Unknown task type: {task_instruction.task_type}")
    
    async def _execute_implementation_task(self, task_instruction: TaskInstruction) -> TaskResult:
        """Execute code implementation task"""
        # Implementation-specific logic
        # Use LLM to process the markdown specification and generate code
        
        # Return result
        return TaskResult(
            task_id=task_instruction.task_id,
            status=TaskStatus.COMPLETED,
            summary="Implemented code according to specification",
            details="Detailed implementation report...",
            artifacts={"implementation.py": "# Generated code..."}
        )
    
    async def _execute_documentation_task(self, task_instruction: TaskInstruction) -> TaskResult:
        """Execute documentation task"""
        # Documentation-specific logic
        return TaskResult(
            task_id=task_instruction.task_id,
            status=TaskStatus.COMPLETED,
            summary="Created documentation according to specification",
            details="Detailed documentation report...",
            artifacts={"README.md": "# Documentation..."}
        )
    
    async def _execute_testing_task(self, task_instruction: TaskInstruction) -> TaskResult:
        """Execute testing task"""
        # Testing-specific logic
        return TaskResult(
            task_id=task_instruction.task_id,
            status=TaskStatus.COMPLETED,
            summary="Created tests according to specification",
            details="Detailed testing report...",
            artifacts={"test_implementation.py": "# Test code..."}
        )
```

## Integration with Agent Factory

The Axel dynamic worker system can be integrated into the agent factory as follows:

```python
from radbot.agent.execution_agent.agent import AxelExecutionAgent

def create_axel_agent(
    name: str = "axel",
    model: Optional[str] = None,
    tools: Optional[List] = None,
    instruction_name: str = "axel",
    config: Optional[ConfigManager] = None
) -> Agent:
    """Create the Axel execution agent."""
    
    # Use agent-specific model or fall back to default
    if model is None:
        model = config_manager.get_agent_model("axel_agent")
        logger.info(f"Using model from config for axel_agent: {model}")
    
    # Get the instruction
    try:
        instruction = cfg.get_instruction(instruction_name)
    except FileNotFoundError:
        logger.warning(f"Instruction '{instruction_name}' not found for axel agent, using minimal instruction")
        instruction = "You are Axel, a specialized execution agent."
    
    # Create the Axel agent
    axel_agent = AxelExecutionAgent(
        name=name,
        model=model,
        instruction=instruction,
        # Add any other required parameters
    )
    
    # Return the agent
    return axel_agent
```

## Sequence Diagram

The following sequence diagram illustrates the execution flow of Axel's dynamic worker system:

```
┌─────┐          ┌────┐          ┌────────────┐          ┌───────┐
│Scout│          │Axel│          │ParallelAgent│          │thing[N]│
└──┬──┘          └─┬──┘          └─────┬──────┘          └───┬───┘
   │               │                    │                     │
   │ Transfer spec │                    │                     │
   │──────────────>│                    │                     │
   │               │                    │                     │
   │               │ Divide work        │                     │
   │               │─────────────┐      │                     │
   │               │             │      │                     │
   │               │<────────────┘      │                     │
   │               │                    │                     │
   │               │ Create workers     │                     │
   │               │─────────────┐      │                     │
   │               │             │      │                     │
   │               │<────────────┘      │                     │
   │               │                    │                     │
   │               │Create ParallelAgent│                     │
   │               │──────────────────->│                     │
   │               │                    │                     │
   │               │                    │ Execute workers     │
   │               │                    │────────────────────>│
   │               │                    │                     │
   │               │                    │      Progress       │
   │               │<───────────────────┼─────────────────────│
   │               │                    │                     │
   │               │                    │     Task result     │
   │               │                    │<────────────────────│
   │               │                    │                     │
   │               │    All results     │                     │
   │               │<───────────────────│                     │
   │               │                    │                     │
   │               │ Aggregate results  │                     │
   │               │─────────────┐      │                     │
   │               │             │      │                     │
   │               │<────────────┘      │                     │
   │               │                    │                     │
   │ Final summary │                    │                     │
   │<──────────────│                    │                     │
   │               │                    │                     │
```

## Integration with Scout

The Axel dynamic worker system is designed to integrate with Scout as follows:

1. Scout researches and creates a comprehensive design specification in markdown format
2. Scout transfers control to Axel along with the specification
3. Axel divides the work into domain-specific tasks:
   - Code implementation
   - Documentation
   - Testing
4. Axel creates dynamic worker agents ("thing0", "thing1", "thing2") for each task
5. Workers execute tasks in parallel
6. Axel aggregates the results and provides a summary
7. Axel transfers control back to Scout with the execution summary

## Error Handling

The system includes the following error handling mechanisms:

1. **Worker Timeouts**: Each worker has a 15-minute execution timeout
2. **Exception Handling**: Exceptions in worker execution are caught and reported
3. **Partial Execution**: If some workers fail and others succeed, Axel will aggregate the successful results and report the failures
4. **Resource Limits**: The maximum number of concurrent workers is limited to 3

## Conclusion

The Axel dynamic worker system provides a powerful mechanism for parallel task execution within the ADK framework. By dynamically creating worker agents and executing them in parallel, Axel can efficiently process complex implementation tasks divided across multiple domains. The system includes robust error handling, resource management, and result aggregation capabilities.

This architecture enables Axel to serve as an effective complement to Scout in the design-to-implementation workflow, bridging the gap between research/design and precise implementation.