from fastapi.testclient import TestClient
from src.main import app

# Initialize FastAPI TestClient (utilizes httpx underneath)
client = TestClient(app)

def test_health_check():
    """
    Validates container liveness probe contract for GCP Cloud Run load balancers.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "agentic-rag-engine"}

def test_query_endpoint_contract():
    """
    Validates end-to-end multi-agent execution and Pydantic response schema.
    """
    payload = {"query": "How do we handle GCP secret rotation?"}
    response = client.post("/query", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Contract Schema Assertions
    assert "query" in data
    assert data["query"] == payload["query"]
    assert data["current_step"] == "analyst_completed"
    assert isinstance(data["retrieved_docs"], list)
    assert len(data["retrieved_docs"]) > 0
    assert data["error"] is None

def test_empty_query_validation():
    """
    Validates that empty string payloads are rejected at the API schema layer.
    """
    payload = {"query": ""}
    response = client.post("/query", json=payload)

    assert response.status_code == 422  # HTTP 422 Unprocessable Entity