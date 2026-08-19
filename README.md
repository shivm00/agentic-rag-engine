### System Architecture

* **Layer 1: Batch Ingestion & Compute** (`pipelines/databricks_medallion_ingestion.py`)
  Handles offline, distributed text extraction, chunking, and dense vector embedding generation across Databricks PySpark worker nodes into Delta Lake tables, keeping heavy compute completely isolated from live user traffic.

* **Layer 2: Data Quality & Validation** (`pipelines/data_quality.py`)
  Functions as an automated circuit breaker within the ingestion pipeline, leveraging Great Expectations to enforce strict schema consistency, uniqueness, and vector integrity assertions before writing data to production vector indexes.

* **Layer 3: Analytics & Data Modeling** (`dbt/models/fct_agent_runs.sql`)
  Transforms raw, unformatted API execution logs in BigQuery/Snowflake into structured analytical data marts using ELT SQL models, enabling granular tracking of latency, token spend, and error rates.

* **Layer 4: Workflow Orchestration** (`dags/enterprise_rag_orchestrator.py`)
  Manages end-to-end task scheduling, retry policies, and dependency chains across the pipeline with Apache Airflow—ensuring data quality checks pass before vector index syncs and warehouse updates occur.

* **Layer 5: Real-Time Serving & Agents** (`src/main.py` & `src/workflow.py`)
  Exposes high-throughput asynchronous REST endpoints using FastAPI that orchestrate a multi-agent LangGraph state machine (Retrieval & Analyst) to perform sub-second vector lookups and synthesize grounded answers.

* **Layer 6: Operational Telemetry & Audit Logging** (`src/warehouse/telemetry_logger.py`)
  Streams real-time query performance, token usage metrics, and cost estimations to Google BigQuery using non-blocking FastAPI background workers to eliminate user-facing latency penalties.
  
