# Before you send this out

For the facilitator only — not part of the exercise package itself (don't
forward this file to the participant).

## Prerequisites to confirm

- [ ] Participant has the AI Dev Kit installed and `/de-init` works in a
      fresh Claude Code session.
- [ ] Participant has a Databricks CLI profile for `qubika-training`
      (`/de-databricks-setup`) and can create their own
      `qubika_dev_<their-code>` catalog — confirm with data-platform if
      you're not sure everyone has `CAN_CREATE_CATALOG`.
- [ ] The Databricks MCP connection works in Claude Code before you hand
      this off — a broken MCP wrapper wastes their time debugging your
      environment instead of learning the kit.

## Validate the exercise is actually completable

Before sending this out, build it yourself once, following `EXERCISE.md`
exactly as written, against `qubika-training`. This confirms the task is
achievable with the data provided and gives you a rough sense of what a
reasonable Gold table looks like, in case a participant asks whether their
numbers seem right.

## Known gotchas (keep these to yourself unless someone's stuck)

Two things bit this build the first time through — if a participant hits
either, you'll recognize it immediately instead of debugging from scratch:

1. **DQX API**: the `qubika-data-quality` skill's own doc examples show
   `DQRowRule(check_function="is_not_null")` — a string. The real installed
   `databricks-labs-dqx` package requires `DQRowRule(check_func=is_not_null)`
   — an actual function reference from `databricks.labs.dqx.check_funcs`,
   with extra params via `check_func_kwargs={...}`. The string form raises a
   pydantic `ValidationError`. This is a real bug in the skill's docs
   (flagged upstream) — if someone hits it, it's not their mistake.
2. **Local PySpark tests need a JDK.** If a participant tries to run
   `pytest` locally and hits `Unable to locate a Java Runtime`, they need
   `brew install openjdk@17` (or equivalent) — pyspark doesn't bundle one.

Let them find and fix these themselves if you want to keep the exercise
fully hands-on — debugging a real skill-doc bug is itself a reasonable
thing to learn from. Use this list only to recognize the problem quickly if
they ask for a nudge.
