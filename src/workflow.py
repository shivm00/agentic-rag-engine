from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.agents.retrieval import retrieval_agent_node
from src.agents.analyst import analyst_agent_node

def build_graph():
    """
    Constructs and compiles the 2-agent state machine.
    Execution Flow: START -> Retrieval Agent -> Analyst Agent -> END
    """
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("retrieval_agent", retrieval_agent_node)
    workflow.add_node("analyst_agent", analyst_agent_node)

    # Define State Transitions (Edges)
    workflow.add_edge(START, "retrieval_agent")
    workflow.add_edge("retrieval_agent", "analyst_agent")
    workflow.add_edge("analyst_agent", END)

    return workflow.compile()

# Expose compiled runnable graph instance
app_graph = build_graph()

if __name__ == "__main__":
    initial_state: AgentState = {
        "query": "How do we handle GCP secret rotation?",
        "retrieved_docs": [],
        "analysis_output": None,
        "current_step": "initialized",
        "error": None
    }

    result = app_graph.invoke(initial_state)
    print("--- Pipeline Execution Output ---")
    print(f"Final Step    : {result['current_step']}")
    print(f"Retrieved Docs: {result['retrieved_docs']}")
    print(f"Error         : {result.get('error')}")
    print(f"Analysis      : {result['analysis_output']}")