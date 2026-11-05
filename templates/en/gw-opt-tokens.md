<!-- galivelop-workflow v0.5.1 -->
# gw-opt-tokens — project notes

Read by the `gw-opt-tokens` skill before proposing anything, and updated when the person approves a change. Created by
the workflow once; from then on it belongs to the project.

## Tools that already save

<!-- One line each, with how to run it. -->
- `python3 .claude/gw/scripts/recover.py --state` and `--search "<text>"`: get back what a compaction dropped.
- `gw-orchestrate-dealer`: multi-step work dealt to clean-context subagents.

## Known costs

<!-- What has been seen to cost a lot in this project (big files read whole, long command outputs...). -->

## Settings in force

- Auto-compaction window: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in `.claude/settings.json`.

## Baselines

<!-- Measured figures to compare against: date, session, average context, calls, total. -->
