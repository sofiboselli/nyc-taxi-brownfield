# Further Work: Alternate Ingestion Patterns

## Scenario

Brownfield's Bronze has only ever handled one shape of source: someone
drops a monthly parquet file into a Volume. Real projects don't stay
that simple for long — three different "we have a new source" requests
land in the same week, and each one is shaped completely differently
from the others.

1. Trip data starts arriving continuously throughout the day instead of
   once a month.
2. An ops team offers to let you pull zone/reference data straight from
   their own database instead of exporting a file for you.
3. A driver-payments vendor exposes trip payment records through their
   own REST API — no file, no database connection, just HTTP.

**An honest note before starting:** none of these three sources actually
exist in the shared training workspace — there's no live Kafka/Kinesis
topic, no Lakehouse Federation connection to an external database, no
real SaaS API credential. Every other module in this series deploys and
validates against something real; this one can't, without inventing an
external system that has nothing to do with this exercise. What's still
genuinely checkable is whether the *design* — the code, the load type,
the config choices — actually matches the right pattern for each source.
That's real and worth verifying carefully; running it against a live
external system isn't available here.

**Prerequisite:** none beyond having a general sense of Brownfield's
current Bronze shape (`bronze/ingest_trips.py`'s original one-shot batch
read), since each step below is explicitly a *change* from that shape.

---

## Step 1: Files, but continuous now

Ask Claude Code:

> "Trip data used to arrive as one file a month. Now it's landing
> continuously in small batches throughout the day. Change Bronze to
> handle that."

**Validation:** "continuous small-batch arrival" doesn't automatically
mean "build an always-on streaming job" — a scheduled job using
`availableNow` can still be the right, cheaper answer if data being a
few minutes old is fine. Check that the trigger choice actually got
reasoned about instead of defaulted. Confirm both a checkpoint location
and a schema location got set — missing either isn't a style nitpick,
it's the specific thing that makes a restart replay everything from
scratch or crash on the next schema change.

> Auto Loader alone isn't new here — Iteration 1 already reached for it.
> What's actually new is the trigger decision. The relevant skill's own
> framing is blunt about this: most pipelines at Qubika are batch, and
> streaming (an always-on `processingTime` trigger) is for when the
> business genuinely needs sub-hourly freshness, not just because files
> now arrive more often than once a month.

---

## Step 2: Skip the file, read the source database directly

Ask:

> "The ops team wants to let us pull zone reference data straight from
> their own database instead of exporting a file for us to land."

**Validation:** the correct answer here is not hand-rolled JDBC code —
Qubika's convention is a specific metadata-driven control-table pattern,
and reaching for a custom Spark JDBC read instead is itself the mistake
to catch. Even without a real connection to test against, check whether
the design correctly distinguishes a full load from an incremental one,
and — if it picks incremental — that it names a real watermark column
rather than just filling the field in because the schema requires it.

> This is `qubika-federated-ingestion`. It has a real prerequisite this
> module can't satisfy — a Lakehouse Federation connection to the source
> database, which is admin-provisioned, not something an engineer sets
> up mid-task. Worth keeping straight from Step 3: this pattern is for a
> database Databricks can connect to directly, not a SaaS product's API
> — those are two different skills for a reason.

---

## Step 3: A vendor's REST API, not a database or a file

Ask:

> "A driver-payments vendor exposes trip payment records through their
> own REST API — no file, no database connection we can use, just
> HTTP."

**Validation:** check the design lands *both* the raw JSON payload and a
typed projection — landing only one or the other is a named anti-pattern
here, not a style preference: raw-only means every downstream query pays
a parse cost, typed-only means data silently disappears the day the
vendor adds a field. Confirm any API token routes through a secret
scope, never inlined. Confirm it reasons about whether the vendor's API
actually exposes a modified-at filter before deciding between an
incremental watermark and a full snapshot — not defaulting to whichever
is simpler to write.

> This is `qubika-saas-api-ingestion`. Real vendors return pagination in
> wildly different shapes — a cursor parameter, a `Link` header, an
> `after` token — so the specific parameter names in any generated code
> are illustrative, not something to treat as universal. What
> transfers across every vendor is the retry/backoff loop shape and the
> raw-plus-typed landing discipline, not the field names.

---

## Where this leaves you

Same underlying event three times — a new source shows up — and three
completely different correct answers depending on what kind of source it
actually is. Files arriving more often doesn't mean streaming is
automatically right. A database willing to be queried directly doesn't
mean hand-rolled JDBC. A REST API doesn't mean skipping the typed-
projection discipline just because Bronze has, until now, only ever
looked like the output of a monthly file. None of this got run against a
real external system in this exercise — that's a disclosed limitation of
a shared training workspace, not something to pretend around.
