# Further Work: Migration

## Scenario

Two different "bring someone else's system into ours" requests, and
they're not variations on the same problem:

1. A new client engagement lands — years of analytics running on a
   different SQL platform entirely (Snowflake, in this case), and it all
   needs to become Databricks SQL.
2. Separately, this workspace still has old tables sitting on the legacy
   Hive Metastore from before Unity Catalog was adopted here — nobody
   ever got around to moving them.

The first is a cross-platform translation problem. The second is a
within-Databricks governance problem. Both get called "migration" and
both call for a completely different tool.

**An honest note before starting:** neither of these can be run for real
in this exercise. There's no actual Snowflake SQL to transpile, and this
shared training workspace has no legacy Hive Metastore tables to migrate
— everything here was built UC-native from the start. Beyond that, the
Hive-to-UC tool specifically requires Workspace Admin *and* Account Admin
permissions, which a training account won't have regardless. What's
still genuinely worth checking is whether a proposed plan actually
follows the real sequencing these tools require — that's a design
question, answerable without ever running the command.

**Prerequisite:** none specific to Brownfield — this module is
deliberately a planning/reasoning exercise, not a deploy-and-validate
one, for the reasons above.

---

## Step 1: A different SQL platform entirely

Ask Claude Code:

> "A new client has years of Snowflake SQL — views, stored procedures —
> that need to become Databricks SQL. Where do we even start?"

**Validation:** sequencing is the actual test here. The plan should
analyze before it transpiles — running a full conversion first and
discovering a large failure rate mid-migration is the named failure mode
this tool exists to prevent. It should pass explicit catalog and schema
flags rather than leaving table references unresolved. And if it
proposes reconciliation, check it starts with a schema-level check
before a full data-level one — skipping straight to data comparison
means a silent type mismatch (say, decimal precision) never gets caught.

> This is `qubika-lakebridge`. One thing worth surfacing regardless of
> which engine the plan proposes: transpilation converts SQL text only —
> it does not move any data. If the plan implies that transpiling the
> SQL also migrates the underlying tables, that's worth correcting;
> those are two separate steps with two separate tools.

---

## Step 2: Tables still on the legacy Hive Metastore

Ask:

> "Some tables in this workspace are still on the legacy Hive Metastore,
> never moved to Unity Catalog. Bring them in properly."

**Validation:** assessment-first is non-negotiable here, more than in
Step 1 — the tool's own guidance is blunt that migrating without running
an assessment first means hitting blockers mid-migration instead of
before touching anything. Check the plan proposes moving schema by
schema rather than everything at once (one failed table blocking an
entire workspace migration is the named anti-pattern), and that it uses
an alias step so downstream jobs don't break the moment a table moves —
not a silent cutover.

> This is `qubika-uc-migration` (UCX). It's worth being explicit that
> this step is unusually plan-only even by this module's standard: UCX's
> group-migration phase specifically requires both Workspace Admin and
> Account Admin permissions, which isn't something any individual
> engineer just has by default — it has to be requested, not assumed.

---

## Where this leaves you

Two of the most admin-gated, highest-blast-radius tools in the kit —
appropriately so, since both move or rewrite an entire system's worth of
tables at once. Neither got run for real here. What's actually
checkable, and what this module tests, is whether a proposed plan
respects the safety rails these tools build in on purpose: analyze
before you transpile, assess before you migrate, alias instead of a
silent cutover, one schema at a time instead of everything at once.
