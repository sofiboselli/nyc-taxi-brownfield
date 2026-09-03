# Brownfield: Joining an Existing Project

## Overview & Scenario

**Goal:** Guide the user through an iterative, step-by-step process of
joining an *existing*, already-productive Databricks project — auditing
what's there, then bringing it up to Qubika AI Dev Kit standards one layer
at a time, via VS Code.

**Dataset:** NYC Yellow Taxi Trip Data

**Catalog:** `dev_ai_kit_demo_brownfield` — the one Unity Catalog catalog
provisioned for this exercise, created ahead of time by whoever set this
up (it needs elevated permissions most learners won't have). It's the
only thing that isn't self-service — everything else, you build yourself,
starting with the "already broken" state itself. Layer separation happens
through schemas within this one catalog.

**The scenario:** Six months ago a contractor built a working Bronze →
Silver → Gold pipeline for a one-off executive demo, using flat
`bronze/` / `silver/` / `gold/` notebooks and a job thrown together with
no real project bundle behind it. It still runs. Nobody who currently
works here wrote it. You'll deploy the exact same starting state yourself
in Step 2, via `seed/` — a throwaway bundle whose only job is to
materialize this mess for real, so it's something you can actually
inspect and run, not just read about.

**Why this repo doesn't pass Qubika standards — exactly:**

- **Naming & schema separation:** everything lives in one flat schema
  (`dev_ai_kit_demo_brownfield.taxi_legacy`), with Bronze/Silver/Gold
  distinguished only by a table-name prefix (`bronze_`, `silver_`,
  `gold_`), not separate schemas. The catalog itself is correct — it's the
  shared training catalog everyone in this exercise uses — the gap is
  entirely at the schema level.
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
- **Deployment:** no project bundle, no dev/staging/prod targets — just a
  job deployed once via `seed/` (see below) and left alone. `seed/` isn't
  the project bundle either; it's disposable infrastructure that exists
  only to stand this state up.
- **Governance:** the job is owned by whoever deployed it — one
  individual's account, not a group. No tags, no failure-alert
  notifications, no autotermination on the cluster.
- **Testing:** none. Not one unit test anywhere in the repo.

The pipeline isn't *broken* — the numbers it produces are directionally
fine, it just doesn't meet the standards we want to enforce at Qubika to ensure the secuirty, organization and data quality we promise to our clients. 

**Approach:** Audit → Fix → Deploy → Validate in Databricks → Repeat.

---

## Step-by-Step Draft

### 1. Prerequisites & Overview

- 1.1 Read the "Kit Introduction" doc (quick context on what the kit is).
- 1.2 Follow the "Download & Install the Kit" guide.

> Installing
> the kit is what turns Claude Code from a generic coding agent into one
> that has Qubika's 40+ skills, its `/de-*` slash commands, and its hooks
> loaded. Every time Claude
> Code starts inside a project, a `SessionStart` hook prints a banner —
> kit version, whether it can see a bundle in the current folder, the
> resolved catalog env, whether usage tracking is on. If you don't see
> that banner, the kit isn't wired up yet, and nothing else in this
> walkthrough will work as described.

### 2. Local Repository Setup — and standing up the mess you're about to join

- 2.1 Clone the repo:
  ```
  git clone https://github.com/sofiboselli/nyc-taxi-brownfield.git
  cd nyc-taxi-brownfield
  ```

- 2.2 Authenticate the Databricks CLI against `qubika-training`. From
  inside `seed/` (where `databricks.yml` lives, host already filled in),
  run `/de-databricks-setup` in Claude Code and follow the prompts — it
  writes a profile to `~/.databrickscfg` and validates it for you. If you
  already have a working profile for this workspace, skip this.

- 2.3 Deploy the seed bundle
  ```
  cd seed
  databricks bundle deploy -t dev
  ```
- 2.4 Land the sample data into the volume the seed bundle just created
  (commands in `seed/README.md`), then run the legacy job once:
  ```
  databricks bundle run legacy_taxi_job -t dev
  cd ..
  ```
  At this point `dev_ai_kit_demo_brownfield.taxi_legacy` has real tables
  in it, produced by a real (if badly configured) job — the same thing a
  brownfield engineer would find on day one, except you now know exactly
  how it was made, which `seed/README.md` documents in full.

### 3. Onboarding with Claude Code

- 3.1 Launch Claude Code in VS Code, inside the cloned repo.
- 3.2 Run `/de-init`. Because the folder already has content in flat
  `bronze/` / `silver/` / `gold/` directories — the kit's own signal for
  "this is the legacy pre-bundle layout" — detection kicks in
  automatically and `/de-init` routes to its **brownfield** branch instead
  of scaffolding a fresh project on top. It wraps `/de-audit` and writes
  `docs/project-profile.md` (full inventory) and `docs/first-steps.md`
  (a prioritized punch list).

- 3.3 Read the top priorities `/de-init` surfaces. `/de-audit`'s scope is
  governance and drift — ownership gaps, missing `databricks.yml`/`CLAUDE.md`,
  stale jobs, comment coverage — so expect it to catch the individual-owner
  problem and the missing bundle, not the Bronze/Silver/Gold code issues.
  It doesn't check data-quality posture or code-level conventions yet
  (that's documented in its own command reference, not a guess).

> `/de-init` is
> a small deterministic script (`scripts/init/detect.py`) that checks for
> five concrete signals, one of which is exactly "do `bronze/`, `silver/`,
> or `gold/` exist with content in them" — the legacy layout this repo
> was deliberately built with. That's what routes `/de-init` to its
> brownfield branch instead of scaffolding a fresh project on top of your
> existing code. From there it wraps `/de-audit`, which does something a
> person skimming the repo for ten minutes wouldn't: it inventories the
> repo *and* the live workspace, then ranks what it finds by severity
> (CRITICAL / HIGH / MEDIUM / LOW) instead of handing you an unordered
> wall of observations. That ranked list is `docs/first-steps.md`.

- 3.4 Run `/de-assist review` — a separate check, specifically for
  pipeline code compliance: full catalog paths, Silver `MERGE` vs.
  `overwrite`, Bronze `_ingested_at`/`_source_file` columns, Delta
  constraints, tests, monitoring/alerting. This is the tool that actually
  surfaces the Bronze/Silver/Gold gaps `/de-audit` doesn't check — it
  reports violations with file and line number, and offers to fix them.
  Iterations 1–3 below respond to what this turns up, not to a
  pre-decided plan.

> Worth being precise about which tool does what, since it's easy to
> assume one all-knowing "the kit" scans everything: `/de-audit` and
> `/de-assist review` check different things, and the union of the two is
> what covers the full "why this repo doesn't pass" list at the top of
> this doc. Neither one alone does.

### 4. Iteration 1: The Bronze Layer — From Notebook to Bundle

- 4.1 Take what `/de-assist review` reported for `bronze/ingest_trips.py`
  — plain batch read instead of Auto Loader, no `_ingested_at` /
  `_source_file`, catalog hardcoded — and ask Claude Code to fix it inside
  a proper Databricks Asset Bundle: `databricks.yml` + `resources/` +
  `src/ingest/`. The catalog stays `dev_ai_kit_demo_brownfield` (pulled
  into a `${var.catalog}` bundle variable instead of hardcoded), but the
  target schema becomes `raw_main` — separate from the legacy pipeline's
  `taxi_legacy` schema — so the new tables (`raw_main.yellow_trips`,
  `raw_main.taxi_zone_lookup`) land alongside the old ones without
  colliding.

- 4.2 Ask Claude Code to deploy this first bundle version to the Databricks
  sandbox (Bronze only — Silver/Gold still point at the old tables for now).

- 4.3 **Validation in Databricks:** run the job, confirm the new
  `dev_ai_kit_demo_brownfield.raw_main` tables land correctly in Unity
  Catalog, and compare row counts against the legacy
  `dev_ai_kit_demo_brownfield.taxi_legacy.bronze_trips` /
  `bronze_zones` tables — they should match.

> The Auto Loader code Claude Code writes for
> `src/ingest/main.py` isn't invented fresh — it comes from a specific,
> named pattern in `qubika-streaming-pipelines` (the `cloudFiles` format,
> `schemaLocation`, `mergeSchema=true`), and the `_ingested_at` /
> `_source_file` metadata-column convention comes from
> `qubika-medallion-architecture`. The bundle shape itself
> (`databricks.yml` + `resources/` + `src/`) comes from
> `qubika-databricks-bundles`. Concretely: without the kit, "add Bronze
> metadata columns" is a convention someone has to remember and enforce by
> hand across every project; with it, Claude pulls the same pattern every
> time because it's reading it from the same skill file. Also watch for
> this: the kit's own scaffolding refuses to silently create catalog or
> schema objects — it's supposed to ask you to confirm the exact name
> before creating anything in Unity Catalog.

### 5. Iteration 2: The Silver Layer — Adding the Quality Gate That Was Never There

- 5.1 Now that Bronze is on the bundle, re-run `/de-assist review` (or
  read what it already flagged for `silver/clean_trips.py`): `overwrite`
  instead of `MERGE`, no Delta constraints — and prompt Claude Code
  (`/de-pipeline` or directly) to rebuild it as a proper Silver step,
  writing to `dev_ai_kit_demo_brownfield.curated_main.trips`. The review
  checklist doesn't have a line item for "no DQX," but it's the same
  category of gap and the bigger one in practice: the legacy notebook
  cleans nothing. Every negative fare, every null, every out-of-range
  timestamp in the source data has been flowing straight into
  `taxi_legacy.silver_trips` untouched since day one. Rejected rows
  should land in a new `quarantine_main.trips` table, not disappear.

- 5.2 Highlight the Kit in action: Qubika guardrails/hooks asking for
  confirmation before touching anything in a prod-like catalog, naming
  convention nudges, the DQX pattern reference — this is the moment to
  show the kit steering the work, not just generating code.

- 5.3 Deploy the update and re-run in Databricks.

> The DQX rules Claude Code writes come from
> `qubika-data-quality` — `DQRowRule`/`DQDatasetRule`, `criticality`
> (`error` drops/quarantines a row, `warn` flags it without losing it),
> and the incremental `MERGE` + build-order-gate pattern comes from
> `qubika-medallion-architecture`. The kit points you at the right framework, the right
> concepts (row-level vs dataset-level checks, error vs warn), and the
> right place to look. It doesn't mean every line it generates is
> guaranteed correct without you checking it runs.

### 6. Iteration 3: Gold Layer & Closing the Governance Gaps

- 6.1 Same pattern once more: check what `/de-assist review` says about
  `gold/kpi_by_borough_hour.py`, then prompt Claude Code to rebuild it on
  top of the new Silver table, writing to
  `dev_ai_kit_demo_brownfield.analytics_main.kpi_borough_hour` — same KPI
  shape, now with table/column comments and a snapshot-date partition so
  history isn't lost on every `CREATE OR REPLACE`.
- 6.2 Wrap the whole project properly, closing the gaps `docs/first-steps.md`
  flagged in Step 3: all three bundle targets defined (dev/staging/prod —
  dev is the one that actually deploys here, since
  `dev_ai_kit_demo_brownfield` is the only catalog provisioned for this
  exercise; staging/prod stay structural placeholders), compute tagging,
  the job re-owned by a **group** instead of whoever happened to run
  `bundle deploy` in Step 2, failure-alert notifications configured,
  autotermination set on every cluster.
- 6.3 Run an end-to-end test, execute the same analytical SQL queries
  against the new Gold table, and re-run `/de-audit --sync` — compare its
  recommendations list against the Step 3 snapshot to see the gap close.

> The Gold aggregation shape (grouped
> aggregation + `snapshot_date` partition) comes from
> `qubika-medallion-architecture`'s Gold pattern. The governance cleanup
> in 6.2 draws on several skills at once, each covering one gap: compute
> tagging comes from `qubika-compute-tagging`; the "job owner must be a
> group, never an individual" rule is baked directly into the kit's own
> bundle scaffolding template (it's the default convention `/de-init`
> writes into any fresh `databricks.yml` — the fix here is applying a rule
> the kit already enforces by default on new projects); failure alerting
> comes from `qubika-monitoring-observability`. The
> closing move — `/de-audit --sync` — is the clearest "kit vs. no kit"
> comparison in the whole walkthrough: without it, "prove this got
> better" means someone's subjective read of the code; with it, you have
> the same tool, run twice, producing a ranked list that's measurably
> shorter.

---

## Where this walkthrough hands off

Once Iteration 3 is deployed and validated, go through
`docs/final-checklist.md` — the standards checklist for this exercise.
Every item on it maps back to something this project was *missing*, so
it's a fair final test of whether the gaps actually closed.
