# The workflow on one page

> [Español](../es/flujo.md)

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
| Log (`docs/traspaso.md`) | Current state, next step, done and pending; updated in the same commit as the work |
| Skills | How to pick model and skill, orchestrate subagents, review, run retros |
| Hooks | Recover the state after `/clear`; don't push code without review or with the check failing |
| `.claude/gw.json` | What varies between projects (language, log, check, protected branch…) |

## The rules that matter most

1. **What isn't pushed doesn't exist:** commit + push at every stable point.
2. **The log goes in the same commit** as the work it describes.
3. **Last line of the commit:** `Next: <concrete step>` (`Siguiente:` in Spanish projects).
4. **To the protected branch, only with confirmation** and with the diff reviewed.
5. **What can be checked is checked by a script**, not by an agent's opinion.
