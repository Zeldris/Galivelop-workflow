# Galivelop-workflow

[Español](README.es.md)

The Galivelop workshop's way of working with AI coding agents (Claude Code first), extracted from real projects and
generalised for any repository. It is the **single, versioned source** of its skills, hooks and templates.

> **Status: `0.1.0`, under construction (stage 1, phase 1).** Not ready to apply yet. See the
> [plan](docs/plan.en.md) and the [log](docs/traspaso.md).

## What it solves

1. **Hand-offs without loss.** A session can end at any moment (tokens, container, account switch) and the next one
   carries on without asking: an up-to-date log, commit + push at every stable point.
2. **Choosing well before starting.** A selector decides which skill and model each task needs, and cheap
   subagents take the mechanical work.
3. **Nothing unreviewed reaches `main`.** Code review of the diff, a review mark stored in the repo, and hooks that
   refuse to push code without it.
4. **Few tokens without losing quality.** Orchestration, compaction, recovery after `/clear`, and retros that
   measure and propose improvements.

## How it will be applied

- **Stage 1:** an AI agent applies the workflow to your project by reading this repo (guide + templates +
  deterministic scripts), and a `doctor` script confirms it is set up correctly.
- **Stage 2:** automatic installation without AI, for new projects (recommended) and existing ones.

The workflow rules live in `AGENTS.md` (an open standard any agent reads); skills follow the open
[Agent Skills](https://github.com/agentskills/agentskills) format.

## Documentation

- [Workflow overview](docs/en/workflow.md)
- [Applying it to a project](docs/en/apply.md) · [Configuration](docs/en/config.md) · [Patterns](docs/en/patterns.md)
- [Troubleshooting](docs/en/troubleshooting.md) · [Changing the workflow](docs/en/contributing.md)
- [Plan](docs/plan.en.md) · [Changelog](CHANGELOG.md)

## Acknowledgements

We learned to work this way from **[Matt Pocock](https://github.com/mattpocock)**'s work, above all his
[mattpocock/skills](https://github.com/mattpocock/skills): the idea of steering agents with small, well-written
skills, the review-and-retro loop, and many of the skills shipped here, which are his (MIT), credited in each one and
listed in [`CREDITS.md`](CREDITS.md). Thank you, Matt.

## Licence

[MIT](LICENSE). Skills from [mattpocock/skills](https://github.com/mattpocock/skills) keep their MIT licence
([`LICENSE-mattpocock-skills`](LICENSE-mattpocock-skills)); see [`CREDITS.md`](CREDITS.md).
