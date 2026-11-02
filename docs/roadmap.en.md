# Roadmap

[Español](roadmap.md)

What goes into each version, with one identifier per task. It is the **only source of ids** (D13): commits cite them
in `Refs:` (D12, from `0.5`), the CHANGELOG names them and `trace.py <id>` (D14) gathers everything about one. Each
task's design is in [`docs/diseno/`](diseno/README.md) (Spanish); the split, in [`H-roadmap.md`](diseno/H-roadmap.md)
(new map, approved on 2026-11-01). The new features the harvests brought stay in
[`pendiente.md`](registros/pendiente.md), with their version on each line (H12).

## Identifiers

- Each task has its design block's letter and a number with no hyphen: `B3` is question 3 of
  [`B-medicion.md`](diseno/B-medicion.md). The blocks: A framework, B measurement and models, C questions and modes, D
  git, E quality, G Management Center (MMC), H roadmap.
- A new task takes the next free number of its block; a number is never reused, not even a dropped task's. Block A's
  tasks that come from its sections rather than a question start at `A7` (its questions go up to `A-6`).
- Questions that only decided something (for example D1, D2 or D4) are not tasks and are not listed.
- States: `hecho` (done), `en curso` (in progress), `pendiente` (pending). When a task closes, its row names the
  commit.
- Scripts and hooks read the ids from the Spanish version, [`roadmap.md`](roadmap.md); this file translates it.

## Version rule

Only the latest published minor gets patches; new features go to the next minor (H14, plan §7). Work moves through
`0.x`, where a minor may break: **everything that breaks goes into `0.5`**, so projects migrate once. `1.0` is the
MMC. At most one release a day (A-6).

## `0.4.4` — patch

| Id | Task | State |
|---|---|---|
| D6 | `worktree.baseRef: "head"` in the `settings.json` the workflow installs | pending |
| — | Retro `0.4.2` P5: the `pre-commit` QUOTED rule without false positives in `.md` ([`pendiente.md`](registros/pendiente.md)) | pending |
| — | Ubuntu and macOS CI fixes (branch `ccr-6dfbc880-ddr41g`, `4b7bf8a`..`66a4ecd`) | done |

## `0.5` "Base" — what breaks

In this order, because each step uses the previous one.

| Id | Task | State |
|---|---|---|
| H14 | New version rule in `AGENTS.md` and plan §7 | done (`a1ac1e3`) |
| D13 | This roadmap, with the ids, in Spanish and English | done |
| H12 | `pendiente-1.0.0.md` → `pendiente.md`, with the version on each line | done |
| A7 | Plan rewritten after A1's table (§1, §2, §7, §9, §10): public repo, every version released here | done |
| A8 | Names (A2, A-3, A-4): `gw-` on our own skills, scripts in English, project paths in English and configurable in `gw.json`; `gw-update` renames and the hooks accept both names during `0.x` | in progress |
| A9 | `schemaVersion` in `gw.json` and its migration in `gw-update` (A3.2) | pending |
| D11 | Conventional Commits on the first line (`fix(B1): …`); `version.py` suggests the bump | pending |
| D12 | `Refs: <id>` trailer required by `commit-msg` (except merges), checked against this roadmap | pending |
| D15 | Optional `Agent:` trailer, with no model name | pending |
| D16 | Subagent branches `agent/<id>-…`; `fusionar.sh` copies `Refs:` | pending |
| E2 | Private-data check in `pre-push` (list in `.claude/gw.local.json`); CI, only keys and emails | pending |
| E3 | Published harvests anonymised (`private-project-1`) | pending |
| D3 | Review of the already published harvests with E2's check | pending |
| E1 | Audit of `AGENTS.md` and `CLAUDE.md`, with a line-cap check | pending |
| E6 | Each `REVIEW.md` rule names its check or says "judgement" | pending |
| — | What [`pendiente.md`](registros/pendiente.md) marks `0.5` | pending |

## `0.6` "Measure"

| Id | Task | State |
|---|---|---|
| B1 | `Stop` hook that reads the session logs | pending |
| B2 | `docs/metrics/ledger.jsonl` in the repo | pending |
| B3 | What is stored: tokens by model and type, date, branch, `Refs`, subagent; prices in a dated table | pending |
| B4 | Reports by period: `metrics.py report --period …` and the `gw-metrics` skill | pending |
| B5 | Comparisons: `metrics.py compare` | pending |
| B6 | Warning at `SessionStart` when a model spends 1.5× its average | pending |
| B7 | `models.disabled` in `gw.json`, with its hook | pending |
| B8 | Quality signals next to spend (the deterministic table, under "Later") | pending |
| B10 | The `selector` recommends the main session's model and effort | pending |
| B11 | Model and effort per agent (Claude Code levers) | pending |

## `0.7` "Ask"

| Id | Task | State |
|---|---|---|
| C1 | `docs/questions.md`, one entry per question | pending |
| C2 | Numbered list with a recommendation; answers by number, which a script copies into the file | pending |
| C3 | No repeating questions already answered | pending |
| C4 | Restrictive mode on, with its hook | pending |
| C5 | Restrictive mode off: a warning and "accepted risk" | pending |
| C6 | Default: off in projects, on in this repo | pending |
| C7 | One switch: the `gw-mode` skill | pending |
| C8 | `modes.careful` (before a destructive command), on by default | pending |
| C10 | A subagent does not ask the user: it returns the question | pending |
| D14 | `trace.py <id>` | pending |
| — | What [`pendiente.md`](registros/pendiente.md) marks `0.7` | pending |

## `0.8` "Front end and other agents"

| Id | Task | State |
|---|---|---|
| E4 | Install profiles (minimal/core/full, `core` by default) in `gw-init` and `gw-update` | pending |
| E5 | Front-end tests following the research | pending |
| E7 | Front-end testing guide in `docs/en/patterns.md` and a config template | pending |
| E9-E16 | The front-end checks decided in [`E-calidad.md`](diseno/E-calidad.md) (screenshots, when they run, tokens, preprocessors, accessibility, baselines, no paid services, matrix) | pending |
| D7 | `AGENTS.md` readable without `@include`; skills also in `.agents/skills` (opencode, Codex) | pending |
| B9 | Non-Anthropic models through opencode | pending |
| — | What [`pendiente.md`](registros/pendiente.md) marks `0.8` | pending |

## `0.9` "Stable"

| Id | Task | State |
|---|---|---|
| E8 | Full documentation review, by subagents | pending |
| G2 | Versioned JSON output in the scripts the MMC uses | pending |
| — | What [`pendiente.md`](registros/pendiente.md) marks `0.9` | pending |

## `1.0` — MMC 1, read-only

| Id | Task | State |
|---|---|---|
| G1 | `mmc.py` on `127.0.0.1` | pending |
| G3 | `mmc.py --static` for the cloud | pending |
| G6 | Data views | pending |
| G7 | Git view: branches, environments, tags, check and CI | pending |

## `1.1` — MMC 2, config

| Id | Task | State |
|---|---|---|
| G4 | Config from the MMC through `config.py`, with the diff and no commit | pending |

## `1.2` — MMC 3: profiles, environments and roles

| Id | Task | State |
|---|---|---|
| G5 | Layered profiles | pending |
| G8 | Environments and roles in the MMC | pending |
| D9 | Configurable (`environments` in `gw.json`) and new environments | pending |
| D10 | `rc` tags on `uat` | pending |
| D17 | Roles, with the git user check per environment | pending |

## Later, no version yet

It gets a version when the minor it fits in opens and what it needs exists.

| Id | Task | Needs |
|---|---|---|
| B8 | Deterministic table of models by need (second part) | Four weeks of ledger |
| B13 | Published trend and an A/B test with and without the workflow | Ledger |
| B12 | "Scouts" pattern in `orchestrate-dealer`, measured before and after | Ledger |
| C9 | `modes.freeze <folder>` | C7 |
| G10 | Multi-project MMC | `1.0` |
| — | OpenTelemetry as an option for B1 | B1 |
| — | Harvest of the private repos (R3) | Read access |
