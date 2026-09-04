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
in Step 2, via the seed bundle (`databricks.yml` + `resources/legacy_infra.yml`
at the repo root, see `SEED.md`) — a throwaway deploy whose only job is to
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
- **Deployment:** no real project bundle, no dev/staging/prod targets —
  just a job deployed once via the throwaway seed bundle (see below) and
  left alone. That seed bundle isn't the project bundle either; it's
  disposable infrastructure that exists only to stand this state up, and
  gets replaced wholesale once, in Iteration 3, after Bronze/Silver/Gold
  are all fixed and there's a stable end state to formalize.
- **Governance:** the job is owned by whoever deployed it — one
  individual's account, not a group. No tags, no failure-alert
  notifications, no schedule.
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

- 2.1 Clone the repo and launch Claude Code from the root:
  ```
  git clone https://github.com/sofiboselli/nyc-taxi-brownfield.git
  cd nyc-taxi-brownfield
  claude
  ```

- 2.2 Authenticate the Databricks CLI against `qubika-training` — run
  `/de-databricks-setup`, the kit's own setup command, and follow the
  prompts. It writes a profile to `~/.databrickscfg` and validates it for
  you. If you already have a working profile for this workspace, skip
  this.

- 2.3 Deploy the seed bundle — `databricks.yml` + `resources/legacy_infra.yml`
  at the repo root (see `SEED.md`). Ask Claude Code to run it, or use a
  terminal directly:
  ```
  databricks bundle deploy -t dev
  ```
  This creates the `taxi_legacy` schema, an empty `landing` volume inside
  it, and the "Taxi Analytics - Legacy" job — but no data yet. The job
  will fail if you try to run it now; it has nothing to read.

- 2.4 Copy the sample data into the volume you just created.
  ```
  databricks fs cp sample_data/raw/yellow_tripdata_2024-01_sample.parquet \
    dbfs:/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/yellow_tripdata_2024-01_sample.parquet
  databricks fs cp sample_data/raw/taxi_zone_lookup.csv \
    dbfs:/Volumes/dev_ai_kit_demo_brownfield/taxi_legacy/landing/taxi_zone_lookup.csv
  ```

- 2.5 Now run the legacy job:
  ```
  databricks bundle run legacy_taxi_job -t dev
  ```
  At this point `dev_ai_kit_demo_brownfield.taxi_legacy` has real tables
  in it, produced by a real (if badly configured) job — the same thing a
  brownfield engineer would find on day one.

### 3. Onboarding with Claude Code

- 3.1 Run `/de-init`. Because the folder already has content in flat
  `bronze/` / `silver/` / `gold/` directories — the kit's own signal for
  "this is the legacy pre-bundle layout" — detection kicks in
  automatically and `/de-init` routes to its **brownfield** branch instead
  of scaffolding a fresh project on top. It wraps `/de-audit` and writes
  `docs/project-profile.md` (full inventory) and `docs/first-steps.md`
  (a prioritized punch list). Two prompts along the way:
  - **"Which catalogs should I scan?"** — answer just
    `dev_ai_kit_demo_brownfield`, not all visible `qubika_*` catalogs.
  - **"Include `--deep` cost analysis?"** — decline. Cost/usage isn't
    part of what this exercise tests.

- 3.2 Read the top priorities `/de-init` surfaces. `/de-audit`'s scope is
  governance and drift — ownership gaps, missing `CLAUDE.md`, stale jobs,
  comment coverage — so expect it to catch the individual-owner problem
  and note there's no `CLAUDE.md`. It'll see the seed bundle's
  `databricks.yml` and count its resources, but it doesn't read whether a
  bundle is *structured* well (no `src/`, no real targets, no
  `resources/` beyond the one throwaway file) or check the
  Bronze/Silver/Gold code issues — that's `/de-assist review`, next.

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

- 3.3 Run `/de-assist review` — a separate check, specifically for
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

- 3.4 It may end by asking whether to leave the violations as-is or fix
  them now. **Decline.** Iterations 1–3 below fix things deliberately,
  one layer at a time, deployed and validated separately — not all at
  once from this one prompt.

### 4. Iteration 1: The Bronze Layer

- 4.1 Ask Claude Code, in your own words, to fix what `/de-assist review`
  found for `bronze/ingest_trips.py`:
  > "Fix the Bronze violations you just found."

  This fixes exactly what the review flagged — catalog paths, metadata
  columns, incremental read — and, on its own, nothing more.

- 4.2 Redeploy through the same seed bundle from Step 2 — nothing new to
  set up. `resources/legacy_infra.yml`'s job already points at this
  notebook, so redeploying just picks up the fix:
  ```
  databricks bundle deploy -t dev
  databricks bundle run legacy_taxi_job -t dev
  ```
  Claude Code isn't perfect, the job may fail because of errors it commits. This is just normal when developing with AI, if it fails just tell claude about it and it will fix it. Keep in mind that some fixes may be longer than others, depends on what claude decides to do. 

- 4.3 **Validation in Databricks:** confirm the job ran clean, and that
  `bronze_trips` / `bronze_zones` now carry `_ingested_at` /
  `_source_file` — same tables as before, fixed in place.

> The Bronze "checkpoint/incremental pattern" check in `/de-assist review`
> draws on `qubika-streaming-pipelines`'s Auto Loader convention (the
> `cloudFiles` format, `schemaLocation`), and the `_ingested_at` /
> `_source_file` metadata-column convention comes from
> `qubika-medallion-architecture`. Whether Claude Code actually switches
> the read over to Auto Loader, versus just adding the metadata columns
> to the existing batch read, varies by run — worth checking what you
> actually got against the skill file rather than assuming it's Auto
> Loader just because the review passed.

### 5. Iteration 2: The Silver Layer — Adding the Quality Gate That Was Never There

- 5.1 Now that Bronze is fixed, re-run `/de-assist review` and ask
  Claude Code to fix what it finds for `silver/clean_trips.py`:
  > "Fix the Silver violations you just found."

  This gets you `MERGE` instead of `overwrite` and Delta constraints — the
  two things the review actually checks for Silver. It won't add data
  quality enforcement on its own; "no DQX" isn't a line item in the
  review's checklist, same as project structure wasn't in Iteration 1 —
  the review only ever fixes exactly what it checks for.

- 5.2 Ask for that explicitly:
  > "There's no data quality enforcement here at all. Add real checks."

  Let Claude propose the specifics (which DQX rules, what's `error` vs.
  `warn`, where rejected rows land) rather than naming a quarantine table
  up front — that's the kit's conventions doing the work, not you
  supplying the answer.

- 5.3 If claude hasnt already done so, redeploy through the same seed bundle again and re-run:
  ```
  databricks bundle deploy -t dev
  databricks bundle run legacy_taxi_job -t dev
  ```

> The DQX rules Claude Code writes come from
> `qubika-data-quality` — `DQRowRule`/`DQDatasetRule`, `criticality`
> (`error` drops/quarantines a row, `warn` flags it without losing it),
> and the incremental `MERGE` + build-order-gate pattern comes from
> `qubika-medallion-architecture`. The kit points you at the right framework, the right
> concepts (row-level vs dataset-level checks, error vs warn), and the
> right place to look. It doesn't mean every line it generates is
> guaranteed correct without you checking it runs.

### 6. Iteration 3: Gold Layer & Closing the Governance Gaps

- 6.1 Same pattern once more — re-run `/de-assist review`, then ask Claude
  Code to fix what it finds for `gold/kpi_by_borough_hour.py`:
  > "Fix the Gold violations you just found."

- 6.2 Bronze/Silver/Gold code is fixed now — but ask Claude Code to check
  the deployment itself against Qubika's standards, not just the pipeline
  code:
  > "Does this project's deployment actually meet Qubika's standards —
  > bundle structure, ownership, tagging, alerting, schema separation?
  > Check and fix whatever's missing."

> Unlike every other ask in this walkthrough, this one doesn't point at a
> review tool's output — there's no `/de-assist review` equivalent for
> deployment shape. It works through skill matching alone: naming "bundle
> structure," "ownership," "tagging," "alerting," and "schema separation"
> is enough for Claude Code to pull in `qubika-databricks-bundles` (the
> bundle shape — `databricks.yml` + `resources/` + `src/` — and
> dev/staging/prod targets), `qubika-compute-tagging` (the tag keys),
> `qubika-monitoring-observability` (the alerting pattern),
> `qubika-unity-catalog-governance` (the "group, not individual" ownership
> rule — also just the default `/de-init` writes into any fresh
> `databricks.yml`, so this is applying a convention the kit already
> enforces on new projects), and `qubika-medallion-architecture` (the
> `raw_main`/`curated_main`/`analytics_main` schema-naming convention) —
> on its own, without any of those being named in the prompt above. Which
> skills actually fire depends on how the prompt lands and what Claude
> judges relevant, so it's worth checking what it says it drew on against
> what you'd expect — and the kit's scaffolding is supposed to confirm
> exact schema names with you before creating anything in Unity Catalog,
> not just pick them silently.

- 6.3 Run an end-to-end test, execute the same analytical SQL queries
  against the new Gold table, and re-run `/de-audit --sync` — compare its
  recommendations list against the Step 3 snapshot to see the gap close.

> The Gold aggregation shape (grouped
> aggregation + `snapshot_date` partition) comes from
> `qubika-medallion-architecture`'s Gold pattern. The
> closing move — `/de-audit --sync` — is the clearest "kit vs. no kit"
> comparison in the whole walkthrough: without it, "prove this got
> better" means someone's subjective read of the code; with it, you have
> the same tool, run twice, producing a ranked list that's measurably
> shorter.

- 6.4 Claude Code is not perfect — it will miss things from time to time,
  which is why this iteration process never really ends. If you notice
  something missing, or something on the final checklist that wasn't
  actually fixed, ask Claude Code to look at it specifically. Having the
  kit installed means it knows what and how things should change — a
  generic "fix everything that's wrong" won't get you there, but naming
  the specific gap gets you much further. Even then, verify rather than
  assume it worked: asking specifically doesn't guarantee it fully
  lands, as `6.2`'s ownership fix in this very walkthrough showed.

---

## Where this walkthrough hands off

Once Iteration 3 is deployed and validated, go through
`docs/final-checklist.md` — the standards checklist for this exercise.
Every item on it maps back to something this project was *missing*, so
it's a fair final test of whether the gaps actually closed.
