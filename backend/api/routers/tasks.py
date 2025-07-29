from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from ...database.connection import get_async_db
from ...database.models import User, Task, TaskStatus, TaskPriority, TaskComment
from .auth import get_current_user

router = APIRouter()

# Pydantic models
class TaskCreate(BaseModel):
    title: str
    description: str
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"
    tags: Optional[List[str]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    due_date: Optional[datetime]
    assignee_id: Optional[int]
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    tags: Optional[List[str]]
    
    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    comment: str

# Routes
@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    created_by_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """List tasks with filters"""
    query = db.query(Task)
    
    # Apply filters
    if status:
        try:
            status_enum = TaskStatus(status.lower())
            query = query.filter(Task.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if priority:
        try:
            priority_enum = TaskPriority(priority.lower())
            query = query.filter(Task.priority == priority_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid priority")
    
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    if created_by_id:
        query = query.filter(Task.created_by_id == created_by_id)
    
    # Non-managers can only see their own tasks or tasks they created
    if current_user.role not in ["manager", "admin"]:
        query = query.filter(
            (Task.assignee_id == current_user.id) | 
            (Task.created_by_id == current_user.id)
        )
    
    tasks = query.offset(offset).limit(limit).all()
    
    return tasks

@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Create a new task"""
    # Validate priority
    try:
        priority_enum = TaskPriority(task_data.priority.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid priority")
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        assignee_id=task_data.assignee_id,
        created_by_id=current_user.id,
        due_date=task_data.due_date,
        priority=priority_enum,
        status=TaskStatus.TODO,
        tags=task_data.tags
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Get task details"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions
    if current_user.role not in ["manager", "admin"]:
        if task.assignee_id != current_user.id and task.created_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this task")
    
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Update a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions
    if current_user.role not in ["manager", "admin"]:
        if task.assignee_id != current_user.id and task.created_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this task")
    
    # Update fields
    update_data = task_data.dict(exclude_unset=True)
    
    # Validate enums
    if "status" in update_data:
        try:
            update_data["status"] = TaskStatus(update_data["status"].lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if "priority" in update_data:
        try:
            update_data["priority"] = TaskPriority(update_data["priority"].lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid priority")
    
    # Set completed_at if status changed to completed
    if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    return task

@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    assignee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Assign a task to a user"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions
    if current_user.role not in ["manager", "admin"] and task.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to assign this task")
    
    # Check if assignee exists
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    task.assignee_id = assignee_id
    task.updated_at = datetime.utcnow()
    
    if task.status == TaskStatus.TODO:
        task.status = TaskStatus.IN_PROGRESS
    
    db.commit()
    
    return {"message": f"Task assigned to {assignee.full_name}", "task_id": task_id}

@router.post("/{task_id}/comments")
async def add_task_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Add a comment to a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        comment=comment_data.comment
    )
    
    db.add(comment)
    db.commit()
    
    return {"message": "Comment added successfully", "task_id": task_id}