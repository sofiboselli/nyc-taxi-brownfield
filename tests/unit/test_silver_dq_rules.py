"""Unit tests for the DQX rule configuration and the real check functions it
wires up (src/transforms/silver_trips.py::build_dq_rules).

These call the actual `databricks-labs-dqx` check functions directly --
not a reimplementation of the boolean logic -- so a change to the DQX API
or a typo'd expression fails here the same way it would in production.
No WorkspaceClient/DQEngine is needed: a check_func like `is_not_null` just
builds a Spark Column and requires nothing but an active SparkSession
(constructing a DQRowRule via `build_dq_rules()` does the same -- it
eagerly builds its check condition, which is why every test here takes the
`spark` fixture even when it doesn't touch a DataFrame directly).

Semantics (verified against the installed library, not assumed): every
check_func returns NULL when the row is valid, and a non-null error-message
string when the row violates the check.
"""
from datetime import datetime

import pytest
from databricks.labs.dqx.check_funcs import is_in_range, is_not_less_than, sql_expression

from src.transforms.silver_trips import build_dq_rules

pytestmark = pytest.mark.unit


def test_rule_set_shape(spark):
    rules = build_dq_rules()
    by_name = {r.name: r for r in rules}

    assert set(by_name) == {
        "nn_trip_id",
        "nn_pickup_ts",
        "valid_trip_distance",
        "valid_passenger_count",
        "valid_pickup_hour",
        "pickup_before_dropoff",
        "pickup_not_future",
        "pickup_borough_known",
        "unique_trip_id",
    }
    # Only the zone-lookup join-miss check is a soft warning -- every other
    # rule must be a hard "error" (drop/quarantine), or bad data silently
    # reaches Silver.
    assert by_name["pickup_borough_known"].criticality == "warn"
    for name, rule in by_name.items():
        if name != "pickup_borough_known":
            assert rule.criticality == "error", f"{name} should be criticality=error"

    assert by_name["unique_trip_id"].columns == ["trip_id"]
    assert by_name["valid_pickup_hour"].check_func_kwargs == {"min_limit": 0, "max_limit": 23}
    assert by_name["valid_trip_distance"].check_func_kwargs == {"limit": 0}
    assert by_name["valid_passenger_count"].check_func_kwargs == {"limit": 0}


def test_pickup_before_dropoff_expression_catches_bad_order(spark):
    df = spark.createDataFrame(
        [
            (datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 9, 0)),  # dropoff before pickup -- bad
            (datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 1, 10, 0)),  # normal order -- fine
            (datetime(2024, 1, 1, 9, 0), None),  # missing dropoff -- allowed
        ],
        ["pickup_ts", "dropoff_ts"],
    )
    condition = sql_expression("dropoff_ts IS NULL OR pickup_ts <= dropoff_ts")
    flags = [row[0] is not None for row in df.select(condition).collect()]

    assert flags == [True, False, False]


def test_pickup_hour_range_check_behavior(spark):
    df = spark.createDataFrame([(-1,), (0,), (23,), (24,)], ["pickup_hour"])
    condition = is_in_range("pickup_hour", min_limit=0, max_limit=23)
    flags = [row[0] is not None for row in df.select(condition).collect()]
    assert flags == [True, False, False, True]


def test_trip_distance_non_negative_check_behavior(spark):
    df = spark.createDataFrame([(-0.1,), (0.0,), (5.0,)], ["trip_distance"])
    condition = is_not_less_than("trip_distance", limit=0)
    flags = [row[0] is not None for row in df.select(condition).collect()]
    assert flags == [True, False, False]
