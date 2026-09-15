"""Pure Bronze -> Silver transformation logic for the taxi trips pipeline.

Kept separate from `silver/clean_trips.py` (the notebook task) so it can be
unit tested with a local SparkSession instead of only verified via a
Databricks job run. The notebook imports this module rather than
duplicating the logic, so what's tested is what actually runs.

Deliberately NOT included here (stays in the notebook, since it depends on
live state rather than being a pure function of its inputs):
  - the incremental watermark filter (reads the current Silver table)
  - `_updated_at` (wall-clock time)
  - the DQEngine / WorkspaceClient wiring (needs real Databricks auth)
"""
from __future__ import annotations

from pyspark.sql import DataFrame, functions as F
from databricks.labs.dqx.rule import DQRowRule, DQDatasetRule
from databricks.labs.dqx.check_funcs import (
    is_not_null,
    is_not_less_than,
    is_in_range,
    sql_expression,
    is_unique,
    is_not_in_future,
)


def build_silver_candidate(trips: DataFrame, zones: DataFrame) -> DataFrame:
    """Join Bronze trips to the zone lookup and shape the Silver row set.

    `trip_id` is a sha2 hash of the fields that identify a unique trip --
    the raw NYC taxi export has no native trip ID -- so two Bronze rows
    with identical vendor/pickup/dropoff/location/distance/fare values
    collapse to the same `trip_id` (this is intentional: it's how the
    Silver MERGE dedupes true duplicates instead of just re-inserting them).
    """
    return (
        trips.join(zones, trips.PULocationID == zones.LocationID, "left").select(
            F.sha2(
                F.concat_ws(
                    "|",
                    trips.VendorID.cast("string"),
                    trips.tpep_pickup_datetime.cast("string"),
                    trips.tpep_dropoff_datetime.cast("string"),
                    trips.PULocationID.cast("string"),
                    trips.DOLocationID.cast("string"),
                    trips.trip_distance.cast("string"),
                    trips.fare_amount.cast("string"),
                ),
                256,
            ).alias("trip_id"),
            trips.VendorID.alias("vendor_id"),
            trips.tpep_pickup_datetime.alias("pickup_ts"),
            trips.tpep_dropoff_datetime.alias("dropoff_ts"),
            F.to_date(trips.tpep_pickup_datetime).alias("pickup_date"),
            trips.passenger_count,
            trips.trip_distance,
            trips.PULocationID.alias("pu_location_id"),
            zones.Borough.alias("pickup_borough"),
            trips.fare_amount,
            trips.tip_amount,
            trips.total_amount,
            F.when(trips.fare_amount != 0, trips.tip_amount / trips.fare_amount * 100).alias("tip_pct"),
            F.hour(trips.tpep_pickup_datetime).alias("pickup_hour"),
            trips._source_file.alias("_bronze_source"),
            trips._ingested_at.alias("_bronze_ingested_at"),
        )
    )


def build_dq_rules() -> list[DQRowRule | DQDatasetRule]:
    """The DQX rule set applied to a Silver candidate before the MERGE.

    Returned as a fresh list each call (DQX rule objects aren't meant to be
    shared/mutated across runs) so the notebook and the test suite construct
    identical rules from the same single definition.
    """
    return [
        DQRowRule(name="nn_trip_id", column="trip_id", check_func=is_not_null),
        DQRowRule(name="nn_pickup_ts", column="pickup_ts", check_func=is_not_null),
        DQRowRule(
            name="valid_trip_distance",
            column="trip_distance",
            check_func=is_not_less_than,
            check_func_kwargs={"limit": 0},
        ),
        DQRowRule(
            name="valid_passenger_count",
            column="passenger_count",
            check_func=is_not_less_than,
            check_func_kwargs={"limit": 0},
        ),
        DQRowRule(
            name="valid_pickup_hour",
            column="pickup_hour",
            check_func=is_in_range,
            check_func_kwargs={"min_limit": 0, "max_limit": 23},
        ),
        DQRowRule(
            name="pickup_before_dropoff",
            check_func=sql_expression,
            check_func_kwargs={"expression": "dropoff_ts IS NULL OR pickup_ts <= dropoff_ts"},
        ),
        DQRowRule(name="pickup_not_future", column="pickup_ts", check_func=is_not_in_future),
        # Zone-lookup join miss — worth surfacing, not worth dropping the trip over.
        DQRowRule(name="pickup_borough_known", column="pickup_borough", check_func=is_not_null, criticality="warn"),
        DQDatasetRule(name="unique_trip_id", columns=["trip_id"], check_func=is_unique),
    ]
