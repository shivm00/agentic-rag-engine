+-----------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                      |
|                       Angular / React UI / API Clients                            |
+-----------------------------------------------------------------------------------+
|
HTTP POST /query
v
+-----------------------------------------------------------------------------------+
|                            GCP CLOUD RUN CONTAINER                                |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                     API BOUNDARY (FastAPI + Pydantic)                       |  |
|  |  - Enforces OAuth2/JWT & Pydantic Request/Response Schema Validation        |  |
|  |  - Exposes /health (Liveness Probe), /query, and /ingest Endpoints           |  |
|  +-----------------------------------------------------------------------------+  |
|                                         |                                         |
|                                   Initializes State                               |
|                                         v                                         |
|  +-----------------------------------------------------------------------------+  |
|  |                 AGENTIC STATE MACHINE ENGINE (LangGraph)                    |  |
|  |                                                                             |  |
|  |   [START]                                                                   |  |
|  |      |                                                                      |  |
|  |      v                                                                      |  |
|  |  +-------------------------+      Dense Vector Search    +-----------------+ |  |
|  |  |   Retrieval Agent Node  | --------------------------> |  Embedded DB    | |  |
|  |  |  - Embeds Query Vector  |                             |  (Qdrant)       | |  |
|  |  |  - Runs k-NN Search     | <-------------------------- |  ./qdrant_db    | |  |
|  |  +-------------------------+     Top-K Matches + Payload +-----------------+ |  |
|  |      |                                                                      |  |
|  |      | Updates AgentState["retrieved_docs"]                                 |  |
|  |      v                                                                      |  |
|  |  +-------------------------+                                                |  |
|  |  |   Analyst Agent Node    |                                                |  |
|  |  |  - Data Wrangling       |                                                |  |
|  |  |  - Insight Synthesis    |                                                |  |
|  |  +-------------------------+                                                |  |
|  |      |                                                                      |  |
|  |      v                                                                      |  |
|  |    [END] ---> Returns final state delta payload                             |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+