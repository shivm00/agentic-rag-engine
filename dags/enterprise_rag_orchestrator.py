from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# =====================================================================
# DEFAULT DAG CONFIGURATION & RETRY POLICIES
# =====================================================================
default_args = {
    "owner": "data_platform_team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["alerts@enterprise.com"],
    "retries": 2,  # Automatically retry failed tasks up to 2 times
    "retry_delay": timedelta(minutes=5),  # Wait 5 minutes between retries
}

# =====================================================================
# DAG DEFINITION
# =====================================================================
with DAG(
        dag_id="enterprise_rag_ingestion_and_analytics",
        default_args=default_args,
        description="Orchestrates PySpark Medallion ingestion, Data Quality gates, Vector sync, and dbt analytics.",
        schedule_interval="0 0 * * *",  # Runs automatically every night at midnight (Cron)
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["genai", "pyspark", "dbt", "vector-db", "production"],
) as dag:

    # -----------------------------------------------------------------
    # TASK 1: Trigger Databricks PySpark Medallion Ingestion & DQ Suite
    # -----------------------------------------------------------------
    # Runs Step 1 (PySpark) & Step 2 (Great Expectations Quality Gates)
    run_pyspark_ingestion = BashOperator(
        task_id="run_pyspark_medallion_ingestion",
        bash_command="python /opt/airflow/pipelines/databricks_medallion_ingestion.py dbfs:/Volumes/main/enterprise_rag/raw_docs",
    )

    # -----------------------------------------------------------------
    # TASK 2: Optimize Delta Lake Tables (Compaction & Z-Ordering)
    # -----------------------------------------------------------------
    # Merges small files into optimized chunks for fast vector read queries
    def optimize_delta_tables_func():
        print("Executing Delta Lake table optimization: OPTIMIZE & Z-ORDER BY chunk_id...")
        # Simulated Databricks SQL execution context
        return "Delta tables optimized successfully."

    optimize_delta_tables = PythonOperator(
        task_id="optimize_delta_tables",
        python_callable=optimize_delta_tables_func,
    )

    # -----------------------------------------------------------------
    # TASK 3: Refresh Vector Store Search Index (Qdrant / Spanner)
    # -----------------------------------------------------------------
    # Signals the vector database to reload newly ingested Gold embeddings
    def sync_vector_index_func():
        print("Notifying Vector Engine (Qdrant/Spanner) to sync Gold Delta table vectors...")
        return "Vector index refreshed."

    sync_vector_index = PythonOperator(
        task_id="sync_vector_index",
        python_callable=sync_vector_index_func,
    )

    # -----------------------------------------------------------------
    # TASK 4: Execute dbt Transformations & Warehouse Data Quality Tests
    # -----------------------------------------------------------------
    # Runs Step 3 (dbt SQL transformations and automated data tests)
    run_dbt_transformations = BashOperator(
        task_id="run_dbt_transformations",
        bash_command="cd /opt/airflow/dbt && dbt run --profiles-dir . && dbt test --profiles-dir .",
    )

    # =====================================================================
    # TASK DEPENDENCY GRAPH (THE DEPENDENCY CHAIN)
    # =====================================================================
    # Step 1 & 2 -> Table Optimization -> Vector Sync -> Step 3 dbt Modeling
    (
            run_pyspark_ingestion
            >> optimize_delta_tables
            >> sync_vector_index
            >> run_dbt_transformations
    )