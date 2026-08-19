/*
  dbt Model: fct_agent_runs
  Description: Transforms raw LLM/Agent execution logs into daily operational metrics.
*/

WITH raw_telemetry AS (
    SELECT
        request_id,
        execution_timestamp,
        user_query,
        execution_time_ms,
        vector_similarity_score,
        prompt_tokens,
        completion_tokens,
        total_cost_usd,
        status_code
    FROM {{ source('rag_warehouse', 'fct_agent_telemetry') }}
)

SELECT
    DATE(execution_timestamp) AS run_date,
    COUNT(request_id) AS total_agent_queries,

    -- Performance Metrics
    ROUND(AVG(execution_time_ms), 2) AS avg_latency_ms,
    ROUND(MAX(execution_time_ms), 2) AS max_latency_ms,
    ROUND(AVG(vector_similarity_score), 4) AS avg_cosine_similarity,

    -- Token & Cost Tracking
    SUM(prompt_tokens) AS total_prompt_tokens,
    SUM(completion_tokens) AS total_completion_tokens,
    SUM(prompt_tokens + completion_tokens) AS grand_total_tokens,
    ROUND(SUM(total_cost_usd), 4) AS total_spend_usd,

    -- Error Rate Calculation
    COUNT(CASE WHEN status_code != 200 THEN 1 END) AS error_count,
    ROUND(
    (COUNT(CASE WHEN status_code != 200 THEN 1 END) * 100.0) / COUNT(request_id),
    2
    ) AS error_rate_percentage

FROM raw_telemetry
GROUP BY DATE(execution_timestamp)
ORDER BY run_date DESC