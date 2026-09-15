"""Integration test: the Gold `replaceWhere` overwrite must be idempotent
per snapshot_date -- re-running the same day must not duplicate rows in
that partition, and a different day's partition must be left untouched.
That second property is the exact thing a whole-table `CREATE OR REPLACE`
would have gotten wrong (it's what this pipeline used before the fix).

Uses a local, path-based Delta table (no catalog/metastore needed).
"""
from datetime import date

import pytest
from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

from src.transforms.gold_kpi import compute_kpi

pytestmark = pytest.mark.integration

# Explicit schema, not inferred: real Silver has pickup_hour as INT, but
# Spark infers Python ints as BIGINT by default, which then conflicts with
# Gold's `pickup_hour INT` column on write (DELTA_FAILED_TO_MERGE_FIELDS).
SILVER_SCHEMA = StructType(
    [
        StructField("pickup_borough", StringType()),
        StructField("pickup_hour", IntegerType()),
        StructField("total_amount", DoubleType()),
        StructField("tip_pct", DoubleType()),
    ]
)

GOLD_SCHEMA_SQL = """
    snapshot_date  DATE NOT NULL,
    pickup_borough STRING,
    pickup_hour    INT NOT NULL,
    trip_count     BIGINT,
    total_revenue  DOUBLE,
    avg_tip_pct    DOUBLE
"""


def _run_gold_refresh(spark, gold_path, silver_df, snapshot_date):
    """Mirrors the write step in gold/kpi_by_borough_hour.py against a local path table."""
    if not DeltaTable.isDeltaTable(spark, gold_path):
        spark.sql(f"CREATE TABLE delta.`{gold_path}` ({GOLD_SCHEMA_SQL}) USING DELTA PARTITIONED BY (snapshot_date)")

    kpi = compute_kpi(silver_df).withColumn("snapshot_date", F.lit(snapshot_date))
    (
        kpi.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"snapshot_date = DATE'{snapshot_date}'")
        .save(gold_path)
    )


def test_gold_refresh_is_idempotent_per_snapshot_date(spark, tmp_path):
    silver = spark.createDataFrame([("Manhattan", 8, 10.0, 20.0), ("Brooklyn", 9, 15.0, 5.0)], SILVER_SCHEMA)
    gold_path = str(tmp_path / "gold_kpi")

    _run_gold_refresh(spark, gold_path, silver, date(2024, 1, 1))
    first = spark.read.format("delta").load(gold_path)
    assert first.filter("snapshot_date = DATE'2024-01-01'").count() == 2

    _run_gold_refresh(spark, gold_path, silver, date(2024, 1, 1))  # re-run the same day
    second = spark.read.format("delta").load(gold_path)
    assert second.filter("snapshot_date = DATE'2024-01-01'").count() == 2  # not duplicated


def test_gold_refresh_preserves_other_snapshot_dates(spark, tmp_path):
    silver_day1 = spark.createDataFrame([("Manhattan", 8, 10.0, 20.0)], SILVER_SCHEMA)
    silver_day2 = spark.createDataFrame([("Brooklyn", 9, 15.0, 5.0)], SILVER_SCHEMA)
    gold_path = str(tmp_path / "gold_kpi_history")

    _run_gold_refresh(spark, gold_path, silver_day1, date(2024, 1, 1))
    _run_gold_refresh(spark, gold_path, silver_day2, date(2024, 1, 2))

    result = spark.read.format("delta").load(gold_path)
    assert result.filter("snapshot_date = DATE'2024-01-01'").count() == 1
    assert result.filter("snapshot_date = DATE'2024-01-02'").count() == 1
    assert result.count() == 2
