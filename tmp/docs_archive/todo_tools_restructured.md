# Todo Tools Restructuring

## Overview

The Todo Tool system has been restructured to improve modularity, maintainability, and to provide more specific functionality through granular tool functions. This restructuring includes separating the database operations, models, and API functions into distinct modules, as well as adding new functionality to list all tasks across projects.

## Directory Structure

The revised directory structure is organized as follows:

```
radbot/tools/todo/
├── __init__.py                  # Main exports
├── db/
│   ├── __init__.py              # Database exports
│   ├── connection.py            # Database connection handling
│   ├── schema.py                # Schema creation and management
│   └── queries.py               # SQL queries and operations
├── models/
│   ├── __init__.py              # Model exports
│   └── task.py                  # Task and project models
└── api/
    ├── __init__.py              # Tool function exports
    ├── project_tools.py         # Project-related tools
    ├── task_tools.py            # Task-related tools
    └── list_tools.py            # Specialized list tools (all tasks, project tasks)
```

## Key Improvements

### 1. Module Separation

- **Database Layer**: All database operations are now in the `db/` directory, with separate files for connection management, schema definitions, and query operations
- **Models**: Pydantic models are moved to their own module, making it easier to maintain and extend data validation
- **API Functions**: Tool functions are categorized by their purpose (task, project, list operations)

### 2. New List Tools

Two distinct list tools are now available:

- **list_project_tasks**: Lists tasks for a specific project (previous functionality)
- **list_all_tasks**: New functionality to list tasks across all projects, reducing the need for multiple queries when getting an overview

### 3. Default Hiding of Completed Tasks

Both list tools now hide completed tasks by default, with options to include them:

- Tasks with status 'done' are filtered out unless explicitly requested
- Parameters added:
  - `include_done: bool = False`: Controls whether completed tasks are included
  - `status_filter`: Takes precedence if specified (for backward compatibility)

## Usage Examples

### Listing Project Tasks

```python
# Only see active tasks in the "radbot" project (default behavior)
agent.tools.list_project_tasks(project_id="radbot")

# See all tasks including completed ones
agent.tools.list_project_tasks(project_id="radbot", include_done=True)

# Only see tasks with a specific status
agent.tools.list_project_tasks(project_id="radbot", status_filter="inprogress")
```

### Listing All Tasks

```python
# See all active tasks across all projects
agent.tools.list_all_tasks()

# See all tasks including completed ones
agent.tools.list_all_tasks(include_done=True)

# Only see tasks with a specific status across all projects
agent.tools.list_all_tasks(status_filter="backlog")
```

## Implementation Notes

1. **Database Query Modularity**: Functions like `list_tasks` and `list_all_tasks` in the database layer are focused solely on data retrieval with minimal business logic
2. **API Layer Enhancements**: The API layer handles input validation, error handling, and user-friendly formatting
3. **Consistent Behavior**: Both list tools use the same logic for filtering completed tasks
4. **Backward Compatibility**: All existing functionality is preserved while adding new capabilities

## Future Enhancements

1. **Task Metrics**: Add tools to calculate task completion statistics
2. **Task Dependencies**: Implementation of task relationships and dependencies
3. **Due Dates**: Add support for task deadlines and prioritization
4. **Custom Views**: Create predefined views like "Today's Tasks" or "This Week"
