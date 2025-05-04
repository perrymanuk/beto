"""
Todo tool for the radbot agent.

This package provides the tools for interacting with a PostgreSQL-backed todo list.
"""

from .db import create_schema_if_not_exists
from .api import (
    add_task_tool,
    complete_task_tool,
    remove_task_tool,
    list_projects_tool,
    list_project_tasks_tool,
    list_all_tasks_tool,
    update_task_tool,
    update_project_tool,
    ALL_TOOLS,
)

# Initialize database schema
def init_database():
    """Initialize the database schema if it doesn't exist."""
    create_schema_if_not_exists()

__all__ = [
    "ALL_TOOLS",
    "add_task_tool",
    "complete_task_tool",
    "remove_task_tool",
    "list_projects_tool",
    "list_project_tasks_tool",
    "list_all_tasks_tool",
    "update_task_tool",
    "update_project_tool",
    "init_database",
]
