# Brownfield: Joining an Existing Project

## Overview & Scenario

**Goal:** Guide the user through an iterative, step-by-step process of
joining an *existing*, already-productive Databricks project — auditing
what's there, then bringing it up to Qubika AI Dev Kit standards one layer
at a time, via VS Code.

**Dataset:** NYC Yellow Taxi Trip Data (same as Greenfield — this repo's
`sample_data/`).

**The scenario:** Six months ago a contractor built a working Bronze →
Silver → Gold pipeline for a one-off executive demo, using flat
`bronze/` / `silver/` / `gold/` notebooks and a job clicked together by
hand in the Databricks UI. It still runs. Nobody who currently works here
wrote it, and the person who owns the job has since left the company.

**Why this repo doesn't pass Qubika standards — exactly:**

- **Naming & catalog:** everything lives in one hardcoded catalog/schema
  (`nyc_taxi_analytics.taxi`), not the `qubika_{env}_{code}` convention —
  and Bronze/Silver/Gold are distinguished only by a table-name prefix
  (`bronze_`, `silver_`, `gold_`), not separate schemas.
- **Bronze:** `bronze/ingest_trips.py` is a one-shot batch
  `spark.read.parquet()` off a hardcoded DBFS mount path
  (`/mnt/legacy-landing/taxi/`), not Auto Loader. No `_ingested_at` /
  `_source_file` metadata columns, and no way to land two months of data
  side by side without renaming the table.
- **Silver:** `silver/clean_trips.py` has zero data-quality enforcement.
  No DQX, no Delta constraints, no quarantine table. Every negative fare,
  null, and garbage timestamp already in `sample_data/` has been flowing
  straight through into Gold since day one. It's also a full `overwrite`
  every run, not an incremental `MERGE`.
- **Gold:** `gold/kpi_by_borough_hour.py` is `CREATE OR REPLACE TABLE`
  with no snapshot/partition column, so there's no history — last month's
  numbers are gone the moment this month's run finishes. No table or
  column comments either.
- **Deployment:** no `databricks.yml`, no bundle, no dev/staging/prod
  targets. The whole thing was deployed by clicking through the Databricks
  UI once and left alone (see `docs/existing-job-notes.md`).
- **Governance:** the job is owned by one person's account, not a group —
  and that person no longer works here. No tags, no failure-alert
  notifications, no autotermination on the cluster.
- **Testing:** none. Not one unit test anywhere in the repo.

The pipeline isn't *broken* — the numbers it produces are directionally
fine. Every item above maps directly to a line in `docs/final-checklist.md`;
fixing them, layer by layer, is the exercise.

**Approach:** Audit → Fix → Deploy → Validate in Databricks → Repeat.

---

## Step-by-Step Draft

### 1. Prerequisites & Overview

- 1.1 Read the "Kit Introduction" doc (quick context on what the kit is).
- 1.2 Follow the "Download & Install the Kit" guide.

[Placeholder: Add installation verification command output / screenshot]

### 2. Local Repository Setup (joining an existing project)

Unlike Greenfield, there's no `mkdir` here — the project already exists.

- 2.1 Clone the existing repo:
  ```
  git clone https://github.com/sofiboselli/nyc-taxi-brownfield.git
  cd nyc-taxi-brownfield
  ```

[Placeholder: Add terminal code block with exact commands]
[Placeholder: Add screenshot of the existing (messy, flat bronze/silver/gold) VS Code workspace]

- 2.2 Read `docs/existing-job-notes.md` — what's actually deployed in the
  workspace right now (a hand-built job, an owner who's left the company,
  a cluster with no autotermination). None of this is visible from the
  code alone.

### 3. Onboarding with Claude Code

- 3.1 Launch Claude Code in VS Code, inside the cloned repo.
- 3.2 Run `/de-init`. Because the folder already has content in flat
  `bronze/` / `silver/` / `gold/` directories — the kit's own signal for
  "this is the legacy pre-bundle layout" — detection kicks in
  automatically and `/de-init` routes to its **brownfield** branch instead
  of scaffolding a fresh project on top. It wraps `/de-audit` and writes
  `docs/project-profile.md` (full inventory) and `docs/first-steps.md`
  (a prioritized punch list).

[Placeholder: Add the detection output / AskUserQuestion confirmation shown by /de-init]
[Placeholder: Add screenshot of the generated docs/project-profile.md and docs/first-steps.md]

- 3.3 Read the top 3 priorities `/de-init` surfaces. Confirm they roughly
  match the gaps this walkthrough calls out below — if the kit's audit and
  your own read of the code disagree, that's worth a note for whoever owns
  the audit tooling.

### 4. Iteration 1: The Bronze Layer — From Notebook to Bundle (15-Minute Quick Win)

- 4.1 Ask Claude Code to turn `bronze/ingest_trips.py` into a proper
  Bronze ingestion step inside a Databricks Asset Bundle: `databricks.yml`
  + `resources/` + `src/ingest/`, Auto Loader instead of a one-shot batch
  read, `_ingested_at` / `_source_file` metadata columns added, and the
  catalog name pulled out of the hardcoded `nyc_taxi_analytics` into a
  proper `qubika_{env}_{code}` bundle variable.

[Placeholder: Add before/after diff of the Bronze code]

- 4.2 Ask Claude Code to deploy this first bundle version to the Databricks
  sandbox (Bronze only — Silver/Gold still point at the old tables for now).

[Placeholder: Add terminal output log for the deployment]

- 4.3 **Validation in Databricks:** run the job, confirm the new Bronze
  tables land correctly named in Unity Catalog, and compare row counts
  against the legacy `bronze_trips` / `bronze_zones` tables — they should
  match.

[Placeholder: Add screenshots of Databricks Catalog and job execution]

### 5. Iteration 2: The Silver Layer — Adding the Quality Gate That Was Never There

- 5.1 Now that Bronze is on the bundle, prompt Claude Code (`/de-pipeline`
  or directly) to rebuild `silver/clean_trips.py` as a proper Silver step:
  incremental `MERGE` instead of the legacy `overwrite`, and — the actual
  gap here — **DQX checks that simply never existed.** The legacy notebook
  cleans nothing; every negative fare, every null, every out-of-range
  timestamp in the source data has been flowing straight into
  `silver_trips` untouched since day one.

- 5.2 Highlight the Kit in action: Qubika guardrails/hooks asking for
  confirmation before touching anything in a prod-like catalog, naming
  convention nudges, the DQX pattern reference — this is the moment to
  show the kit steering the work, not just generating code.

[Placeholder: Add screenshot/log showing a Kit guardrail or hook triggering]

- 5.3 Deploy the update and re-run in Databricks.

[Placeholder: Add screenshot of the new Silver table, the quarantine table that now exists, and a before/after row count showing what quality actually caught]

### 6. Iteration 3: Gold Layer & Closing the Governance Gaps

- 6.1 Prompt Claude Code to rebuild `gold/kpi_by_borough_hour.py` on top
  of the new Silver table — same KPI shape, now with table/column
  comments and a snapshot-date partition so history isn't lost on every
  `CREATE OR REPLACE`.
- 6.2 Wrap the whole project properly, closing the gaps `docs/first-steps.md`
  flagged in Step 3: all three bundle targets (dev/staging/prod), compute
  tagging, the job re-owned by a **group** instead of `jsmith@qubika.com`,
  failure-alert notifications configured, autotermination set on every
  cluster.
- 6.3 Run an end-to-end test, execute the same analytical SQL queries
  against the new Gold table, and re-run `/de-audit --sync` — compare its
  recommendations list against the Step 3 snapshot to see the gap close.

[Placeholder: Add before/after /de-audit recommendation counts, final pipeline DAG screenshot, and SQL query results]

---

## Where this walkthrough hands off

Once Iteration 3 is deployed and validated, go through
`docs/final-checklist.md` — the same standards checklist Greenfield ends
on. A brownfield pass is arguably a better test of it: everything on that
list is something this project was *missing*, not something built in from
the start.
