┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 OFFLINE BATCH & DATA ENGINE                                       │
│                                                                                                   │
│  [ RAW DOCS ] ──► [ Databricks + PySpark ] ──► [ Great Expectations ] ──► [ GOLD DELTA TABLE ]    │
│  (S3 / GCS)          (Medallion ETL)            (Data Quality Gate)           & Vector Index    │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
▲
│ Read-Only (ms)
┌─────────────────────────────────────────────────────────────────────────────────────┴─────────────┐
│                                 ONLINE REAL-TIME SERVING LAYER                                    │
│                                                                                                   │
│  [ USER QUERY ] ──► [ FastAPI Server ] ──► [ LangGraph State Machine ] ──► [ Grounded Response ] │
│                         (POST /query)         (Retrieval & Analyst)                               │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
│
▼ (Async Non-Blocking Stream)
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 TELEMETRY & LLMOPS OBSERVABILITY                                  │
│                                                                                                   │
│  [ Background Worker ] ──► [ Google BigQuery ] ──► [ dbt Data Marts ] ──► [ Operational Dashboard]│
│  (Latency & Tokens)        (fct_agent_telemetry)   (fct_agent_runs)       (Cost & Performance)    │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘