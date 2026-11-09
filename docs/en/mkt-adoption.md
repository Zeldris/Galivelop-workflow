# Galivelop-workflow for your team

[Español](../es/mkt-adoption.md)

A workflow for coding with AI agents (Claude Code first), drawn from real projects: **skills, hooks, scripts and
templates** installed in your repository that enforce the rules instead of trusting the agent to remember them.

## What it solves

- **Sessions end:** the log `docs/handoff.md` and the `Siguiente:` (next step) trailer of every commit let the next
  session carry on without asking.
- **What the agent calls done is not always done:** the `pre-push` runs your check on the exact commit being pushed,
  and the protected branch requires a review mark tied to that commit (`reviewed.sh`).
- **Token spend grows unmeasured:** `gw-selector` picks the skill and model per task, `gw-orchestrate-dealer` deals
  work out to clean-context subagents and `gw-opt-tokens` measures where the spend went.

## What gets installed

| Piece | What it does |
|---|---|
| Git hooks | `pre-commit` (secrets), `commit-msg` (format and traces), `pre-push` (check, private data, review) |
| Claude Code hooks | State at start, no ending without pushing, review before a PR, subagent cap |
| Skills | 26, in the open Agent Skills format: 11 of its own (`gw-*`) and 15 by Matt Pocock |
| Scripts | Deterministic, in Python 3.8+ and bash 3.2: `apply.py`, `doctor.py`, `check.sh`, `handoff.py`, `version.py`… |
| Configuration | A single file, `.claude/gw.json`: language, check, protected branch, what is content and what is code |

Everything lives **inside your repository** (`.claude/gw/`, `.claude/skills/`, `.githooks/`), so it also works in
cloud sessions that do not load plugins.

## How to apply it

1. Requirements: `git`, `bash` and `python3` 3.8 or later (on Windows, Git Bash or WSL).
2. In Claude Code, `/gw-init`: the agent decides with you what needs judgement and `apply.py` copies and configures.
3. `/gw-doctor` checks it is set up right and gives the command that fixes each failure.
4. `/gw-update` brings the project to each new version and shows the changes before applying them.

The hooks **fail closed** when a piece of data is missing, and the repo itself passes more than a thousand tests on
Linux and macOS.

Code, docs and releases: [github.com/Zeldris/Galivelop-workflow](https://github.com/Zeldris/Galivelop-workflow).
