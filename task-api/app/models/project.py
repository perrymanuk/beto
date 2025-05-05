from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List, Any, ClassVar, TYPE_CHECKING

# Avoid circular imports
if TYPE_CHECKING:
    from app.models.task import Task

class ProjectBase(BaseModel):
    """Base Project model."""
    name: str


class ProjectInDB(ProjectBase):
    """Project model with database fields."""
    project_id: UUID4
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class Project(ProjectInDB):
    """Project model for responses."""
    pass


class ProjectWithTasks(Project):
    """Project model with tasks included."""
    tasks: List[Any] = []  # Using Any to avoid circular imports