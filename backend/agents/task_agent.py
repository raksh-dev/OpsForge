from typing import Optional, Dict, Any
from .base_agent import BaseAgent
from ..tools.task_tools import (
    create_task_tool,
    assign_task_tool,
    update_task_status_tool,
    get_user_tasks_tool,
    search_tasks_tool
)
import logging
logger = logging.getLogger(__name__)

class TaskAgent(BaseAgent):
    """Agent for managing tasks and assignments"""
    
    def __init__(self, rag_retriever: Optional[Any] = None):
        self.rag_retriever = rag_retriever
        
        tools = [
            create_task_tool,
            assign_task_tool,
            update_task_status_tool,
            get_user_tasks_tool,
            search_tasks_tool
        ]
        
        super().__init__(
            name="Task Management Agent",
            description="Handles task creation, assignment, tracking, and workload management",
            tools=tools,
            temperature=0.3
        )
    
    def _get_system_prompt(self) -> str:
        return """You are the Task Management Agent, responsible for managing tasks and assignments efficiently.

Your responsibilities:
1. Create new tasks with appropriate details
2. Assign tasks to team members based on workload and skills
3. Update task statuses and track progress
4. Search and retrieve task information
5. Monitor deadlines and priorities

Important policies:
- Consider workload when assigning tasks (warn if someone has >10 active tasks)
- High-priority and urgent tasks should be assigned immediately
- Tasks with approaching deadlines should be flagged
- Always confirm task creation and assignment
- Suggest task details if they're missing (like due dates for urgent tasks)

When creating tasks:
- If no due date is specified, ask if one should be set
- If no priority is specified, default to "medium"
- For urgent tasks, suggest a near due date
- Always create descriptive titles

When assigning tasks:
- Check the person's current workload
- Consider their department/skills if mentioned
- Warn about overloaded team members
- Suggest alternatives if someone is too busy

For natural language understanding:
- "Give John the website task" = assign task to John
- "Create a task for..." = create new task
- "What's on my plate?" = get user's tasks
- "Mark task X as done" = update status to completed
- "Find tasks about..." = search tasks

Always extract relevant information from the context and request."""
    
    async def execute(self, input_text: str, context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute with optional RAG enhancement"""
        
        # If we have RAG retriever and the query seems policy-related
        if self.rag_retriever and any(word in input_text.lower() for word in ['policy', 'procedure', 'guideline', 'how to']):
            try:
                # Get relevant documents
                relevant_docs = await self.rag_retriever.get_relevant_documents(
                    input_text,
                    filter={"category": "task_management"}
                )
                
                if relevant_docs:
                    # Add to context
                    if context is None:
                        context = {}
                    context["relevant_policies"] = "\n".join(relevant_docs[:3])  # Top 3 docs
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        return await super().execute(input_text, context, **kwargs)