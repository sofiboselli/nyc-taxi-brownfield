# Further Work: Governance & Cost Breadth

## Scenario

Iteration 3 closed the gaps you knew about going in: schemas split by
layer, the job tagged and owned by a group, comments in place, tests
added. The pipeline runs clean now. But "runs clean" and "is actually
being run responsibly" aren't the same claim, and once something is live
in a shared workspace, someone eventually asks the questions that only
come up *after* deployment:

- What is this actually costing us?
- Is it tagged consistently with everything else running here, or just
  internally consistent with itself?
- If someone points at the Gold table and asks "where did this number
  come from, and who's been touching it," can you answer without
  guessing?
- The job succeeding doesn't mean the data is still healthy — would you
  actually notice if it started quietly drifting?

None of this was on the original "why this repo doesn't pass" list — it
only becomes the obvious next question once you're the one who owns a
live pipeline instead of the one just trying to get it working.

**Prerequisite:** Brownfield completed through Iteration 3 — the job
deployed and run at least once via the restructured bundle, schemas
split (`bronze`/`silver`/`gold`/`quarantine`), tags and group ownership
in place.

**Also needed:** these questions all read from Databricks system tables
(`system.billing`, `system.lakeflow`, `system.compute`, `system.access`,
`system.catalog`). They must be enabled and granted by a metastore admin
— `USE CATALOG` on `system`, plus `USE SCHEMA` + `SELECT` on each schema
above. If a query below fails with a permission or "table not found"
error, that's the fix, not a bug in what you asked for.

---

## Step 1: What does this actually cost?

Ask Claude Code:

> "Now that this pipeline has been running through the exercise,
> investigate what it's actually costing us."

This is the `--deep` cost analysis `/de-init` offered back in Brownfield
Step 3.1 — the one the walkthrough told you to decline because cost
wasn't in scope yet. It's in scope now.

**Validation:** you should get back a ranked report — which runs cost the
most (DBU, duration, or bytes scanned), scoped to this job's warehouse,
not the whole shared workspace. Check that the numbers are plausible
against what you actually ran: three iterations' worth of redeploys and
job runs, on serverless compute, against a 150k-row dataset — this should
read as a small, cheap pipeline, not a mystery bill.

> This pulls from `qubika-cost-investigator`, which reads
> `system.query.history` and `system.billing.usage` — read-only, it never
> modifies anything. If it comes back asking you to narrow the time
> window or pick one metric instead of several, that's the skill's own
> guardrail against a report that quietly mixes duration and cost and
> calls the result one ranking.

---

## Step 2: Is it tagged like everything else here, or just internally consistent?

The cost report in Step 1 likely broke costs down using the tags Iteration
3 added — `Project`, `Environment`, `Owner`, `WorkloadType`. Those tags
were only ever checked against this one job. Ask:

> "Compare how well-tagged this job is against the rest of this
> workspace — am I actually following the tagging convention, or did I
> just make up something that's consistent with itself?"

**Validation:** this should run a tagging-compliance query across all
jobs in `dev_ai_kit_demo_brownfield`'s workspace, not just
`legacy_taxi_job`. You already know from Brownfield Step 3 that this
workspace has other jobs in it — some stale, never run
(`/de-audit` flagged two of them). See where your job actually lands
against that full list, and whether the specific tag keys/casing you used
match the convention exactly (a `project` tag and a `Project` tag are two
different columns in a cost report's `GROUP BY`, not the same thing typed
differently).

> `qubika-compute-tagging` draws the line between what it covers and what
> it doesn't: compute tags (jobs, pipelines, clusters, warehouses) are
> this skill; tagging catalogs/schemas/tables for governance is a
> different skill — Step 3, next.

---

## Step 3: What's actually flowing through this, and who's touching it?

Cost and tags answer "what does this run cost, and is it accounted for."
Neither answers "if someone points at a number in the Gold table and asks
where it came from, or who's been querying it, can you actually answer."
Ask:

> "Show me the full lineage into the Gold table, and who's actually been
> querying this data."

**Validation:** you should get a lineage trace that reads
`bronze.trips`/`bronze.zones` → `silver.trips` → `gold.kpi_by_borough_hour`
— matching the pipeline you actually built, not a guess. The audit query
should show your own job runs as the executor, plus anything you ran by
hand while testing.

> This is `qubika-unity-catalog-governance`'s system-tables pattern —
> `system.access.audit` (who did what, when) and
> `system.catalog.table_lineage` (what fed what) — both queryable as
> plain SQL, no separate lineage tool needed. It's a different part of
> the same skill that gave you ownership/grants/comments back in
> Iteration 3; this walkthrough never had a reason to reach for the
> audit/lineage half of it until now.

---

## Step 4: Would you actually notice if this started quietly breaking?

DQX (Iteration 2) blocks bad rows at write time — a hard gate, checked
once, per run. It says nothing about whether `silver.trips` looks
statistically different a month from now than it does today, and a job
that "succeeds" every night tells you nothing about that. Ask:

> "DQX catches bad rows before they're written. Set up something that
> watches this table over time and tells me if its data starts drifting,
> even when the job keeps succeeding."

**Validation:** confirm a monitor actually gets attached to `silver.trips`
(or `gold.kpi_by_borough_hour` — Claude Code should tell you which it
picked and why), trigger a refresh, and query the profile/drift metric
tables it writes to `dev_ai_kit_demo_brownfield`'s monitoring schema.
You're looking for real output — null rates, value ranges — not just a
monitor object that exists but has never run.

> `qubika-lakehouse-monitoring` is explicit about this not being DQX
> repeated: DQX is a per-write quality gate; this is ongoing statistical
> profiling on data that's already passed those gates. First refresh on a
> `TimeSeries` monitor can take 10-30 minutes since it profiles prior
> history on creation — that's expected, not a hang.

---

## Where this leaves you

Nothing here was on `docs/final-checklist.md` — that checklist tests
whether the pipeline itself meets Qubika's standards, not whether you can
answer for it operationally once it's live. Both are real. This is what
comes after the checklist, once "does it work" stops being the question
and "can I account for it" starts being the one that matters.
