# Seed bundle

Deploys the brownfield starting state for real, into the pre-provisioned
`dev_ai_kit_demo_brownfield` catalog: a `taxi_legacy` schema, a `landing`
volume, and the "Taxi Analytics - Legacy" job wired to the three notebooks
at the repo root (`bronze/`, `silver/`, `gold/`).

This is throwaway infrastructure-as-code — it exists so the messy starting
point is real and reproducible instead of something someone had to
manually click together in the UI ahead of time. It's not the project
bundle, and nothing in the rest of the exercise builds on it. Once it's
deployed and run once, leave it alone.

## Deploy it

```bash
cd seed
databricks bundle deploy -t dev
```

## Land the sample data

The job reads from the volume this just created. Copy the sample data in:

```bash
databricks fs cp ../sample_data/raw/yellow_tripdata_2024-01_sample.parquet \
  dbfs:/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/yellow_tripdata_2024-01_sample.parquet
databricks fs cp ../sample_data/raw/taxi_zone_lookup.csv \
  dbfs:/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/taxi_zone_lookup.csv
```

## Run it once

```bash
databricks bundle run legacy_taxi_job -t dev
```

That populates `taxi_legacy.bronze_trips`, `bronze_zones`, `silver_trips`,
and `gold_kpi_by_borough_hour` — a real, live, ungoverned pipeline, ready
to join.

## Why it's built the way it is

Every choice in `resources/legacy_infra.yml` is deliberate, not sloppy
YAML — see the comment at the top of that file for exactly which
anti-pattern each piece represents (shared cluster with no
autotermination, no tags, no schedule, no explicit ownership). It's
documented there rather than here so the "why" sits next to the code it
explains.
