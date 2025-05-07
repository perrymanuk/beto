# Todo System Implementation

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document provides a comprehensive guide to the Todo System implementation in the radbot project, including database structure, API design, and usage patterns.

## Overview

The Todo System provides a persistent task management system for the radbot agent. It uses a PostgreSQL database backend and provides tools for:

- Creating and managing tasks
- Organizing tasks into projects
- Filtering tasks by status and other criteria
- Updating task information
- Tracking task completion

## Architecture

The Todo System follows a layered architecture:

```
┌───────────────────┐
│  ADK Tool Layer   │ <- Tools exposed to the agent (add_task, list_tasks, etc.)
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│  API Functions    │ <- Business logic, validation, and error handling
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│  Database Layer   │ <- Direct database interaction (SQL queries)
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│  PostgreSQL DB    │ <- Persistent storage
└───────────────────┘
```

## Directory Structure

The system is organized into the following directory structure:

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
    └── list_tools.py            # Specialized list tools
```

## Database Schema

### Tasks Table

```sql
CREATE TYPE task_status AS ENUM ('backlog', 'inprogress', 'done');

CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    description TEXT NOT NULL,
    status task_status NOT NULL DEFAULT 'backlog',
    category TEXT,
    origin TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    related_info JSONB
);

CREATE INDEX idx_tasks_project_status ON tasks (project_id, status);
```

Key fields in the tasks table:

- **task_id**: UUID identifier for the task
- **project_id**: UUID link to the project this task belongs to
- **description**: Main text content of the task
- **status**: One of 'backlog', 'inprogress', or 'done'
- **category**: Optional label for grouping tasks
- **origin**: Optional source information (e.g., 'chat', 'manual')
- **created_at**: Timestamp when the task was created
- **related_info**: JSONB field for storing additional structured data

### Projects Table

```sql
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Key fields in the projects table:

- **project_id**: UUID identifier for the project
- **name**: Unique name for the project
- **description**: Optional description of the project
- **created_at**: Timestamp when the project was created

## Database Connection Management

The system uses connection pooling with psycopg2 to efficiently manage database connections:

```python
# Connection pool setup
pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=MIN_CONN,
    maxconn=MAX_CONN,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Context manager for connections
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pool.getconn()
        yield conn
    finally:
        if conn:
            pool.putconn(conn)

# Context manager for cursors
@contextmanager
def get_db_cursor(conn, commit=False):
    with conn.cursor() as cursor:
        try:
            yield cursor
            if commit:
                conn.commit()
        except:
            conn.rollback()
            raise
```

## Data Models

Pydantic models are used for validation and serialization:

```python
class TaskBase(BaseModel):
    """Base model for common task attributes."""
    project_id: uuid.UUID
    description: str
    category: Optional[str] = None
    origin: Optional[str] = None
    related_info: Optional[Dict[str, Any]] = None

class Task(TaskBase):
    """Full task representation including DB-generated fields."""
    task_id: uuid.UUID
    status: Literal['backlog', 'inprogress', 'done']
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True
```

## API Functions

The Todo System exposes the following main functions:

### Task Management

- **add_task**: Creates a new task in the database
- **update_task**: Updates an existing task's attributes
- **complete_task**: Marks a task as done
- **remove_task**: Deletes a task from the database

### Project Management

- **add_project**: Creates a new project
- **update_project**: Renames a project
- **list_projects**: Lists all projects

### List Operations

- **list_project_tasks**: Lists tasks for a specific project
- **list_all_tasks**: Lists tasks across all projects

## Core Features

### Default Hiding of Completed Tasks

Both list functions hide completed tasks by default:

```python
def list_project_tasks(project_id, status_filter=None, include_done=False):
    """Lists tasks for a specific project."""
    # If status_filter is explicitly set, use it
    if status_filter:
        return db.list_tasks(project_id, status_filter)
    
    # Otherwise, filter out 'done' tasks unless include_done=True
    if not include_done:
        # Get all tasks that aren't 'done'
        tasks = db.list_tasks(project_id)
        return [t for t in tasks if t['status'] != 'done']
    
    # Return all tasks
    return db.list_tasks(project_id)
```

### UUID Handling

The system includes UUID adapter registration to ensure proper handling with PostgreSQL:

```python
# Register UUID adapter for psycopg2
psycopg2.extensions.register_adapter(uuid.UUID, lambda u: psycopg2.extensions.adapt(str(u)))
```

### Partial Updates

The `update_task` function supports partial updates, allowing users to change only specific attributes:

```python
def update_task(task_id, description=None, project_id=None, status=None, 
               category=None, origin=None, related_info=None):
    """Updates only the specified fields of a task."""
    # Collect fields to update
    update_fields = {}
    if description is not None:
        update_fields['description'] = description
    if project_id is not None:
        update_fields['project_id'] = project_id
    # ... and so on for other fields
    
    # Only update if there are changes
    if update_fields:
        return db.update_task(task_id, update_fields)
```

## ADK Tool Integration

The Todo System is integrated with the ADK through FunctionTool wrappers:

```python
from google.adk.tools import FunctionTool

# Create ADK function tools
add_task_tool = FunctionTool(add_task)
list_tasks_tool = FunctionTool(list_project_tasks)
complete_task_tool = FunctionTool(complete_task)
remove_task_tool = FunctionTool(remove_task)

# List of all tools to be registered with the agent
ALL_TOOLS = [add_task_tool, list_tasks_tool, complete_task_tool, remove_task_tool]
```

## Error Handling

The system implements comprehensive error handling:

```python
try:
    # Perform database operation
    result = db.some_operation()
    return {"status": "success", "data": result}
except psycopg2.IntegrityError as e:
    # Handle integrity errors (e.g., duplicate entries)
    error_message = f"Database integrity error: {str(e)}"
    return {"status": "error", "message": error_message}
except ValueError as e:
    # Handle validation errors
    return {"status": "error", "message": str(e)}
except Exception as e:
    # Generic error handling
    error_message = f"An unexpected error occurred: {str(e)}"
    # Truncate long error messages
    truncated_message = (error_message[:197] + '...') if len(error_message) > 200 else error_message
    return {"status": "error", "message": truncated_message}
```

## Recent Enhancements

### 1. Enhanced Filtering

- Added `include_done` parameter to list functions
- By default, completed tasks are now hidden from listings
- Users can explicitly request to see completed tasks

### 2. Module Restructuring

- Separated the system into modular components (db, models, api)
- Improved maintainability and organization
- Added specialized list tools (`list_all_tasks`)

### 3. Update Functionality

- Added functionality to update task attributes
- Added project renaming capability
- Implemented partial updates

### 4. UUID Handling Fix

- Added UUID adapter registration
- Fixed issues with task removal
- Added better error handling for UUID operations

## Usage Examples

### Adding a Task

```python
result = agent.tools.add_task(
    description="Implement Todo System documentation",
    project_id="radbot",
    category="documentation"
)
```

### Listing Tasks

```python
# List active tasks only
tasks = agent.tools.list_project_tasks(project_id="radbot")

# Include completed tasks
all_tasks = agent.tools.list_project_tasks(project_id="radbot", include_done=True)

# Filter by status
in_progress = agent.tools.list_project_tasks(project_id="radbot", status_filter="inprogress")
```

### Updating a Task

```python
# Change a task's description
agent.tools.update_task(
    task_id="123e4567-e89b-12d3-a456-426614174000",
    description="Updated task description"
)

# Change a task's status
agent.tools.update_task(
    task_id="123e4567-e89b-12d3-a456-426614174000",
    status="inprogress"
)
```

### Completing and Removing Tasks

```python
# Mark a task as complete
agent.tools.complete_task(task_id="123e4567-e89b-12d3-a456-426614174000")

# Remove a task
agent.tools.remove_task(task_id="123e4567-e89b-12d3-a456-426614174000")
```

## Future Enhancements

Potential future improvements to the Todo System include:

1. **Task Dependencies**: Implementation of task relationships
2. **Due Dates**: Support for deadlines and time-based prioritization
3. **Task Metrics**: Statistics on task completion rates and patterns
4. **Custom Views**: Predefined views like "Today's Tasks" or "High Priority"
5. **Task Archiving**: Moving completed tasks to an archive for better performance
6. **Date Filtering**: Filtering tasks by creation or completion date
7. **Tagging System**: More flexible categorization beyond the basic category field
8. **User Assignment**: Assigning tasks to specific users in multi-user environments
9. **Recurring Tasks**: Support for tasks that repeat on a schedule

## References

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [ADK Tool Documentation](https://google.github.io/adk-docs/)