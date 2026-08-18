from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Shared mutable state across the agentic pipeline.
    Functions like a Context/DTO object in Spring StateMachine.
    """
    query: str
    retrieved_docs: List[Dict[str, Any]]
    analysis_output: Optional[str]
    current_step: str
    error: Optional[str]