# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi KPIs
# MAGIC The numbers that actually went in the exec deck. Group by borough and
# MAGIC hour, sum/avg the usual suspects.
# MAGIC
# MAGIC Each run computes a fresh snapshot for today and replaces only today's
# MAGIC `snapshot_date` partition — re-running the same day is idempotent, but
# MAGIC a later run doesn't wipe out prior days' numbers the way a full
# MAGIC `CREATE OR REPLACE` would.

# COMMAND ----------

import sys
import os

# This notebook lives at src/gold/kpi_by_borough_hour.py, so two levels up
# is the repo root -- where `src` needs to sit on sys.path to import as a package.
sys.path.append(os.path.abspath("../.."))

from pyspark.sql import functions as F

from src.transforms.gold_kpi import compute_kpi

silver_table = "dev_ai_kit_demo_brownfield.curated.trips"
gold_table = "dev_ai_kit_demo_brownfield.analytics.kpi_by_borough_hour"

spark.sql(f"""
  CREATE TABLE IF NOT EXISTS {gold_table} (
    snapshot_date  DATE NOT NULL,
    pickup_borough STRING,
    pickup_hour    INT NOT NULL,
    trip_count     BIGINT,
    total_revenue  DOUBLE,
    avg_tip_pct    DOUBLE
  )
  USING DELTA
  PARTITIONED BY (snapshot_date)
""")

# ADD CONSTRAINT has no IF NOT EXISTS — guard so re-running this notebook
# on an already-constrained table doesn't error.
_constraints = {
    "trip_count_non_negative": "trip_count IS NULL OR trip_count >= 0",
    "pickup_hour_in_range": "pickup_hour BETWEEN 0 AND 23",
}
for name, expr in _constraints.items():
    try:
        spark.sql(f"ALTER TABLE {gold_table} ADD CONSTRAINT {name} CHECK ({expr})")
    except Exception as e:
        if "already exists" not in str(e).lower():
            raise

# COMMAND ----------

today = spark.sql("SELECT CURRENT_DATE() AS d").first()["d"]

kpi = compute_kpi(spark.table(silver_table)).withColumn("snapshot_date", F.lit(today))

(
    kpi.write.format("delta")
    .mode("overwrite")
    .option("replaceWhere", f"snapshot_date = DATE'{today}'")
    .saveAsTable(gold_table)
)

display(
    spark.table(gold_table).filter(F.col("snapshot_date") == F.lit(today)).orderBy(F.desc("total_revenue"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC `replaceWhere` scopes the overwrite to today's `snapshot_date`
# MAGIC partition only — prior days' snapshots stay untouched, so history is
# MAGIC actually recoverable instead of being clobbered on every run.
