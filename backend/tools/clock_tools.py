from langchain.tools import tool
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database.models import User, ClockRecord, AttendanceStatus
from ..database.connection import SessionLocal
import pytz

@tool
def clock_in_tool(user_id: int, location: Optional[dict] = None, notes: Optional[str] = None) -> str:
    """
    Clock in a user for work.
    
    Args:
        user_id: ID of the user clocking in
        location: Optional location dict with lat, lng, address
        notes: Optional notes about the clock in
    
    Returns:
        Success or error message
    """
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        # Check if already clocked in
        existing_record = db.query(ClockRecord).filter(
            ClockRecord.user_id == user_id,
            ClockRecord.clock_out.is_(None)
        ).first()
        
        if existing_record:
            return f"Error: {user.full_name} is already clocked in since {existing_record.clock_in}"
        
        # Create clock in record
        clock_record = ClockRecord(
            user_id=user_id,
            clock_in=datetime.utcnow(),
            status=AttendanceStatus.CLOCKED_IN,
            location=location,
            notes=notes
        )
        
        db.add(clock_record)
        db.commit()
        
        return f"Successfully clocked in {user.full_name} at {clock_record.clock_in.strftime('%I:%M %p')}"
        
    except Exception as e:
        db.rollback()
        return f"Error clocking in: {str(e)}"
    finally:
        db.close()

@tool
def clock_out_tool(user_id: int, notes: Optional[str] = None) -> str:
    """
    Clock out a user from work.
    
    Args:
        user_id: ID of the user clocking out
        notes: Optional notes about the clock out
    
    Returns:
        Success or error message with total hours worked
    """
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        # Find active clock in record
        clock_record = db.query(ClockRecord).filter(
            ClockRecord.user_id == user_id,
            ClockRecord.clock_out.is_(None)
        ).first()
        
        if not clock_record:
            return f"Error: {user.full_name} is not currently clocked in"
        
        # Update clock out
        clock_out_time = datetime.utcnow()
        clock_record.clock_out = clock_out_time
        clock_record.status = AttendanceStatus.CLOCKED_OUT
        
        # Calculate hours worked
        time_diff = clock_out_time - clock_record.clock_in
        hours_worked = round(time_diff.total_seconds() / 3600, 2)
        clock_record.total_hours = hours_worked
        
        if notes:
            existing_notes = clock_record.notes or ""
            clock_record.notes = f"{existing_notes}\nClock out: {notes}".strip()
        
        db.commit()
        
        return f"Successfully clocked out {user.full_name} at {clock_out_time.strftime('%I:%M %p')}. Total hours worked: {hours_worked}"
        
    except Exception as e:
        db.rollback()
        return f"Error clocking out: {str(e)}"
    finally:
        db.close()

@tool
def get_attendance_status_tool(user_id: int) -> str:
    """
    Get current attendance status for a user.
    
    Args:
        user_id: ID of the user to check
    
    Returns:
        Current attendance status
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        # Find active clock in record
        active_record = db.query(ClockRecord).filter(
            ClockRecord.user_id == user_id,
            ClockRecord.clock_out.is_(None)
        ).first()
        
        if active_record:
            clock_in_time = active_record.clock_in.strftime('%I:%M %p')
            duration = datetime.utcnow() - active_record.clock_in
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            return f"{user.full_name} is currently clocked in since {clock_in_time} ({hours}h {minutes}m ago)"
        else:
            # Get last clock out
            last_record = db.query(ClockRecord).filter(
                ClockRecord.user_id == user_id
            ).order_by(ClockRecord.clock_out.desc()).first()
            
            if last_record and last_record.clock_out:
                last_out = last_record.clock_out.strftime('%I:%M %p on %m/%d/%Y')
                return f"{user.full_name} is currently clocked out. Last clocked out at {last_out}"
            else:
                return f"{user.full_name} has never clocked in"
                
    except Exception as e:
        return f"Error checking attendance status: {str(e)}"
    finally:
        db.close()

@tool
def get_weekly_hours_tool(user_id: int) -> str:
    """
    Get total hours worked this week for a user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        Weekly hours summary
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        # Get start of week (Monday)
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Query records for this week
        records = db.query(ClockRecord).filter(
            ClockRecord.user_id == user_id,
            ClockRecord.clock_in >= start_of_week
        ).all()
        
        total_hours = 0
        daily_hours = {}
        
        for record in records:
            if record.total_hours:
                total_hours += record.total_hours
                day = record.clock_in.strftime('%A')
                daily_hours[day] = daily_hours.get(day, 0) + record.total_hours
        
        # Format response
        response = f"Weekly hours for {user.full_name}:\n"
        response += f"Total hours this week: {round(total_hours, 2)}\n"
        
        if daily_hours:
            response += "\nDaily breakdown:\n"
            for day, hours in sorted(daily_hours.items()):
                response += f"- {day}: {round(hours, 2)} hours\n"
        
        return response
        
    except Exception as e:
        return f"Error getting weekly hours: {str(e)}"
    finally:
        db.close()