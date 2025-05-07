Implementation Guide: PostgreSQL Todo List Feature for ADK Agent1. IntroductionThis document provides a comprehensive guide for implementing a persistent todo list feature within a Python-based agent built using the Google Agent Development Kit (ADK). The primary objective is to replace the existing in-memory task management system with a robust solution leveraging a dedicated PostgreSQL database instance hosted in a homelab environment.The proposed architecture involves:
Database Backend: A PostgreSQL server storing task data.
Database Interaction Module (db_tools.py): A Python module using psycopg2 to handle direct database communication (CRUD operations) via connection pooling.
Data Validation & Serialization: Pydantic models define data structures for inputs and outputs, ensuring type safety and facilitating JSON serialization.
ADK Tool Module (todo_tools.py): Python functions wrapping the database operations, incorporating error handling, and exposed to the ADK agent as FunctionTool instances. These tools form the API the agent uses to interact with the todo list.
This guide details the necessary steps, provides code examples, and explains the rationale behind key design decisions, enabling a mid-level engineer to implement this feature effectively.2. PrerequisitesBefore starting implementation, ensure the following are installed and configured:
Python: Version 3.9 or later.
PostgreSQL Server: An accessible instance (e.g., running in Docker, locally, or on a homelab server). Database connection details (host, port, database name, user, password) are required.
Google Agent Development Kit (ADK): Installed in your Python environment (pip install google-adk).
psycopg2: The PostgreSQL adapter for Python. It's recommended to install the binary version for easier setup: pip install psycopg2-binary.
Pydantic: For data validation and serialization (pip install pydantic).
Google Cloud SDK (Optional but Recommended): If interacting with Vertex AI models, ensure gcloud is installed and configured (gcloud auth application-default login).
3. Database Setup (PostgreSQL)The foundation of this feature is the PostgreSQL database schema.3.1 Schema Definition (tasks table)Execute the following SQL commands on your PostgreSQL server to create the necessary enum type and the tasks table.SQL-- Create the custom ENUM type for task status
CREATE TYPE task_status AS ENUM ('backlog', 'inprogress', 'done');

-- Create the tasks table
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

-- Optional: Create an index on project_id and status for faster filtering
CREATE INDEX idx_tasks_project_status ON tasks (project_id, status);
3.2 Column Explanations
task_id UUID PRIMARY KEY DEFAULT gen_random_uuid():

Uses the UUID data type for the primary key.1
UUIDs are 128-bit values, offering globally unique identifiers, which is highly beneficial in distributed systems or scenarios where multiple agents might eventually interact with the same database, minimizing the chance of ID collisions compared to traditional SERIAL types.1
Using DEFAULT gen_random_uuid() automatically generates a version 4 UUID upon insertion if no ID is provided, simplifying application logic.1 Note: While pgcrypto's gen_random_uuid() is common, newer PostgreSQL versions include this function natively. Older versions might require installing the uuid-ossp extension (CREATE EXTENSION IF NOT EXISTS "uuid-ossp";) and using uuid_generate_v4().1 Using time-based UUIDs (like uuid_generate_v1mc() from uuid-ossp) can sometimes offer performance benefits by reducing index fragmentation, but random UUIDs are generally simpler to implement and sufficient for many use cases.3


project_id UUID NOT NULL: Links the task to a project (assuming a future projects table or external system using UUIDs). Marked NOT NULL as a task should belong to a project.
description TEXT NOT NULL: Stores the main content of the task. NOT NULL ensures every task has a description.
status task_status NOT NULL DEFAULT 'backlog':

Uses the custom task_status ENUM type created earlier.4
ENUMs restrict the column to a predefined set of values ('backlog', 'inprogress', 'done'), ensuring data consistency and integrity.4 Attempting to insert an invalid status will result in a database error.4
Compared to using a foreign key relationship to a separate statuses table, ENUMs can offer better performance (no join needed) and simpler queries for fixed, unlikely-to-change lists.4 However, adding or removing values requires an ALTER TYPE statement (a schema migration), making them less flexible than lookup tables if the status list changes frequently.5 Removing ENUM values is generally discouraged due to potential index corruption issues.5
NOT NULL ensures every task has a status, defaulting to 'backlog'.


category TEXT: An optional, user-defined category string.
origin TEXT: Optional field to track the source of the task (e.g., 'chat', 'manual').
created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP:

Records the task creation time, including timezone information.
DEFAULT CURRENT_TIMESTAMP automatically sets the timestamp to the time the transaction started when a new row is inserted without specifying created_at.7 NOW() is a common alias for CURRENT_TIMESTAMP and functions identically.7 Using TIMESTAMP WITH TIME ZONE is generally recommended for storing time data to avoid ambiguity.


related_info JSONB:

Uses the JSONB (JSON Binary) data type for flexible storage of structured or semi-structured data (links, sub-notes, metadata).10
JSONB stores data in an optimized binary format, which is generally more efficient for querying and indexing compared to the plain JSON type.10 JSONB also removes insignificant whitespace and duplicate keys during storage.10
It supports powerful operators for querying nested data (->, ->>, @>, ?, etc.) and can be indexed using GIN indexes for performance.10 This provides flexibility without needing to alter the table schema for minor related data additions.


4. Database Interaction Layer (db_tools.py)This module encapsulates all direct communication with the PostgreSQL database using the psycopg2 library. It utilizes connection pooling for efficiency and defines private functions for core CRUD operations.4.1 Library Selectionpsycopg2 is the most widely used and mature PostgreSQL adapter for Python, providing comprehensive support for PostgreSQL features and adhering to the Python DB-API 2.0 specification.134.2 Connection PoolingEstablishing a new database connection for every request is computationally expensive and can negatively impact performance.15 Connection pooling maintains a set of ready-to-use connections, significantly reducing overhead.15Implementation:Use psycopg2.pool.ThreadedConnectionPool for applications that might handle requests concurrently (common in agent frameworks). SimpleConnectionPool is suitable only for single-threaded applications.16Python# db_tools.py
import os
import psycopg2
import psycopg2.pool
import psycopg2.extras # For RealDictCursor if needed
import uuid
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Generator

# --- Connection Pool Setup ---

# Load database configuration securely (e.g., from environment variables)
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# Basic validation
if not all():
    raise ValueError("Database credentials (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD) must be set.")

# Configure and initialize the connection pool
# Adjust minconn and maxconn based on expected load
MIN_CONN = 1
MAX_CONN = 5 # Start conservatively

try:
    pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=MIN_CONN,
        maxconn=MAX_CONN,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print(f"Database connection pool initialized (Min: {MIN_CONN}, Max: {MAX_CONN})")
except psycopg2.OperationalError as e:
    print(f"FATAL: Could not connect to database: {e}")
    # Handle fatal error appropriately - maybe exit or raise
    raise

# --- Context Manager for Connections ---

@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Provides a database connection from the pool, managing cleanup."""
    conn = None
    try:
        conn = pool.getconn()
        yield conn
    except psycopg2.Error as e:
        # Log or handle pool errors if necessary
        print(f"Error getting connection from pool: {e}")
        raise # Re-raise the original psycopg2 error
    finally:
        if conn:
            pool.putconn(conn) # Return connection to the pool

@contextmanager
def get_db_cursor(conn: psycopg2.extensions.connection, commit: bool = False) -> Generator[psycopg2.extensions.cursor, None, None]:
    """Provides a cursor from a connection, handling commit/rollback."""
    # Optional: Use RealDictCursor for dictionary-like row access
    # with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
    with conn.cursor() as cursor:
        try:
            yield cursor
            if commit:
                conn.commit()
        except psycopg2.Error as e:
            print(f"Database operation failed. Rolling back transaction. Error: {e}")
            conn.rollback()
            raise # Re-raise the original psycopg2 error
        # No finally block needed for cursor, 'with' handles closing

# --- Private CRUD Functions ---
# (Implementation follows in the next section)

Pool Sizing Considerations: The minconn and maxconn parameters are crucial.15
minconn: Connections created immediately. Setting this too high wastes database resources if the application is idle.
maxconn: The upper limit. If all connections are in use and a new request arrives, pool.getconn() will block or raise an error if the limit is reached. Setting this too low can cause application bottlenecks under load. Setting it too high can overwhelm the PostgreSQL server (each connection consumes memory and process resources).
Start with conservative values (e.g., minconn=1, maxconn=5 or 10) and monitor application performance and database load. Adjust these values based on observed usage patterns.
The provided get_db_connection context manager simplifies acquiring and releasing connections back to the pool reliably.16 The get_db_cursor context manager further simplifies cursor creation and transaction management.4.3 Core CRUD Functions (Private Implementation)These functions perform the actual database operations. They are prefixed with an underscore (_) to indicate they are intended for internal use within the db_tools.py module and should be called by the public-facing ADK tool functions defined later. Each function accepts a connection object obtained via get_db_connection.Python# db_tools.py (continued)

def _add_task(conn: psycopg2.extensions.connection, description: str, project_id: uuid.UUID, category: Optional[str], origin: Optional[str], related_info: Optional[Dict]) -> uuid.UUID:
    """Inserts a new task into the database and returns its UUID."""
    sql = """
        INSERT INTO tasks (description, project_id, category, origin, related_info)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING task_id;
    """
    # psycopg2 automatically handles JSON serialization for related_info if it's a dict
    params = (description, project_id, category, origin, related_info)
    try:
        with get_db_cursor(conn, commit=True) as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            if result:
                return result
            else:
                # This should ideally not happen with RETURNING if insert succeeds
                raise psycopg2.DatabaseError("INSERT operation did not return task_id.")
    except psycopg2.IntegrityError as e:
        print(f"Integrity error adding task: {e}")
        # Could potentially parse the error for specifics (e.g., constraint violation)
        raise # Re-raise to be handled by the calling tool function
    except psycopg2.Error as e:
        print(f"Database error adding task: {e}")
        raise # Re-raise for generic handling

def _list_tasks(conn: psycopg2.extensions.connection, project_id: uuid.UUID, status_filter: Optional[str]) -> List[Dict[str, Any]]:
    """Retrieves tasks, optionally filtered by status."""
    base_sql = """
        SELECT task_id, project_id, description, status, category, origin, created_at, related_info
        FROM tasks
        WHERE project_id = %s
    """
    params: List[Any] = [project_id]

    if status_filter:
        # Validate status_filter against allowed ENUM values if desired
        allowed_statuses = ('backlog', 'inprogress', 'done')
        if status_filter not in allowed_statuses:
             raise ValueError(f"Invalid status filter: {status_filter}. Must be one of {allowed_statuses}")
        base_sql += " AND status = %s"
        params.append(status_filter)

    base_sql += " ORDER BY created_at DESC;" # Example ordering

    try:
        # Using RealDictCursor for easy dictionary conversion
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(base_sql, tuple(params))
            results = cursor.fetchall()
            # Convert RealDictRow objects to standard dicts for broader compatibility
            return [dict(row) for row in results]
    except psycopg2.Error as e:
        print(f"Database error listing tasks: {e}")
        raise

def _complete_task(conn: psycopg2.extensions.connection, task_id: uuid.UUID) -> bool:
    """Updates a task's status to 'done'."""
    sql = """
        UPDATE tasks
        SET status = 'done'
        WHERE task_id = %s
        RETURNING task_id;
    """
    params = (task_id,)
    try:
        with get_db_cursor(conn, commit=True) as cursor:
            cursor.execute(sql, params)
            # Check if a row was actually updated
            return cursor.rowcount > 0
    except psycopg2.Error as e:
        print(f"Database error completing task {task_id}: {e}")
        raise

def _remove_task(conn: psycopg2.extensions.connection, task_id: uuid.UUID) -> bool:
    """Deletes a task from the database."""
    sql = """
        DELETE FROM tasks
        WHERE task_id = %s
        RETURNING task_id;
    """
    params = (task_id,)
    try:
        with get_db_cursor(conn, commit=True) as cursor:
            cursor.execute(sql, params)
            # Check if a row was actually deleted
            return cursor.rowcount > 0
    except psycopg2.Error as e:
        print(f"Database error removing task {task_id}: {e}")
        raise

Key Implementation Details:
Parameterization: Uses %s placeholders exclusively for all variable data passed into SQL queries.13 This is crucial for preventing SQL injection vulnerabilities. psycopg2 correctly handles quoting and type conversion. Never use Python f-strings or string concatenation (+) to build SQL queries with user-provided data.13
RETURNING task_id: Used in INSERT, UPDATE, and DELETE statements to get the affected task_id back immediately, confirming the operation's target.19
Optional Parameters (_list_tasks): The SELECT query is built dynamically. If status_filter is provided, an AND status = %s clause and the corresponding parameter are added. This avoids complex WHERE (status = %s OR %s IS NULL) logic, which can sometimes hinder index usage.20 Input validation for the status_filter ensures only valid ENUM values are used.
Fetching Results: _list_tasks uses cursor.fetchall() to get all matching rows. Using psycopg2.extras.RealDictCursor provides results as dictionary-like objects, simplifying conversion to the required output format.21 We explicitly convert these to standard dictionaries.
Confirmation: _complete_task and _remove_task check cursor.rowcount after UPDATE or DELETE to determine if any rows were actually affected, returning a boolean success indicator.
JSONB Handling: psycopg2 automatically serializes Python dictionaries passed as parameters for JSONB columns.
4.4 Transaction ManagementDatabase operations (especially those involving multiple steps, though less critical here) should occur within transactions to ensure atomicity (all or nothing).
Context Managers: The recommended approach is using the connection and cursor objects as context managers (with get_db_connection() as conn: with get_db_cursor(conn, commit=True) as cursor:). The get_db_cursor context manager automatically calls conn.commit() if the block executes successfully and conn.rollback() if any psycopg2.Error (or subclass) is raised within the block.19 This significantly simplifies transaction handling and ensures resources are managed correctly.
Explicit Commit/Rollback: Alternatively, one could manage transactions explicitly:
Python# Explicit Example (less preferred)
conn = pool.getconn()
try:
    cursor = conn.cursor()
    #... cursor.execute(...)...
    conn.commit() # Commit on success
    cursor.close()
except psycopg2.Error as e:
    conn.rollback() # Rollback on error
    # Handle error...
finally:
    pool.putconn(conn)

This is more verbose and error-prone than using context managers.
Autocommit: psycopg2 connections can be set to autocommit mode (conn.autocommit = True), where each statement executes in its own transaction.23 While simpler for single-statement operations, it's generally less safe for multi-step logic and offers less control. The context manager approach provides the best balance of safety and simplicity.
This guide uses the context manager approach (get_db_cursor) for clarity and robustness.5. Data Serialization & Validation with PydanticPydantic models serve two crucial roles:
Data Validation: Defining the expected structure and types for data flowing into and out of the ADK tools.
Serialization: Easily converting Python objects (like database results) into JSON-compatible dictionaries for API responses.
Create a models.py file or define these within todo_tools.py.Python# models.py (or within todo_tools.py)
import uuid
import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator

# --- Base Task Model ---
class TaskBase(BaseModel):
    """Base model for common task attributes."""
    project_id: uuid.UUID
    description: str
    category: Optional[str] = None
    origin: Optional[str] = None
    related_info: Optional[Dict[str, Any]] = None

# --- Model for Creating Tasks ---
class TaskCreate(TaskBase):
    """Data required to create a new task (input)."""
    # Inherits fields from TaskBase
    # description and project_id are implicitly required
    pass

# --- Model for Representing Tasks from DB ---
class Task(TaskBase):
    """Full task representation including DB-generated fields."""
    task_id: uuid.UUID
    status: Literal['backlog', 'inprogress', 'done'] # Use Literal for strict validation
    created_at: datetime.datetime

    class Config:
        orm_mode = True # Allows creating model from ORM objects or dicts easily

# --- Models for Tool Inputs ---
class ToolInputAddTask(TaskCreate):
    """Specific input structure for the add_task tool."""
    pass # Currently identical to TaskCreate, but allows future divergence

class ToolInputListTasks(BaseModel):
    """Input structure for the list_tasks tool."""
    project_id: uuid.UUID
    status_filter: Optional[Literal['backlog', 'inprogress', 'done']] = None

class ToolInputUpdateTaskStatus(BaseModel):
    """Input structure for tools modifying task status (complete/remove)."""
    task_id: uuid.UUID

# --- Models for Tool Outputs ---
class ToolOutputStatus(BaseModel):
    """Generic success/error status output."""
    status: Literal['success', 'error']
    message: Optional[str] = None # Used for error messages

class ToolOutputTask(ToolOutputStatus):
    """Success output for operations returning a single task ID."""
    status: Literal['success'] = 'success'
    task_id: uuid.UUID

class ToolOutputTaskList(ToolOutputStatus):
    """Success output for list_tasks."""
    status: Literal['success'] = 'success'
    tasks: List # List of full Task objects

class ToolErrorOutput(ToolOutputStatus):
    """Standard error output."""
    status: Literal['error'] = 'error'
    message: str # Error message is required

Key Pydantic Features Used:
BaseModel: The foundation for all Pydantic models.25
Type Hinting: Standard Python types (str, int, float, datetime.datetime, uuid.UUID, List, Dict, Any) are used. Optional[X] is equivalent to Union[X, None].26 Literal restricts values to a specific set, mirroring the database ENUM.26
Optional Fields: Fields with a default value (= None) or annotated as Optional without a default are considered optional during validation.25 Note that in Pydantic V2, Optional[str] does not automatically imply default=None; a default must be explicitly provided if the field should be optional and have a default value.27
Field(): Can be used to add metadata like default values (default=..., default_factory=...), aliases (alias=...), descriptions, etc..27
Validation: When data (e.g., a dictionary from an incoming request) is passed to a model's constructor (e.g., ToolInputAddTask(**request_data)), Pydantic automatically validates that the data conforms to the defined types and constraints. If validation fails, it raises a ValidationError with detailed information about the mismatch.25 FastAPI and ADK typically handle this validation implicitly when type hints are used.
Serialization:

model.model_dump(): Converts a Pydantic model instance into a dictionary. It recursively converts nested models and handles types like UUID and datetime into JSON-compatible formats (usually strings).29 This is the preferred method in Pydantic V2.
model.model_dump_json(): Serializes the model directly into a JSON string.29
These methods ensure that the data returned by the ADK tools is always in a valid JSON structure.


6. Implementing ADK FunctionTools (todo_tools.py)This module defines the public functions that the ADK agent will call. These functions act as a bridge between the agent's requests and the database interaction logic in db_tools.py. They handle input parsing, calling the appropriate database function, error handling, and formatting the response.Python# todo_tools.py
import uuid
import traceback
from typing import Optional, Dict, List, Any
from google.adk.tools import FunctionTool

# Import database interaction functions and Pydantic models
from. import db_tools
from. import models

# --- Tool Function Implementations ---

def add_task(description: str, project_id: uuid.UUID, category: Optional[str] = None, origin: Optional[str] = None, related_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Adds a new todo task to the persistent database.

    This tool creates a new task entry with the provided details. It requires
    a description and the project ID the task belongs to. Category, origin,
    and related information are optional.

    Args:
        description: The main text content describing the task. (Required)
        project_id: The UUID identifier for the project associated with this task. (Required)
        category: An optional label to categorize the task (e.g., 'work', 'personal').
        origin: An optional string indicating the source of the task (e.g., 'chat', 'email', 'manual').
        related_info: An optional dictionary for storing supplementary structured data,
                      such as {'link': 'http://example.com', 'notes': 'Further details...'}.

    Returns:
        A dictionary indicating the outcome.
        On success: {"status": "success", "task_id": "new_task_uuid_string"}
        On failure: {"status": "error", "message": "Concise error description..."}
    """
    try:
        # Optional: Validate input using Pydantic model if desired (ADK often handles basic type checks)
        # input_data = models.ToolInputAddTask(description=description, project_id=project_id,...)

        with db_tools.get_db_connection() as conn:
            new_task_id = db_tools._add_task(
                conn=conn,
                description=description,
                project_id=project_id,
                category=category,
                origin=origin,
                related_info=related_info
            )
        # Use Pydantic model for consistent success response structure
        response = models.ToolOutputTask(task_id=new_task_id)
        return response.model_dump()

    except Exception as e:
        # Handle error (logging, truncation, formatting) - see Section 7
        error_message = f"Failed to add task: {str(e)}"
        print(f"Error in add_task tool: {error_message}")
        print(traceback.format_exc()) # Log full traceback for debugging
        truncated_message = (error_message[:197] + '...') if len(error_message) > 200 else error_message

        # Use Pydantic model for consistent error response structure
        response = models.ToolErrorOutput(message=truncated_message)
        return response.model_dump()


def list_tasks(project_id: uuid.UUID, status_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves a list of todo tasks for a specific project, optionally filtered by status.

    Fetches tasks associated with the given project UUID. You can optionally filter
    the results to include only tasks with a specific status ('backlog', 'inprogress', 'done').
    Tasks are returned ordered by creation date, newest first.

    Args:
        project_id: The UUID identifier of the project whose tasks should be listed. (Required)
        status_filter: An optional status to filter tasks by. Accepted values are
                       'backlog', 'inprogress', or 'done'. If omitted, tasks of all
                       statuses are returned.

    Returns:
        A dictionary containing the list of tasks or an error message.
        On success: {"status": "success", "tasks": [{"task_id":..., "description":...,...},...]}
        On failure: {"status": "error", "message": "Concise error description..."}
    """
    try:
        # Optional: Validate input
        # input_data = models.ToolInputListTasks(project_id=project_id, status_filter=status_filter)

        with db_tools.get_db_connection() as conn:
            task_dicts = db_tools._list_tasks(conn, project_id, status_filter)

        # Validate/structure output using Pydantic Task model
        tasks_list =
        response = models.ToolOutputTaskList(tasks=tasks_list)
        return response.model_dump()

    except ValueError as e: # Catch specific validation errors (e.g., invalid status_filter)
        error_message = f"Input validation error listing tasks: {str(e)}"
        print(f"Error in list_tasks tool: {error_message}")
        response = models.ToolErrorOutput(message=error_message) # No need to truncate validation errors usually
        return response.model_dump()
    except Exception as e:
        error_message = f"Failed to list tasks for project {project_id}: {str(e)}"
        print(f"Error in list_tasks tool: {error_message}")
        print(traceback.format_exc())
        truncated_message = (error_message[:197] + '...') if len(error_message) > 200 else error_message
        response = models.ToolErrorOutput(message=truncated_message)
        return response.model_dump()


def complete_task(task_id: uuid.UUID) -> Dict[str, Any]:
    """
    Marks a specific todo task as 'done'.

    Updates the status of the task identified by the given UUID to 'done'.

    Args:
        task_id: The UUID identifier of the task to mark as completed. (Required)

    Returns:
        A dictionary indicating the outcome.
        On success: {"status": "success", "task_id": "completed_task_uuid_string"}
        On failure: {"status": "error", "message": "Concise error description..."}
                    (e.g., if the task ID doesn't exist)
    """
    try:
        # Optional: Validate input
        # input_data = models.ToolInputUpdateTaskStatus(task_id=task_id)

        with db_tools.get_db_connection() as conn:
            success = db_tools._complete_task(conn, task_id)

        if success:
            response = models.ToolOutputTask(task_id=task_id)
            return response.model_dump()
        else:
            # Task not found or already done (depending on desired logic)
            response = models.ToolErrorOutput(message=f"Task with ID {task_id} not found or could not be updated.")
            return response.model_dump()

    except Exception as e:
        error_message = f"Failed to complete task {task_id}: {str(e)}"
        print(f"Error in complete_task tool: {error_message}")
        print(traceback.format_exc())
        truncated_message = (error_message[:197] + '...') if len(error_message) > 200 else error_message
        response = models.ToolErrorOutput(message=truncated_message)
        return response.model_dump()


def remove_task(task_id: uuid.UUID) -> Dict[str, Any]:
    """
    Permanently deletes a specific todo task from the database.

    Removes the task identified by the given UUID. This action cannot be undone.

    Args:
        task_id: The UUID identifier of the task to delete. (Required)

    Returns:
        A dictionary indicating the outcome.
        On success: {"status": "success", "task_id": "deleted_task_uuid_string"}
        On failure: {"status": "error", "message": "Concise error description..."}
                    (e.g., if the task ID doesn't exist)
    """
    try:
        # Optional: Validate input
        # input_data = models.ToolInputUpdateTaskStatus(task_id=task_id)

        with db_tools.get_db_connection() as conn:
            success = db_tools._remove_task(conn, task_id)

        if success:
            response = models.ToolOutputTask(task_id=task_id)
            return response.model_dump()
        else:
            # Task not found
            response = models.ToolErrorOutput(message=f"Task with ID {task_id} not found for deletion.")
            return response.model_dump()

    except Exception as e:
        error_message = f"Failed to remove task {task_id}: {str(e)}"
        print(f"Error in remove_task tool: {error_message}")
        print(traceback.format_exc())
        truncated_message = (error_message[:197] + '...') if len(error_message) > 200 else error_message
        response = models.ToolErrorOutput(message=truncated_message)
        return response.model_dump()


# --- ADK Tool Wrapping ---

add_task_tool = FunctionTool(add_task)
list_tasks_tool = FunctionTool(list_tasks)
complete_task_tool = FunctionTool(complete_task)
remove_task_tool = FunctionTool(remove_task)

# List of all tools to be registered with the agent
ALL_TOOLS = [add_task_tool, list_tasks_tool, complete_task_tool, remove_task_tool]

Docstrings are Critical:The docstrings for add_task, list_tasks, complete_task, and remove_task are not just for human developers. The ADK framework uses the function signature and its docstring (especially the Args: section) to generate a schema or description that the underlying Large Language Model (LLM) uses to understand what the tool does, what parameters it expects, and when it should be called.31Therefore, clear, accurate, and detailed docstrings are functionally essential for the agent to use the tools correctly. Vague or incorrect docstrings will lead the LLM to make mistakes, such as calling the wrong tool, providing incorrect parameters, or failing to use the tool when appropriate. The description should clearly state the tool's purpose and any important constraints or behaviors. The Args: section must accurately describe each parameter, including its type and whether it's required or optional.32ADK FunctionTool Wrapper:The line add_task_tool = FunctionTool(add_task) (and similar lines for other functions) is where ADK takes the standard Python function and wraps it, making it available to the agent.31 ADK handles the introspection of the function signature and docstring to create the necessary configuration for the LLM's function-calling mechanism.Tool Interface Summary:The following table summarizes the API exposed to the agent through these tools:Tool FunctionParametersReturn Schema (Success)Return Schema (Error)add_taskdescription: str, project_id: uuid.UUID, category: Optional[str], origin: Optional[str], related_info: Optional[Dict]{"status": "success", "task_id": str(UUID)}{"status": "error", "message": str}list_tasksproject_id: uuid.UUID, status_filter: Optional[str]{"status": "success", "tasks": List[Dict]}{"status": "error", "message": str}complete_tasktask_id: uuid.UUID{"status": "success", "task_id": str(UUID)}{"status": "error", "message": str}remove_tasktask_id: uuid.UUID{"status": "success", "task_id": str(UUID)}{"status": "error", "message": str}This table provides a quick reference for the expected inputs and outputs of each tool, ensuring consistency during implementation and agent prompting.7. Robust Error HandlingReliable software anticipates failures. In this context, database operations can fail due to connection issues, invalid data, constraint violations, or query errors. The ADK tools must handle these gracefully and provide informative feedback to the agent.Strategy:
Centralized Handling: Implement try...except blocks within the public ADK tool functions (todo_tools.py) where the calls to db_tools.py functions are made. This keeps the error formatting logic consistent for the agent interface.
Catch Specific Exceptions: Catch relevant psycopg2 exceptions like psycopg2.OperationalError (connection problems), psycopg2.IntegrityError (e.g., unique constraint violation), psycopg2.DataError (invalid data format), psycopg2.ProgrammingError (SQL syntax errors), and the base psycopg2.DatabaseError for broader coverage.14 Also, catch standard Python exceptions (ValueError, TypeError, Exception).
Log Detailed Errors: Inside the except block, log the full exception details (including traceback) using print or a proper logging framework. This is essential for debugging.
Format User-Facing Error: Extract a concise message from the exception (str(e)). Truncate this message to a predefined maximum length (e.g., 200 characters) as specified in the requirements to prevent overwhelming the agent or user.
Standardized Error Response: Return the error as a JSON dictionary conforming to the ToolErrorOutput Pydantic model: {"status": "error", "message": "Truncated error details..."}.
Example (within add_task function):Python    except psycopg2.IntegrityError as e:
        # Specific handling for constraint violations, etc.
        error_message = f"Database integrity error adding task: {str(e)}"
        print(f"Error in add_task tool: {error_message}")
        print(traceback.format_exc())
        # Maybe provide a more user-friendly message based on common integrity errors
        user_message = "Failed to add task due to a data conflict (e.g., duplicate)."
        response = models.ToolErrorOutput(message=user_message)
        return response.model_dump()

    except psycopg2.OperationalError as e:
        # Specific handling for connection issues
        error_message = f"Database connection error: {str(e)}"
        print(f"Error in add_task tool: {error_message}")
        print(traceback.format_exc())
        user_message = "Could not connect to the task database. Please check the connection."
        response = models.ToolErrorOutput(message=user_message)
        return response.model_dump()

    except Exception as e:
        # Generic fallback for other errors
        error_message = f"An unexpected error occurred while adding the task: {str(e)}"
        print(f"Error in add_task tool: {error_message}")
        print(traceback.format_exc()) # Log full traceback
        truncated_message = (error_message[:197] + '...') if len(error_message) > 200 else error_message
        response = models.ToolErrorOutput(message=truncated_message)
        return response.model_dump()
Balancing Detail: While catching specific exceptions like IntegrityError or OperationalError provides valuable debugging information (which should be logged) 36, directly exposing raw database error messages or stack traces to the end-user via the agent is generally unhelpful and confusing. The implemented strategy logs the details for developers but returns a standardized, truncated, and potentially more user-friendly message to the agent. The agent, guided by its instructions, can then present this status to the user appropriately (e.g., "Sorry, I encountered a database connection issue while trying to add your task.").8. Integration & Usage Notes8.1 Agent RegistrationTo make the todo list tools available to the agent, import the ALL_TOOLS list from todo_tools.py and pass it to the tools parameter when initializing the Agent in your main agent definition file (e.g., agent.py).Python# agent.py (or your main agent definition file)

from google.adk.agents import Agent
# Assuming todo_tools.py is in the same directory or accessible via Python path
from.todo_tools import ALL_TOOLS

# Configure your LLM (example using Vertex AI)
# Ensure GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI are set in.env or environment
# model_config =... # Configure model as needed

todo_agent = Agent(
    name="persistent_todo_agent",
    # model=model_config, # Pass your configured model
    model="gemini-1.5-flash", # Example model name
    description="An agent capable of managing a persistent todo list stored in a PostgreSQL database.",
    instruction="You are a helpful assistant. You can manage a user's todo list. "
                "Use the available tools to add, list, complete, or remove tasks. "
                "Always confirm the project ID with the user if ambiguous. "
                "When reporting errors from tools, state the problem clearly based on the message provided by the tool.",
    tools=ALL_TOOLS  # Register the imported todo tools here
)

# If this is the root agent to run:
root_agent = todo_agent
Refer to ADK documentation for specifics on model configuration.358.2 TestingThorough testing is essential:
Unit Tests (db_tools.py): Write tests (e.g., using pytest) that directly call the private functions (_add_task, _list_tasks, etc.). These tests should connect to a dedicated test database and verify that the SQL operations work correctly, data is inserted/updated/deleted as expected, and edge cases (e.g., non-existent IDs) are handled. Mocking the database connection might be necessary for true unit tests.
Tool Function Tests (todo_tools.py): Test the public tool functions (add_task, list_tasks, etc.). Mock the underlying db_tools functions to isolate the tool's logic (input parsing, response formatting, error handling). Verify that correct success/error dictionaries are returned based on mocked db_tools behavior.
Integration Tests: Test the interaction between todo_tools.py and db_tools.py by calling the tool functions and letting them interact with the test database. Verify the end-to-end flow for each tool.
Agent Interaction Tests: Run the agent using the ADK CLI (adk run your_agent_module) or the web UI (adk serve).35 Interact with the agent using natural language prompts designed to trigger the todo list tools. Examples:

"Add 'Review implementation guide' to project 'agent-dev'"
"What are the pending tasks for project 'agent-dev'?" (Requires project ID handling)
"Show me the 'inprogress' tasks for project '...' "
"Mark task '...' as done." (Requires task ID handling)
"Remove task '...' "
Observe the agent's responses, check the debug logs for tool calls, and verify the database state changes accordingly. Test error conditions (e.g., asking to complete a non-existent task).


9. (Optional) Advanced Considerations9.1 ORM vs. Raw SQLThis guide uses raw psycopg2 for database interaction. An alternative is using an Object-Relational Mapper (ORM) like SQLAlchemy.
Raw psycopg2:

Pros: Direct control over SQL, potentially better performance for simple queries, fewer dependencies.
Cons: Requires manual SQL writing, mapping results to objects can be manual (though RealDictCursor helps).


SQLAlchemy (ORM):

Pros: Abstracts SQL, maps database tables to Python classes, potentially faster development for complex relationships/queries, built-in migration tools (Alembic).
Cons: Adds a layer of abstraction, potential learning curve, might have slight overhead compared to optimized raw SQL.


For the defined CRUD operations in this feature, raw psycopg2 provides sufficient control and clarity, aligning well with the direct use of its features like connection pooling and error handling discussed here. If the application evolves to have significantly more complex data relationships and queries, migrating to an ORM could be considered.9.2 LangChain IntegrationLangChain offers tools like SQLDatabaseChain and SQL Agents that allow an LLM to interact with SQL databases based on natural language questions.38
SQLDatabaseChain: Primarily designed for question-answering over a database schema. The LLM generates SQL queries based on the user's question and the provided schema information.38
Current Approach: This implementation exposes predefined, specific operations (add, list, complete, remove) via ADK FunctionTools. The LLM's role is to understand which predefined tool to call based on the user request, not to generate arbitrary SQL.
Why the current approach is suitable: It provides a controlled, secure API to the database. Allowing an LLM to generate arbitrary SQL via SQLDatabaseChain directly within a tool could pose security risks (potential for unintended data modification/deletion if the LLM generates incorrect SQL) and is less predictable than calling predefined functions.It is possible to wrap a SQLDatabaseChain inside a custom ADK FunctionTool if the goal was to create a tool that specifically answers natural language questions about the todo data by generating SQL. However, for implementing the defined CRUD actions, wrapping the custom psycopg2 functions is the more direct, secure, and appropriate method.9.3 Schema MigrationsAs the application evolves, the tasks table schema might need changes (e.g., adding new columns, modifying existing ones). Manually applying ALTER TABLE statements can become error-prone, especially across different environments (development, testing, production).Using a database migration tool like Alembic (commonly used with SQLAlchemy, but can be used independently) is highly recommended for managing schema changes systematically. Migrations are scripted, version-controlled changes that can be applied and rolled back reliably. While not part of the initial implementation, consider adopting a migration tool if the schema is expected to change in the future.10. ConclusionThis guide provides a detailed roadmap for implementing a PostgreSQL-backed todo list feature within an ADK agent. By following the outlined steps for database schema definition, implementing the psycopg2-based interaction layer with connection pooling, defining Pydantic models for data integrity, and wrapping the logic in robust ADK FunctionTools with clear docstrings and error handling, a mid-level engineer can successfully build this persistent task management capability. The chosen architecture prioritizes control, security, and performance by exposing specific CRUD operations rather than allowing arbitrary SQL generation, while leveraging standard libraries like psycopg2 and Pydantic for efficient and reliable implementation. Remember to test thoroughly at each stage – unit, integration, and agent interaction – to ensure correctness and robustness.
