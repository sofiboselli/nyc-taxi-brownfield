"""Pure Silver -> Gold aggregation logic for the taxi KPI pipeline.

Kept separate from `gold/kpi_by_borough_hour.py` (the notebook task) so it
can be unit tested with a local SparkSession. `snapshot_date` is added by
the notebook (it's wall-clock time, not a function of the input data).
"""
from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


def compute_kpi(silver_trips: DataFrame) -> DataFrame:
    """Aggregate Silver trips into per-borough, per-hour KPIs.

    `AVG(tip_pct)` skips NULLs (standard SQL aggregate semantics) --
    `tip_pct` is NULL on trips with zero fare, so those trips still count
    toward `trip_count`/`total_revenue` but don't drag the average down to
    zero.
    """
    return silver_trips.groupBy("pickup_borough", "pickup_hour").agg(
        F.count(F.lit(1)).alias("trip_count"),
        F.sum("total_amount").alias("total_revenue"),
        F.avg("tip_pct").alias("avg_tip_pct"),
    )
