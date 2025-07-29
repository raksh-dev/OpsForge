from typing import Dict, Any, Optional
from .clock_agent import ClockAgent
from .task_agent import TaskAgent
from .report_agent import ReportAgent
from ..database.connection import SessionLocal
from ..rag.retriever import RAGRetriever
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages all AI agents"""
    
    def __init__(self):
        self.agents = {}
        self.rag_retriever = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all agents"""
        if self._initialized:
            return
        
        try:
            # Initialize RAG retriever
            self.rag_retriever = RAGRetriever()
            await self.rag_retriever.initialize()
            
            # Initialize agents
            self.agents = {
                "clock": ClockAgent(),
                "task": TaskAgent(self.rag_retriever),
                "report": ReportAgent(self.rag_retriever),
            }
            
            self._initialized = True
            logger.info("Agent Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Agent Manager: {e}")
            raise
    
    async def execute_action(
        self,
        agent_type: str,
        action: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute an action with the specified agent"""
        
        if not self._initialized:
            await self.initialize()
        
        # Get the agent
        agent = self.agents.get(agent_type)
        if not agent:
            return {
                "success": False,
                "error": f"Unknown agent type: {agent_type}",
                "agent": agent_type
            }
        
        # Prepare input based on action
        if action == "process_natural_language":
            input_text = parameters.get("query", "")
        else:
            # Format parameters as natural language
            input_text = f"Action: {action}\n"
            for key, value in parameters.items():
                input_text += f"{key}: {value}\n"
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Execute agent
            result = await agent.execute(
                input_text=input_text,
                context=context,
                user_id=user_id,
                save_to_db=True,
                db_session=db
            )
            
            return result
            
        finally:
            db.close()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about all available agents"""
        return {
            agent_name: {
                "name": agent.name,
                "description": agent.description,
                "available": True
            }
            for agent_name, agent in self.agents.items()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.rag_retriever:
            await self.rag_retriever.cleanup()
        
        for agent in self.agents.values():
            agent.clear_memory()
        
        self._initialized = False
        logger.info("Agent Manager cleaned up")

# Global instance
agent_manager = AgentManager()

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance"""
    return agent_manager