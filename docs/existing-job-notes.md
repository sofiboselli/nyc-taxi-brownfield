# What's already running in the workspace

This is the part that can't live in the repo — a Databricks Job someone
set up by hand in the UI, months ago. Write it down here so whoever joins
the project (and `/de-audit`, once it can reach the workspace) has
something to compare the live state against.

## Job: "Taxi Analytics - Legacy"

| Field | Value |
|---|---|
| Created by | a contractor, ~6 months ago, for a one-off exec demo |
| Owner | `jsmith@qubika.com` — **no longer with the company** |
| Schedule | daily, 06:00 UTC (nobody's confirmed anyone still needs this) |
| Tasks | 3, chained by hand in the UI: `bronze/ingest_trips.py` → `silver/clean_trips.py` → `gold/kpi_by_borough_hour.py` — all notebook tasks, no bundle behind any of them |
| Cluster | a single all-purpose cluster, not a job cluster — `spark_version` several versions behind current, no `autotermination_minutes` set |
| Tags | none |
| Failure notifications | none configured |
| Permissions | `CAN_MANAGE` on the departed owner's account only; nobody else can edit the job without an admin override |

## Why this matters for the exercise

None of this is visible from the repo alone — it's exactly the kind of
gap that's easy to miss when "the pipeline runs fine" is the only bar
being checked. Part of joining this project is reconciling what's in git
against what's actually deployed, not just reading the code.

If you get real workspace access, a few things worth checking directly in
Databricks before you start changing anything:

- Confirm the job is still on the schedule described above (things drift).
- Note the current cluster's `spark_version` and idle cost — an
  all-purpose cluster with no autotermination left running is a real
  (if small) cost leak.
- Check whether `jsmith@qubika.com`'s account is still active. If the job
  owner's account gets deactivated, the job silently stops running — a
  common way "the pipeline runs fine" quietly becomes "the pipeline
  stopped running three weeks ago and nobody noticed."
