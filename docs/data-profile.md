# Source data profile

What's actually in `sample_data/raw/` — read this before you start writing
Bronze ingestion code. Profiling your source before you build is good
practice in general (see the `qubika-bronze-profiler` skill if you want the
kit's own guidance on this).

## Files

- **`yellow_tripdata_2024-01_sample.parquet`** — 150,000 NYC Yellow Taxi
  trip records, trimmed from the real public [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
  for January 2024.
- **`taxi_zone_lookup.csv`** — 265 rows mapping `LocationID` to a
  `Borough` and `Zone` name. Trip records reference locations by ID only.

## Trip file schema

| Column | Type | Notes |
|---|---|---|
| `VendorID` | int | |
| `tpep_pickup_datetime` | timestamp | |
| `tpep_dropoff_datetime` | timestamp | |
| `passenger_count` | double, nullable | |
| `trip_distance` | double | miles |
| `RatecodeID` | double, nullable | |
| `store_and_fwd_flag` | string, nullable | |
| `PULocationID` | int | pickup location, joins to `taxi_zone_lookup.LocationID` |
| `DOLocationID` | int | dropoff location, joins to `taxi_zone_lookup.LocationID` |
| `payment_type` | int | |
| `fare_amount` | double | |
| `extra` | double | |
| `mta_tax` | double | |
| `tip_amount` | double | |
| `tolls_amount` | double | |
| `improvement_surcharge` | double | |
| `total_amount` | double | |
| `congestion_surcharge` | double, nullable | |
| `Airport_fee` | double, nullable | |

There is **no natural primary key** — no single column or obvious
combination uniquely identifies a trip. Worth deciding how you want to
handle that once you get to incremental/idempotent writes in Silver.

## Zone lookup schema

`LocationID` (int), `Borough` (string), `Zone` (string), `service_zone` (string).

## Data quality — what you'll actually find in this sample

This is real data, not a clean synthetic set, so it has the kind of mess
you'd expect from any real source system. In the 150,000-row sample:

- **~1,957 rows** have a negative `fare_amount`.
- **~1,638 rows** have `passenger_count == 0`.
- **~7,114 rows** have nulls in `passenger_count`, `RatecodeID`,
  `store_and_fwd_flag`, `congestion_surcharge`, and `Airport_fee` together
  (they're null in the same rows).
- **A couple of rows** have `tpep_pickup_datetime` values from
  outside January 2024 entirely (as old as 2002) — garbage in the source
  system.
- `trip_distance == 0` with a non-zero `fare_amount` also shows up — a
  common TLC data smell (meter started, GPS never moved).

None of this is prescriptive about what to do — deciding whether something
is an error to reject, a warning to flag, or acceptable to pass through is
part of the exercise. If you want a second opinion on how bad a source
table looks before you commit to a cleaning strategy, the kit's
`qubika-bronze-profiler` skill is built for exactly that.
