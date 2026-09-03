# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi ingest
# MAGIC Loads the monthly trip export + zone lookup someone drops into the
# MAGIC landing folder. Built by a contractor for a one-off exec demo — see
# MAGIC the team channel if you need context, nobody currently on the team
# MAGIC wrote this.
# MAGIC
# MAGIC Run manually or via the "Taxi Analytics - Legacy" job — see `seed/`
# MAGIC at the repo root for how that job gets deployed.

# COMMAND ----------

landing_path = "/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/"

trips = spark.read.parquet(landing_path + "yellow_tripdata_2024-01_sample.parquet")
trips.write.mode("overwrite").saveAsTable("dev_ai_kit_demo_brownfield.taxi_legacy.bronze_trips")

zones = (
    spark.read.option("header", "true")
    .option("inferSchema", "true")
    .csv(landing_path + "taxi_zone_lookup.csv")
)
zones.write.mode("overwrite").saveAsTable("dev_ai_kit_demo_brownfield.taxi_legacy.bronze_zones")

print(f"bronze_trips: {trips.count()} rows")
print(f"bronze_zones: {zones.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC That's it — whoever set this up just re-runs this notebook (or the
# MAGIC scheduled job) whenever a new month's file shows up in the landing
# MAGIC folder. `mode("overwrite")` on the whole table, so re-running with the
# MAGIC same file is harmless, but there's no way to land two months side by
# MAGIC side without renaming the table.
