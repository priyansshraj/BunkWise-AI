from typing import Annotated, Any, Dict, List, Optional, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class BunkAgentState(TypedDict):
    # add_messages appends new chat messages instead of overwriting history
    messages: Annotated[List[AnyMessage], add_messages]
    student_id: int
    planned_absent_dates: List[str]
    missing_fields: List[str]
    needs_clarification: bool
    bunk_reports: List[Dict[str, Any]]
    final_answer: Optional[str]
