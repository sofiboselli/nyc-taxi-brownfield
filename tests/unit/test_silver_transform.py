"""Unit tests for the pure Bronze -> Silver transformation
(src/transforms/silver_trips.py::build_silver_candidate).

No Delta I/O here -- DataFrame in, DataFrame out -- so these run fast and
don't depend on any table state.
"""
from datetime import datetime

import pytest

from src.transforms.silver_trips import build_silver_candidate

pytestmark = pytest.mark.unit

TRIP_COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "_source_file",
    "_ingested_at",
]
ZONE_COLUMNS = ["LocationID", "Borough"]


def make_trip(
    vendor_id=1,
    pickup=datetime(2024, 1, 15, 8, 30, 0),
    dropoff=datetime(2024, 1, 15, 8, 45, 0),
    passenger_count=1.0,
    trip_distance=2.5,
    pu_location_id=100,
    do_location_id=200,
    fare_amount=10.0,
    tip_amount=2.0,
    total_amount=12.0,
    source_file="dbfs:/landing/trip.parquet",
    ingested_at=datetime(2024, 2, 1, 0, 0, 0),
):
    return (
        vendor_id,
        pickup,
        dropoff,
        passenger_count,
        trip_distance,
        pu_location_id,
        do_location_id,
        fare_amount,
        tip_amount,
        total_amount,
        source_file,
        ingested_at,
    )


@pytest.fixture
def zones(spark):
    return spark.createDataFrame([(100, "Manhattan"), (200, "Brooklyn")], ZONE_COLUMNS)


def test_join_matches_pickup_borough(spark, zones):
    trips = spark.createDataFrame([make_trip(pu_location_id=100)], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()
    assert result[0]["pickup_borough"] == "Manhattan"


def test_join_preserves_unmatched_trip_with_null_borough(spark, zones):
    """A trip whose pickup zone isn't in the lookup should still survive the
    left join (with a null borough) instead of being silently dropped."""
    trips = spark.createDataFrame([make_trip(pu_location_id=999)], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()
    assert len(result) == 1
    assert result[0]["pickup_borough"] is None


def test_trip_id_distinguishes_different_trips(spark, zones):
    trip_a = make_trip(vendor_id=1)
    trip_b = make_trip(vendor_id=2)  # differs only by vendor
    trips = spark.createDataFrame([trip_a, trip_b], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()

    ids = {row["trip_id"] for row in result}
    assert len(ids) == 2
    assert all(len(tid) == 64 for tid in ids)  # sha2-256 hex digest length


def test_identical_natural_key_produces_the_same_trip_id(spark, zones):
    """Two Bronze rows that are true duplicates (identical vendor/pickup/
    dropoff/locations/distance/fare) must collapse to the same trip_id --
    that's what lets the Silver MERGE dedupe them instead of double-counting."""
    dup = make_trip()
    trips = spark.createDataFrame([dup, dup], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()

    assert len(result) == 2
    assert len({row["trip_id"] for row in result}) == 1


def test_tip_pct_is_null_on_zero_fare(spark, zones):
    """Guards the F.when(fare_amount != 0, ...) branch -- without it this
    would be a division by zero."""
    trips = spark.createDataFrame([make_trip(fare_amount=0.0, tip_amount=0.0)], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()
    assert result[0]["tip_pct"] is None


def test_tip_pct_computed_correctly(spark, zones):
    trips = spark.createDataFrame([make_trip(fare_amount=20.0, tip_amount=5.0)], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()
    assert result[0]["tip_pct"] == pytest.approx(25.0)


def test_pickup_hour_and_date_derived_from_pickup_ts(spark, zones):
    trips = spark.createDataFrame([make_trip(pickup=datetime(2024, 3, 10, 23, 15, 0))], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones).collect()
    assert result[0]["pickup_hour"] == 23
    assert str(result[0]["pickup_date"]) == "2024-03-10"


def test_output_has_expected_columns(spark, zones):
    trips = spark.createDataFrame([make_trip()], TRIP_COLUMNS)
    result = build_silver_candidate(trips, zones)
    expected = {
        "trip_id",
        "vendor_id",
        "pickup_ts",
        "dropoff_ts",
        "pickup_date",
        "passenger_count",
        "trip_distance",
        "pu_location_id",
        "pickup_borough",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "tip_pct",
        "pickup_hour",
        "_bronze_source",
        "_bronze_ingested_at",
    }
    assert set(result.columns) == expected
