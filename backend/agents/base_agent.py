from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, HumanMessage
from ..config.settings import settings
from ..database.models import AgentAction
from ..utils.llm_factory import get_llm
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(
        self, 
        name: str, 
        description: str,
        tools: List = None,
        temperature: float = 0.3,
        model: str = None  # Will use default from settings
    ):
        self.name = name
        self.description = description
        self.tools = tools or []
        
        # Initialize LLM using factory
        self.llm = get_llm(
            model=model,
            temperature=temperature,
            streaming=True
        )
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Remember last 10 exchanges
        )
        
        # Create prompt
        self.prompt = self._create_prompt()
        
        # Create agent if tools are provided
        if self.tools:
            self.agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            
            self.executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                return_intermediate_steps=True
            )
        else:
            self.executor = None
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for the agent"""
        system_prompt = self._get_system_prompt()
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    async def execute(
        self, 
        input_text: str, 
        context: Dict[str, Any] = None,
        user_id: Optional[int] = None,
        save_to_db: bool = True,
        db_session = None
    ) -> Dict[str, Any]:
        """Execute the agent with input text"""
        start_time = time.time()
        
        try:
            # Add context to input
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                full_input = f"Context:\n{context_str}\n\nUser Request: {input_text}"
            else:
                full_input = input_text
            
            # Execute agent
            if self.executor:
                result = await self.executor.ainvoke({"input": full_input})
                output = result["output"]
                intermediate_steps = result.get("intermediate_steps", [])
            else:
                # For agents without tools, just use the LLM
                response = await self.llm.ainvoke([
                    SystemMessage(content=self._get_system_prompt()),
                    HumanMessage(content=full_input)
                ])
                output = response.content
                intermediate_steps = []
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Prepare result
            result_data = {
                "success": True,
                "output": output,
                "agent": self.name,
                "execution_time_ms": execution_time,
                "intermediate_steps": intermediate_steps
            }
            
            # Save to database if requested
            if save_to_db and db_session:
                await self._save_action(
                    db_session=db_session,
                    user_id=user_id,
                    action_type="execute",
                    input_data={"input": input_text, "context": context},
                    output_data=result_data,
                    success=True,
                    execution_time_ms=execution_time
                )
            
            logger.info(f"{self.name} executed successfully in {execution_time}ms")
            return result_data
            
        except Exception as e:
            logger.error(f"{self.name} execution error: {str(e)}")
            execution_time = int((time.time() - start_time) * 1000)
            
            error_result = {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "execution_time_ms": execution_time
            }
            
            # Save error to database
            if save_to_db and db_session:
                await self._save_action(
                    db_session=db_session,
                    user_id=user_id,
                    action_type="execute",
                    input_data={"input": input_text, "context": context},
                    output_data=error_result,
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time
                )
            
            return error_result
    
    async def _save_action(
        self,
        db_session,
        user_id: Optional[int],
        action_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        success: bool,
        execution_time_ms: int,
        error_message: Optional[str] = None
    ):
        """Save agent action to database"""
        try:
            action = AgentAction(
                agent_name=self.name,
                action_type=action_type,
                input_data=input_data,
                output_data=output_data,
                success=success,
                error_message=error_message,
                user_id=user_id,
                execution_time_ms=execution_time_ms
            )
            db_session.add(action)
            db_session.commit()
        except Exception as e:
            logger.error(f"Error saving agent action: {e}")
            db_session.rollback()
    
    def clear_memory(self):
        """Clear the agent's memory"""
        self.memory.clear()