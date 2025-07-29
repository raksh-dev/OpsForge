from langchain.tools import tool
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ..database.models import User, Task, ClockRecord, Report, TaskStatus, TaskPriority
from ..database.connection import SessionLocal
import json

@tool
def generate_attendance_report_tool(
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    department: Optional[str] = None
) -> str:
    """
    Generate an attendance report for a date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        user_id: Optional specific user ID
        department: Optional department filter
    
    Returns:
        Formatted attendance report
    """
    db = SessionLocal()
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Build query
        query = db.query(ClockRecord).filter(
            and_(
                ClockRecord.clock_in >= start,
                ClockRecord.clock_in <= end + timedelta(days=1)
            )
        )
        
        # Apply filters
        if user_id:
            query = query.filter(ClockRecord.user_id == user_id)
        
        if department:
            query = query.join(User).filter(User.department == department)
        
        records = query.all()
        
        if not records:
            return "No attendance records found for the specified period"
        
        # Process data
        user_data = {}
        total_hours_all = 0
        
        for record in records:
            user = record.user
            if user.id not in user_data:
                user_data[user.id] = {
                    "name": user.full_name,
                    "department": user.department,
                    "days_worked": 0,
                    "total_hours": 0,
                    "late_arrivals": 0,
                    "records": []
                }
            
            user_data[user.id]["days_worked"] += 1
            
            if record.total_hours:
                user_data[user.id]["total_hours"] += record.total_hours
                total_hours_all += record.total_hours
            
            # Check for late arrivals (after 9:15 AM)
            if record.clock_in.hour > 9 or (record.clock_in.hour == 9 and record.clock_in.minute > 15):
                user_data[user.id]["late_arrivals"] += 1
        
        # Format report
        report = f"# Attendance Report\n"
        report += f"Period: {start_date} to {end_date}\n"
        report += f"Total Employees: {len(user_data)}\n"
        report += f"Total Hours Worked: {round(total_hours_all, 2)}\n\n"
        
        # Individual summaries
        for user_id, data in user_data.items():
            avg_hours = round(data["total_hours"] / data["days_worked"], 2) if data["days_worked"] > 0 else 0
            report += f"## {data['name']} ({data['department']})\n"
            report += f"- Days Worked: {data['days_worked']}\n"
            report += f"- Total Hours: {round(data['total_hours'], 2)}\n"
            report += f"- Average Hours/Day: {avg_hours}\n"
            report += f"- Late Arrivals: {data['late_arrivals']}\n\n"
        
        # Save report to database
        report_record = Report(
            title=f"Attendance Report {start_date} to {end_date}",
            type="attendance",
            content={
                "summary": user_data,
                "total_hours": total_hours_all,
                "employee_count": len(user_data)
            },
            generated_by_id=1,  # System generated
            date_from=start,
            date_to=end
        )
        db.add(report_record)
        db.commit()
        
        return report
        
    except Exception as e:
        return f"Error generating attendance report: {str(e)}"
    finally:
        db.close()

@tool
def generate_task_report_tool(
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    include_completed: bool = True
) -> str:
    """
    Generate a task completion report for a date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        user_id: Optional specific user ID
        include_completed: Include completed tasks in report
    
    Returns:
        Formatted task report
    """
    db = SessionLocal()
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Build query
        query = db.query(Task).filter(
            and_(
                Task.created_at >= start,
                Task.created_at <= end + timedelta(days=1)
            )
        )
        
        if user_id:
            query = query.filter(Task.assignee_id == user_id)
        
        tasks = query.all()
        
        if not tasks:
            return "No tasks found for the specified period"
        
        # Process data
        stats = {
            "total": len(tasks),
            "completed": 0,
            "in_progress": 0,
            "todo": 0,
            "overdue": 0,
            "by_priority": {"low": 0, "medium": 0, "high": 0, "urgent": 0},
            "completion_rate": 0
        }
        
        completed_tasks = []
        pending_tasks = []
        
        for task in tasks:
            # Status counts
            if task.status == TaskStatus.COMPLETED:
                stats["completed"] += 1
                completed_tasks.append(task)
            elif task.status == TaskStatus.IN_PROGRESS:
                stats["in_progress"] += 1
                pending_tasks.append(task)
            elif task.status == TaskStatus.TODO:
                stats["todo"] += 1
                pending_tasks.append(task)
            
            # Priority counts
            stats["by_priority"][task.priority.value] += 1
            
            # Check overdue
            if task.due_date and task.due_date < datetime.utcnow() and task.status != TaskStatus.COMPLETED:
                stats["overdue"] += 1
        
        stats["completion_rate"] = round((stats["completed"] / stats["total"]) * 100, 1)
        
        # Format report
        report = f"# Task Report\n"
        report += f"Period: {start_date} to {end_date}\n\n"
        
        report += f"## Summary\n"
        report += f"- Total Tasks: {stats['total']}\n"
        report += f"- Completed: {stats['completed']} ({stats['completion_rate']}%)\n"
        report += f"- In Progress: {stats['in_progress']}\n"
        report += f"- To Do: {stats['todo']}\n"
        report += f"- Overdue: {stats['overdue']}\n\n"
        
        report += f"## By Priority\n"
        for priority, count in stats["by_priority"].items():
            report += f"- {priority.capitalize()}: {count}\n"
        report += "\n"
        
        if include_completed and completed_tasks:
            report += f"## Completed Tasks ({len(completed_tasks)})\n"
            for task in completed_tasks[:10]:  # Show top 10
                report += f"- [{task.id}] {task.title}"
                if task.assignee:
                    report += f" (by {task.assignee.full_name})"
                report += "\n"
            if len(completed_tasks) > 10:
                report += f"... and {len(completed_tasks) - 10} more\n"
            report += "\n"
        
        if pending_tasks:
            report += f"## Pending Tasks ({len(pending_tasks)})\n"
            # Sort by priority and due date
            pending_tasks.sort(key=lambda t: (
                -list(TaskPriority).index(t.priority),
                t.due_date or datetime.max
            ))
            
            for task in pending_tasks[:10]:
                report += f"- [{task.id}] {task.title} ({task.priority.value})"
                if task.assignee:
                    report += f" - {task.assignee.full_name}"
                if task.due_date:
                    days_until = (task.due_date.date() - datetime.utcnow().date()).days
                    if days_until < 0:
                        report += f" - OVERDUE"
                    elif days_until == 0:
                        report += f" - DUE TODAY"
                    else:
                        report += f" - Due in {days_until} days"
                report += "\n"
        
        # Save report
        report_record = Report(
            title=f"Task Report {start_date} to {end_date}",
            type="task",
            content=stats,
            generated_by_id=1,
            date_from=start,
            date_to=end
        )
        db.add(report_record)
        db.commit()
        
        return report
        
    except Exception as e:
        return f"Error generating task report: {str(e)}"
    finally:
        db.close()

@tool
def generate_weekly_summary_tool(user_id: int) -> str:
    """
    Generate a weekly summary for a specific user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        Formatted weekly summary
    """
    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        # Calculate week boundaries
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Get attendance data
        clock_records = db.query(ClockRecord).filter(
            and_(
                ClockRecord.user_id == user_id,
                ClockRecord.clock_in >= start_of_week,
                ClockRecord.clock_in <= end_of_week + timedelta(days=1)
            )
        ).all()
        
        total_hours = sum(r.total_hours or 0 for r in clock_records)
        days_worked = len(set(r.clock_in.date() for r in clock_records))
        
        # Get task data
        completed_tasks = db.query(Task).filter(
            and_(
                Task.assignee_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= start_of_week,
                Task.completed_at <= end_of_week + timedelta(days=1)
            )
        ).all()
        
        active_tasks = db.query(Task).filter(
            and_(
                Task.assignee_id == user_id,
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            )
        ).all()
        
        # Format summary
        summary = f"# Weekly Summary for {user.full_name}\n"
        summary += f"Week: {start_of_week.strftime('%B %d')} - {end_of_week.strftime('%B %d, %Y')}\n\n"
        
        summary += f"## Attendance\n"
        summary += f"- Days Worked: {days_worked}/5\n"
        summary += f"- Total Hours: {round(total_hours, 2)}\n"
        summary += f"- Average Hours/Day: {round(total_hours/days_worked, 2) if days_worked > 0 else 0}\n\n"
        
        summary += f"## Tasks\n"
        summary += f"- Completed This Week: {len(completed_tasks)}\n"
        summary += f"- Currently Active: {len(active_tasks)}\n\n"
        
        if completed_tasks:
            summary += f"### Completed Tasks:\n"
            for task in completed_tasks[:5]:
                summary += f"- {task.title}\n"
            if len(completed_tasks) > 5:
                summary += f"... and {len(completed_tasks) - 5} more\n"
            summary += "\n"
        
        if active_tasks:
            summary += f"### Active Tasks:\n"
            high_priority = [t for t in active_tasks if t.priority in [TaskPriority.HIGH, TaskPriority.URGENT]]
            if high_priority:
                summary += "High Priority:\n"
                for task in high_priority:
                    summary += f"- {task.title}"
                    if task.due_date:
                        summary += f" (Due: {task.due_date.strftime('%m/%d')})"
                    summary += "\n"
        
        # Save summary
        report_record = Report(
            title=f"Weekly Summary - {user.full_name} - Week of {start_of_week}",
            type="weekly",
            content={
                "hours_worked": total_hours,
                "days_worked": days_worked,
                "tasks_completed": len(completed_tasks),
                "active_tasks": len(active_tasks)
            },
            generated_by_id=user_id,
            date_from=start_of_week,
            date_to=end_of_week
        )
        db.add(report_record)
        db.commit()
        
        return summary
        
    except Exception as e:
        return f"Error generating weekly summary: {str(e)}"
    finally:
        db.close()

@tool  
def send_report_email_tool(
    report_content: str,
    recipient_email: str,
    subject: str
) -> str:
    """
    Send a report via email.
    
    Args:
        report_content: The report content to send
        recipient_email: Email address to send to
        subject: Email subject line
    
    Returns:
        Success or error message
    """
    # This would integrate with your email service
    # For now, we'll simulate it
    return f"Report '{subject}' sent successfully to {recipient_email}"