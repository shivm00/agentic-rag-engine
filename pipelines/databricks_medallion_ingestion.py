import os
import uuid
from typing import List
import pandas as pd
from fastembed import TextEmbedding
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, explode, lit, pandas_udf
from pyspark.sql.types import ArrayType, StringType

# =====================================================================
# CATALOG & SCHEMA CONFIGURATION (Unity Catalog / Delta Lake)
# =====================================================================
CATALOG = "main"
SCHEMA = "enterprise_rag"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dimensional dense vectors
CHUNK_SIZE = 500  # Character window size
CHUNK_OVERLAP = 50  # Character overlap for context retention


# =====================================================================
# DISTRIBUTED PYSPARK VECTORIZED UDFs (User Defined Functions)
# =====================================================================
@pandas_udf(ArrayType(StringType()))
def chunk_text_udf(contents: pd.Series) -> pd.Series:
    """Sliding-window text chunker executed across distributed Spark workers."""

    def chunk_single_text(text: str) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunks.append(text[start:end])
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks

    return contents.apply(chunk_single_text)


@pandas_udf(ArrayType(ArrayType(StringType())))
def generate_embeddings_udf(chunks: pd.Series) -> pd.Series:
    """Generates 384-dim FastEmbed vector embeddings in vectorized Pandas batches."""
    # Instantiated inside worker node process space
    model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    def embed_batch(chunk_list: List[str]) -> List[List[str]]:
        if not chunk_list:
            return []
        embeddings = list(model.embed(chunk_list))
        # Convert numpy float arrays to string arrays for clean Delta serialization
        return [[str(val) for val in vec] for vec in embeddings]

    return chunks.apply(embed_batch)


# =====================================================================
# MEDALLION PIPELINE EXECUTION ENGINE
# =====================================================================
def run_medallion_pipeline(raw_storage_path: str):
    """Executes the Bronze -> Silver -> Gold Delta Lake Ingestion Pipeline."""
    spark = (
        SparkSession.builder.appName("Databricks-Medallion-RAG-Ingestion")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )

    print(f"Starting Databricks Medallion Ingestion from Source: {raw_storage_path}")

    # -----------------------------------------------------------------
    # 1. BRONZE LAYER: Raw Data Ingestion & Unaltered Delta Persistence
    # -----------------------------------------------------------------
    # Reads raw markdown/text files recursively from Cloud Storage / DBFS Volumes
    raw_df = (
        spark.read.format("binaryFile")
        .option("pathGlobFilter", "*.txt")
        .option("recursiveFileLookup", "true")
        .load(raw_storage_path)
        .select(
            col("path").alias("file_path"),
            col("content").cast("string").alias("raw_text"),
        )
        .withColumn("ingested_at", current_timestamp())
    )

    # Write unaltered raw payload to Bronze Delta Table
    raw_df.write.format("delta").mode("append").option(
        "mergeSchema", "true"
    ).saveAsTable(f"{CATALOG}.{SCHEMA}.bronze_raw_documents")
    print("Bronze Layer written successfully (Raw Document Storage).")

    # -----------------------------------------------------------------
    # 2. SILVER LAYER: Text Cleaning, Chunking & Structuring
    # -----------------------------------------------------------------
    # Splits raw document blocks into structured sliding-window text chunks
    silver_df = (
        raw_df.withColumn("chunks", chunk_text_udf(col("raw_text")))
        .withColumn("chunk_text", explode(col("chunks")))
        .withColumn("chunk_id", lit(str(uuid.uuid4())))
        .select("chunk_id", "file_path", "chunk_text", "ingested_at")
    )

    # Write cleaned chunks to Silver Delta Table
    silver_df.write.format("delta").mode("append").option(
        "mergeSchema", "true"
    ).saveAsTable(f"{CATALOG}.{SCHEMA}.silver_cleaned_chunks")
    print("Silver Layer written successfully (Text Chunking & Tokenization).")

    # -----------------------------------------------------------------
    # 3. GOLD LAYER: Dense Vector Generation & Search Indexing
    # -----------------------------------------------------------------
    # Computes 384-dimensional FastEmbed dense vectors across all chunks
    gold_df = silver_df.withColumn(
        "embedding_vector", generate_embeddings_udf(col("chunk_text"))
    ).select(
        "chunk_id",
        "file_path",
        "chunk_text",
        "embedding_vector",
        "ingested_at",
    )

    # Write finalized vectors to Gold Delta Table
    gold_df.write.format("delta").mode("append").option(
        "mergeSchema", "true"
    ).saveAsTable(f"{CATALOG}.{SCHEMA}.gold_vector_embeddings")
    print("Gold Layer written successfully (384-dim Vector Embeddings).")


# Main Method
if __name__ == "__main__":
    import sys

    input_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "dbfs:/Volumes/main/enterprise_rag/raw_docs"
    )
    run_medallion_pipeline(input_path)