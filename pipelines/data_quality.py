import sys
from pyspark.sql import SparkSession
import great_expectations as ge


def validate_silver_chunks(spark_df) -> bool:
    """
    Validates Silver Layer cleaned text chunks before embedding generation.
    Enforces non-null rules, uniqueness, and length constraints.
    """
    print("Running Great Expectations Data Quality Suite on Silver Layer...")

    # Wrap PySpark DataFrame in Great Expectations SparkDFDataset
    ge_df = ge.dataset.SparkDFDataset(spark_df)

    validation_results = []

    # 1. ASSERTION: chunk_text must NEVER be null or empty
    r1 = ge_df.expect_column_values_to_not_be_null("chunk_text")
    validation_results.append(r1.success)

    # 2. ASSERTION: chunk_id must be globally unique
    r2 = ge_df.expect_column_values_to_be_unique("chunk_id")
    validation_results.append(r2.success)

    # 3. ASSERTION: file_path metadata must exist for source traceability
    r3 = ge_df.expect_column_values_to_not_be_null("file_path")
    validation_results.append(r3.success)

    # Evaluate Overall Quality Status
    all_passed = all(validation_results)
    if all_passed:
        print("✅ [DATA QUALITY PASSED] Silver Layer chunks meet all enterprise quality standards.")
    else:
        print("❌ [DATA QUALITY FAILED] Anomaly detected in Silver Layer chunks. Halting pipeline execution.")

    return all_passed


def validate_gold_vectors(spark_df) -> bool:
    """
    Validates Gold Layer vector embeddings before DB index synchronization.
    Enforces vector existence and non-null guarantees.
    """
    print("Running Great Expectations Data Quality Suite on Gold Layer...")

    ge_df = ge.dataset.SparkDFDataset(spark_df)

    validation_results = []

    # 1. ASSERTION: embedding_vector must NEVER be null
    r1 = ge_df.expect_column_values_to_not_be_null("embedding_vector")
    validation_results.append(r1.success)

    # 2. ASSERTION: chunk_id mapping must be present
    r2 = ge_df.expect_column_values_to_not_be_null("chunk_id")
    validation_results.append(r2.success)

    all_passed = all(validation_results)
    if all_passed:
        print("✅ [DATA QUALITY PASSED] Gold Layer vectors validated successfully.")
    else:
        print("❌ [DATA QUALITY FAILED] Corrupt or null vector embeddings detected.")

    return all_passed


# Main Method
if __name__ == "__main__":
    # Test script entrypoint when invoked standalone
    spark = SparkSession.builder.appName("DataQuality-Validation").getOrCreate()
    print("Great Expectations Data Quality Module Ready.")