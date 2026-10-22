# Galivelop-workflow — repository creation plan

> Document for the Claude session that will create the repo. Read it in full before starting and follow it phase
> by phase: each phase ends with commit + push and its box ticked in the new repo's `docs/traspaso.md`.
> Written on 2026-10-21 from the workflow in use in **Portal-Galivelop** and **World-Maker-Fantasy (Tarkor)**.
> Spanish version: `plan.md` (same content).
> **Revised on 2026-10-21 when closing Phase 0** with the user's decisions (§0). Research in `docs/investigacion/`.

## 0. Changes after Phase 0 (user decisions, 2026-10-21)

1. **Two stages.** *Stage 1:* an AI agent applies the workflow to a project by reading this repo (agent guide +
   templates + deterministic scripts). *Stage 2:* automatic installation **without AI**, for new projects (the
   recommended case) and existing ones. Stage 2 does not start until stage 1 is stable in the pilots.
2. **The workflow is copied into the target repo** (skills, scripts and hooks, versioned) as the base path: it is
   what an agent does when applying it, and it works in the cloud, which **does not load plugins declared in the
   repo** (verified). The plugin and marketplace become an optional stage-2 path (local, or the cloud environment's
   setup script).
3. **Workflow rules in `AGENTS.md`** (open standard, valid for any agent); `CLAUDE.md` = `@AGENTS.md` + Claude-specific
   bits.
4. **`gw.json` keys in English**; **`check` is a list of commands**; **review mark committed** to the repo for both
   push modes.
5. **Port piece by piece** from the repo that has the best version of each (table in
   `docs/investigacion/casos-reales.md`), not "from the portal".
6. **This repo uses its own workflow** from Phase 1, applied as a copy like in any project.
7. **Skills follow the Agent Skills specification** (`name`, `description`, `license`, `compatibility`,
   `metadata.version`); checkable things are done by scripts (e.g. `doctor`), not skills.
8. **Harvesting improvements from projects** (user, 2026-10-21): a `gw-harvest` skill (§5.1) that reviews the
   connected repos using the workflow and records their changes, new skills and ideas as proposals.


## 1. What it is and why

**Galivelop-workflow** is the Galivelop workshop's way of working with Claude Code, extracted from its projects
and generalised for any repository. It is the **single, versioned source** of its skills, hooks and templates: an
improvement is made here once, bumps the version and reaches every project, instead of being copied by hand repo
by repo (which is how it works today: Portal and Tarkor each have their own copy and they already diverge).

What the workflow solves:

1. **Hand-offs without loss.** A session can end (tokens, container, account switch) and the next one carries on
   without asking: an up-to-date log, commit + push at every stable point, "what isn't pushed doesn't exist".
2. **Choosing well before starting.** A `selector` decides which skill and model each task needs, and a subagent
   ladder hands mechanical work to cheap models.
3. **Nothing unreviewed reaches `main`.** `/code-review` of the diff, a review mark stored in the repo, and hooks
   that refuse to push code without it or with the check failing.
4. **Spending few tokens without losing quality.** `orchestrate-dealer`, compaction at 200k, recovery after
   `/clear`, and `opt-tokens` + `retro`, which measure and propose environment improvements.

**End of the road:** after a long run-in on real projects and with the criteria in §10 met, the repo goes public,
is published on the Galivelop portal as a project (page in Spanish, Galician and English), and publishing it on npm
is considered.

## 2. Decisions already made (by the user, 2026-10-21)

| Decision | Value |
|---|---|
| Repo name | `Galivelop-workflow` (private until §10) |
| Languages | **Spanish and English** (see §4.4) |
| Distribution | The most convenient and clean: **a Claude Code plugin served from the repo itself as a marketplace**. npm considered at the end |
| Versioning | The repo is the version point for all skills and improvements |
| Publishing | Public + Galivelop page only once the workflow is proven 100 % functional and applicable to any system |

> **Revised in §0:** the base distribution is the managed copy; the plugin stays as a stage-2 option.

**Why a plugin and not a file-copying script** (original reasoning): the plugin comes with versioning, updates (`/plugin update`) and
uninstall out of the box; skills are not duplicated in every repo; and in a project a single entry in
`.claude/settings.json` makes any session (cloud included) load it. What **cannot** live in the plugin (git hooks,
`CLAUDE.md`, the log, project-specific bits) is created in the target repo by a bootstrap skill, `/gw-init`, and
maintained by `/gw-update` (§5.4).

## 3. Inventory: what comes from where

Main source: **Portal-Galivelop** (the most recent, already-fixed version: 29 hook bugs fixed in its 2026-10-21
retro). Tarkor contributes what the portal dropped as "small-website-irrelevant" (milestone roadmap).
**Both repos are read-only; never modify them from the session that creates this one.**

| Piece | Source (path in Portal-Galivelop) | Generalisation |
|---|---|---|
| `selector` | `.claude/skills/selector/SKILL.md` | Remove portal cases (routes, SEO, three languages). Generic table + extra rows the project declares in its config (§6) |
| `orchestrate-dealer` | `.claude/skills/orchestrate-dealer/SKILL.md` | Brief template with `{check}`, `{log}` and the project's languages instead of fixed ones |
| `opt-tokens` + `medir.py` | `.claude/skills/opt-tokens/` | `medir.py` as is (already generic) with `QA-*` references cleaned; `proyecto.md` becomes a target-repo file (`.claude/gw/opt-tokens.md`) |
| `retro` | `.claude/skills/retro/SKILL.md` | Keep the MIT body; the "In this repository" note becomes generic (review the plugin's skills and propose changes **to the plugin** when an improvement is general) |
| `grilling`, `grill-with-docs`, `domain-modeling`, `diagnosing-bugs`, `codebase-design`, `improve-codebase-architecture`, `writing-for-agents`, `pr`, `prototype`, `research` | `.claude/skills/*` | As is (MIT, mattpocock/skills). Only the portal notes are removed. Licence and credits kept |
| Workflow runbook | `docs/runbooks/skills-y-modelos.md` | Becomes the plugin's generic `docs/<lang>/workflow.md` |
| `REVIEW.md` | `REVIEW.md` | Target-repo template with the generic sections ("One fact, one place", "Hooks and scripts") and slots for project rules |
| `GLOSSARY.md` | `GLOSSARY.md` | Empty template with the workflow's terms (log, stable point, review mark…) |
| `CLAUDE.md` | root of both repos | Template: "At the start of every session", hand-off and commit rules, with `{{…}}` slots |
| Log | `docs/traspaso.md` (portal) and `docs/registros/traspaso.md` (Tarkor) | Template with the portal's sections: Current state · For the next release · Done (last 10) · Pending · Check the state |
| `SessionStart` hook | `.claude/hooks/session-start.sh` | To the plugin. Sets `core.hooksPath`, installs dependencies in the cloud with the config's command |
| Recovery after `/clear` | `tools/qa/recuperar.py` | To the plugin; reads the log path from the config |
| PR-to-`main` hook | `.claude/hooks/revision-antes-de-main.sh` | To the plugin; protected branch and mark path from the config |
| `pre-push` | `.githooks/pre-push` | Template copied into the target repo by `/gw-init` (git cannot load it from the plugin): check of the pushed commit + review mark for `main` |
| `es-codigo.sh`, `revisado.sh` | `tools/qa/` | To the plugin; "content" patterns come from the config |
| Hook tests | `tools/qa/tests/test-ganchos.sh` | To the plugin, extended to run against a temporary test repo |
| Roadmap and milestones (optional) | Tarkor: `tools/roadmap/cobertura.py`, `docs/producto/21-roadmap.md` | Optional module enabled in the config (`roadmap: true`) |
| Per-branch log | Installer: `tools/qa/bitacora.py`, `tools/qa/prepush-ramas.sh` | One row per branch; character limit and plan path configurable |
| QA utilities | Tarkor/installer: `fusionar.sh`, `rojo-sin-arreglo.sh`, `tests-relacionados.sh`, `enlaces-md.py` | Generic; the related-tests command comes from the config |
| Closing tasks | Tarkor: `tools/roadmap/cerrar.py` | Part of the `roadmap` module |
| Retro required before the mark | Tarkor/installer: `revisado.sh` | Config option (`requireRetro`) |
| `scout-updates` | Tarkor: `.claude/skills/scout-updates/` | Optional skill (on request only) |
| `opt-ai` + `medir.py` | Tarkor/installer: `.claude/skills/opt-ai/` | Optional skill for projects with local AI models; project specifics in `.claude/gw/opt-ai.md` |

> **Source per piece (Phase 0):** the "best version of each piece" table in `docs/investigacion/casos-reales.md`
> overrides the "Source" column above.

**Not brought over:** project-specific material (the portal's three languages, Tarkor's lore, the concrete weekly
task, play-test rounds). `opt-ai` and `scout-updates` are brought over as optional skills (table above). The **weekly scheduled task** is documented as an optional
pattern in `docs/<lang>/patterns.md`, without a concrete prompt.

## 4. Repository layout

```text
Galivelop-workflow/
├── AGENTS.md                     # workflow rules for working ON this repo (any agent)
├── .claude-plugin/               # kept valid; optional stage-2 path
│   ├── marketplace.json          # the repo is its own marketplace (one plugin)
│   └── plugin.json               # name, version (semver: the single source), description, author, licence
├── skills/                       # one folder per skill, SKILL.md in English (§4.4)
│   ├── selector/  orchestrate-dealer/  opt-tokens/  retro/  pr/
│   ├── grilling/  grill-with-docs/  domain-modeling/  diagnosing-bugs/
│   ├── codebase-design/  improve-codebase-architecture/  writing-for-agents/
│   ├── prototype/  research/
│   ├── gw-init/                  # bootstraps the workflow in a repo (§5.4)
│   ├── gw-update/                # brings the repo's templates up to the plugin version
│   ├── gw-doctor/                # checks the workflow is set up correctly
│   └── gw-harvest/               # records changes from repos using the workflow as proposals
├── hooks/
│   └── hooks.json                # SessionStart (startup|resume|clear, clear|compact) and PreToolUse (PR to main)
├── scripts/                      # called by hooks and skills; root via ${CLAUDE_PLUGIN_ROOT}
│   ├── session-start.sh  revision-antes-de-main.sh
│   ├── recoger.py                # deterministic part of gw-harvest
│   ├── recuperar.py  medir.py  es-codigo.sh  revisado.sh  bitacora.py  prepush-ramas.sh
│   ├── doctor.py                 # deterministic workflow check (used by gw-doctor and CI)
│   ├── aplicar.py                # copies templates, skills and scripts without overwriting (stage 1, base of 2)
│   └── config.py                 # reads and validates the project's .claude/gw.json (the only reader)
├── templates/                    # what /gw-init copies into the target repo, in es/ and en/
│   ├── es/  AGENTS.md  CLAUDE.md  REVIEW.md  GLOSSARY.md  traspaso.md  opt-tokens.md
│   ├── en/  (the same)
│   ├── githooks/pre-push
│   ├── github/comprobar.yml      # minimal CI: the project's check
│   └── gw.json                   # sample config, commented in the README
├── schema/gw.schema.json         # JSON Schema for the config
├── tests/
│   ├── test-ganchos.sh           # creates a temporary git repo and tests every hook and script
│   └── test-plantillas.sh        # /gw-init on an empty repo yields what is expected; idempotent
├── docs/
│   ├── es/  flujo.md  aplicar.md  instalar.md  config.md  patrones.md  problemas.md  contribuir.md
│   └── en/  workflow.md  apply.md  install.md  config.md  patterns.md  troubleshooting.md  contributing.md
├── CLAUDE.md                     # @AGENTS.md + Claude-specific bits
├── .claude/  .githooks/          # the workflow applied to this repo (copy generated by scripts/aplicar.py)
├── docs/traspaso.md              # its log
├── REVIEW.md  GLOSSARY.md
├── README.md  (en)   README.es.md
├── CHANGELOG.md                  # Keep a Changelog, bilingual per entry
├── LICENSE                       # MIT (compatible with mattpocock's skills)
├── LICENSE-mattpocock-skills  CREDITS.md
└── .github/workflows/
    ├── comprobar.yml             # shellcheck, tests, JSON validated against schema, plugin.json == latest CHANGELOG entry
    └── release.yml               # on tag vX.Y.Z: checks the version and creates the release from its CHANGELOG entry
```

### 4.1 The repo uses its own workflow

From Phase 1 on, the repo is worked on with its own workflow, **applied exactly as in any project**: `AGENTS.md`,
`CLAUDE.md`, the log and, as they are built, the copy of skills in `.claude/skills/`, scripts in `.claude/gw/` and
hooks. That copy is generated by `scripts/aplicar.py` from `skills/` and `scripts/`, and a test checks it doesn't
drift. That is the first run-in test: if something in the workflow gets in the way here, it gets in the way
everywhere.

### 4.2 Names

- Project and plugin: `galivelop-workflow`. Copied into the target repo, skills are called by their name
  (`selector`); via the plugin, `galivelop-workflow:selector`.
- Management skills carry the `gw-` prefix so they don't clash with project skills.
- Project config: `.claude/gw.json`. Workflow-owned files in the target repo: `.claude/gw/` (scripts) and
  `.claude/skills/<skill>/` (skills). Everything copied carries its version (`metadata.version` in skills, a
  `galivelop-workflow vX.Y.Z` header in scripts and templates).

### 4.3 Paths

Every script takes its own root from its path (`$(dirname "$0")`) or `${CLAUDE_PLUGIN_ROOT}`, and the project's
from `git rev-parse --show-toplevel`. In `.claude/settings.json`, `$CLAUDE_PROJECT_DIR` is only used to **locate**
the script; inside it, the root is computed as just described, **never** from `$CLAUDE_PROJECT_DIR` or the current directory: in the cloud
the session may start in `/home/user` (portal lesson, `REVIEW.md` § "Hooks and scripts").

### 4.4 Languages: Spanish and English

- **Human documentation** (README, `docs/`, CHANGELOG, templates): in both languages. `README.md` in English
  (what GitHub and npm show) with a link to `README.es.md` at the top; parallel `docs/es/` and `docs/en/`. A test
  checks every file in `docs/es/` has its pair in `docs/en/` and vice versa.
- **Skills (`SKILL.md`)**: in **English, one version only**. They are loaded into the agent's context; duplicating
  them doubles their cost. mattpocock's skills are already in English. The agent replies in the project's
  language (`language` in the config), as the generated `CLAUDE.md` states.
- **Templates**: `/gw-init` copies those in `templates/<language>/` according to the config.
- **Script messages**: in English, with the exact command that fixes the failure.

## 5. Components in detail

### 5.1 Skills

Every `SKILL.md` under 200 lines (`writing-for-agents`), with `name` and a `description` that says **when** to use
it. mattpocock's keep their text; the own ones are rewritten generically:

- **`selector`**: table of generic cases (design, bug, large change, scoped change, mechanical, bringing from
  another repo, review before `main`, closing a block, writing for agents) with skill, session model and subagent
  model. Rules: the user picks the session model and Claude states it in one line; subagent ladder
  `sonnet low → sonnet medium → opus medium → opus high`, two failures and it stops; when in doubt, the
  higher-risk row. Reads extra rows from `selector.cases` in the config.
- **`orchestrate-dealer`**: the main session plans, decides and reviews; subagents read, implement chunks and
  push. Brief template with pointers, a done criterion and a ≤15-line reply
  (`DONE · COMMIT · MISSING · QUESTIONS`). One at a time on the same branch if they write.
- **`opt-tokens`**: as in the portal ("quality first", average context × calls dominates). Project-specific
  material in `.claude/gw/opt-tokens.md`.
- **`retro`**: gains a new outlet: if an improvement applies to any project, the proposal is an **issue or PR on
  the `Galivelop-workflow` repo**, not a local patch. That way the workflow learns from every project.
- **`gw-harvest`** (used from this repo; the "pull" that complements `retro`'s "push"): for each repo connected to
  the session that has `.claude/gw.json`, it collects what is new since the last harvest:
  - **local changes to workflow pieces** (skills, scripts, templates): the copy compared with the workflow version it
    was applied with (`metadata.version` and headers);
  - **new skills** born in the project (in `.claude/skills/` and not part of the workflow);
  - **general ideas and improvements** in its retros and its log.

  The mechanical part (which files differ, which skills are new, which commits since last time) is done by
  `scripts/recoger.py`, without AI; the agent only judges whether each change is general or project-specific and
  writes it up. Output: `docs/propuestas/YYYY-MM-DD-<repo>.md` (source with path and commit, what changes,
  general/specific, version bump it would need: patch, minor or major), and the last harvested commit per repo in
  `docs/propuestas/estado.json`. **It never applies anything without confirmation**: what is approved goes in as a
  normal change, with a CHANGELOG entry and a new version. Repos are read-only, via a subagent.
- **`gw-init`, `gw-update`, `gw-doctor`**: see §5.4.

### 5.2 Claude Code hooks (`hooks/hooks.json`)

| Event | What it does |
|---|---|
| `SessionStart` (`startup\|resume\|clear`) | `session-start.sh`: `core.hooksPath=.githooks` if none is set, cloud dependencies (config `install`, only if `CLAUDE_CODE_REMOTE=true` and the lockfile changed), warning if `gw.json` is missing or the copied version lags behind the workflow's |
| `SessionStart` (`clear\|compact`) | `recuperar.py --estado`: the log's state row, `git status`, latest commits, how to search for a detail |
| `PreToolUse` (`create_pull_request\|merge_pull_request` from the GitHub MCP and `gh pr create\|merge` via Bash) | `revision-antes-de-main.sh`: blocks without a review mark for the same code or with CI not green. Fails closed |

### 5.3 Git hooks and CI (in the target repo)

- `.githooks/pre-push` (copied by `/gw-init`, with a `# galivelop-workflow vX.Y.Z` header): runs the config's
  `check` **on the commit being pushed** (temporary worktree if it isn't the working copy); to the protected
  branch, requires the review mark if it brings code. `--no-verify` only for a red `WIP:`.
- Review mark: `revisado.sh` writes the sha to the config's `reviewMark` (default `docs/registros/revisado.txt`) and
  commits it. It travels with the repo, so scheduled tasks and other accounts see it.
- `es-codigo.sh`: "code" is everything that doesn't match the config's `content`. Only code needs review.
- `.github/workflows/comprobar.yml`: `install` + `check` on every push not to the protected branch and on every PR.

### 5.4 Apply, update and check

- **`docs/<lang>/apply.md` (stage 1):** the guide an agent follows to apply the workflow. It separates what needs
  judgement (inferring `install`/`check` from `package.json`, `pyproject.toml`, `Cargo.toml`, `Makefile`…; merging an
  existing `CLAUDE.md`/`AGENTS.md`, showing the block first) from the mechanical part, which is always a script.
- **`scripts/aplicar.py`:** writes `.claude/gw.json`, copies templates, skills and scripts **without overwriting
  anything** (what exists is left as a `*.gw-nuevo` proposal to review), adds the hooks to `.claude/settings.json` and
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`, and sets `core.hooksPath` if no other manager owns it. Idempotent. Commit
  `Galivelop-workflow vX.Y.Z workflow` with a `Next:` line.
- **`/gw-init`, `/gw-update`** (skills with `disable-model-invocation: true`): thin wrappers over `apply.md` and
  `aplicar.py`. `gw-update` compares versions and shows the diff of the template change (not of the file the project
  filled in) before applying what the user confirms.
- **`scripts/doctor.py`** (and `/gw-doctor`, which calls it): checks and lists, with the fixing command for each:
  config valid against the schema, `core.hooksPath` and coexistence with other hook managers, `pre-push` executable
  and current, log with its sections, `check` commands exist, CI present, copy not drifted.

## 6. Project config: `.claude/gw.json`

Everything that varies between projects, and nothing else. Only `scripts/config.py` reads it (one fact, one place).
Keys in English (Phase 0 decision).

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/zeldris/Galivelop-workflow/v1.0.0/schema/gw.schema.json",
  "version": "0.1.0",                       // workflow version it was applied with
  "language": "es",                         // es | en: templates and reply language
  "visibleLanguages": ["es", "gl", "en"],   // optional: what REVIEW.md requires of visible text
  "log": "docs/traspaso.md",
  "logRows": false,                         // optional: one row per branch with a limit (bitacora.py)
  "protectedBranch": "main",
  "pushToProtected": "direct",              // direct | pr: direct push (pre-push asks for the mark in both) or PR (PreToolUse too)
  "install": ["npm ci"],
  "check": ["npm run check"],               // list of commands, run in order on the commit being pushed
  "reviewMark": "docs/registros/revisado.txt",
  "requireRetro": true,                     // optional (on in the template): revisado.sh requires a retro on the branch
  "content": ["^docs/", "^public/", "^src/data/", "\\.md$"],   // regex: what does NOT need /code-review
  "roadmap": false,                         // optional milestones module (Tarkor)
  "selector": { "cases": [] },              // extra project-specific rows
  "designReferences": [],                   // optional: what design is contrasted with (grilling, selector)
  "protectedPaths": [],                     // optional: paths an agent may not commit (pre-commit)
  "staleRefs": [],                          // optional: patterns that must not appear in docs/ (enlaces-md.py)
  "plan": [], "taskId": "[A-Z]{2,5}-\\d+",   // optional: plan with ticks and task ids (bitacora.py)
  "relatedTests": { "fast": [], "slow": [] } // optional: tests of what changed, in pre-push
}
```

Examples the pilots must cover: the portal (Node, direct push, three visible languages), Tarkor (backend + frontend,
milestone roadmap, several accounts, PR) and the Tarkor installer (Rust/Tauri: the non-Node case).

## 7. Versioning

- **SemVer** in `plugin.json`. Major: the config or a template changes in a way that requires touching the target
  repo. Minor: new skill or hook, or a compatible improvement. Patch: fixes.
- **`CHANGELOG.md`** (Keep a Changelog), one entry per version with `### ES` and `### EN`. CI fails if the
  `plugin.json` version has no entry.
- **Tags `vX.Y.Z`** and a GitHub release with the CHANGELOG entry (`release.yml`).
- **`main` branch = latest published version**; work happens on branches and goes to `main` only with
  confirmation (the workflow itself).
- **Pinning a version in a project**: add the marketplace with `#vX.Y.Z` when a project doesn't want automatic
  updates. Normal case: follow `main` and `/plugin update`.
- Version `0.x` throughout the run-in; `1.0.0` only once §10 is met.

## 8. Installing in a project

**Stage 1 (what `docs/<lang>/apply.md` will say):** from a session with the project and this repo at hand, ask the
agent to "apply Galivelop-workflow following `docs/en/apply.md`". The agent decides what needs judgement, runs
`scripts/aplicar.py` and finishes with `scripts/doctor.py` green. It works in the cloud with no setup, because the
result lives in the repo.

**Stage 2 (what `docs/<lang>/install.md` will say):** installation without AI, e.g. with Copier (three-way merge for
updates) or an own script needing only git, bash and python3; decided in its phase. Optional paths: the plugin from
the repo's marketplace (local) or installed by the cloud environment's setup script.

The installer covers **both things, installing and updating**, with a single command that looks at the project and
decides:

- **Install:** the project has no workflow (new, or existing without it): it creates `.claude/gw.json` and copies
  everything without overwriting what already exists.
- **Update:** the project already has `.claude/gw.json`: it moves the workflow from its `version` to the new one,
  keeps what is the project's own and marks the conflicts.
- **Older copy without `gw.json`** (like VeriNews_AI, or the pilots before applying the workflow): treated as an
  update that replaces that copy; never as a clean install that duplicates it.

Both paths have their tests and are tried on the pilots.

```text
claude plugin marketplace add zeldris/Galivelop-workflow
claude plugin install galivelop-workflow@galivelop-workflow
```

> Verified in Phase 0 (`docs/investigacion/plugins.md`): a private repo can be added as a marketplace from the CLI,
> in the cloud too; the cloud does **not** load what the repo's `.claude/settings.json` declares; a plugin installed
> before Claude starts does load.

## 9. Build phases

Each phase: working branch, steps with commit + push at every stable point, log in the same commit, tests green,
and on closing `/code-review` before going to `main` (with confirmation). Model per the `selector`: design and hooks
with the large model; porting skills and templates with the medium one. From Phase 1, all with the workflow itself
(§4.1).

**Stage 1 — applicable by an agent**

| Phase | What | Done when |
|---|---|---|
| **0. Verify** ✅ | Official docs on plugins, marketplaces and hooks; cloud tests; three real cases; standards | §0 decided; notes in `docs/investigacion/` |
| **1. Skeleton** | `LICENSE`, `AGENTS.md` + `CLAUDE.md`, README ES/EN, log, CHANGELOG `0.1.0`, valid `.claude-plugin/`, CI (shellcheck, JSON, ES/EN pairs, version == CHANGELOG) | CI green and the repo worked on with its own `AGENTS.md` |
| **2. Skills** | Port the skills (§3) piece by piece, with Agent Skills fields and a test that validates them; `gw-harvest` + `scripts/recoger.py` | All validate; `writing-for-agents` applied to the own ones; licences and credits; `gw-harvest` collects real proposals from Tarkor, the installer, the portal and VeriNews |
| **3. Hooks and scripts** | `config.py`, `doctor.py`, `session-start.sh`, `recuperar.py`, `revision-antes-de-main.sh`, `es-codigo.sh`, `revisado.sh`, `bitacora.py`, `prepush-ramas.sh`, `medir.py`, `pre-push` template. Tests against a temporary repo: the 29 bugs' categories, shallow clone, conflict markers, another hook manager. Applied to this repo | Tests green on Linux and macOS; fail closed without config |
| **4. Templates and apply** | `templates/es` and `templates/en`, `gw.schema.json`, `aplicar.py`, `apply.md`, `gw-init`, `gw-update`, `test-plantillas.sh`, `troubleshooting.md` | An agent applies the workflow to an empty repo and `doctor.py` accepts it; twice changes nothing |
| **5. Pilot: Portal-Galivelop** | In a portal session (with permission): an agent applies it following `apply.md` and replaces its copy | `npm run check` green, `pre-push` and mark working, weekly task unchanged |
| **6. Pilot: Tarkor and installer** | Same in World-Maker-Fantasy (`roadmap: true`, PR) and Instalador-WMF-Tarkor (Rust). VeriNews_AI (Java + Vite) moves to Phase 8, with no AI agent | Hand-off between accounts with nothing lost; gaps come back as a new version |
| **7. Stage-1 run-in** | Weeks of real use; every `retro` with a general improvement → issue/PR here | §10 criteria for stage 1 |

**Stage 2 — automatic installation without AI**

| Phase | What | Done when |
|---|---|---|
| **8. Installer** | Choose Copier or an own script; one command that **installs** (new project, or existing one without the workflow: no overwrites, conflicts marked) or **updates** (with `gw.json`, or an older copy without it) depending on what it finds (§8) | Install without AI on a new repo; update without AI the pilots (from their version to the new one) and VeriNews_AI (older copy without `gw.json`); `doctor.py` green |
| **9. Plugin and npm** | The repo's marketplace as an optional path (local and cloud setup script); consider npm (§11) | Decided and documented |
| **10. Public** | `/security-review`, remove private paths or names, `1.0.0`, public repo, portal page (three languages) | Repo public and page published |

## 10. Criteria for "100 % functional and applicable to any system" (move to 1.0)

- Works in **three projects** on different stacks (at least one without Node: the Tarkor installer or VeriNews
  are the candidates) for **≥ 4 weeks** each.
- **Hand-offs proven**: at least 5 session cuts (tokens, `/clear`, account switch) with no loss, verified
  against the log.
- **Hooks**: no false positives and no unreviewed push to `main` during the run-in; hook tests green on Linux and
  macOS. Windows: documented (Git Bash or WSL) and tested at least once.
- **Clean install**: stage 1, an agent with `apply.md` + `doctor.py` on a new repo without manual edits; stage 2, the
  same without AI.
- **Nothing private** in the repo: no Tarkor or portal paths, no internal identifiers, no personal data.
- ES/EN documentation complete and paired (the test checks it).

## 11. npm (at the end, optional)

Package `galivelop-workflow` (or scoped `@galivelop/workflow`) with an `npx galivelop-workflow init` binary that
adds the marketplace and runs the init, for whoever prefers not to use `/plugin`. Decide in Phase 9 whether it
adds anything over the GitHub marketplace; if published, `release.yml` also runs `npm publish` and the version
comes from the same `plugin.json`.

## 12. Lessons already paid for (don't repeat them)

From the portal's retro (2026-10-21) and the work on Tarkor:

- Repo root from the script's path, never from `$CLAUDE_PROJECT_DIR` or the current directory.
- A push hook checks **the commit being pushed**, not the working copy.
- Hooks **fail closed** when missing data (absent commit, API not responding).
- What is brought from a project is adapted to how that project ships (direct to `main` or via PR).
- Every change to hooks or scripts comes with its test case.
- Quality first: a token saving that worsens the result is not a saving.
- Read other repos with a subagent that returns a summary; the main session doesn't read whole files.

## 13. First message for the session that creates the repo

```text
You are going to create the Galivelop-workflow repo following the attached plan (galivelop-workflow-plan.en.md).
Start with Phase 0. Portal-Galivelop and World-Maker-Fantasy are read-only.
Work on branch claude/galivelop-workflow-inicio, commit + push at every stable point,
log in the new repo's docs/traspaso.md. To main, only with my confirmation.
```
