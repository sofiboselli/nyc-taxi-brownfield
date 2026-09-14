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
and `taxi_zone_lookup.csv` are structured data, not prose. So the first
step here is producing one, deliberately small: not a production
knowledge base, just enough real written content to prove the retrieval
flow actually works end to end.

**Prerequisite:** Brownfield completed through Iteration 3 — mainly for
the real borough/zone names in `bronze.zones` this step writes about.

---

## Step 1: Give it something real to search

Ask Claude Code:

> "Using the real borough and zone names from `bronze.zones`, write a
> handful of short support-style reference notes — a paragraph each,
> the kind of thing a support rep would want on hand. Land them as a
> proper Silver chunk table, not a Bronze dump."

**Validation:** check the resulting table has a real primary key and
Change Data Feed enabled — both are hard requirements for what Step 2
needs, not optional polish. Read a few of the actual notes; they should
reference real zone/borough names from the data, not generic filler.

> This is genuinely new content this repo didn't have — a small, real
> text corpus, not a fabricated stand-in for one. Keep it small on
> purpose: the point of this module is proving the retrieval flow works,
> not building a production knowledge base.

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
