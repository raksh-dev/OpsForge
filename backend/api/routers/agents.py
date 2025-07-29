from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...agents.agent_manager import get_agent_manager
from ...database.connection import get_async_db
from ...database.models import AgentAction, User
from .auth import get_current_user, get_current_manager
import logging
import re
import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class AgentRequest(BaseModel):
    agent_type: str
    action: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = {}

class AgentResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    agent: str
    execution_time_ms: int
    action_id: Optional[int] = None

class AgentActionOverride(BaseModel):
    reason: str
    corrective_action: Dict[str, Any]

class AgentInfo(BaseModel):
    name: str
    description: str
    available: bool

# Routes
@router.post("/execute", response_model=AgentResponse)
async def execute_agent_action(
    request: AgentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Execute an agent action"""
    try:
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Add user context
        request.context["user_id"] = current_user.id
        request.context["user_name"] = current_user.full_name
        request.context["user_role"] = current_user.role
        request.context["user_department"] = current_user.department
        
        # Execute action
        result = await agent_manager.execute_action(
            agent_type=request.agent_type,
            action=request.action,
            parameters=request.parameters,
            context=request.context,
            user_id=current_user.id
        )
        
        # Get the action ID from database (last action by this user)
        last_action = db.query(AgentAction).filter(
            AgentAction.user_id == current_user.id
        ).order_by(AgentAction.id.desc()).first()
        
        return AgentResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            agent=result["agent"],
            execution_time_ms=result["execution_time_ms"],
            action_id=last_action.id if last_action else None
        )
        
    except Exception as e:
        logger.error(f"Agent execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info", response_model=Dict[str, AgentInfo])
async def get_agents_info(current_user: User = Depends(get_current_user)):
    """Get information about available agents"""
    agent_manager = get_agent_manager()
    return agent_manager.get_agent_info()

@router.get("/actions/history")
async def get_agent_actions(
    limit: int = 50,
    offset: int = 0,
    agent_type: Optional[str] = None,
    success_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Get history of agent actions"""
    query = db.query(AgentAction).order_by(AgentAction.timestamp.desc())
    
    # Filter by agent type if specified
    if agent_type:
        query = query.filter(AgentAction.agent_name == agent_type)
    
    # Filter by success if specified
    if success_only:
        query = query.filter(AgentAction.success == True)
    
    # Non-managers can only see their own actions
    if current_user.role not in ["manager", "admin"]:
        query = query.filter(AgentAction.user_id == current_user.id)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    actions = query.offset(offset).limit(limit).all()
    
    # Format response
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "actions": [
            {
                "id": action.id,
                "agent_name": action.agent_name,
                "action_type": action.action_type,
                "success": action.success,
                "error_message": action.error_message,
                "execution_time_ms": action.execution_time_ms,
                "timestamp": action.timestamp.isoformat(),
                "user_id": action.user_id,
                "overridden": action.overridden
            }
            for action in actions
        ]
    }

@router.get("/actions/{action_id}")
async def get_agent_action_detail(
    action_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_async_db)
):
    """Get detailed information about a specific agent action"""
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Check permissions
    if current_user.role not in ["manager", "admin"] and action.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this action")
    
    return {
        "id": action.id,
        "agent_name": action.agent_name,
        "action_type": action.action_type,
        "input_data": action.input_data,
        "output_data": action.output_data,
        "success": action.success,
        "error_message": action.error_message,
        "execution_time_ms": action.execution_time_ms,
        "timestamp": action.timestamp.isoformat(),
        "user": {
            "id": action.user.id,
            "name": action.user.full_name,
            "email": action.user.email
        } if action.user else None,
        "overridden": action.overridden,
        "overridden_by": {
            "id": action.overridden_by.id,
            "name": action.overridden_by.full_name
        } if action.overridden_by else None,
        "override_reason": action.override_reason
    }

@router.post("/actions/{action_id}/override")
async def override_agent_action(
    action_id: int,
    override_data: AgentActionOverride,
    current_user: User = Depends(get_current_manager),
    db: Session = Depends(get_async_db)
):
    """Override an agent action (managers only)"""
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if action.overridden:
        raise HTTPException(status_code=400, detail="Action already overridden")
    
    # Mark as overridden
    action.overridden = True
    action.overridden_by_id = current_user.id
    action.override_reason = override_data.reason
    
    # TODO: Implement corrective action based on action type
    # This would involve calling the appropriate tools/functions
    # to reverse or modify the original action
    
    db.commit()
    
    return {"message": "Action overridden successfully", "action_id": action_id}
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None

def validate_date_format(date_string: str, format: str = "%Y-%m-%d") -> bool:
    """Validate date string format"""
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>\"\'`;]', '', text)
    
    return text