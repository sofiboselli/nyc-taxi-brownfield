# NYC Taxi — Brownfield

An onboarding walkthrough for the Qubika AI Dev Kit: **join** an existing,
already-productive Databricks project — a working but ungoverned NYC Taxi
pipeline — and bring it up to Qubika standards one layer at a time.

## What's in this repo

- **`WALKTHROUGH.md`** — start here. The full step-by-step: deploy the
  seed bundle, let `/de-init` detect the legacy layout and audit it, then
  three iterations (Bronze → Silver → Gold) that fix what the audit and
  `/de-assist review` surface.
- **`seed/`** — a throwaway bundle that deploys the "already productive"
  starting state for real: a schema, a landing volume, and the badly
  configured "Taxi Analytics - Legacy" job. Run once, at the start.
- **`bronze/`, `silver/`, `gold/`** — the *existing* pipeline, exactly as
  it was left: three flat notebooks, no bundle, no data-quality checks,
  hardcoded catalog naming. This is what gets audited and rebuilt, not a
  reference to copy from.
- **`docs/data-profile.md`** — schema and known data-quality issues in
  `sample_data/raw/`.
- **`docs/final-checklist.md`** — the standards checklist this exercise
  ends on: `/de-audit`, then a manual pass against Qubika's conventions.
- **`sample_data/raw/`** — the data itself: a trimmed real sample of NYC
  Yellow Taxi trip records plus a zone lookup table.

## Before you start

You'll need:

- The AI Dev Kit installed (Claude Code, Cursor, or another supported
  client) — if `/de-init` isn't a recognized command, it isn't installed yet.
- A Databricks CLI profile for the `qubika-training` workspace, with
  access to the `dev_ai_kit_demo_brownfield` catalog — everyone doing this
  exercise shares it. Run `/de-databricks-setup` if you don't have a
  profile yet, or ask whoever set up this exercise for catalog access.
  That's the only prerequisite — everything else, including the "already
  broken" pipeline itself, you deploy yourself in `WALKTHROUGH.md` Step 2.

Then open `WALKTHROUGH.md` and go.
