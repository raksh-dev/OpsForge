from langchain.tools import tool
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..database.models import User, Task, TaskStatus, TaskPriority, TaskComment
from ..database.connection import SessionLocal

@tool
def create_task_tool(
    title: str,
    description: str,
    assignee_id: Optional[int] = None,
    due_date: Optional[str] = None,
    priority: str = "medium",
    created_by_id: int = 1,
    tags: Optional[List[str]] = None
) -> str:
    """
    Create a new task.
    
    Args:
        title: Task title
        description: Task description
        assignee_id: ID of user to assign to (optional)
        due_date: Due date in YYYY-MM-DD format (optional)
        priority: Priority level (low, medium, high, urgent)
        created_by_id: ID of task creator
        tags: List of tags (optional)
    
    Returns:
        Success message with task details
    """
    db = SessionLocal()
    try:
        # Parse due date
        due_datetime = None
        if due_date:
            try:
                due_datetime = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return f"Error: Invalid date format. Use YYYY-MM-DD"
        
        # Validate priority
        try:
            priority_enum = TaskPriority(priority.lower())
        except ValueError:
            return f"Error: Invalid priority. Use: low, medium, high, or urgent"
        
        # Create task
        task = Task(
            title=title,
            description=description,
            assignee_id=assignee_id,
            created_by_id=created_by_id,
            due_date=due_datetime,
            priority=priority_enum,
            status=TaskStatus.TODO,
            tags=tags
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = f"Task created successfully!\n"
        response += f"ID: {task.id}\n"
        response += f"Title: {task.title}\n"
        response += f"Priority: {task.priority.value}\n"
        
        if assignee_id:
            assignee = db.query(User).filter(User.id == assignee_id).first()
            if assignee:
                response += f"Assigned to: {assignee.full_name}\n"
        
        if due_date:
            response += f"Due date: {due_date}\n"
        
        return response
        
    except Exception as e:
        db.rollback()
        return f"Error creating task: {str(e)}"
    finally:
        db.close()

@tool
def assign_task_tool(task_id: int, assignee_id: int) -> str:
    """
    Assign or reassign a task to a user.
    
    Args:
        task_id: ID of the task
        assignee_id: ID of the user to assign to
    
    Returns:
        Success or error message
    """
    db = SessionLocal()
    try:
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return f"Error: Task with ID {task_id} not found"
        
        # Get assignee
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            return f"Error: User with ID {assignee_id} not found"
        
        # Check workload
        active_tasks = db.query(Task).filter(
            Task.assignee_id == assignee_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
        ).count()
        
        warning = ""
        if active_tasks >= 10:
            warning = f"\nWarning: {assignee.full_name} already has {active_tasks} active tasks!"
        
        # Assign task
        old_assignee = None
        if task.assignee_id:
            old_user = db.query(User).filter(User.id == task.assignee_id).first()
            old_assignee = old_user.full_name if old_user else "Unknown"
        
        task.assignee_id = assignee_id
        task.updated_at = datetime.utcnow()
        
        if task.status == TaskStatus.TODO:
            task.status = TaskStatus.IN_PROGRESS
        
        db.commit()
        
        response = f"Task '{task.title}' assigned to {assignee.full_name}"
        if old_assignee:
            response += f" (previously assigned to {old_assignee})"
        response += warning
        
        return response
        
    except Exception as e:
        db.rollback()
        return f"Error assigning task: {str(e)}"
    finally:
        db.close()

@tool
def update_task_status_tool(task_id: int, new_status: str, comment: Optional[str] = None) -> str:
    """
    Update the status of a task.
    
    Args:
        task_id: ID of the task
        new_status: New status (todo, in_progress, review, completed, cancelled)
        comment: Optional comment about the status change
    
    Returns:
        Success or error message
    """
    db = SessionLocal()
    try:
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return f"Error: Task with ID {task_id} not found"
        
        # Validate status
        try:
            status_enum = TaskStatus(new_status.lower())
        except ValueError:
            return f"Error: Invalid status. Use: todo, in_progress, review, completed, or cancelled"
        
        old_status = task.status
        task.status = status_enum
        task.updated_at = datetime.utcnow()
        
        if status_enum == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            if task.clock_in:
                # Calculate actual hours if there was a clock-in
                task.actual_hours = (task.completed_at - task.created_at).total_seconds() / 3600
        
        # Add comment if provided
        if comment and task.assignee_id:
            task_comment = TaskComment(
                task_id=task_id,
                user_id=task.assignee_id,
                comment=f"Status changed from {old_status.value} to {status_enum.value}: {comment}"
            )
            db.add(task_comment)
        
        db.commit()
        
        response = f"Task '{task.title}' status updated from {old_status.value} to {status_enum.value}"
        
        if task.assignee:
            response += f"\nAssigned to: {task.assignee.full_name}"
        
        return response
        
    except Exception as e:
        db.rollback()
        return f"Error updating task status: {str(e)}"
    finally:
        db.close()

@tool
def get_user_tasks_tool(user_id: int, status_filter: Optional[str] = None) -> str:
    """
    Get all tasks for a specific user.
    
    Args:
        user_id: ID of the user
        status_filter: Optional status filter (todo, in_progress, completed, etc.)
    
    Returns:
        List of tasks for the user
    """
    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        # Build query
        query = db.query(Task).filter(Task.assignee_id == user_id)
        
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter.lower())
                query = query.filter(Task.status == status_enum)
            except ValueError:
                return f"Error: Invalid status filter. Use: todo, in_progress, review, completed, or cancelled"
        
        # Get tasks ordered by priority and due date
        tasks = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast()
        ).all()
        
        if not tasks:
            return f"No tasks found for {user.full_name}"
        
        # Format response
        response = f"Tasks for {user.full_name}:\n\n"
        
        # Group by status
        tasks_by_status = {}
        for task in tasks:
            status = task.status.value
            if status not in tasks_by_status:
                tasks_by_status[status] = []
            tasks_by_status[status].append(task)
        
        for status, status_tasks in tasks_by_status.items():
            response += f"{status.upper()} ({len(status_tasks)} tasks):\n"
            for task in status_tasks:
                response += f"- [{task.id}] {task.title}"
                if task.priority != TaskPriority.MEDIUM:
                    response += f" ({task.priority.value})"
                if task.due_date:
                    days_until = (task.due_date.date() - datetime.utcnow().date()).days
                    if days_until < 0:
                        response += f" - OVERDUE by {-days_until} days"
                    elif days_until == 0:
                        response += " - DUE TODAY"
                    elif days_until <= 3:
                        response += f" - Due in {days_until} days"
                response += "\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error getting user tasks: {str(e)}"
    finally:
        db.close()

@tool
def search_tasks_tool(
    search_term: str,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    assigned_only: bool = True
) -> str:
    """
    Search for tasks based on various criteria.
    
    Args:
        search_term: Text to search in title and description
        status_filter: Optional status filter
        priority_filter: Optional priority filter
        assigned_only: Only show assigned tasks (default True)
    
    Returns:
        List of matching tasks
    """
    db = SessionLocal()
    try:
        # Build query
        query = db.query(Task)
        
        # Search filter
        query = query.filter(
            db.or_(
                Task.title.ilike(f"%{search_term}%"),
                Task.description.ilike(f"%{search_term}%")
            )
        )
        
        # Status filter
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter.lower())
                query = query.filter(Task.status == status_enum)
            except ValueError:
                pass
        
        # Priority filter
        if priority_filter:
            try:
                priority_enum = TaskPriority(priority_filter.lower())
                query = query.filter(Task.priority == priority_enum)
            except ValueError:
                pass
        
        # Assigned filter
        if assigned_only:
            query = query.filter(Task.assignee_id.isnot(None))
        
        # Get results
        tasks = query.order_by(Task.created_at.desc()).limit(20).all()
        
        if not tasks:
            return f"No tasks found matching '{search_term}'"
        
        # Format response
        response = f"Found {len(tasks)} tasks matching '{search_term}':\n\n"
        
        for task in tasks:
            response += f"[{task.id}] {task.title}\n"
            response += f"   Status: {task.status.value} | Priority: {task.priority.value}\n"
            if task.assignee:
                response += f"   Assigned to: {task.assignee.full_name}\n"
            if task.due_date:
                response += f"   Due: {task.due_date.strftime('%Y-%m-%d')}\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error searching tasks: {str(e)}"
    finally:
        db.close()