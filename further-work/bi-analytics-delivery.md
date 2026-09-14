# Further Work: BI & Analytics Delivery

## Scenario

`gold.kpi_by_borough_hour` is trustworthy now — fixed pipeline, real
comments, snapshotted history instead of numbers that vanish on the next
run. So far the only person who's ever queried it is you, the engineer
who built it. That changes the moment someone else wants access to it —
someone who doesn't write SQL and isn't going to file a ticket every time
they have a new question.

Two requests come in, and they sound similar on the surface but aren't
the same problem:

1. "I have a question about this data almost every day, and it's rarely
   the same question twice. I don't want to wait on you for a new query
   each time."
2. "Actually, there are only three or four numbers I check every Monday
   morning. I just want those, the same way, every week — no typing
   required."

**Prerequisite:** Brownfield completed through Iteration 3 —
`gold.kpi_by_borough_hour` exists, is commented, and is the one table
either request below should ever point at. Neither request gets access
to `bronze.*` or `silver.*` — those aren't curated for someone outside
the team to query directly.

**Also needed:** a SQL warehouse in the shared workspace, and permission
to use it. If you don't have one, that's the same kind of ask-your-team-
lead prerequisite as the catalog grants back in the main README — resolve
it before Step 1, not mid-way through.

---

## Step 1: "A different question every time"

Ask Claude Code, describing the need rather than naming a tool:

> "A stakeholder wants to ask this Gold table questions in plain English
> — a different question every time, no SQL. Set that up."

**Validation:** don't just confirm something got created — actually use
it. Ask it a real question ("which borough had the most trips?"), then a
real follow-up that depends on the first ("now break that down by hour")
in the *same* conversation rather than starting fresh each time. Confirm
you get back real generated SQL and real rows, not just a text
clarification asking you to rephrase — and confirm the SQL only ever
touches `gold.kpi_by_borough_hour`, never `bronze.*`/`silver.*`.

> This is `qubika-genie` — a Genie Space, a conversational natural-
> language-to-SQL interface built via the Databricks SDK (`w.genie.*`),
> not a slash command. It needs an explicit `warehouse_id`; Claude Code
> should confirm which warehouse with you rather than picking one on its
> own. What actually governs what it can answer isn't just the prompt —
> it's three layers stacking: Unity Catalog grants (can the querying
> identity even `SELECT` the table), the Space's own configured table
> list (only tables you deliberately pointed it at), and how well it's
> been curated with example Q&A pairs for anything domain-specific ("rush
> hour," "a big tip") that it can't infer from column names alone. An
> uncurated Space answers plausibly and sometimes wrong — if a number
> looks off, that's a curation gap, not a bug to route around.

---

## Step 2: "The same numbers, every week, no typing"

Ask Claude Code:

> "Now they want the same three or four numbers every Monday morning,
> without asking anything — a fixed view, not a conversation."

Before it builds anything, expect Claude Code to stop and confirm a plan
with you first — which catalog, which warehouse, what pages and widgets
— rather than deploying straight away. Don't rubber-stamp it without
reading it; that's the same "verify, don't assume it landed" discipline
from the main walkthrough, just earlier in the process this time.

**Validation:** the real test isn't that a dashboard object exists — it's
that every widget on it actually renders real numbers instead of
"Invalid widget definition." Open it and confirm each widget's SQL was
genuinely tested against the live table before deployment, not written
and shipped blind.

> This is `qubika-aibi-dashboards` — Databricks AI/BI (Lakeview)
> dashboards. Its own workflow is explicit about testing every dataset's
> SQL against the real table before building any widget JSON, precisely
> because an untested query produces a dashboard that looks fine in the
> editor and breaks the moment someone opens it. Two things worth
> watching for here, specific to this repo: the skill's own examples
> default to a `qubika_dev`-style catalog naming convention that doesn't
> match this project's real catalog (`dev_ai_kit_demo_brownfield`) — make
> sure Claude Code confirms the actual catalog rather than following the
> example verbatim. And this skill's tools (inspecting the table,
> testing SQL, deploying the dashboard) are provided by a Databricks MCP
> server — if that server isn't connected in your environment, this step
> fails with a missing-tool error, not a data or query problem. Worth
> checking your session's MCP server status before assuming something
> about the dashboard logic is wrong.

---

## Where this leaves you

Two different requests, two different tools, and the distinction is real,
not incidental: a Genie Space is for questions you can't enumerate ahead
of time; a dashboard is for the fixed, known set you want rendered the
same way every time. Reach for the wrong one and you either get a rigid
dashboard someone keeps asking you to add "just one more chart" to, or a
conversational tool that's the wrong shape for a number someone actually
wanted to see the same way every Monday without asking.
