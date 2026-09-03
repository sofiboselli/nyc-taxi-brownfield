# Final checklist: does this match Qubika's AI Dev Kit standards?

For you, the person doing this exercise, to run through once you've got
something working — not a grade, no passing score, nobody's reviewing this
against you. It's here so you have something concrete to compare your own
work against. If something's unchecked, that's a fine place to stop and
ask Claude "how should I fix this?" rather than something to feel bad about.

## Step 1 — run the kit's own audit

```
/de-audit --catalogs dev_ai_kit_demo_brownfield
```

This is the kit's real, automated check — it scans your repo *and* your
live workspace and writes `docs/project-profile.md` with a ranked
`recommendations:` list (governance gaps, ownership, stale jobs, missing
`databricks.yml`/`CLAUDE.md`, etc). Read the top few recommendations before
moving on to the manual list below — it doesn't check data-quality posture
or code-level conventions yet, which is what the rest of this checklist is
for.

## Step 2 — manual checklist

### Naming & catalog conventions
*(`qubika-unity-catalog-governance`, `qubika-medallion-architecture`)*

- [ ] Catalog follows the `qubika_{env}_{code}` convention (this exercise
      is the documented exception — everyone shares
      `dev_ai_kit_demo_brownfield` as the training catalog, so the thing
      to actually check here is schema separation, next item)
- [ ] Bronze / Silver / Gold live in clearly separate schemas (not all
      tables dumped into one schema)
- [ ] Table and column names are snake_case and descriptive
- [ ] Every query is catalog-qualified (`catalog.schema.table`) — no bare
      table names that only work because of a default context

### Bronze layer

- [ ] Used the managed ingestion path for the source type (Auto Loader for
      files, Lakeflow Connect for supported SaaS, federated ingestion for
      databases) rather than custom one-off code
- [ ] `_ingested_at` and `_source_file` (or equivalent) metadata columns on
      every Bronze table
- [ ] Schema evolution allowed (`mergeSchema=true` or equivalent) — Bronze
      shouldn't reject a new column
- [ ] No filtering or "cleaning" happening at Bronze — it should be a
      faithful copy of the source

### Silver layer

- [ ] Incremental `MERGE`, not `INSERT OVERWRITE` — re-running the job
      shouldn't duplicate or lose rows
- [ ] At least one real DQX check applied (`DQRowRule`/`DQDatasetRule`) —
      not zero quality enforcement
- [ ] Delta table constraints (`CHECK`/`NOT NULL`) as a second, hard guard
      alongside DQX — DQX catches issues before the write, constraints are
      the last line of defense if something writes to the table another way
- [ ] Criticality choices make sense: `error` only for what should actually
      block/quarantine a row; `warn` for things worth flagging without
      losing otherwise-valid data
- [ ] Rejected/flagged rows land somewhere visible (a `quarantine_*`
      table), not silently dropped
- [ ] A build-order gate exists — the pipeline fails loud if the upstream
      table is empty, instead of quietly building an empty/misleading
      Silver table

### Gold layer

- [ ] Each metric's business definition would be clear to someone outside
      the team who only reads the table/column comments
- [ ] The aggregation grain is obvious from the schema (what does one row
      represent?)
- [ ] A snapshot/partition date column exists, unless there's a specific
      reason not to — you generally want to be able to time-travel
- [ ] Gold isn't built on a possibly-empty Silver table without a
      build-order gate first

### Bundle / deployment
*(`qubika-databricks-bundles`)*

- [ ] `databricks.yml` defines all three targets: `dev`, `staging`, `prod`
- [ ] No catalog name hardcoded anywhere — always `${var.catalog}` or
      equivalent, so the same code deploys cleanly to every environment
- [ ] `mode: development` on dev/staging (auto-pauses schedules so they
      don't fire on a cron while you're iterating); `mode: production` on
      prod
- [ ] Job owner is a **group**, never an individual person
- [ ] Failure email/alert notifications configured on the job
- [ ] `databricks bundle validate -t <target>` passes clean on every target

### Testing
*(`qubika-pipeline-testing`)*

- [ ] The pure transformation logic (not the I/O) has at least a couple of
      unit tests
- [ ] Those tests run without needing a live Databricks connection

### Governance
*(`qubika-unity-catalog-governance`)*

- [ ] Tables and schemas have `COMMENT`s explaining what they're for
- [ ] If anything in the data could plausibly be considered sensitive,
      you've at least thought about who should have access — even for this
      exercise's public taxi data, it's worth asking the question

## What if a lot of this is unchecked?

That's normal, especially your first time through — this is a long list on
purpose, so you have something concrete to compare against later once
you've built a few more pipelines. Pick two or three unchecked items that
seem most interesting and ask Claude to help you fix them; that's a better
use of remaining time than trying to check every box.
