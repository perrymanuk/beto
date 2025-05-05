from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models import Task as TaskModel, Project as ProjectModel
from app.models.task import Task, TaskWithProject

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskWithProject])
def get_tasks(
    status: Optional[str] = None,
    project_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of all tasks with filters.
    """
    query = db.query(
        TaskModel, 
        ProjectModel.name.label("project_name")
    ).join(
        ProjectModel, 
        TaskModel.project_id == ProjectModel.project_id
    )
    
    # Apply filters if provided
    if status:
        query = query.filter(TaskModel.status == status)
    
    if project_id:
        query = query.filter(TaskModel.project_id == project_id)
    
    results = query.offset(skip).limit(limit).all()
    
    # Convert the query results to Pydantic models
    tasks = []
    for task, project_name in results:
        task_dict = {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "description": task.description,
            "status": task.status,
            "category": task.category,
            "origin": task.origin,
            "created_at": task.created_at,
            "related_info": task.related_info,
            "project_name": project_name
        }
        tasks.append(TaskWithProject.model_validate(task_dict))
    
    return tasks


@router.get("/{task_id}", response_model=TaskWithProject)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve details for a specific task.
    """
    result = db.query(
        TaskModel, 
        ProjectModel.name.label("project_name")
    ).join(
        ProjectModel, 
        TaskModel.project_id == ProjectModel.project_id
    ).filter(
        TaskModel.task_id == task_id
    ).first()
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    task, project_name = result
    
    task_dict = {
        "task_id": task.task_id,
        "project_id": task.project_id,
        "description": task.description,
        "status": task.status,
        "category": task.category,
        "origin": task.origin,
        "created_at": task.created_at,
        "related_info": task.related_info,
        "project_name": project_name
    }
    
    return TaskWithProject.model_validate(task_dict)