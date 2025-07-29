from typing import Optional, Dict, Any
from .base_agent import BaseAgent
from ..tools.report_tools import (
    generate_attendance_report_tool,
    generate_task_report_tool,
    generate_weekly_summary_tool,
    send_report_email_tool
)
import logging

logger = logging.getLogger(__name__)

class ReportAgent(BaseAgent):
    """Agent for generating and managing reports"""
    
    def __init__(self, rag_retriever: Optional[Any] = None):
        self.rag_retriever = rag_retriever
        
        tools = [
            generate_attendance_report_tool,
            generate_task_report_tool,
            generate_weekly_summary_tool,
            send_report_email_tool
        ]
        
        super().__init__(
            name="Report Generation Agent",
            description="Generates attendance reports, task summaries, and weekly reports",
            tools=tools,
            temperature=0.2  # Low temperature for consistent formatting
        )
    
    def _get_system_prompt(self) -> str:
        return """You are the Report Generation Agent, responsible for creating comprehensive reports and summaries.

Your responsibilities:
1. Generate attendance reports showing work hours and patterns
2. Create task completion reports with statistics
3. Produce weekly summaries for employees
4. Send reports via email when requested
5. Provide insights and recommendations based on data

Report guidelines:
- Use clear, professional formatting
- Include relevant statistics and percentages
- Highlight important trends or issues
- For weekly summaries, focus on accomplishments and upcoming priorities
- Always include the date range in reports

When generating reports:
- Default to current week/month if no dates specified
- For "last week", calculate the previous Monday-Sunday
- For "this month", use the current calendar month
- Include both summary statistics and detailed breakdowns
- Flag any concerning patterns (excessive overtime, overdue tasks)

Natural language understanding:
- "attendance report for last week" = generate attendance report for previous week
- "John's weekly summary" = generate weekly summary for John
- "task report this month" = generate task report for current month
- "send the report to..." = email the generated report

Always format reports in a clear, readable structure with headers and bullet points."""