"""Shared pytest fixtures for the taxi pipeline test suite.

A session-scoped local SparkSession with Delta enabled -- runs with plain
`pytest`, no Databricks cluster required. Needs a local JVM (JAVA_HOME set)
and, on first run, network access to fetch the Delta JARs via Maven
(cached by Ivy locally afterward, so later runs are fast and offline).
"""
import pytest
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip


@pytest.fixture(scope="session")
def spark():
    builder = (
        SparkSession.builder.master("local[2]")
        .appName("nyc-taxi-brownfield-tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
    )
    session = configure_spark_with_delta_pip(builder).getOrCreate()
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()
