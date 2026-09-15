# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi ingest
# MAGIC Loads the monthly trip export + zone lookup someone drops into the
# MAGIC landing folder. Built by a contractor for a one-off exec demo — see
# MAGIC the team channel if you need context, nobody currently on the team
# MAGIC wrote this.
# MAGIC
# MAGIC Run manually or via the "Taxi Analytics - Legacy" job — see
# MAGIC `SEED.md` at the repo root for how that job gets deployed.
# MAGIC
# MAGIC `raw.trips` uses Auto Loader (`cloudFiles`) so each month's file is
# MAGIC picked up once and appended — multiple months can land side by side
# MAGIC without clobbering each other. `raw.zones` stays a batch overwrite:
# MAGIC it's a small reference table meant to be replaced wholesale, not
# MAGIC accumulated.

# COMMAND ----------

from pyspark.sql import functions as F

landing_path = "/Volumes/dev_ai_kit_demo_brownfield/raw/landing/"
checkpoint_path = "/Volumes/dev_ai_kit_demo_brownfield/raw/checkpoints/trips/"

(
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", checkpoint_path + "_schema")
    .option("pathGlobFilter", "yellow_tripdata_*.parquet")
    .load(landing_path)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .writeStream
    .format("delta")
    .option("checkpointLocation", checkpoint_path)
    .option("mergeSchema", "true")
    .outputMode("append")
    .trigger(availableNow=True)
    .toTable("dev_ai_kit_demo_brownfield.raw.trips")
    .awaitTermination()
)

zones = (
    spark.read.option("header", "true")
    .option("inferSchema", "true")
    .csv(landing_path + "taxi_zone_lookup.csv")
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)
zones.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    "dev_ai_kit_demo_brownfield.raw.zones"
)

trips_count = spark.table("dev_ai_kit_demo_brownfield.raw.trips").count()
print(f"raw.trips: {trips_count} rows (cumulative)")
print(f"raw.zones: {zones.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC `raw.trips` is now append-only and checkpointed — re-running this
# MAGIC notebook (or the scheduled job) only picks up files Auto Loader hasn't
# MAGIC seen before, so it's safe to leave old months in the landing folder.
# MAGIC `raw.zones` is still a full overwrite every run, by design.
