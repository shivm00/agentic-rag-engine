"""
This script initializes an embedded local Qdrant database writing to ./qdrant_db, embeds document chunks using FastEmbed
(BAAI/bge-small-en-v1.5), and upserts vectors into the enterprise_docs collection.
"""


from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from typing import List, Dict, Any

COLLECTION_NAME = "enterprise_docs"
STORAGE_PATH = "./qdrant_db"

def get_qdrant_client() -> QdrantClient:
    """
    Returns a persistent, embedded Qdrant client stored on local disk.
    Analogous to an embedded H2 or SQLite database in Java development.
    """
    return QdrantClient(path=STORAGE_PATH)

def initialize_collection(client: QdrantClient, vector_size: int = 384):
    """
    Ensures the vector collection exists with Cosine similarity indexing.
    """
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

def ingest_documents(documents: List[Dict[str, Any]]):
    """
    ETL Ingestion Pipeline: Embeds text payloads and upserts vector points to Qdrant.
    """
    client = get_qdrant_client()
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    texts = [doc["content"] for doc in documents]
    embeddings = list(embedding_model.embed(texts))

    initialize_collection(client, vector_size=len(embeddings[0]))

    points = []
    for idx, (doc, embedding) in enumerate(zip(documents, embeddings)):
        points.append(
            PointStruct(
                id=idx + 1,
                vector=embedding.tolist(),
                payload={
                    "doc_id": doc.get("id", f"doc_{idx}"),
                    "content": doc["content"],
                    "category": doc.get("category", "general")
                }
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Successfully ingested {len(points)} document vectors into Qdrant collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    sample_enterprise_docs = [
        {
            "id": "policy_01",
            "category": "security",
            "content": "GCP Secret Manager keys must be rotated every 90 days using automated KMS triggers."
        },
        {
            "id": "policy_02",
            "category": "deployment",
            "content": "Cloud Run services require a minimum of 1 warm instance for low-latency enterprise SLA compliance."
        },
        {
            "id": "policy_03",
            "category": "database",
            "content": "Cloud Spanner transactions must use read-only multi-region replicas for analytics workloads."
        }
    ]
    ingest_documents(sample_enterprise_docs)