# Seeding the brownfield starting state

`databricks.yml` + `resources/legacy_infra.yml` at the repo root deploy the
brownfield starting state for real, into the pre-provisioned
`dev_ai_kit_demo_brownfield` catalog: a `taxi_legacy` schema, a `landing`
volume, and the "Taxi Analytics - Legacy" job wired to the notebooks in
`bronze/`, `silver/`, `gold/`.

This is throwaway infrastructure-as-code, run once at the start of the
exercise. In Iteration 1 you replace it with the real project bundle —
same filename (`databricks.yml`), different job. Nothing later in the
exercise depends on `resources/legacy_infra.yml` still being there.

## Deploy it

Needs `USE CATALOG`, `CREATE SCHEMA`, and `CREATE VOLUME` on
`dev_ai_kit_demo_brownfield` — see the main `README.md` prerequisites if
this fails with a permissions error.

```bash
databricks bundle deploy -t dev
```

## Land the sample data

Deploying above creates the volume empty — no data in it yet, and the job
will fail without this step. **Required every time you deploy fresh**
(including after a `bundle destroy`), not a one-time setup thing. Copy the
sample data in:

```bash
databricks fs cp sample_data/raw/yellow_tripdata_2024-01_sample.parquet \
  dbfs:/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/yellow_tripdata_2024-01_sample.parquet
databricks fs cp sample_data/raw/taxi_zone_lookup.csv \
  dbfs:/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/taxi_zone_lookup.csv
```

## Run it once

Runs on serverless compute — no cluster-creation rights needed.

```bash
databricks bundle run legacy_taxi_job -t dev
```

That populates `taxi_legacy.bronze_trips`, `bronze_zones`, `silver_trips`,
and `gold_kpi_by_borough_hour` — a real, live, ungoverned pipeline, ready
to join.

## Why it's built the way it is

Every choice in `resources/legacy_infra.yml` is deliberate, not sloppy
YAML — the file itself stays clean (no narration explaining what's wrong
with it, on purpose), so the explanation lives here instead:

- No `tags`, no `email_notifications`, and no `schedule` block on the job
  (a real version of this would be scheduled and left running — we don't
  provision that here so a shared training workspace doesn't accumulate a
  daily job per learner).
- No `permissions:` block — whoever runs `bundle deploy` becomes the sole
  owner, which is the point: an individual, not a group.
- Compute is serverless (no `job_clusters` block) rather than a classic
  all-purpose cluster — a real version of this legacy job would more
  likely be on a shared classic cluster with no autotermination and an
  old runtime, but that requires cluster-creation rights most learners
  won't have. Serverless sidesteps that permission entirely, at the cost
  of losing the "no autotermination" anti-pattern as something you
  actually discover and fix.
