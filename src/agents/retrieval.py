from typing import Dict, Any
from fastembed import TextEmbedding
from src.state import AgentState
from src.ingestion import get_qdrant_client, COLLECTION_NAME

# Shared singleton embedding instance
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def retrieval_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Retrieval Agent: Embeds query, executes k-NN vector search against Qdrant,
    and returns top matching documents with similarity scores.
    """
    query = state.get("query", "")

    if not query.strip():
        return {
            "error": "Empty query provided to Retrieval Agent.",
            "current_step": "retrieval_failed"
        }

    try:
        client = get_qdrant_client()
        query_vector = list(embedding_model.embed([query]))[0].tolist()

        # Modern Qdrant client query method (qdrant-client >= 1.10)
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=2
        )

        retrieved_docs = [
            {
                "id": point.payload.get("doc_id"),
                "content": point.payload.get("content"),
                "category": point.payload.get("category"),
                "score": round(point.score, 4)
            }
            for point in response.points
        ]

        return {
            "retrieved_docs": retrieved_docs,
            "current_step": "retrieval_completed"
        }
    except Exception as e:
        return {
            "error": f"Vector search failure: {str(e)}",
            "current_step": "retrieval_failed"
        }