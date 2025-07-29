from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ...database.connection import get_async_db
from ...database.models import User, ClockRecord
from .auth import get_current_user, get_current_manager

router = APIRouter()

# Pydantic models
class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class AttendanceRecord(BaseModel):
    id: int
    clock_in: datetime
    clock_out: Optional[datetime]
    total_hours: Optional[float]
    status: str
    location: Optional[dict]
    notes: Optional[str]
    
    class Config:
        from_attributes = True

# Routes
@router.get("")
async def list_employees(
    department: Optional[str] = None,
    role: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """List all employees (with filters)"""
    query = db.query(User)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    if department:
        query = query.filter(User.department == department)
    
    if role:
        query = query.filter(User.role == role)
    
    employees = query.all()
    
    return [
        {
            "id": emp.id,
            "email": emp.email,
            "full_name": emp.full_name,
            "department": emp.department,
            "role": emp.role,
            "is_active": emp.is_active
        }
        for emp in employees
    ]

@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Get employee details"""
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check permissions
    if current_user.role not in ["manager", "admin"] and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this employee")
    
    return {
        "id": employee.id,
        "email": employee.email,
        "username": employee.username,
        "full_name": employee.full_name,
        "department": employee.department,
        "role": employee.role,
        "is_active": employee.is_active,
        "created_at": employee.created_at.isoformat()
    }

@router.put("/{employee_id}")
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_manager),
    db: Session = Depends(get_async_db)
):
    """Update employee information (managers only)"""
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Update fields
    update_data = employee_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    employee.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(employee)
    
    return {"message": "Employee updated successfully", "employee_id": employee_id}

@router.get("/{employee_id}/attendance", response_model=List[AttendanceRecord])
async def get_employee_attendance(
    employee_id: int,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Get attendance records for an employee"""
    # Check permissions
    if current_user.role not in ["manager", "admin"] and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this attendance")
    
    query = db.query(ClockRecord).filter(ClockRecord.user_id == employee_id)
    
    # Apply date filters
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(ClockRecord.clock_in >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(ClockRecord.clock_in < end)
    
    records = query.order_by(ClockRecord.clock_in.desc()).all()
    
    return records