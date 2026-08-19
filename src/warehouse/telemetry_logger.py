import os
import uuid
import datetime
from typing import Dict, Any

# Set to 'true' in production environments with GCP credentials configured
ENABLE_BIGQUERY = os.getenv("ENABLE_BIGQUERY", "false").lower() == "true"
BIGQUERY_DATASET_TABLE = os.getenv("BIGQUERY_TABLE", "my_project.analytics.fct_agent_telemetry")

if ENABLE_BIGQUERY:
    try:
        from google.cloud import bigquery
        bq_client = bigquery.Client()
    except Exception as e:
        print(f"[Telemetry Logger Warning] BigQuery SDK init failed: {str(e)}")
        bq_client = None
else:
    bq_client = None


def log_telemetry(query: str, result: Dict[str, Any], execution_time_ms: float):
    """
    Asynchronous background task that formats and streams API query
    telemetry directly into Google BigQuery for LLMOps cost & latency auditing.
    """
    try:
        request_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()

        retrieved_docs = result.get("retrieved_docs", [])
        retrieved_count = len(retrieved_docs)
        has_error = result.get("error") is not None
        status_code = 500 if has_error else 200
        error_msg = str(result.get("error")) if has_error else None

        # Standard token estimation heuristic (4 chars ~ 1 token)
        prompt_tokens = len(query.split()) * 4
        completion_tokens = len(str(result.get("analysis_output", "")).split()) * 4
        total_tokens = prompt_tokens + completion_tokens

        # Blended LLM API Cost Model ($0.000005 per prompt token, $0.000015 per completion token)
        estimated_cost_usd = round(((prompt_tokens * 0.000005) + (completion_tokens * 0.000015)), 6)

        # Structured record matching BigQuery schema & dbt model inputs
        payload = {
            "request_id": request_id,
            "execution_timestamp": timestamp,
            "user_query": query,
            "execution_time_ms": execution_time_ms,
            "retrieved_docs_count": retrieved_count,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "total_cost_usd": estimated_cost_usd,
            "status_code": status_code,
            "error_message": error_msg
        }

        if bq_client:
            # Stream directly into BigQuery table asynchronously
            errors = bq_client.insert_rows_json(BIGQUERY_DATASET_TABLE, [payload])
            if errors:
                print(f"❌ [BigQuery Insert Error]: {errors}")
            else:
                print(f"✅ [BigQuery Stream Success] Logged {request_id} | Latency: {execution_time_ms}ms | Cost: ${estimated_cost_usd}")
        else:
            # Local development fallback output
            print(f"ℹ️ [Telemetry Logger Local] Request: {request_id} | Latency: {execution_time_ms}ms | Cost: ${estimated_cost_usd}")

    except Exception as e:
        # Guaranteed silent failure in background worker so user response is never disrupted
        print(f"[Telemetry Logger Exception]: {str(e)}")