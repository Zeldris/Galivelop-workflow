<!-- galivelop-workflow v0.4.1 -->
# opt-ai — project notes

Read by the `opt-ai` skill first; everything specific to this project's local AI models lives here. Created by the
workflow once; from then on it belongs to the project.

## Engines and models

<!-- Which engine each task uses and where the model names live (a config file; never copy the names here). -->

## Tasks

<!-- The values of app.task the code emits, and the ones to exclude (warm-up calls). -->

## Machine profiles

<!-- Names (app.machine_profile), which one is the minimum (always measured), how the profile is set and how the
     log is switched on. -->

## Settings

Read by `scripts/medir.py` of the skill; relative paths resolve against the repo root.

```opt-ai
# log: <this round's per-call log>
# previous: <the earlier round's log>
exclude_tasks: warmup
cold_ms: 100
```

## Benchmark

<!-- The command that replays a fixed scenario with the log on, and how long it takes. -->

## Quality cases

<!-- The command that evaluates retrieval on a fixed case set, where the cases live, where findings are listed. -->

## Acceptable times

<!-- Per task, once measured. -->

## Already in place

<!-- Every tool or setting approved before, one line each, so it is not proposed again. -->
