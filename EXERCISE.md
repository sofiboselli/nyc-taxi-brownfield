# Exercise: build a Bronze → Silver → Gold pipeline from scratch

## The point of this exercise

You're going to build a small Databricks pipeline from an empty folder,
using the Qubika AI Dev Kit end to end. **The goal is learning to use the
kit — not producing a perfect pipeline.** Nobody is grading the final
numbers. If your Gold table is a little off, or you skip a stretch goal,
that's fine. What matters is that you go through the kit's actual workflow:
its setup wizard, its guided pipeline builder, its skills for
Auto Loader / data quality / catalog conventions — the same tools you'd
reach for on a real project.

There's no reference implementation included here on purpose. Use the kit
the way you would on day one of a real project: ask it questions, read the
skills it points you to, and build.

## Background: what a medallion pipeline is

If you haven't built one before — Qubika's Databricks projects are
organized into three layers:

- **Bronze**: raw data, landed as close to its original form as possible.
  No cleaning, no filtering — just captured, with metadata about where it
  came from and when.
- **Silver**: cleaned, typed, and quality-checked. This is where you decide
  what "bad data" means for your source and do something about it (reject
  it, flag it, fix it).
- **Gold**: business-ready aggregations — the numbers someone would actually
  put in a dashboard.

You'll build all three.

## The task

Using the data in `sample_data/raw/` (see `docs/data-profile.md` for what's
in it — read that before you start), build a pipeline that answers:

> **What's the total revenue, trip count, and average tip % for NYC Yellow
> Taxi trips in January 2024, broken down by pickup borough and hour of
> day?**

## Suggested workflow

1. `mkdir` a fresh, empty directory somewhere on your machine and `cd` into
   it. Don't build inside this exercise folder — keep the data/instructions
   separate from your own working project.
2. Open Claude Code and run **`/de-init`** — the kit's setup wizard. It'll
   ask you a few questions (project name, a short customer code for catalog
   naming, source type, target environment, data sensitivity) and scaffold
   a proper Databricks Asset Bundle project.
3. Copy the data in: `cp -r <path-to-this-folder>/sample_data .`
4. From here, you have two reasonable paths — pick whichever, or mix:
   - Run **`/de-pipeline`** — the kit's guided Bronze → Silver → Gold
     wizard. It asks questions, builds one layer at a time, and pauses
     between each for you to review before continuing. This is the
     "let the kit walk you through it" path.
   - Build it more manually, consulting the relevant skills directly as you
     go: `qubika-streaming-pipelines` (Auto Loader ingestion),
     `qubika-medallion-architecture` (layer conventions, naming, the MERGE
     pattern), `qubika-data-quality` (DQX checks), and
     `qubika-unity-catalog-governance` (catalog/schema naming). This is the
     "look things up as you need them" path — closer to how you'd actually
     work day to day.
5. Either way: **`databricks bundle validate -t dev`** before every deploy
   attempt. It catches typos before they cost you a real deploy.

## What "done" looks like

You don't need all of this to get value out of the exercise, but aim for:

- [ ] A Bronze table with the trip data landed via Auto Loader, and a
      second Bronze table (or equivalent) for the zone lookup
- [ ] A Silver table that's cleaned and typed, joined to the zone lookup so
      you have a pickup borough on each row, with **at least one real data
      quality check** applied via DQX (your choice of what to check — the
      data profile has plenty of candidates)
- [ ] A Gold table grouped by pickup borough and hour of day, with at least
      trip count, total revenue, and average tip %
- [ ] Bonus, if you want to push further: a second DQX rule, or a quick
      Genie space / dashboard on top of your Gold table

## Sanity-checking your result

Once you've got a Gold table, a quick query like this should show
recognizable patterns even if your exact numbers don't match anyone
else's:

```sql
SELECT pickup_borough, pickup_hour, trip_count, avg_tip_pct
FROM <your_catalog>.<your_gold_schema>.<your_table>
ORDER BY total_revenue_usd DESC
LIMIT 10;
```

- Manhattan should dominate revenue.
- Airport zones (JFK / LGA / EWR — check `taxi_zone_lookup`) should show up
  with noticeably higher average fares than everywhere else.
- If whatever quarantine/rejected-rows table you built is completely empty,
  double-check your quality rule actually runs against the data — the
  sample has real rows that should trip a reasonable fare or timestamp
  check (see `docs/data-profile.md`).

## Last step: check it against Qubika's standards

Once you've got something working (doesn't need to be everything above),
go through **`docs/final-checklist.md`**. It starts with `/de-audit` — the
kit's own automated check — then a manual checklist of the conventions a
Qubika pipeline is expected to follow (naming, MERGE vs overwrite, DQX
criticality, bundle targets, tests, and so on). It's there to show you what
"good" looks like against real standards, not to mark you down for
whatever you didn't get to.

## If you get stuck

This is exactly what the kit is for — ask Claude directly ("how do I add a
DQX rule that rejects negative fares?", "what does the Auto Loader Bronze
pattern look like?"), or read the skill it points you to
(`qubika-streaming-pipelines`, `qubika-medallion-architecture`,
`qubika-data-quality`, `qubika-unity-catalog-governance`). Getting
comfortable asking the kit for help *is* the skill this exercise is
building.
