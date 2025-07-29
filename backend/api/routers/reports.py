from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from ...database.connection import get_async_db
from ...database.models import User, Report
from .auth import get_current_user

router = APIRouter()

# Pydantic models
class ReportGenerate(BaseModel):
    report_type: str  # "attendance", "task", "weekly"
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    filters: Optional[dict] = {}

class ReportResponse(BaseModel):
    id: int
    title: str
    type: str
    content: dict
    generated_by_id: int
    date_from: datetime
    date_to: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Routes
@router.post("/generate")
async def generate_report(
    report_data: ReportGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Generate a new report using AI agent"""
    from ...agents.agent_manager import get_agent_manager
    
    # Prepare parameters
    parameters = {
        "start_date": report_data.start_date,
        "end_date": report_data.end_date,
        **report_data.filters
    }
    
    # Map report types to agent actions
    action_map = {
        "attendance": "generate_attendance_report",
        "task": "generate_task_report",
        "weekly": "generate_weekly_summary"
    }
    
    action = action_map.get(report_data.report_type)
    if not action:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    # Add user context for weekly reports
    if report_data.report_type == "weekly":
        parameters["user_id"] = report_data.filters.get("user_id", current_user.id)
    
    # Execute report generation
    agent_manager = get_agent_manager()
    result = await agent_manager.execute_action(
        agent_type="report",
        action=action,
        parameters=parameters,
        context={"user_id": current_user.id},
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))
    
    # Get the generated report from database
    latest_report = db.query(Report).filter(
        Report.generated_by_id == current_user.id
    ).order_by(Report.created_at.desc()).first()
    
    return {
        "message": "Report generated successfully",
        "report_id": latest_report.id if latest_report else None,
        "content": result["output"]
    }

@router.get("", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """List all reports"""
    query = db.query(Report).order_by(Report.created_at.desc())
    
    if report_type:
        query = query.filter(Report.type == report_type)
    
    # Non-managers can only see their own reports
    if current_user.role not in ["manager", "admin"]:
        query = query.filter(Report.generated_by_id == current_user.id)
    
    reports = query.offset(offset).limit(limit).all()
    
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Get report details"""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions
    if current_user.role not in ["manager", "admin"] and report.generated_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")
    
    return report