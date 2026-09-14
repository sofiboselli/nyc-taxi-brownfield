# Further Work: GenAI & Apps

## Scenario

Everything built so far answers questions with numbers — aggregates,
KPIs, structured rows. A rider-support lead asks for something
different: reps fielding "what's the deal with this zone" questions need
to search actual written knowledge — short notes about boroughs and
service areas — in plain English, and get back the relevant note, not a
row of numbers. That's a search problem over text, not a query problem
over a table, and nothing built so far handles it.

There's no existing text corpus in this repo to search — `silver.trips`
and `taxi_zone_lookup.csv` are structured data, not prose.
`further-work/data/borough_notes.csv` provides one: five short,
real support-style notes, one per NYC borough, each grounded in actual
counts from `taxi_zone_lookup.csv` (zone counts, the Yellow Zone/Boro
Zone/Airports split) rather than generic filler. Deliberately small —
not a production knowledge base, just enough real written content to
prove the retrieval flow actually works end to end.

**Prerequisite:** Brownfield completed through Iteration 3 — mainly so
the notes' references to real zone/service-zone facts line up with
what's actually in `bronze.zones`.

---

## Step 1: Land the notes as a real Silver chunk table

Ask Claude Code:

> "Land `further-work/data/borough_notes.csv` as a proper Silver chunk
> table — not a Bronze dump."

**Validation:** check the resulting table has a real primary key and
Change Data Feed enabled — both are hard requirements for what Step 2
needs, not optional polish. Read a few of the actual notes in the
table; they should match `borough_notes.csv` exactly, not a paraphrase
or a regenerated version of them.
---

## Step 2: Make it searchable by meaning, not just keyword

Ask:

> "Make these notes searchable in plain English — someone should be able
> to ask about a topic and get back the relevant note, even if they don't
> use the exact words in it."

Expect Claude Code to stop and ask you a series of concrete configuration
questions — environment, schema, index type, embedding model, pipeline
type, endpoint type — one at a time, before writing anything. Don't
rubber-stamp through them; each has a real cost or correctness
consequence (a `CONTINUOUS` pipeline costs meaningfully more than
`TRIGGERED` for data that barely changes; the wrong embedding source
column produces garbage vectors).

The environment question specifically assumes dev/staging/prod always
exist — this project only has one real catalog, so there's no genuine
second choice to offer. Don't be surprised if that step errors out or
gets skipped instead of presenting a clean multi-choice prompt; what
matters is whether Claude Code recognizes there's no real second option
and reasons through it directly, rather than inventing a fake
`staging`/`prod` choice just to force the question into a shape that
fits.

**Validation:** the column it embeds must be the actual text column —
if it points at a primary key or numeric ID instead, that's not a
config nitpick, it's a broken index that will "work" (return results)
while returning nonsense. Once it's built, actually query it — ask
something that doesn't share exact words with any note — and confirm
real, relevant text comes back, not an empty or garbage result.

> There are two Qubika skills that cover this ground, with slightly
> different conventions for naming and endpoints — worth checking which
> one Claude Code says it drew from and whether its output matches what
> you'd expect, rather than assuming there's one single obvious source of
> truth here. Either way, the core discipline is the same: never let a
> configuration choice — embedding model, pipeline type, which column
> gets embedded — get picked silently. Every one of them is expensive or
> wrong to undo later.

---

## Step 3: Give it a surface someone can actually use

Ask:

> "Build a simple internal tool where a support rep can type a question
> and see the matching notes — nothing fancy."

**Validation:** for an internal tool like this, the default should be a
lightweight, DE-buildable app, not a decision to reach for a heavier
frontend stack — check that Claude Code actually reasoned about that
choice rather than defaulting to whichever it happens to generate first.
Confirm it deliberately picked between showing every rep the same view
versus respecting individual permissions, rather than silently choosing
one. After deploying, remember that deploying an app and starting it are
two different steps — don't conclude something's broken if it deploys
but the URL doesn't respond yet. Actually open it and type one real
question; confirm you get a real note back, not a placeholder screen.

> This is `qubika-databricks-apps`. Any resource this app touches — the
> warehouse, the index — should be wired by reference, never a hardcoded
> ID copy-pasted into the code; that's what makes the same app deployable
> to a different environment without editing source.

---

## Step 4: Tear it down when you're done

Same discipline as anything else in this series that leaves real
infrastructure running:

> "I'm done exploring. Tear down the index and the app so neither keeps
> costing anything."

**Validation:** confirm the index is actually deleted (not just idle),
and — if you were the last thing using the shared vector search endpoint
— that the endpoint gets cleaned up too, rather than sitting there
unused. Confirm the app is stopped or deleted, not left running for
nobody to use.

---

## Where this leaves you

A tiny, real text corpus, a search index built on real (not fabricated)
config decisions, and a surface someone other than an engineer can
actually use — the same "someone else now depends on what you built"
shift that shows up anywhere in this series someone besides the original
engineer starts relying on the pipeline. And the same closing discipline
as every module that stands up live infrastructure: it doesn't tear
itself down.
