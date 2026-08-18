from typing import Dict, Any
from src.state import AgentState

def analyst_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyst Agent: Evaluates retrieved documents and formats final analysis.
    """
    docs = state.get("retrieved_docs", [])
    query = state.get("query", "")

    if not docs:
        return {
            "analysis_output": "No relevant documents found to perform analysis.",
            "current_step": "analyst_completed"
        }

    doc_summary = " | ".join([d["content"] for d in docs])
    analysis = f"Analysis for '{query}': Evaluated {len(docs)} document(s). Key Insights: {doc_summary}"

    return {
        "analysis_output": analysis,
        "current_step": "analyst_completed"
    }