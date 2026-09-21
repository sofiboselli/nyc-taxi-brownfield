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
  kit_version: 1.6.0
  mode: repo-and-workspace
  scan_scope:
    profile: nyc-taxi-brownfield-seed-dev
  scanned_at: '2026-09-21T17:15:08.964195Z'
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
    schemas: 1
    volumes: 1
  layout:
    bronze_dir: bronze
    bundles_dir: resources
    gold_dir: gold
    silver_dir: silver
  notes:
  - No `CLAUDE.md` in repo root — kit directives won't load automatically for sessions
    in this project.
  tech_stack:
    dbt: false
    frameworks:
    - databricks-asset-bundles
    languages:
    - python
workspace:
  catalogs:
    dev_ai_kit_demo_brownfield:
      owner: eugenia.millan@qubika.com
      schemas_count: 3
      schemas_sample:
      - default
      - information_schema
      - taxi_legacy
      tables:
        taxi_legacy.bronze_trips:
          column_count: 19
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
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-21T16:41:43.952000Z'
          owner: sofia.boselli@qubika.com
          schema_name: taxi_legacy
          table_type: TableType.MANAGED
        taxi_legacy.bronze_zones:
          column_count: 4
          column_names:
          - LocationID
          - Borough
          - Zone
          - service_zone
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-21T16:41:48.759000Z'
          owner: sofia.boselli@qubika.com
          schema_name: taxi_legacy
          table_type: TableType.MANAGED
        taxi_legacy.gold_kpi_by_borough_hour:
          column_count: 5
          column_names:
          - pickup_borough
          - pickup_hour
          - trip_count
          - total_revenue
          - avg_tip_pct
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-21T16:42:14.337000Z'
          owner: sofia.boselli@qubika.com
          schema_name: taxi_legacy
          table_type: TableType.MANAGED
        taxi_legacy.silver_trips:
          column_count: 12
          column_names:
          - vendor_id
          - pickup_ts
          - dropoff_ts
          - passenger_count
          - trip_distance
          - pu_location_id
          - pickup_borough
          - fare_amount
          - tip_amount
          - total_amount
          - tip_pct
          - pickup_hour
          columns_with_comment: 0
          has_comment: false
          last_altered: '2026-09-21T16:42:02.904000Z'
          owner: sofia.boselli@qubika.com
          schema_name: taxi_legacy
          table_type: TableType.MANAGED
      tables_total: 4
      tables_truncated: false
    dev_ai_kit_demo_greenfield:
      owner: eugenia.millan@qubika.com
      schemas_count: 10
      schemas_sample:
      - default
      - information_schema
      - logistics_gold
      - nyc_taxi_1_bronze
      - nyc_taxi_2_bronze
      - nyc_taxi_2_gold
      - nyc_taxi_2_silver
      - nyc_taxi_3_bronze
      - nyc_taxi_3_silver
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
  - id: 737066527829005
    name: '[dev sofia_boselli] Taxi Analytics - Legacy'
  - id: 454026672608044
    name: '[dev marcio_bittar] nyc-taxi-limo-3 - main pipeline'
    paused: false
  - id: 472167339565098
    name: '[dev marcio_bittar] nyc-taxi-limo-1 - nyc_taxi_1 pipeline'
    paused: false
  - id: 728253583888035
    name: '[dev marcio_bittar] nyc-taxi-limo-2 - nyc_taxi_2 pipeline'
    paused: false
  - id: 683340637414104
    name: '[prod] Gold checksum (fox_dev)'
  - id: 318685890051151
    name: '[prod] FOX pipeline · end-to-end (fox_dev)'
  pipelines: []
---

# nyc-taxi-brownfield — Project Profile

*Generated by `/de-audit` on 2026-09-21T17:15:08+00:00 (mode: `repo-and-workspace`).*

## Summary

- **Tech stack**: python, databricks-asset-bundles
- **DAB resources**: 1 job(s), 0 pipeline(s), 1 schema(s)
- **Connected to**: `dbc-001bbe9b-5a5e.cloud.databricks.com` (id `7474653767053494`) as `sofia.boselli@qubika.com` via profile `nyc-taxi-brownfield-seed-dev`
- **Workspace**: 3 catalog(s) visible, 6 job(s), 0 pipeline(s)

## Catalogs

| Catalog | Schemas | Owner | Deep |
|---|---|---|---|
| `dev_ai_kit_demo_brownfield` | 3 | eugenia.millan@qubika.com | 4 tables |
| `dev_ai_kit_demo_greenfield` | 10 | eugenia.millan@qubika.com | — |
| `qubika_training_general` | 2 | _workspace_admins_qubika_training_7474653767053494 | — |

## Deep scan: `dev_ai_kit_demo_brownfield`

- **Tables**: 4 (0 commented, 0%)
- **Columns**: 40 (0 commented, 0%)

| Table | Type | Columns | Owner |
|---|---|---|---|
| `taxi_legacy.bronze_trips` ⚠ | TableType.MANAGED | 19 | sofia.boselli@qubika.com |
| `taxi_legacy.bronze_zones` ⚠ | TableType.MANAGED | 4 | sofia.boselli@qubika.com |
| `taxi_legacy.gold_kpi_by_borough_hour` ⚠ | TableType.MANAGED | 5 | sofia.boselli@qubika.com |
| `taxi_legacy.silver_trips` ⚠ | TableType.MANAGED | 12 | sofia.boselli@qubika.com |

## Jobs (sample)

- `737066527829005` — [dev sofia_boselli] Taxi Analytics - Legacy
- `454026672608044` — [dev marcio_bittar] nyc-taxi-limo-3 - main pipeline
- `472167339565098` — [dev marcio_bittar] nyc-taxi-limo-1 - nyc_taxi_1 pipeline
- `728253583888035` — [dev marcio_bittar] nyc-taxi-limo-2 - nyc_taxi_2 pipeline
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
