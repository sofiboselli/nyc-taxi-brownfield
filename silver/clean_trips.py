# Databricks notebook source
# MAGIC %md
# MAGIC ## Taxi cleaning
# MAGIC Joins trips to the zone lookup, casts columns, and now runs every row
# MAGIC through DQX before the MERGE. Rows that fail a hard check never reach
# MAGIC `silver_trips` — they land in `quarantine_trips` instead, tagged with
# MAGIC whichever rule(s) rejected them.

# COMMAND ----------

# MAGIC %pip install databricks-labs-dqx

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

from pyspark.sql import functions as F
from delta.tables import DeltaTable
from databricks.labs.dqx.engine import DQEngine
from databricks.labs.dqx.rule import DQRowRule, DQDatasetRule
from databricks.labs.dqx.check_funcs import is_not_null, is_not_less_than, is_unique, sql_expression
from databricks.sdk import WorkspaceClient

# Same widget pattern as bronze — no hardcoded catalog name here either.
dbutils.widgets.text("catalog", "dev_ai_kit_demo_brownfield", "Catalog")
catalog = dbutils.widgets.get("catalog")

bronze_trips_table = f"{catalog}.taxi_legacy.bronze_trips"
bronze_zones_table = f"{catalog}.taxi_legacy.bronze_zones"
silver_table = f"{catalog}.taxi_legacy.silver_trips"
quarantine_table = f"{catalog}.taxi_legacy.quarantine_trips"

# COMMAND ----------

# MAGIC %md
# MAGIC The source has no natural trip identifier, so `trip_id` is a
# MAGIC deterministic hash of the immutable trip attributes. That's what makes
# MAGIC the MERGE below idempotent — re-running on the same Bronze rows
# MAGIC produces the same keys and upserts in place instead of duplicating.

# COMMAND ----------

# Databricks' CREATE TABLE only accepts inline PRIMARY KEY / FOREIGN KEY --
# CHECK constraints have to be added afterward via ALTER TABLE. Only run
# that ALTER on first creation; re-adding the same-named CHECK on a table
# that already has it raises an error.
table_existed = spark.catalog.tableExists(silver_table)

spark.sql(f"""
  CREATE TABLE IF NOT EXISTS {silver_table} (
    trip_id           STRING NOT NULL,
    vendor_id         INT,
    pickup_ts         TIMESTAMP NOT NULL,
    dropoff_ts        TIMESTAMP NOT NULL,
    pickup_date       DATE,
    passenger_count   DOUBLE,
    trip_distance     DOUBLE,
    pu_location_id    INT,
    pickup_borough    STRING,
    fare_amount       DOUBLE,
    tip_amount        DOUBLE,
    total_amount      DOUBLE,
    tip_pct           DOUBLE,
    pickup_hour       INT,
    _updated_at        TIMESTAMP,
    _bronze_source      STRING,
    _bronze_ingested_at TIMESTAMP
  )
  USING DELTA
  PARTITIONED BY (pickup_date)
  TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")

if not table_existed:
    spark.sql(f"""
      ALTER TABLE {silver_table}
      ADD CONSTRAINT silver_trips_distance_non_negative CHECK (trip_distance >= 0)
    """)

# COMMAND ----------

# Only pull Bronze rows newer than the last MERGE — same incremental
# watermark pattern as the Bronze -> Silver skeleton, now that Bronze
# actually carries _ingested_at to watermark against.
watermark = spark.sql(
    f"SELECT COALESCE(MAX(_bronze_ingested_at), TIMESTAMP'1900-01-01') AS w FROM {silver_table}"
).first()["w"]

# Both bronze_trips and bronze_zones carry _ingested_at / _source_file now
# (see the Bronze fix), so after the join a bare F.col("_source_file") is
# ambiguous. Referencing columns off the named DataFrames disambiguates it.
trips = spark.table(bronze_trips_table).filter(F.col("_ingested_at") > watermark)
zones = spark.table(bronze_zones_table)

candidate_rows = (
    trips
    .join(zones, trips["PULocationID"] == zones["LocationID"], "left")
    .select(
        F.sha2(
            F.concat_ws(
                "||",
                trips["VendorID"].cast("string"),
                trips["tpep_pickup_datetime"].cast("string"),
                trips["tpep_dropoff_datetime"].cast("string"),
                trips["PULocationID"].cast("string"),
                trips["DOLocationID"].cast("string"),
                trips["trip_distance"].cast("string"),
            ),
            256,
        ).alias("trip_id"),
        trips["VendorID"].alias("vendor_id"),
        trips["tpep_pickup_datetime"].alias("pickup_ts"),
        trips["tpep_dropoff_datetime"].alias("dropoff_ts"),
        F.to_date(trips["tpep_pickup_datetime"]).alias("pickup_date"),
        trips["passenger_count"],
        trips["trip_distance"],
        trips["PULocationID"].alias("pu_location_id"),
        zones["Borough"].alias("pickup_borough"),
        trips["fare_amount"],
        trips["tip_amount"],
        trips["total_amount"],
        F.when(trips["fare_amount"] != 0, trips["tip_amount"] / trips["fare_amount"] * 100).alias("tip_pct"),
        F.hour(trips["tpep_pickup_datetime"]).alias("pickup_hour"),
        F.current_timestamp().alias("_updated_at"),
        trips["_source_file"].alias("_bronze_source"),
        trips["_ingested_at"].alias("_bronze_ingested_at"),
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC Rules below are calibrated against what's actually in `bronze_trips`
# MAGIC today, not guessed: ~1,957 rows carry a negative `fare_amount`
# MAGIC (refunds/adjustments, not real fares — quarantined), 1 row has
# MAGIC `dropoff_ts` before `pickup_ts` (quarantined), and ~7,114 rows are
# MAGIC missing `passenger_count` (common enough in this source that dropping
# MAGIC them would throw away otherwise-valid trips — flagged with `warn`
# MAGIC instead). Same reasoning for `pickup_borough`: a left join miss on an
# MAGIC unmapped `PULocationID` is worth flagging, not worth losing the trip
# MAGIC over.

# COMMAND ----------

rules = [
    DQRowRule(name="nn_pickup_ts", column="pickup_ts", check_func=is_not_null),
    DQRowRule(name="nn_dropoff_ts", column="dropoff_ts", check_func=is_not_null),
    DQRowRule(name="valid_fare_amount", column="fare_amount", check_func=is_not_less_than, check_func_kwargs={"limit": 0}),
    DQRowRule(name="valid_trip_distance", column="trip_distance", check_func=is_not_less_than, check_func_kwargs={"limit": 0}),
    DQRowRule(name="dropoff_after_pickup", check_func=sql_expression,
              check_func_kwargs={"expression": "dropoff_ts >= pickup_ts"}),
    DQRowRule(name="passenger_count_known", column="passenger_count", check_func=is_not_null, criticality="warn"),
    DQRowRule(name="pickup_borough_known", check_func=sql_expression,
              check_func_kwargs={"expression": "pickup_borough IS NOT NULL"}, criticality="warn"),
    DQDatasetRule(name="unique_trip_id", columns=["trip_id"], check_func=is_unique),
]

engine = DQEngine(spark=spark, workspace_client=WorkspaceClient())

# apply_checks_and_split's "bad" side is any row with an error OR a warning
# (DQEngineCore.get_invalid: `_errors IS NOT NULL OR _warnings IS NOT NULL`,
# checked against the installed dqx source) -- that would quarantine every
# missing-passenger_count / unmapped-borough row too, which is exactly what
# criticality="warn" was supposed to avoid. Splitting manually on `_errors
# IS NOT NULL` instead keeps warn-only rows in Silver, flagged but not
# dropped, and only routes real (error-criticality) violations to
# quarantine.
checked = engine.apply_checks(df=candidate_rows, checks=rules)
good_rows = engine.get_valid(checked)  # _errors IS NULL -- may still carry a warning; diagnostic columns dropped
bad_rows = checked.where(F.col("_errors").isNotNull())

# COMMAND ----------

# Quarantine's schema is owned by DQX's `_errors`/`_warnings` struct columns,
# not hand-declared like Silver's — mergeSchema lets Delta infer it instead
# of us guessing the struct shape and getting it wrong.
(
    bad_rows
    .withColumn("_quarantined_at", F.current_timestamp())
    .write.format("delta")
    .mode("append")
    .option("mergeSchema", "true")
    .saveAsTable(quarantine_table)
)

# Drop DQX's diagnostic columns before the MERGE — Silver's schema is the
# declared business schema above, not DQX's check-result columns.
merge_source = good_rows.select(*candidate_rows.columns)

(
    DeltaTable.forName(spark, silver_table)
    .alias("target")
    .merge(merge_source.alias("source"), "target.trip_id = source.trip_id")
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

# Read the physical tables back for run-scoped counts rather than
# re-touching good_rows/bad_rows (see the note above).
quarantined_this_run = spark.table(quarantine_table).filter(F.col("_bronze_ingested_at") > watermark).count()
print(f"silver_trips: {spark.table(silver_table).count()} rows")
print(f"quarantined this run: {quarantined_this_run} rows -> {quarantine_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC MERGE on `trip_id`, gated on Bronze's `_ingested_at` watermark and
# MAGIC now on DQX passing first — a re-run only reprocesses Bronze rows
# MAGIC newer than what's already in Silver, matching rows update in place
# MAGIC rather than duplicating, and rows that fail a hard check land in
# MAGIC `quarantine_trips` instead of silently corrupting `silver_trips`.
