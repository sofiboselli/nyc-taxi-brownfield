# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi ingest
# MAGIC Auto Loader ingestion of the monthly trip export + zone lookup dropped
# MAGIC into the landing volume. Built by a contractor for a one-off exec demo
# MAGIC — see the team channel if you need context, nobody currently on the
# MAGIC team wrote the original version of this.
# MAGIC
# MAGIC Run manually or via the "Taxi Analytics - Legacy" job — see
# MAGIC `SEED.md` at the repo root for how that job gets deployed.

# COMMAND ----------

from pyspark.sql import functions as F

# `catalog` is passed in as a job base_parameter (see resources/legacy_infra.yml)
# so this notebook never hardcodes an environment's catalog name. The default
# below only kicks in for an ad-hoc manual run with no widget value set.
dbutils.widgets.text("catalog", "dev_ai_kit_demo_brownfield", "Catalog")
catalog = dbutils.widgets.get("catalog")

landing_path = f"/Volumes/{catalog}/taxi_legacy/landing/"
bronze_trips_table = f"{catalog}.taxi_legacy.bronze_trips"
bronze_zones_table = f"{catalog}.taxi_legacy.bronze_zones"

# COMMAND ----------

# MAGIC %md
# MAGIC Auto Loader (`cloudFiles`) instead of a one-shot batch `spark.read` +
# MAGIC `overwrite`. `availableNow=True` processes whatever's new in the landing
# MAGIC volume and then stops — same "run it and it finishes" feel as the old
# MAGIC notebook, but the checkpoint means only *new* files get picked up on
# MAGIC the next run, and `append` means a second month's file lands alongside
# MAGIC the first instead of replacing it.
# MAGIC
# MAGIC Checkpoints live under the landing volume itself (`_checkpoints/...`) —
# MAGIC it's the only volume this project provisions today. `pathGlobFilter`
# MAGIC keeps each stream scoped to its own file extension so the checkpoint
# MAGIC directories are never mistaken for source data.

# COMMAND ----------

(
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", landing_path + "_checkpoints/bronze_trips/_schema")
    .option("pathGlobFilter", "*.parquet")
    .load(landing_path)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .writeStream
    .format("delta")
    .option("checkpointLocation", landing_path + "_checkpoints/bronze_trips")
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(bronze_trips_table)
    .awaitTermination()
)

# COMMAND ----------

(
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("header", "true")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaLocation", landing_path + "_checkpoints/bronze_zones/_schema")
    .option("pathGlobFilter", "*.csv")
    .load(landing_path)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .writeStream
    .format("delta")
    .option("checkpointLocation", landing_path + "_checkpoints/bronze_zones")
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(bronze_zones_table)
    .awaitTermination()
)

# COMMAND ----------

print(f"bronze_trips: {spark.table(bronze_trips_table).count()} rows")
print(f"bronze_zones: {spark.table(bronze_zones_table).count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC Both tables now carry `_ingested_at` / `_source_file` on every row, and
# MAGIC re-running with the same file is still harmless — Auto Loader's
# MAGIC checkpoint skips files it's already processed rather than relying on a
# MAGIC full-table overwrite to make re-runs idempotent.
