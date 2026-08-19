import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from src.retrieval import search_vector_store

# =====================================================================
# AGENT STATE DEFINITION
# =====================================================================
class AgentState(TypedDict):
    query: str
    retrieved_chunks: List[dict]
    final_answer: str
    source_documents: List[str]

# =====================================================================
# NODE 1: RETRIEVAL AGENT
# =====================================================================
def retrieval_agent_node(state: AgentState) -> AgentState:
    """Retrieves relevant text chunks from pre-computed Gold vector tables."""
    user_query = state["query"]
    print(f"[Retrieval Agent] Querying Gold Vector Store for: {user_query}")

    # Executes k-NN Cosine Similarity search against Qdrant / Gold tables
    search_results = search_vector_store(query_text=user_query, top_k=3)

    chunks = [res["chunk_text"] for res in search_results]
    sources = list(set([res["file_path"] for res in search_results]))

    return {
        **state,
        "retrieved_chunks": chunks,
        "source_documents": sources
    }

# =====================================================================
# NODE 2: ANALYST AGENT
# =====================================================================
def analyst_agent_node(state: AgentState) -> AgentState:
    """Synthesizes facts from retrieved context into a grounded answer."""
    query = state["query"]
    chunks = state["retrieved_chunks"]
    sources = state["source_documents"]

    print("[Analyst Agent] Evaluating context and synthesizing final answer...")

    if not chunks:
        synthesized_text = "I could not find relevant documentation to answer your request."
    else:
        context_block = "\n---\n".join(chunks)
        # Production LLM Call (e.g., GPT-4o / Claude 3.5 / Gemini)
        synthesized_text = f"Based on enterprise documentation:\n{context_block[:300]}...\n\n[Sources: {', '.join(sources)}]"

    return {
        **state,
        "final_answer": synthesized_text
    }

# =====================================================================
# LANGGRAPH STATE MACHINE ASSEMBLY
# =====================================================================
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("retrieval_agent", retrieval_agent_node)
workflow.add_node("analyst_agent", analyst_agent_node)

# Set Entry Point and Transitions
workflow.set_entry_point("retrieval_agent")
workflow.add_edge("retrieval_agent", "analyst_agent")
workflow.add_edge("analyst_agent", END)

# Compile Executable Graph
rag_agent_app = workflow.compile()