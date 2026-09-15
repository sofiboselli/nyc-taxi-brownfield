# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi cleaning
# MAGIC Joins trips to the zone lookup and does light type casting, then
# MAGIC MERGEs incrementally into `curated.trips`. The raw NYC taxi export has
# MAGIC no trip ID, so `trip_id` is a sha2 hash of the fields that make a trip
# MAGIC unique — that's what makes the MERGE idempotent instead of duplicating
# MAGIC rows on re-run.
# MAGIC
# MAGIC Rows are validated with DQX before the MERGE: anything that fails a
# MAGIC critical rule (bad ordering, out-of-range values, missing key) is
# MAGIC quarantined to `quarantine.trips` instead of reaching Silver. Delta
# MAGIC `CHECK` constraints on the table are the backstop in case something
# MAGIC writes to it outside this notebook.

# COMMAND ----------

import sys
import os

# This notebook lives at src/silver/clean_trips.py, so two levels up is the
# repo root -- where `src` needs to sit on sys.path to import as a package.
sys.path.append(os.path.abspath("../.."))

from pyspark.sql import functions as F
from delta.tables import DeltaTable
from databricks.labs.dqx.engine import DQEngine
from databricks.sdk import WorkspaceClient

from src.transforms.silver_trips import build_silver_candidate, build_dq_rules

bronze_table = "dev_ai_kit_demo_brownfield.raw.trips"
zones_table = "dev_ai_kit_demo_brownfield.raw.zones"
silver_table = "dev_ai_kit_demo_brownfield.curated.trips"
quarantine_table = "dev_ai_kit_demo_brownfield.quarantine.trips"

spark.sql(f"""
  CREATE TABLE IF NOT EXISTS {silver_table} (
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
  )
  USING DELTA
  PARTITIONED BY (pickup_date)
  TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")

# ADD CONSTRAINT has no IF NOT EXISTS — guard so re-running this notebook
# on an already-constrained table doesn't error. These are the last-line
# hard guards; DQX below is what actually keeps bad rows out in practice.
_constraints = {
    # Delta CHECK constraints require the expression to evaluate to TRUE --
    # a NULL result (e.g. from `nullable_col >= 0` on a null value) counts
    # as a violation, not a pass, so every nullable column gets an explicit
    # `IS NULL OR ...` guard.
    "trip_distance_non_negative": "trip_distance IS NULL OR trip_distance >= 0",
    "passenger_count_non_negative": "passenger_count IS NULL OR passenger_count >= 0",
    "pickup_hour_in_range": "pickup_hour IS NULL OR pickup_hour BETWEEN 0 AND 23",
    "dropoff_not_before_pickup": "dropoff_ts IS NULL OR pickup_ts <= dropoff_ts",
}
for name, expr in _constraints.items():
    try:
        spark.sql(f"ALTER TABLE {silver_table} ADD CONSTRAINT {name} CHECK ({expr})")
    except Exception as e:
        if "already exists" not in str(e).lower():
            raise

# COMMAND ----------

trips = spark.table(bronze_table)
zones = spark.table(zones_table)

watermark = spark.sql(
    f"SELECT COALESCE(MAX(_bronze_ingested_at), TIMESTAMP '1900-01-01') AS wm FROM {silver_table}"
).first()["wm"]

candidate = build_silver_candidate(
    trips.filter(F.col("_ingested_at") > F.lit(watermark)), zones
).withColumn("_updated_at", F.current_timestamp())

# COMMAND ----------

dq_engine = DQEngine(spark=spark, workspace_client=WorkspaceClient())

valid_df, quarantine_df = dq_engine.apply_checks_and_split(df=candidate, checks=build_dq_rules())

quarantine_count = quarantine_df.count()
if quarantine_count:
    quarantine_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(
        quarantine_table
    )

# COMMAND ----------

(
    DeltaTable.forName(spark, silver_table)
    .alias("target")
    .merge(valid_df.alias("source"), "target.trip_id = source.trip_id")
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

silver_count = spark.table(silver_table).count()
print(f"curated.trips: {silver_count} rows (cumulative)")
print(f"quarantine.trips: {quarantine_count} row(s) quarantined this run")

# COMMAND ----------

# MAGIC %md
# MAGIC Only Bronze rows newer than Silver's current `_bronze_ingested_at`
# MAGIC watermark are read each run, and the `trip_id` MERGE key means
# MAGIC re-running with the same Bronze data updates matching rows instead of
# MAGIC duplicating them. Rows failing a critical DQX rule never reach the
# MAGIC MERGE — they land in `quarantine.trips` with the rule that failed.
