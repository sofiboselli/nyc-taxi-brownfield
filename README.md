# NYC Taxi — Greenfield exercise

A hands-on exercise for learning the Qubika DE AI Dev Kit: build a small
Bronze → Silver → Gold Databricks pipeline from an empty folder, using the
kit's setup wizard and skills instead of hand-rolling everything.

## What's in this folder

- **`EXERCISE.md`** — start here. The task, the suggested workflow, and
  what "done" looks like.
- **`docs/data-profile.md`** — what's actually in the sample data (schema,
  known data-quality issues). Read this before you start building.
- **`docs/final-checklist.md`** — once you've got something working, use
  this to check it against the conventions a Qubika pipeline is expected to
  follow. Starts with `/de-audit`, the kit's own automated check.
- **`sample_data/raw/`** — the data itself: a trimmed real sample of NYC
  Yellow Taxi trip records plus a zone lookup table.

There's no pipeline code in this repo — that's the point. You build it,
in your own separate project folder, guided by `EXERCISE.md`.

## Before you start

You'll need:

- The AI Dev Kit installed (Claude Code, Cursor, or another supported
  client) — if `/de-init` isn't a recognized command, it isn't installed yet.
- A Databricks CLI profile for the `qubika-training` workspace, with
  permission to create your own catalog. Run `/de-databricks-setup` if you
  don't have one yet, or ask whoever gave you this exercise.

Then open `EXERCISE.md` and go.
