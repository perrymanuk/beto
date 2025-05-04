# Todo Tools Update Functionality

## Overview

This document describes the update functionality added to the Todo Tools system. This functionality allows users to modify existing tasks and projects, changing details such as descriptions, status, categories, and project names.

## New Features

Two new tools have been implemented:

1. **update_task_tool**: Allows for updating any attribute of an existing task
2. **update_project_tool**: Allows for renaming existing projects

## Database Changes

New database functions have been added to support the update operations:

- `update_task`: Updates a task with specified fields
- `update_project`: Updates a project's name
- `get_task`: Retrieves a specific task by ID
- `get_project`: Retrieves a specific project by ID

## API Functions

### Update Task

```python
def update_task(task_id: str, description: Optional[str] = None, 
               project_id: Optional[str] = None, status: Optional[str] = None,
               category: Optional[str] = None, origin: Optional[str] = None,
               related_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
```

This function allows updating any of the following task attributes:
- **description**: Change the task text
- **project_id**: Move the task to a different project
- **status**: Change the status ('backlog', 'inprogress', 'done')
- **category**: Update or add a category label
- **origin**: Change the origin information
- **related_info**: Update supplementary data

Only the fields that are provided (not None) will be updated; all other fields remain unchanged. The function validates inputs, checks for the task's existence, and returns both the task ID and the updated task data.

### Update Project

```python
def update_project(project_id: str, name: str) -> Dict[str, Any]:
```

This function renames a project. It validates the project ID, checks for the project's existence, and ensures the new name doesn't conflict with existing projects.

## Usage Examples

### Updating a Task

```python
# Update a task's description
agent.tools.update_task(
    task_id="123e4567-e89b-12d3-a456-426614174000",
    description="Updated task description"
)

# Change a task's status
agent.tools.update_task(
    task_id="123e4567-e89b-12d3-a456-426614174000",
    status="inprogress"
)

# Move a task to a different project
agent.tools.update_task(
    task_id="123e4567-e89b-12d3-a456-426614174000",
    project_id="Development"  # Can use project name instead of UUID
)

# Update multiple fields at once
agent.tools.update_task(
    task_id="123e4567-e89b-12d3-a456-426614174000",
    description="Revised task description",
    status="inprogress",
    category="high-priority"
)
```

### Updating a Project

```python
# Rename a project
agent.tools.update_project(
    project_id="123e4567-e89b-12d3-a456-426614174000",
    name="New Project Name"
)
```

## Implementation Details

1. **Partial Updates**: Both functions support partial updates, allowing users to update only the fields they want to change.

2. **Validation**:
   - Task/project existence is checked before attempting updates
   - Task status is validated against allowed values ('backlog', 'inprogress', 'done')
   - Project names are checked for uniqueness

3. **Project Names and IDs**:
   - The `update_task` function accepts either a project UUID or a project name
   - If a name is provided, it looks up or creates the project automatically

4. **Error Handling**:
   - UUID parsing errors
   - Invalid status values
   - Duplicate project names
   - Missing tasks or projects

5. **Response Format**:
   - Success responses include both the ID and the full updated entity
   - Error responses include a descriptive message
