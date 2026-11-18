# The workflow on one page

> [Español](../es/workflow.md)

A summary for people. The detail will grow in this folder as the workflow is built (plan §9).

## The idea

A session with an agent can end at any moment. The workflow is designed so that the next session, from the same
account or another one, carries on **without losing anything and without asking where things stood**, and so that
nothing unreviewed reaches the protected branch.

## The pieces

| Piece | What for |
|---|---|
| `AGENTS.md` | Workflow rules for any agent: session start, hand-offs, commits, branches |
| `CLAUDE.md` | `@AGENTS.md` + Claude Code-specific bits |
| Log (`docs/handoff.md`) | Current state, next step, done and pending; updated in the same commit as the work |
| Skills | How to pick model and skill, orchestrate subagents, review, run retros |
| Hooks | Recover the state after `/clear`; don't push code without review or with the check failing |
| Metrics (`docs/metrics/ledger.jsonl`) | Token spend by model, agent, branch and task; period reports (`gw-metrics`) and quality signals next to the spend |
| `.claude/gw.json` | What varies between projects (language, log, check, protected branch…) |

## Where it comes from

From the Galivelop workshop's projects and, before that, from **Matt Pocock**'s work
([mattpocock/skills](https://github.com/mattpocock/skills)), from whom we learned this way of working with agents.
His skills included here carry his credit and licence ([credits](../../CREDITS.md)).

## The rules that matter most

1. **What isn't pushed doesn't exist:** commit + push at every stable point.
2. **The log goes in the same commit** as the work it describes.
3. **Last line of the commit:** `Next: <concrete step>` (`Siguiente:` in Spanish projects).
4. **To the protected branch, only with confirmation** and with the diff reviewed: serious or medium findings are
   fixed; minor ones are logged as pending and not reviewed again in that PR. Each finding cites its anchor (a rule,
   an acceptance criterion of the task record, a plan line or a demonstrated failure) in the format
   `path:line | severity | anchor | problem. fix.`; with no anchor it goes to «Observations», with no severity.
5. **What can be checked is checked by a script**, not by an agent's opinion.

## The task record

With `taskRecord.enabled` ([`config.md`](config.md)), every task with code has a record `docs/tasks/<id>.md`
(`python3 .claude/gw/scripts/task.py new <id>`): `Goal`, `Scope`, `Acceptance` (checkboxes), `Files`, `Change log` and
`Verification`. Each agent that touches the task also adds a new entry in `docs/tasks/<id>/`
(`task.py log <id> --agent <skill|session>`) with three sections: `Why`, `Alternatives` and `Changed because`; nobody
edits an entry once pushed. The `commit-msg` asks, for at least one id of `Refs:`, for the record (it must exist, not be edited) and a new valid entry in a `feat`, `fix` or `hotfix` commit that changes code
(not in `docs`, `WIP:`, merges or the review mark); an `--amend` adds no file, so add an entry first with `task.py log`. The commit of each entry is not written into the file:
`task.py resolve <id>` reads it from git.

## Guides

- [Applying the workflow to a project](apply.md) (the agent's guide, new and existing projects)
- [Configuration: `gw.json`](config.md)
- [The workflow from opencode and Codex](other-agents.md)
- [Optional patterns](patterns.md)
- [Troubleshooting](troubleshooting.md)
- [Changing the workflow](contributing.md)
