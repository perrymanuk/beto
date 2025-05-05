from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.db.models import Project as ProjectModel
from app.models.project import Project, ProjectWithTasks
from app.models.task import Task
from app.db.models import Task as TaskModel

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[Project])
def get_projects(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of all projects.
    """
    projects = db.query(ProjectModel).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve details for a specific project.
    """
    project = db.query(ProjectModel).filter(ProjectModel.project_id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project


@router.get("/{project_id}/tasks", response_model=List[Task])
def get_project_tasks(
    project_id: UUID,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of tasks for a specific project.
    """
    # Check if project exists
    project = db.query(ProjectModel).filter(ProjectModel.project_id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    # Query tasks
    query = db.query(TaskModel).filter(TaskModel.project_id == project_id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(TaskModel.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks