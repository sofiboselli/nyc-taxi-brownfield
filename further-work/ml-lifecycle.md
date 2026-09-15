# Further Work: ML Lifecycle

## Scenario

`silver.trips` already computes `tip_pct` on every row — it's been sitting
there since Iteration 2, used only to report averages after the fact. A
data scientist joining the team asks a genuinely different kind of
question: instead of reporting what tipping looked like last month, can
you predict it — flag a trip as likely to under-tip before it becomes a
pattern someone complains about, instead of noticing it in a Gold
aggregate weeks later.

This is the first module in the series that builds something new rather
than asking new questions of something that already exists. It also
costs real money once an endpoint is live — worth scaling it down or
tearing it down once you're done exploring, not leaving it running.

**Prerequisite:** Brownfield completed through Iteration 3 —
`silver.trips` populated, `tip_pct` present. You'll also need a
Python-capable compute path that can train a small scikit-learn model.

---

## Step 1: Where do these inputs actually belong?

Ask Claude Code, before it builds anything:

> "I want to predict `tip_pct` from attributes already in `silver.trips`.
> Before you build anything, tell me where the model's input features
> should actually live."

**Validation:** the correct answer is not the Feature Store — the right
destination is either Gold Delta or no new table at all (reading
straight from `silver.trips`) depending on whether any real
transformation is happening, not a fixed answer either way.

> `qubika-feature-engineering` exists mainly to stop duplicated,
> ungoverned features when multiple models and teams share a workspace.
> This project doesn't have that problem yet — one model, one consumer.
> The skill is still the right one to reach for, because *deciding*
> Feature Store doesn't apply is exactly what its decision matrix is for;
> it's just that the correct output this time is "don't use me."

---

## Step 2: Train it, and track it like it'll need to be audited later

Ask:

> "Train a small regression model predicting `tip_pct` from
> `trip_distance`, `passenger_count`, `pickup_hour`, and
> `pickup_borough`. Hold out a real test set first — don't evaluate on
> what it trained on. Track the run properly."

**Validation:** check the experiment path — it should encode team,
project, and environment (`/{team}/{project}/{env}`), not a flat name
like `tip-model`. Check the run's tags for the seven Qubika requires:
`project`, `team`, `env`, `jira_ticket`, `dataset_version`, `feature`,
`framework`. If there's no real Jira ticket for this exploratory work,
that's worth surfacing honestly rather than inventing a ticket ID to fill
the slot — a placeholder value defeats the whole point of a tag meant for
audit. Confirm it used the framework-specific autolog call
(`mlflow.sklearn.autolog(...)`, not the
generic `mlflow.autolog()`), since the generic one silently drops
framework-specific artifacts.

> `qubika-ml-experiment-tracking` is what makes a run auditable months
> later instead of an orphaned experiment nobody remembers the context
> for. The promotion-ready checklist it defines requires an eval against
> a genuinely held-out set — this is why Step 2's prompt asks for the
> split up front instead of leaving it for later, where it's tempting to
> just check training accuracy and call it done.

---

## Step 3: Is it actually any good?

Ask, giving it the run ID from Step 2:

> "Evaluate this run end-to-end against the held-out test set before I
> trust it — run_id `<paste it here>`."

**Validation:** the deliverable is a self-contained HTML report logged
back to the *same* MLflow run under `evaluation/` — not a new run, which
would sever the link to what was actually trained. Read the verdict
(`PROMOTION-READY` or `DO NOT PROMOTE`) and check it's grounded in the
held-out metric against a real threshold, not just "the numbers look
fine." If the model you trained doesn't expose feature importances (a
plain linear model, for instance), confirm the report says so explicitly
rather than fabricating a chart for a metric the model can't actually
produce.

> This is `qubika-ml-model-evaluator` — read-only at the registry level,
> deliberately. It never promotes anything on its own; it hands back a
> verdict and it's your call what to do with it. Same "verify, don't
> rubber-stamp" discipline as declining the auto-fix offer back in the
> main walkthrough's onboarding step — a clean-looking report isn't the
> same thing as a model worth serving.

---

## Step 4: Actually serving it

If — and only if — Step 3 came back promotion-ready, ask:

> "Register this model and stand up a real endpoint I can query."

**Validation:** before any code gets written, expect a names-and-
locations proposal — the model's UC path, the endpoint name, the
inference table — and expect Claude Code to wait for you to confirm it
rather than proceeding on its own. Check `scale_to_zero_enabled` is set
for a dev context (true), not left as an always-on prod default. Once
the endpoint is live, actually query it with one real row from
`silver.trips` and confirm you get back a real predicted `tip_pct`, not
just a "the endpoint exists" confirmation.

> This is `qubika-mle-model-serving`. A canary rollout (10% → 50% → 100%
> traffic split across two versions) is the convention for shipping a
> *second* version safely — not relevant for this first deployment, but
> worth knowing before anyone on this project ever ships a v2 straight to
> 100%. The inference table this step sets up isn't a one-off either — it
> feeds directly into `qubika-lakehouse-monitoring`'s `InferenceLog`
> profile if prediction drift over time ever becomes a real question
> here — a different monitor type than a `TimeSeries` monitor on a Delta
> table, but the same underlying skill.

---

## Step 5: Tear it down when you're done

Once you're finished exploring — not before, and don't skip this because
`scale_to_zero_enabled` was set in Step 4:

> "I'm done with this exercise. Tear down the endpoint so it stops
> costing anything."

**Validation:** scaling to zero still leaves the endpoint object,
inference table, and registered model version in place — fine for a real
project you might come back to, but if the point is "make sure this
stops costing money," confirm the endpoint is actually deleted, not just
idle. Check back after: list serving endpoints and confirm this one is
genuinely gone, rather than trusting the delete call's own "success"
message. `scale_to_zero_enabled=True` protects you from runaway compute
cost if you forget this step — it does not protect you from an endpoint
nobody remembers exists six months from now.

> Per `qubika-mle-model-serving`'s own guidance, scaling to zero rather
> than deleting is the *default* recommendation — it preserves the
> serving URL and inference table history for a project that's actually
> ongoing. Full deletion is explicitly the exception, reserved for
> retiring the model for good. For a one-off exploration like this one,
> that exception is the right call.

---

## Where this leaves you

Five decisions, in order: where the inputs belong (and knowing when the
governed answer is "don't use the fancy tool"), a run that's actually
auditable months from now, an evaluation that can't lie to you by
grading its own homework, a deployment nobody can silently break by
skipping the confirmation step, and — unlike every other module in this
series — a real teardown at the end, because this is the one module that
leaves live, billed infrastructure behind if you just walk away.
