# NYC Taxi — Brownfield

An onboarding walkthrough for the Qubika AI Dev Kit: **join** an existing,
already-productive Databricks project — a working but ungoverned NYC Taxi
pipeline — and bring it up to Qubika standards one layer at a time.

This is the paired counterpart to the Greenfield track (same dataset, same
kit, opposite starting point): Greenfield builds from an empty folder;
Brownfield starts from a project that already runs and has to be improved
without breaking it.

## What's in this repo

- **`WALKTHROUGH.md`** — start here. The full step-by-step: clone, let
  `/de-init` detect the legacy layout and audit it, then three iterations
  (Bronze → Silver → Gold) that fix what the audit surfaces.
- **`bronze/`, `silver/`, `gold/`** — the *existing* pipeline, exactly as
  it was left: three flat notebooks, no bundle, no data-quality checks,
  hardcoded catalog naming. This is what gets audited and rebuilt, not a
  reference to copy from.
- **`docs/existing-job-notes.md`** — what's deployed in the Databricks
  workspace that isn't visible in the code (the hand-built job, its
  departed owner, its cluster config).
- **`docs/data-profile.md`** — schema and known data-quality issues in
  `sample_data/raw/` (same data as Greenfield).
- **`docs/final-checklist.md`** — the standards checklist both tracks end
  on: `/de-audit`, then a manual pass against Qubika's conventions.
- **`sample_data/raw/`** — the data itself: a trimmed real sample of NYC
  Yellow Taxi trip records plus a zone lookup table.

## Before you start

You'll need:

- The AI Dev Kit installed (Claude Code, Cursor, or another supported
  client) — if `/de-init` isn't a recognized command, it isn't installed yet.
- A Databricks CLI profile for the `qubika-training` workspace, with
  access to the catalog this project's legacy pipeline already writes to.
  Run `/de-databricks-setup` if you don't have one yet, or ask whoever set
  up this exercise.
- The legacy pipeline (this repo's `bronze/`/`silver/`/`gold/` notebooks)
  already deployed and run at least once against `qubika-training`, so
  there's a real, already-running job to join. If that hasn't happened
  yet, ask whoever set up this exercise.

Then open `WALKTHROUGH.md` and go.
