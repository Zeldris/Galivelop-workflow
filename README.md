# Galivelop-workflow

[Español](README.es.md)

The Galivelop workshop's way of working with AI coding agents (Claude Code first), extracted from real projects and
generalised for any repository. It is the **single, versioned source** of its skills, hooks, scripts and templates.

> **Status: `0.4.2`, stage 1 being run in.** It is already applied to real projects by an AI agent. The `0.4`
> series is the last one before `1.0.0`: from here on only `0.4.x` patches ship, and new work goes into `1.0.0`. See
> the [plan](docs/plan.en.md), the [log](docs/traspaso.md) and the [changelog](CHANGELOG.md).

## What it solves

1. **Hand-offs without loss.** A session can end at any moment (tokens, container, account switch) and the next one
   carries on without asking: an up-to-date log, commit + push at every stable point, and state recovery after
   `/clear` or a compaction.
2. **Choosing well before starting.** A selector decides which skill and model each task needs, and cheap
   subagents take the mechanical work.
3. **Nothing unreviewed reaches the protected branch.** Three phases before pushing (code review, environment and
   closing), a review mark stored in the repo, and hooks that refuse to push code without it or with a failing check.
4. **Few tokens without losing quality.** Orchestration with subagents, compaction, and retros that measure spending
   and propose improvements.

## What's included

- **24 skills** in the open [Agent Skills](https://github.com/agentskills/agentskills) format: 11 of its own
  (`selector`, `orchestrate-dealer`, `opt-tokens`, `opt-ai`, `scout-updates` and the `gw-*` ones: `gw-init`,
  `gw-update`, `gw-doctor`, `gw-harvest`, `gw-media-content` and `gw-media-content-now`) and 13 by Matt Pocock (see
  [Acknowledgements](#acknowledgements)).
- **Git hooks:** `pre-commit` (scans for secrets before every commit), `commit-msg` (checks the message) and
  `pre-push` (runs the project's check on the commit being pushed and requires the review mark for the protected
  branch).
- **Claude Code hooks:** recover the log's state when a session starts and guard pushes to the protected branch.
- **Deterministic scripts** (Python, and bash that runs on macOS): `aplicar.py` sets it up in a project, `doctor.py`
  says what is missing and which command fixes it, and `revisado.sh` writes the review mark.
- **Templates** for what gets copied into the project: rules, log and configuration.

## How it is applied

- **Stage 1 (today):** an AI agent applies the workflow to your project, new (recommended) or existing, following
  the [apply guide](docs/en/apply.md). It decides with you whatever needs judgement; `scripts/aplicar.py` copies and
  configures, and `scripts/doctor.py` confirms it is set up correctly. In Claude Code, `/gw-init` applies it,
  `/gw-update` brings it up to a new version and `/gw-doctor` checks it.
- Everything lives **in the project's repo** (`.claude/gw/`, `.claude/skills/`, `.githooks/` and `.claude/gw.json`),
  so it works in cloud sessions too.
- Requirements: `git`, `bash` and `python3` 3.8 or later (on Windows, Git Bash or WSL).
- **Stage 2 (later):** automatic installation without AI, for new and existing projects.

The workflow rules live in `AGENTS.md` (an open standard any agent reads).

## Documentation

- [Workflow overview](docs/en/workflow.md)
- [Applying it to a project](docs/en/apply.md) · [Configuration](docs/en/config.md) · [Patterns](docs/en/patterns.md)
- [Troubleshooting](docs/en/troubleshooting.md) · [Changing the workflow](docs/en/contributing.md)
- [Plan](docs/plan.en.md) · [Agent map](docs/mapa-agente.md) · [Changelog](CHANGELOG.md)

## Acknowledgements

We learned to work this way from **[Matt Pocock](https://github.com/mattpocock)**'s work, above all his
[mattpocock/skills](https://github.com/mattpocock/skills): the idea of steering agents with small, well-written
skills, the review-and-retro loop, and many of the skills shipped here, which are his (MIT), credited in each one and
listed in [`CREDITS.md`](CREDITS.md). Thank you, Matt.

## Licence

[MIT](LICENSE). Skills from [mattpocock/skills](https://github.com/mattpocock/skills) keep their MIT licence
([`LICENSE-mattpocock-skills`](LICENSE-mattpocock-skills)); see [`CREDITS.md`](CREDITS.md).
