# Further Work: Kit Operations

## Scenario

A real ticket lands: "Before we call this production-ready, prove it
holds up at real volume — not the 150k-row sample it's been running on
this whole time." Before touching the pipeline itself, this is exactly
the moment a few operational habits matter more than any Bronze/Silver/
Gold convention: check that your own tooling is actually healthy before
you start debugging your own code, keep this chunk of work's cost
attributed to the right thing instead of lumped into everything else
you've already done, and reach for fabricated data instead of scavenging
more real NYC files (or, worse, anything more sensitive) for a test that
only cares about scale.

**Prerequisite:** Brownfield completed through Iteration 3.

---

## Step 1: Is this the kit, or is it me?

Run:

> `/de-doctor`

**Validation:** read the pass/warn/fail table for real, don't skim past a
`[!]`. The current
checks cover prerequisites (git/python/node/CLI versions), auth, kit
install integrity, and tracker file permissions. A clean `/de-doctor` run
means those specific things are fine.

---

## Step 2: Track this specific chunk of work

Run:

> `/de-track start "load-test synthetic volume"`

**What this should do:** `/de-track` checks for a credentials file before
anything else. If it's present, you get a real checkpoint — a feature
switch, with token counts for whatever was open before. If it's missing
(a fresh install, or a workspace where tracking was never wired up), it
should never silently proceed as if tracking is on. Expect it to offer to
bootstrap tracking non-interactively; if that bootstrap fails — most
likely because the `claude-code-tracker` secret scope isn't provisioned
in this workspace, which is a one-time admin action, not something an
individual engineer can self-serve — it should name the fallback
(`setup_tracker.sh`, with credentials pasted by a team lead) and state
plainly that this session's usage, including this checkpoint, was not
recorded. A command that reports success here without a real credentials
file has quietly started lying to you about cost attribution.

**Validation:** don't just read the confirmation message — check the
numbers. If a different feature was already open from earlier work,
confirm *that* one's token delta got closed out and reported before this
one starts, and that the counts look like a real conversation's worth of
tokens, not zero. If tracking turned out to be unconfigured, confirm the
command said so outright rather than reporting a checkpoint it didn't
actually write — and if it's missing, that's worth noticing on its own:
every hour spent with this kit up to now may not be showing up anywhere
for attribution.

---

## Step 3: Load-test at real volume, without touching more real data

Run (it's interactive — answer its questions as they come):

> `/de-synthetic-data`

Unlike `/de-doctor` and `/de-track`, this command wraps a named skill —
expect it to announce `[Using skill: qubika-synthetic-data]` before it
asks you anything. That's the source of the conventions the rest of this
step checks: the gated confirmations, the `synthetic_*` naming, the
comment marking the data as fake.

When it asks for a domain, describe this project's own schema (trip
records, zone lookups) instead of reaching for the built-in banking
template, and give it a volume that matches an actual load-test target —
meaningfully larger than the current 150k-row sample, not an arbitrary
huge number just to see what happens.

**Validation:** this command gates on two explicit confirmations before
it creates anything in Unity Catalog — read the proposed plan (target
schema, row counts, columns) rather than approving on reflex. After it
runs, check that its own validation step actually happened: row counts
match what you asked for, zero orphaned foreign keys on the referential-
integrity check, and the schema/table comments literally say this is
synthetic — not something a future learner could mistake for real data.

This is a genuinely different data source than anything else in this
repo. `SEED.md`'s parquet file is real (trimmed) NYC TLC data; this
generates fabricated rows from a schema description, landed in an
obviously-fake target — never anywhere near
`dev_ai_kit_demo_brownfield`'s real schemas.

---

## Step 4: Close the checkpoint

Run:

> `/de-track end`

**Validation:** confirm you get a real close-out with actual token
counts, not "nothing to end." If there's nothing to close, Step 2 didn't
actually open anything, and this whole chunk of work went untracked.

---

## Where this leaves you

Nothing here touched the pipeline. What it demonstrates instead is that
the kit is also a set of operational habits, not just medallion
conventions: check your own tooling before you debug your own code, keep
cost attribution honest instead of letting it default to "untracked,"
and reach for fabricated data the moment the question is "does this
scale" rather than "is this correct."
