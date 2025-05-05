import uuid
from sqlalchemy import Column, ForeignKey, String, Text, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base

# Define task status enum values
task_status = ('backlog', 'inprogress', 'done')

class Project(Base):
    """Project database model."""
    
    __tablename__ = "projects"
    
    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationship with Task model
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project {self.name}>"


class Task(Base):
    """Task database model."""
    
    __tablename__ = "tasks"
    
    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("projects.project_id", ondelete="CASCADE"), 
        nullable=False
    )
    description = Column(Text, nullable=False)
    status = Column(
        Enum(*task_status, name="task_status", create_type=False),
        nullable=False,
        default="backlog"
    )
    category = Column(Text)
    origin = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    related_info = Column(JSONB)
    
    # Relationship with Project model
    project = relationship("Project", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task {self.task_id}: {self.description[:20]}...>"