from typing import List
from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from app.agent.graph import bunk_agent_graph

router = APIRouter(prefix="/api/v1/agent", tags=["AI Bunk Planner Agent"])

class AgentChatRequest(BaseModel):
    student_id: int = Field(default=1, description="ID of the student chatting with the agent")
    message: str = Field(
        default="Can I bunk on 2026-11-12 and 2026-11-13?",
        description="Student question for the AI Bunk Planner",
    )
    planned_absent_dates: List[str] = Field(
        default_factory=list,
        examples=[[]],
        description="Optional list of YYYY-MM-DD dates to simulate skipping",
    )
    thread_id: str = Field(default="default-thread")

@router.post("/chat")
def chat_with_bunk_agent(payload: AgentChatRequest):
    config = {"configurable": {"thread_id": f"student-{payload.student_id}-{payload.thread_id}"}}
    result = bunk_agent_graph.invoke(
        {
            "messages": [HumanMessage(content=payload.message)],
            "student_id": payload.student_id,
            "planned_absent_dates": payload.planned_absent_dates,
        },
        config=config,
    )
    return {
        "student_id": payload.student_id,
        "needs_clarification": result.get("needs_clarification", False),
        "missing_fields": result.get("missing_fields", []),
        "planned_absent_dates": result.get("planned_absent_dates", []),
        "reply": result.get("final_answer", ""),
        "bunk_reports": result.get("bunk_reports", []),
    }
