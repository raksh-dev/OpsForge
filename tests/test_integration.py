import pytest
from datetime import datetime, timedelta
from backend.database.connection import SessionLocal
from backend.database.models import User, Task, ClockRecord
from backend.agents.agent_manager import AgentManager

@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete workflow: clock in, create task, generate report"""
    db = SessionLocal()
    
    try:
        # Create test user
        user = User(
            email="workflow@test.com",
            username="workflowtest",
            full_name="Workflow Test",
            hashed_password="hashed",
            department="Engineering"
        )
        db.add(user)
        db.commit()
        
        # Initialize agent manager
        agent_manager = AgentManager()
        await agent_manager.initialize()
        
        # 1. Clock in
        result = await agent_manager.execute_action(
            agent_type="clock",
            action="clock_in",
            parameters={"user_id": user.id},
            context={},
            user_id=user.id
        )
        assert result["success"] == True
        
        # 2. Create task
        result = await agent_manager.execute_action(
            agent_type="task",
            action="create_task",
            parameters={
                "title": "Complete integration test",
                "description": "Test the full workflow",
                "assignee_id": user.id,
                "priority": "high"
            },
            context={},
            user_id=user.id
        )
        assert result["success"] == True
        
        # 3. Update task status
        task = db.query(Task).filter(Task.assignee_id == user.id).first()
        result = await agent_manager.execute_action(
            agent_type="task",
            action="update_status",
            parameters={
                "task_id": task.id,
                "new_status": "completed"
            },
            context={},
            user_id=user.id
        )
        assert result["success"] == True
        
        # 4. Clock out
        result = await agent_manager.execute_action(
            agent_type="clock",
            action="clock_out",
            parameters={"user_id": user.id},
            context={},
            user_id=user.id
        )
        assert result["success"] == True
        
        # 5. Generate report
        result = await agent_manager.execute_action(
            agent_type="report",
            action="generate_weekly_summary",
            parameters={"user_id": user.id},
            context={},
            user_id=user.id
        )
        assert result["success"] == True
        assert "Weekly Summary" in result["output"]
        
    finally:
        # Cleanup
        db.query(User).filter(User.email == "workflow@test.com").delete()
        db.commit()
        db.close()
        await agent_manager.cleanup()