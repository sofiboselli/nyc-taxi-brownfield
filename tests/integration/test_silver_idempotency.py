"""Integration test: the Silver MERGE (build_silver_candidate + trip_id
MERGE key) must be idempotent -- running it twice on the same Bronze data
must not duplicate rows. This directly guards against the overwrite-vs-
append cutover bug this pipeline actually hit (a table already populated
under the old write mode ended up with duplicated data after switching to
an incremental write).

Uses a local, path-based Delta table (no catalog/metastore needed) so it
runs the same way in CI as it does here. Deliberately skips the DQX
quarantine step -- DQEngine requires a WorkspaceClient, which needs real
Databricks auth this test suite shouldn't depend on. DQX's own check
behavior is covered by tests/unit/test_silver_dq_rules.py; this test is
purely about the MERGE mechanics.
"""
from datetime import datetime

import pytest
from delta.tables import DeltaTable
from pyspark.sql import functions as F

from src.transforms.silver_trips import build_silver_candidate

pytestmark = pytest.mark.integration

TRIP_COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "_source_file",
    "_ingested_at",
]
ZONE_COLUMNS = ["LocationID", "Borough"]

SILVER_SCHEMA_SQL = """
    trip_id             STRING NOT NULL,
    vendor_id           INT,
    pickup_ts           TIMESTAMP NOT NULL,
    dropoff_ts          TIMESTAMP,
    pickup_date         DATE,
    passenger_count     DOUBLE,
    trip_distance       DOUBLE,
    pu_location_id      INT,
    pickup_borough      STRING,
    fare_amount         DOUBLE,
    tip_amount          DOUBLE,
    total_amount        DOUBLE,
    tip_pct             DOUBLE,
    pickup_hour         INT,
    _updated_at         TIMESTAMP,
    _bronze_source      STRING,
    _bronze_ingested_at TIMESTAMP
"""


def _run_silver_merge(spark, silver_path, trips, zones):
    """Mirrors the MERGE step in silver/clean_trips.py against a local path table."""
    if not DeltaTable.isDeltaTable(spark, silver_path):
        spark.sql(f"CREATE TABLE delta.`{silver_path}` ({SILVER_SCHEMA_SQL}) USING DELTA")

    candidate = build_silver_candidate(trips, zones).withColumn("_updated_at", F.current_timestamp())

    (
        DeltaTable.forPath(spark, silver_path)
        .alias("target")
        .merge(candidate.alias("source"), "target.trip_id = source.trip_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def test_silver_merge_is_idempotent(spark, tmp_path):
    zones = spark.createDataFrame([(100, "Manhattan"), (200, "Brooklyn")], ZONE_COLUMNS)
    trips = spark.createDataFrame(
        [
            (
                1,
                datetime(2024, 1, 1, 8, 0),
                datetime(2024, 1, 1, 8, 20),
                1.0,
                3.0,
                100,
                200,
                10.0,
                2.0,
                12.0,
                "trip.parquet",
                datetime(2024, 2, 1),
            ),
            (
                2,
                datetime(2024, 1, 1, 9, 0),
                datetime(2024, 1, 1, 9, 15),
                2.0,
                1.5,
                200,
                100,
                8.0,
                1.0,
                9.0,
                "trip.parquet",
                datetime(2024, 2, 1),
            ),
        ],
        TRIP_COLUMNS,
    )
    silver_path = str(tmp_path / "silver_trips")

    _run_silver_merge(spark, silver_path, trips, zones)
    first_count = spark.read.format("delta").load(silver_path).count()

    _run_silver_merge(spark, silver_path, trips, zones)  # re-run with the SAME bronze data
    second_count = spark.read.format("delta").load(silver_path).count()

    assert first_count == 2
    assert second_count == first_count  # no duplicates
