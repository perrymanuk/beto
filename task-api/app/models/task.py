from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, Dict, Any, Literal, TYPE_CHECKING
from enum import Enum

# Avoid circular imports
if TYPE_CHECKING:
    from app.models.project import Project


class TaskStatus(str, Enum):
    """Task status enum."""
    BACKLOG = "backlog"
    INPROGRESS = "inprogress"
    DONE = "done"


class TaskBase(BaseModel):
    """Base Task model."""
    description: str
    status: TaskStatus = TaskStatus.BACKLOG
    category: Optional[str] = None
    origin: Optional[str] = None
    related_info: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    """Task model for creation."""
    project_id: UUID4


class TaskInDB(TaskBase):
    """Task model with database fields."""
    task_id: UUID4
    project_id: UUID4
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class Task(TaskInDB):
    """Task model for responses."""
    pass


class TaskWithProject(Task):
    """Task model with project details included."""
    project_name: str


class TaskUpdate(BaseModel):
    """Task model for updates."""
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    category: Optional[str] = None
    origin: Optional[str] = None
    related_info: Optional[Dict[str, Any]] = None