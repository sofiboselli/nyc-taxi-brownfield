# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi cleaning
# MAGIC Joins trips to the zone lookup and does some light type casting.
# MAGIC "Cleaning" is a bit generous — nothing here actually rejects or flags
# MAGIC bad rows, it just reshapes columns.

# COMMAND ----------

from pyspark.sql import functions as F

trips = spark.table("dev_ai_kit_demo_brownfield.taxi_legacy.bronze_trips")
zones = spark.table("dev_ai_kit_demo_brownfield.taxi_legacy.bronze_zones")

silver = (
    trips
    .join(zones, trips.PULocationID == zones.LocationID, "left")
    .select(
        trips.VendorID.alias("vendor_id"),
        trips.tpep_pickup_datetime.alias("pickup_ts"),
        trips.tpep_dropoff_datetime.alias("dropoff_ts"),
        trips.passenger_count,
        trips.trip_distance,
        trips.PULocationID.alias("pu_location_id"),
        zones.Borough.alias("pickup_borough"),
        trips.fare_amount,
        trips.tip_amount,
        trips.total_amount,
    )
    .withColumn("tip_pct", F.when(trips.fare_amount != 0, trips.tip_amount / trips.fare_amount * 100))
    .withColumn("pickup_hour", F.hour(trips.tpep_pickup_datetime))
)

silver.write.mode("overwrite").saveAsTable("dev_ai_kit_demo_brownfield.taxi_legacy.silver_trips")
print(f"silver_trips: {silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC Full `overwrite` every run — whatever was in `bronze_trips` at the time
# MAGIC becomes the entirety of `silver_trips`. No dedup logic needed today
# MAGIC because Bronze only ever holds one month at a time (see the ingest
# MAGIC notebook), but that's an assumption baked in, not something enforced
# MAGIC anywhere.
