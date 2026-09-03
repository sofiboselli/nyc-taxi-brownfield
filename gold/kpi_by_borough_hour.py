# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi KPIs
# MAGIC The numbers that actually went in the exec deck. Group by borough and
# MAGIC hour, sum/avg the usual suspects.

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE nyc_taxi_analytics.taxi.gold_kpi_by_borough_hour AS
SELECT
  pickup_borough,
  pickup_hour,
  COUNT(*)                    AS trip_count,
  SUM(total_amount)           AS total_revenue,
  AVG(tip_pct)                AS avg_tip_pct
FROM nyc_taxi_analytics.taxi.silver_trips
GROUP BY pickup_borough, pickup_hour
""")

display(spark.table("nyc_taxi_analytics.taxi.gold_kpi_by_borough_hour").orderBy("total_revenue", ascending=False))

# COMMAND ----------

# MAGIC %md
# MAGIC No partitioning, no comments on the table, no snapshot date — it's a
# MAGIC `CREATE OR REPLACE` every run, so there's no history if last month's
# MAGIC numbers ever need to be pulled back up.
