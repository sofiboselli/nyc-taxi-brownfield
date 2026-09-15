"""Unit tests for the pure Silver -> Gold aggregation
(src/transforms/gold_kpi.py::compute_kpi).
"""
import pytest

from src.transforms.gold_kpi import compute_kpi

pytestmark = pytest.mark.unit

SILVER_COLUMNS = ["pickup_borough", "pickup_hour", "total_amount", "tip_pct"]


def test_groups_by_borough_and_hour(spark):
    rows = [
        ("Manhattan", 8, 10.0, 20.0),
        ("Manhattan", 8, 20.0, 10.0),
        ("Brooklyn", 9, 15.0, 5.0),
    ]
    silver = spark.createDataFrame(rows, SILVER_COLUMNS)
    result = {(r["pickup_borough"], r["pickup_hour"]) for r in compute_kpi(silver).collect()}
    assert result == {("Manhattan", 8), ("Brooklyn", 9)}


def test_trip_count_and_total_revenue(spark):
    rows = [
        ("Manhattan", 8, 10.0, 20.0),
        ("Manhattan", 8, 20.0, 10.0),
    ]
    silver = spark.createDataFrame(rows, SILVER_COLUMNS)
    row = compute_kpi(silver).collect()[0]

    assert row["trip_count"] == 2
    assert row["total_revenue"] == pytest.approx(30.0)


def test_avg_tip_pct_ignores_nulls(spark):
    """A zero-fare trip has tip_pct = NULL upstream (see the Silver transform
    tests) -- AVG should skip it rather than treat it as 0 and drag the mean
    down."""
    rows = [
        ("Manhattan", 8, 10.0, 20.0),
        ("Manhattan", 8, 0.0, None),  # zero-fare trip: no tip_pct, still counted
    ]
    silver = spark.createDataFrame(rows, SILVER_COLUMNS)
    row = compute_kpi(silver).collect()[0]

    assert row["trip_count"] == 2  # both trips counted
    assert row["avg_tip_pct"] == pytest.approx(20.0)  # NULL excluded from the average


def test_distinct_borough_hour_combinations_stay_separate(spark):
    rows = [
        ("Manhattan", 8, 10.0, 20.0),
        ("Manhattan", 9, 10.0, 20.0),
        ("Brooklyn", 8, 10.0, 20.0),
    ]
    silver = spark.createDataFrame(rows, SILVER_COLUMNS)
    assert compute_kpi(silver).count() == 3
