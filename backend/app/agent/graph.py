from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from app.agent.nodes import (
    ask_clarification_node,
    bunk_planner_node,
    clarification_router,
    context_loader_node,
)
from app.agent.state import BunkAgentState

def build_bunk_agent_graph():
    builder = StateGraph(BunkAgentState)

    # 1. Register nodes
    builder.add_node("context_loader_node", context_loader_node)
    builder.add_node("ask_clarification_node", ask_clarification_node)
    builder.add_node("bunk_planner_node", bunk_planner_node)

    # 2. Define edges & conditional routing
    builder.add_edge(START, "context_loader_node")
    builder.add_conditional_edges(
        "context_loader_node",
        clarification_router,
        {
            "ask_clarification_node": "ask_clarification_node",
            "bunk_planner_node": "bunk_planner_node",
        },
    )
    builder.add_edge("ask_clarification_node", END)
    builder.add_edge("bunk_planner_node", END)

    # 3. Compile with MemorySaver checkpointer for multi-turn conversation threads
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

bunk_agent_graph = build_bunk_agent_graph()
