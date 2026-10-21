# Galivelop-workflow — repository creation plan

> Document for the Claude session that will create the repo. Read it in full before starting and follow it phase
> by phase: each phase ends with commit + push and its box ticked in the new repo's `docs/traspaso.md`.
> Written on 2026-10-21 from the workflow in use in **Portal-Galivelop** and **World-Maker-Fantasy (Tarkor)**.
> Spanish version: `galivelop-workflow-plan.es.md` (same content).

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

**Why a plugin and not a file-copying script:** the plugin comes with versioning, updates (`/plugin update`) and
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

**Not brought over:** project-specific material (the portal's three languages, Tarkor's lore, the concrete weekly
task, `opt-ai`, `scout-updates`, play-test rounds). The **weekly scheduled task** is documented as an optional
pattern in `docs/<lang>/patterns.md`, without a concrete prompt.

## 4. Repository layout

```text
Galivelop-workflow/
├── .claude-plugin/
│   ├── marketplace.json          # the repo is its own marketplace (one plugin)
│   └── plugin.json               # name, version (semver), description, author, licence
├── skills/                       # one folder per skill, SKILL.md in English (§4.4)
│   ├── selector/  orchestrate-dealer/  opt-tokens/  retro/  pr/
│   ├── grilling/  grill-with-docs/  domain-modeling/  diagnosing-bugs/
│   ├── codebase-design/  improve-codebase-architecture/  writing-for-agents/
│   ├── prototype/  research/
│   ├── gw-init/                  # bootstraps the workflow in a repo (§5.4)
│   ├── gw-update/                # brings the repo's templates up to the plugin version
│   └── gw-doctor/                # checks the workflow is set up correctly
├── hooks/
│   └── hooks.json                # SessionStart (startup|resume|clear, clear|compact) and PreToolUse (PR to main)
├── scripts/                      # called by hooks and skills; root via ${CLAUDE_PLUGIN_ROOT}
│   ├── session-start.sh  revision-antes-de-main.sh
│   ├── recuperar.py  medir.py  es-codigo.sh  revisado.sh
│   └── config.py                 # reads and validates the project's .claude/gw.json (the only reader)
├── templates/                    # what /gw-init copies into the target repo, in es/ and en/
│   ├── es/  CLAUDE.md  REVIEW.md  GLOSSARY.md  traspaso.md  opt-tokens.md
│   ├── en/  (the same)
│   ├── githooks/pre-push
│   ├── github/comprobar.yml      # minimal CI: the project's check
│   └── gw.json                   # sample config, commented in the README
├── schema/gw.schema.json         # JSON Schema for the config
├── tests/
│   ├── test-ganchos.sh           # creates a temporary git repo and tests every hook and script
│   └── test-plantillas.sh        # /gw-init on an empty repo yields what is expected; idempotent
├── docs/
│   ├── es/  flujo.md  instalar.md  config.md  patrones.md  contribuir.md
│   └── en/  workflow.md  install.md  config.md  patterns.md  contributing.md
├── CLAUDE.md                     # instructions for working ON this repo (it uses its own workflow)
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

From Phase 1 on, the repo is worked on with its own plugin installed from the local folder
(`/plugin marketplace add ./`). That is the first run-in test: if something in the workflow gets in the way here,
it gets in the way everywhere.

### 4.2 Names

- Plugin: `galivelop-workflow`. Skills appear as `galivelop-workflow:selector`, etc.
- Management skills carry the `gw-` prefix so they don't clash with project skills.
- Project config: `.claude/gw.json`. Workflow-owned files in the target repo: `.claude/gw/`.

### 4.3 Paths

Every script takes its own root from its path (`$(dirname "$0")`) or `${CLAUDE_PLUGIN_ROOT}`, and the project's
from `git rev-parse --show-toplevel`, **never** from `$CLAUDE_PROJECT_DIR` or the current directory: in the cloud
the session may start in `/home/user` (portal lesson, `REVIEW.md` § "Hooks and scripts").

### 4.4 Languages: Spanish and English

- **Human documentation** (README, `docs/`, CHANGELOG, templates): in both languages. `README.md` in English
  (what GitHub and npm show) with a link to `README.es.md` at the top; parallel `docs/es/` and `docs/en/`. A test
  checks every file in `docs/es/` has its pair in `docs/en/` and vice versa.
- **Skills (`SKILL.md`)**: in **English, one version only**. They are loaded into the agent's context; duplicating
  them doubles their cost. mattpocock's skills are already in English. The agent replies in the project's
  language (`idioma` in the config), as the generated `CLAUDE.md` states.
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
  higher-risk row. Reads extra rows from `selector.casos` in the config.
- **`orchestrate-dealer`**: the main session plans, decides and reviews; subagents read, implement chunks and
  push. Brief template with pointers, a done criterion and a ≤15-line reply
  (`DONE · COMMIT · MISSING · QUESTIONS`). One at a time on the same branch if they write.
- **`opt-tokens`**: as in the portal ("quality first", average context × calls dominates). Project-specific
  material in `.claude/gw/opt-tokens.md`.
- **`retro`**: gains a new outlet: if an improvement applies to any project, the proposal is an **issue or PR on
  the `Galivelop-workflow` repo**, not a local patch. That way the workflow learns from every project.
- **`gw-init`, `gw-update`, `gw-doctor`**: see §5.4.

### 5.2 Claude Code hooks (`hooks/hooks.json`)

| Event | What it does |
|---|---|
| `SessionStart` (`startup\|resume\|clear`) | `session-start.sh`: `core.hooksPath=.githooks` if none is set, cloud dependencies (config `instalar`, only if `CLAUDE_CODE_REMOTE=true` and the lockfile changed), warning if `gw.json` is missing or the templates' version lags behind the plugin |
| `SessionStart` (`clear\|compact`) | `recuperar.py --estado`: the log's state row, `git status`, latest commits, how to search for a detail |
| `PreToolUse` (`create_pull_request\|merge_pull_request` from the GitHub MCP and `gh pr create\|merge` via Bash) | `revision-antes-de-main.sh`: blocks without a review mark for the same code or with CI not green. Fails closed |

### 5.3 Git hooks and CI (in the target repo)

- `.githooks/pre-push` (copied by `/gw-init`, with a `# galivelop-workflow vX.Y.Z` header): runs the config's
  `check` **on the commit being pushed** (temporary worktree if it isn't the working copy); to the protected
  branch, requires the review mark if it brings code. `--no-verify` only for a red `WIP:`.
- Review mark: `revisado.sh` writes the sha to the config's `marca` (default `docs/registros/revisado.txt`) and
  commits it. It travels with the repo, so scheduled tasks and other accounts see it.
- `es-codigo.sh`: "code" is everything that doesn't match the config's `contenido`. Only code needs review.
- `.github/workflows/comprobar.yml`: `instalar` + `check` on every push not to the protected branch and on every PR.

### 5.4 `/gw-init`, `/gw-update`, `/gw-doctor`

- **`/gw-init`**: asks the minimum (or infers it: `package.json`, `pyproject.toml`, `Cargo.toml`, `Makefile`…),
  writes `.claude/gw.json` and copies templates without overwriting anything (if `CLAUDE.md` exists, it proposes
  a block to add and shows it first). Adds the marketplace and the enabled plugin to `.claude/settings.json`, plus
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`. Commit `Galivelop-workflow vX.Y.Z workflow` with a `Next:` line.
- **`/gw-update`**: compares each copied template's version header with the plugin's; shows the diff of the
  template change (not of the file, which the project will have filled in) and applies what the user confirms.
- **`/gw-doctor`**: checks and lists, with the fixing command for each: config valid against the schema,
  `core.hooksPath`, `pre-push` executable and current, log with its sections, `check` exists, CI present, plugin
  enabled in `settings.json`.

## 6. Project config: `.claude/gw.json`

Everything that varies between projects, and nothing else. Only `scripts/config.py` reads it (one fact, one place).

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/zeldris/Galivelop-workflow/v1.0.0/schema/gw.schema.json",
  "version": "0.1.0",                       // plugin version the templates were generated with
  "idioma": "es",                           // es | en: templates and reply language
  "idiomasVisibles": ["es", "gl", "en"],    // optional: what REVIEW.md requires of visible text
  "bitacora": "docs/traspaso.md",
  "ramaProtegida": "main",
  "subidaAProtegida": "directa",            // directa | pr: which hook guards it (pre-push or PreToolUse)
  "instalar": "npm ci",
  "check": "npm run check",
  "marca": "docs/registros/revisado.txt",
  "contenido": ["^docs/", "^public/", "^src/data/", "\\.md$"],   // regex: what does NOT need /code-review
  "roadmap": false,                         // optional milestones module (Tarkor)
  "selector": { "casos": [] }               // extra project-specific rows
}
```

> Key names stay in Spanish for continuity with the existing repos; Phase 0 may decide to switch them to English
> before `1.0.0` (a major change after that).

Examples Phase 5 must cover: the portal (Node, direct push, three visible languages) and Tarkor (backend +
frontend, milestone roadmap, several accounts). Phase 7 adds one that is not Node (Python or Rust).

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

## 8. Installing in a project (what `docs/<lang>/install.md` will say)

```text
/plugin marketplace add zeldris/Galivelop-workflow
/plugin install galivelop-workflow@galivelop-workflow
/galivelop-workflow:gw-init
```

`/gw-init` writes `extraKnownMarketplaces` and `enabledPlugins` into the project's `.claude/settings.json`, so any
session that opens the repo (another account, the cloud) loads it without manual steps.

> **To verify in Phase 0** (don't take it for granted): that a cloud session installs a marketplace from a
> **private** repo with the session's GitHub access. If it can't, plan B while it stays private is for `/gw-init`
> to also copy the skills into `.claude/skills/` with a version header and for `/gw-update` to refresh them.
> Also check the exact field names of `plugin.json`, `marketplace.json` and `hooks.json` against the current
> official Claude Code plugin documentation.

## 9. Build phases

Each phase: working branch, steps with commit + push at every stable point, log in the same commit, tests green,
and on closing `/code-review` before going to `main` (with confirmation). Model per the portal's `selector`:
design and hooks with the large model; porting skills and templates with the medium one.

| Phase | What | Done when |
|---|---|---|
| **0. Verify** | Read the official docs on plugins, marketplaces and hooks; test a private marketplace in the cloud; write notes to `docs/investigacion/plugins.md` (`research` skill) | §8 questions answered and the plan adjusted if needed |
| **1. Skeleton** | Create the repo, `LICENSE`, `.claude-plugin/`, README ES/EN, `CLAUDE.md`, log, CHANGELOG `0.1.0`, CI with shellcheck and JSON validation. Install the plugin locally | `/plugin` lists it and CI is green |
| **2. Skills** | Port the 14 skills (§3) and write `gw-doctor` | All load; `writing-for-agents` applied to the own ones; licences and credits in place |
| **3. Hooks and scripts** | `config.py`, `session-start.sh`, `recuperar.py`, `revision-antes-de-main.sh`, `es-codigo.sh`, `revisado.sh`, `medir.py` and the `pre-push` template, all reading the config. `tests/test-ganchos.sh` against a temporary repo, including the portal's 29 bug cases | Tests green on Linux and macOS (CI matrix); fail closed without config |
| **4. Templates and init** | `templates/es` and `templates/en`, `gw.schema.json`, `gw-init`, `gw-update`, `test-plantillas.sh` | `gw-init` on an empty repo yields a workflow `gw-doctor` accepts; running it twice changes nothing |
| **5. Pilot: Portal-Galivelop** | On a portal branch (with the user's permission in that session): replace its copy with the plugin + `gw.json`. Compare behaviour with the previous setup | `npm run check` green, `pre-push` and review mark working, weekly task unchanged. Gaps come back as a new plugin version |
| **6. Pilot: Tarkor** | Same in World-Maker-Fantasy, with `roadmap: true` | A hand-off between the two accounts with the plugin, nothing lost |
| **7. Run-in** | A non-Node project; weeks of real use. Every `retro` with a general improvement → issue/PR here | §10 criteria |
| **8. Public** | Security review (`/security-review`), remove private paths or names, `1.0.0`, public repo, Galivelop portal page (three languages, link to the public repo), consider npm (§11) | Repo public and page published |

## 10. Criteria for "100 % functional and applicable to any system" (move to 1.0)

- Works in **three projects** on different stacks (at least one without Node) for **≥ 4 weeks** each.
- **Hand-offs proven**: at least 5 session cuts (tokens, `/clear`, account switch) with no loss, verified
  against the log.
- **Hooks**: no false positives and no unreviewed push to `main` during the run-in; hook tests green on Linux and
  macOS. Windows: documented (Git Bash or WSL) and tested at least once.
- **Clean install**: `gw-init` + `gw-doctor` on a new repo without any manual edits.
- **Nothing private** in the repo: no Tarkor or portal paths, no internal identifiers, no personal data.
- ES/EN documentation complete and paired (the test checks it).

## 11. npm (at the end, optional)

Package `galivelop-workflow` (or scoped `@galivelop/workflow`) with an `npx galivelop-workflow init` binary that
adds the marketplace and runs the init, for whoever prefers not to use `/plugin`. Decide in Phase 8 whether it
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
