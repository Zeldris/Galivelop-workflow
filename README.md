# Galivelop-workflow

[Español](README.es.md)

The Galivelop workshop's way of working with AI coding agents (Claude Code first), extracted from real projects and
generalised for any repository. It is the **single, versioned source** of its skills, hooks, scripts and templates:
an improvement is made once here and reaches every project that uses it.

> **Status: `0.4.2`, stage 1 being run in.** It is already applied to real projects by an AI agent. The `0.4`
> series is the last one before `1.0.0`: from here on only `0.4.x` patches ship, and new work goes into `1.0.0`. See
> the [plan](docs/plan.en.md), the [log](docs/traspaso.md) and the [changelog](CHANGELOG.md).

## What it solves

Working with AI agents brings four problems that show up in every project:

1. **Sessions end.** Because of tokens, the container or an account switch, and the next session doesn't know where
   the last one was.
2. **The choice isn't always right.** An expensive model for a mechanical task, or a cheap one for a task that needs
   judgement.
3. **What the agent calls done isn't always done.** Unreviewed code on the protected branch, tests that pass with
   and without the bug, a CI run that never started.
4. **Token spend grows without anyone measuring it.** Long context is almost all of the cost.

Galivelop-workflow answers all four with written rules and, above all, with **scripts and hooks that enforce them**.

## What makes it different

### Rules are enforced by scripts, not by the agent's good intentions

An agent can forget a rule written in a `.md`; a hook can't. Whatever can be checked is checked by a script, and
skills and guides are left for what needs judgement. If a rule keeps being broken, it becomes a check.

- `pre-push` runs the project's check **on the exact commit being pushed**, not on whatever is in the folder.
- Hooks **fail closed**: if data is missing (no config, no git), they don't let things through.
- The `Stop` hook won't let the agent finish with unpushed commits or with changes the log doesn't mention.

### Real hand-offs between sessions and accounts

- **What isn't pushed doesn't exist.** Commit + push at every stable point, and the log (`docs/traspaso.md`) is
  updated **in the same commit** as the work it describes, never at the end.
- Every commit ends with `Siguiente: <concrete step>` (next step): the next session knows what to do without asking.
- After a compaction or a `/clear`, `recuperar.py` returns the log's state and the latest commits, and finds a lost
  detail in the session transcript without reading it all again.
- **Several sessions at once** (two accounts, one local and one in the cloud): each session has its own branch, and
  with `"logRows": true` each branch writes only to its own row of the log; `pre-push` rejects touching another's.
  Always merge, never rebase, because branches are pushed.

### Nothing unreviewed reaches the protected branch

- **Three phases** before pushing: code review (`/code-review` of the diff against the protected branch),
  environment (`opt-tokens` and `retro`, presented to the person) and closing.
- `revisado.sh` writes a **review mark tied to a specific commit**; without the mark for that same commit, the
  hooks reject the push or the pull request.
- **Code and content are told apart.** Each project declares with regular expressions what is content (docs, data,
  texts, images) and needs no code review; everything else is code and does.
- A Claude Code hook won't create or merge a pull request without a review of that same code, and merging requires
  green CI. **A CI run that never starts** (no quota, no runners) **counts as red**.
- The protected branch is only reached with the person's confirmation.

### Tests that actually prove something

- `rojo-sin-arreglo.sh` checks that a new test **fails without its fix**: a test that passes either way proves
  nothing.
- A test that expects a failure checks **the reason**, not just the exit code.
- `pre-push` can also run the tests related to what changed.

### Token spend is measured, not assumed

- `selector` picks the skill and the model at the start of every task: the person chooses the session's model, and
  subagents get the cheapest one that does the job well.
- `orchestrate-dealer` turns the main session into an orchestrator: it deals work out to clean-context subagents
  and can keep going for hours without `/clear`.
- `opt-tokens` measures in the session transcript where the spend went and proposes environment changes.
- A hook asks the person when a session has launched many subagents, so a loop doesn't burn tokens unseen.
- **Quality first:** a saving that worsens the result is no saving.

### The workflow learns from the projects that use it

- A `retro` that finds a general improvement doesn't patch the local copy, which the next version would overwrite:
  it leaves it in its file under `## For Galivelop-workflow`.
- From this repo, `gw-harvest` (with `recoger.py`) goes through the connected projects and collects, as proposals,
  their edited copies, their new skills and what their retros say. **Nothing is applied without confirmation**: what
  is approved comes in with its CHANGELOG entry and a new version.
- `/gw-update` brings each project up to the new version and **shows the template changes** before applying what the
  person confirms.

### It protects itself

- A hook asks the person for permission before the agent edits the workflow's own configuration.
- `enlaces-md.py` finds broken links and stale references in the Markdown, and `mapa-agente.py` checks that the agent
  map doesn't point at anything that no longer exists.
- The repo itself runs **more than a thousand automated tests**, on Linux and macOS, and is worked on with its own
  workflow: if a rule gets in the way here, it gets in the way in every project.

## What a task looks like

1. **At the start:** the session reads the log, brings in the protected branch (merge, never rebase) and checks the
   check is green before touching anything.
2. **Before working:** `selector` says in one line which skill and model the task needs.
3. **While working:** commit + push at every stable point, never more than 30-45 minutes without pushing, with the
   log in the same commit. Multi-step work goes to subagents with `orchestrate-dealer`.
4. **Before the protected branch:** the three phases, the mark with `revisado.sh`, and the push with the person's
   confirmation.
5. **When a phase closes:** the CI of the last push is checked and, with the log up to date, a `/clear` is
   recommended.

## What's included

### Skills

24 skills in the open [Agent Skills](https://github.com/agentskills/agentskills) format.

**The workflow's own (11):**

| Skill | What for |
|---|---|
| `selector` | Pick the skill and models at the start of every task |
| `orchestrate-dealer` | Deal work out to clean-context subagents and work for hours without `/clear` |
| `opt-tokens` | Measure where a session's spend went and propose how to cut it without worsening results |
| `opt-ai` | Optional: measure latency, quality and configuration of local AI models (Ollama, llama.cpp, vLLM…) per machine |
| `scout-updates` | Optional: look for updates to dependencies, images, CI actions and models in primary sources, as proposals only |
| `gw-init` | Apply the workflow to a new or existing project |
| `gw-update` | Bring a project up to the new version, showing the changes first |
| `gw-doctor` | Check it is set up correctly and explain every failure with its fix |
| `gw-harvest` | Collect as proposals what projects changed or invented |
| `gw-media-content` | Propose posts for the project's social channels |
| `gw-media-content-now` | Produce one specific post, with texts per channel and images |

**By [Matt Pocock](https://github.com/mattpocock) (13):** `codebase-design`, `diagnosing-bugs`, `domain-modeling`,
`grill-with-docs`, `grilling`, `improve-codebase-architecture`, `pr`, `prototype`, `research`, `retro`,
`to-questionnaire`, `wait-what` and `writing-for-agents` (see [Acknowledgements](#acknowledgements)).

### Hooks

- **Git:** `pre-commit` (scans for secrets: `.env` or `.pem` files and known key patterns), `commit-msg` (checks the
  message) and `pre-push` (check on the commit being pushed, review mark and log rules).
- **Claude Code:** recover state at start-up, don't finish without pushing, review before a pull request, warning on
  too many subagents, and a guard on the configuration.

### Scripts

Deterministic, in Python and in bash that runs on macOS's version: `aplicar.py` (set up the workflow), `doctor.py`
(diagnosis with the command that fixes each problem), `revisado.sh` (review mark), `recuperar.py` (state after
`/clear`), `fusionar.sh` (bring in a subagent's branch with a green check and clean up its working copy),
`rojo-sin-arreglo.sh`, `recoger.py` and the checks for links and for the agent map.

### Optional patterns

For cases not every project has ([patterns](docs/en/patterns.md)): a **scheduled weekly task** that updates and
publishes on its own, **two accounts taking turns**, a **local session that can't create PRs** and leaves that to
the cloud one, **social media content**, and **harvesting improvements** back into the workflow.

## How it is applied

- **Stage 1 (today):** an AI agent applies the workflow to your project, new (recommended) or existing, following
  the [apply guide](docs/en/apply.md). It decides with you whatever needs judgement (language, check, protected
  branch, what counts as content…); `scripts/aplicar.py` copies and configures, and `scripts/doctor.py` confirms it
  is set up correctly. In Claude Code, `/gw-init` applies it, `/gw-update` brings it up to date and `/gw-doctor`
  checks it.
- Everything lives **in the project's repo** (`.claude/gw/`, `.claude/skills/`, `.githooks/` and `.claude/gw.json`),
  so it works in cloud sessions too, which don't load plugins.
- What is specific to each project goes in a single file, `.claude/gw.json` ([configuration](docs/en/config.md)).
- Requirements: `git`, `bash` and `python3` 3.8 or later (on Windows, Git Bash or WSL).
- **Stage 2 (later):** automatic installation without AI, for new and existing projects.

The workflow rules live in `AGENTS.md`, an open standard any agent reads; `CLAUDE.md` imports it and adds what is
specific to Claude Code.

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
