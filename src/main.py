from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import QueryRequest, QueryResponse, IngestRequest, IngestResponse
from src.workflow import app_graph
from src.ingestion import ingest_documents
from src.state import AgentState

app = FastAPI(
    title="Enterprise Agentic RAG Engine",
    version="1.0.0",
    description="Production-Grade GCP Agentic RAG Engine with LangGraph and Qdrant."
)

# Enable CORS for frontend clients (Angular/React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check probe utilized by GCP Cloud Run load balancers to monitor container liveness.
    """
    return {"status": "healthy", "service": "agentic-rag-engine"}

@app.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_pipeline(request: QueryRequest):
    """
    Synchronously triggers the LangGraph state machine workflow for an incoming query.
    """
    initial_state: AgentState = {
        "query": request.query,
        "retrieved_docs": [],
        "analysis_output": None,
        "current_step": "initialized",
        "error": None
    }

    try:
        result = app_graph.invoke(initial_state)

        return QueryResponse(
            query=result["query"],
            current_step=result["current_step"],
            retrieved_docs=result.get("retrieved_docs", []),
            analysis_output=result.get("analysis_output"),
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution error: {str(e)}"
        )

@app.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_docs_endpoint(request: IngestRequest):
    """
    REST trigger to run vector embedding ingestion into Qdrant.
    """
    try:
        ingest_documents(request.documents)
        return IngestResponse(
            status="success",
            message=f"Ingested {len(request.documents)} documents into Qdrant vector store."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector ingestion failure: {str(e)}"
        )