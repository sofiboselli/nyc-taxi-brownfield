---
drift:
  stale_jobs:
  - id: 683340637414104
    name: '[prod] Gold checksum (fox_dev)'
  stale_jobs_threshold_days: 30
governance:
  catalogs_scanned:
  - dev_ai_kit_demo_brownfield
  columns_commented_pct: 0.0
  ownership_gaps: []
  pii_candidate_columns: []
  tables_commented_pct: 0.0
meta:
  kit_version: 1.4.0
  mode: repo-and-workspace
  scan_scope:
    profile: nyc-taxi-brownfield-seed-dev
  scanned_at: '2026-09-15T18:43:25.161685Z'
  scanned_by:
    email: sofiboselli@hotmail.com
    machine_id: sofia-boselli.local
  schema_version: 1
project:
  name: nyc-taxi-brownfield
recommendations:
- area: drift
  evidence: 'Jobs: `[prod] Gold checksum (fox_dev)` (id=683340637414104)'
  fix: Delete the job if it was a one-off test, or trigger a first run to confirm
    it works. Jobs with no runs are invisible to monitoring.
  issue: 1 job(s) have never run — likely orphaned test deploys or half-finished work.
  priority: HIGH
- area: governance
  evidence: 'Scanned: `dev_ai_kit_demo_brownfield`'
  fix: Add `COMMENT 'one-line purpose'` on each table. Prioritise Bronze landing tables
    (source of all downstream questions) and Gold marts (consumer-facing).
  issue: Only 0% of tables have a COMMENT — readers have to guess what each table
    is for.
  priority: HIGH
- area: governance
  fix: Add `COMMENT` per column in CREATE TABLE / ALTER TABLE ADD COLUMNS. The `qubika-unity-catalog-governance`
    skill has a copy-pasteable template.
  issue: Only 0% of columns have a COMMENT — Gold-layer consumers can't self-serve
    without asking the team.
  priority: MEDIUM
repo:
  dab_resources:
    jobs: 1
    pipelines: 0
    schemas: 4
    volumes: 2
  layout:
    bundles_dir: resources
    tests_dir: tests
  notes:
  - No `CLAUDE.md` in repo root — kit directives won't load automatically for sessions
    in this project.
  tech_stack:
    dbt: false
    frameworks:
    - databricks-asset-bundles
    languages:
    - python
    package_manager: uv-or-poetry
    test_framework: pytest
workspace:
  catalogs:
    dev_ai_kit_demo_brownfield:
      owner: eugenia.millan@qubika.com
      schemas_count: 6
      schemas_sample:
      - analytics
      - curated
      - default
      - information_schema
      - quarantine
      - raw
      tables:
        analytics.kpi_by_borough_hour:
          column_count: 6
          column_names:
          - snapshot_date
          - pickup_borough
          - pickup_hour
          - trip_count
          - total_revenue
          - avg_tip_pct
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-15T18:40:06.506000Z'
          owner: sofia.boselli@qubika.com
          schema_name: analytics
          table_type: TableType.MANAGED
        curated.trips:
          column_count: 17
          column_names:
          - trip_id
          - vendor_id
          - pickup_ts
          - dropoff_ts
          - pickup_date
          - passenger_count
          - trip_distance
          - pu_location_id
          - pickup_borough
          - fare_amount
          - tip_amount
          - total_amount
          - tip_pct
          - pickup_hour
          - _updated_at
          - _bronze_source
          - _bronze_ingested_at
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-15T18:39:47.243000Z'
          owner: sofia.boselli@qubika.com
          schema_name: curated
          table_type: TableType.MANAGED
        quarantine.trips:
          column_count: 19
          column_names:
          - trip_id
          - vendor_id
          - pickup_ts
          - dropoff_ts
          - pickup_date
          - passenger_count
          - trip_distance
          - pu_location_id
          - pickup_borough
          - fare_amount
          - tip_amount
          - total_amount
          - tip_pct
          - pickup_hour
          - _bronze_source
          - _bronze_ingested_at
          - _updated_at
          - _errors
          - _warnings
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-15T18:39:38.348000Z'
          owner: sofia.boselli@qubika.com
          schema_name: quarantine
          table_type: TableType.MANAGED
        raw.trips:
          column_count: 22
          column_names:
          - VendorID
          - tpep_pickup_datetime
          - tpep_dropoff_datetime
          - passenger_count
          - trip_distance
          - RatecodeID
          - store_and_fwd_flag
          - PULocationID
          - DOLocationID
          - payment_type
          - fare_amount
          - extra
          - mta_tax
          - tip_amount
          - tolls_amount
          - improvement_surcharge
          - total_amount
          - congestion_surcharge
          - Airport_fee
          - _rescued_data
          - _ingested_at
          - _source_file
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-15T18:38:03.880000Z'
          owner: sofia.boselli@qubika.com
          schema_name: raw
          table_type: TableType.MANAGED
        raw.zones:
          column_count: 6
          column_names:
          - LocationID
          - Borough
          - Zone
          - service_zone
          - _ingested_at
          - _source_file
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-15T18:41:06.834000Z'
          owner: sofia.boselli@qubika.com
          schema_name: raw
          table_type: TableType.MANAGED
      tables_total: 5
      tables_truncated: false
    dev_ai_kit_demo_greenfield:
      owner: eugenia.millan@qubika.com
      schemas_count: 4
      schemas_sample:
      - default
      - information_schema
      - nyc_taxi_bronze
      - raw_main
      tables: {}
      tables_truncated: false
    qubika_training_general:
      owner: _workspace_admins_qubika_training_7474653767053494
      schemas_count: 2
      schemas_sample:
      - default
      - information_schema
      tables: {}
      tables_truncated: false
  connection:
    account_id: 68ffa087-ddf8-45d4-b3dd-31ab32c6b8b0
    current_user: sofia.boselli@qubika.com
    host: dbc-001bbe9b-5a5e.cloud.databricks.com
    profile: nyc-taxi-brownfield-seed-dev
    workspace_id: 7474653767053494
  jobs:
  - id: 126485041662923
    name: '[dev marcio_bittar] nyc-taxi-limo - nyc_taxi pipeline'
    paused: false
  - id: 737024765533173
    name: '[dev sofia_boselli] Taxi Analytics - Legacy'
  - id: 683340637414104
    name: '[prod] Gold checksum (fox_dev)'
  - id: 318685890051151
    name: '[prod] FOX pipeline · end-to-end (fox_dev)'
  pipelines: []
---

# nyc-taxi-brownfield — Project Profile

*Generated by `/de-audit` on 2026-09-15T18:43:25+00:00 (mode: `repo-and-workspace`).*

## Summary

- **Tech stack**: python, databricks-asset-bundles
- **DAB resources**: 1 job(s), 0 pipeline(s), 4 schema(s)
- **Connected to**: `dbc-001bbe9b-5a5e.cloud.databricks.com` (id `7474653767053494`) as `sofia.boselli@qubika.com` via profile `nyc-taxi-brownfield-seed-dev`
- **Workspace**: 3 catalog(s) visible, 4 job(s), 0 pipeline(s)

## Catalogs

| Catalog | Schemas | Owner | Deep |
|---|---|---|---|
| `dev_ai_kit_demo_brownfield` | 6 | eugenia.millan@qubika.com | 5 tables |
| `dev_ai_kit_demo_greenfield` | 4 | eugenia.millan@qubika.com | — |
| `qubika_training_general` | 2 | _workspace_admins_qubika_training_7474653767053494 | — |

## Deep scan: `dev_ai_kit_demo_brownfield`

- **Tables**: 5 (0 commented, 0%)
- **Columns**: 70 (0 commented, 0%)

| Table | Type | Columns | Owner |
|---|---|---|---|
| `analytics.kpi_by_borough_hour` ⚠ | TableType.MANAGED | 6 | sofia.boselli@qubika.com |
| `curated.trips` ⚠ | TableType.MANAGED | 17 | sofia.boselli@qubika.com |
| `quarantine.trips` ⚠ | TableType.MANAGED | 19 | sofia.boselli@qubika.com |
| `raw.trips` ⚠ | TableType.MANAGED | 22 | sofia.boselli@qubika.com |
| `raw.zones` ⚠ | TableType.MANAGED | 6 | sofia.boselli@qubika.com |

## Jobs (sample)

- `126485041662923` — [dev marcio_bittar] nyc-taxi-limo - nyc_taxi pipeline
- `737024765533173` — [dev sofia_boselli] Taxi Analytics - Legacy
- `683340637414104` — [prod] Gold checksum (fox_dev)
- `318685890051151` — [prod] FOX pipeline · end-to-end (fox_dev)

## Governance

*Computed from `--catalogs dev_ai_kit_demo_brownfield` deep-scan data.*

- **Tables with comment**: 0.0%
- **Columns with comment**: 0.0%
- **Ownership gaps**: none
- **PII candidate columns**: none flagged by heuristics

## Drift

- **Stale jobs** (no run in ≥30 days): 1
    - `683340637414104` `[prod] Gold checksum (fox_dev)` — never run

## Recommendations

*Synthesized from governance + drift + usage signals. Frontmatter contains the full ranked list.*

### [HIGH] drift
- **Issue**: 1 job(s) have never run — likely orphaned test deploys or half-finished work. — Jobs: `[prod] Gold checksum (fox_dev)` (id=683340637414104)
- **Fix**: Delete the job if it was a one-off test, or trigger a first run to confirm it works. Jobs with no runs are invisible to monitoring.

### [HIGH] governance
- **Issue**: Only 0% of tables have a COMMENT — readers have to guess what each table is for. — Scanned: `dev_ai_kit_demo_brownfield`
- **Fix**: Add `COMMENT 'one-line purpose'` on each table. Prioritise Bronze landing tables (source of all downstream questions) and Gold marts (consumer-facing).

### [MEDIUM] governance
- **Issue**: Only 0% of columns have a COMMENT — Gold-layer consumers can't self-serve without asking the team.
- **Fix**: Add `COMMENT` per column in CREATE TABLE / ALTER TABLE ADD COLUMNS. The `qubika-unity-catalog-governance` skill has a copy-pasteable template.

## Repo notes

- No `CLAUDE.md` in repo root — kit directives won't load automatically for sessions in this project.


---
*This file is regenerated by `/de-audit`. Edits to the body below the frontmatter are not preserved.*
