# Roadmap

[Español](roadmap.md)

What goes into each version, with one identifier per task. It is the **only source of ids** (D13): commits cite them
in `Refs:` (D12, from `0.5`), the CHANGELOG names them and `trace.py <id>` (D14) gathers everything about one. Each
task's design is in [`docs/design/`](design/README.md) (Spanish); the split, in [`H-roadmap.md`](design/H-roadmap.md)
(new map, approved on 2026-11-01). The new features the harvests brought stay in
[`pending.md`](records/pending.md), with their version on each line (H12).

## Identifiers

- Each task has its design block's letter and a number with no hyphen: `B3` is question 3 of
  [`B-measurement.md`](design/B-measurement.md). The blocks: A framework, B measurement and models, C questions and modes, D
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
MMC: each patch leaves what it touches configurable (thresholds, paths, behaviours) so the MMC can edit it (G4;
user, 2026-11-04). At most one release a day (A-6).

## `0.4.4` — patch (not released)

The user decided on 2026-11-03 to release `0.5.0` directly: its fixes ship in it and what is pending moves to
`0.5.1`.

| Id | Task | State |
|---|---|---|
| D6 | `worktree.baseRef: "head"` in the `settings.json` the workflow installs | pending (moves to `0.5.1`) |
| — | Retro `0.4.2` P5: the `pre-commit` QUOTED rule without false positives in `.md` ([`pending.md`](records/pending.md)) | pending (moves to `0.5.1`) |
| — | Ubuntu and macOS CI fixes (branch `ccr-6dfbc880-ddr41g`, `4b7bf8a`..`66a4ecd`) | done |
| D32 | `harvest.py` recognises skills with their pre-A8 name and an old copy of `writing-for-agents` (image-generator P1, P12) | done (`0.5.0`, `c8681f4`) |
| D33 | `config-guard.py`: `settings.local.json`, worktrees and more writing commands; no false positive on `touch -r` (portal P2, WMF P8) | done (`0.5.0`, `cfd8f55`) |
| D34 | `commit-msg` lets a `WIP:` through when `gw.json` cannot be read and does not fail outside a work tree (portal P4, WMF P11) | done (`0.5.0`, `df55355`) |
| D35 | `/gw-update` on a single-branch clone uses the tags (portal P3) | done (`0.5.0`, `ea6195a`) |
| D36 | `reviewed.sh` suggests `--footer` on failure and adds a default `Siguiente:` with `commitNext` (WMF P2) | done (`0.5.0`, `b0b7fbf`) |
| E18 | Tests of installed skills isolated from the project they run in (WMF P3) | done (`0.5.0`, `fd6b6cc`) |
| D37 | `pre-commit`: `KEY_FORMATS` with keys glued to a letter or digit; no false positive on test dictionaries (image-generator P2, P3) | done (`0.5.0`, `c57d5b4`) |
| D38 | The `pre-push` push-in-progress mark, one per worktree (portal P5) | done (`0.5.0`, `eccbad8`) |
| D39 | `subagent-cap.py`: counter that is cleaned and safe from symlinks (portal P7, WMF P9) | done (`0.5.0`, `bdaef9d`) |

## `0.5` "Base" — what breaks

In this order, because each step uses the previous one.

| Id | Task | State |
|---|---|---|
| H14 | New version rule in `AGENTS.md` and plan §7 | done (`a1ac1e3`) |
| D13 | This roadmap, with the ids, in Spanish and English | done |
| H12 | `pendiente-1.0.0.md` → `pending.md`, with the version on each line | done |
| H15 | `0.5` harvest (`gw-harvest`) and its proposals, to the user | done (D32-D40, E18, E19, B14, B15) |
| A7 | Plan rewritten after A1's table (§1, §2, §7, §9, §10): public repo, every version released here | done |
| A8 | Names (A2, A-3, A-4): `gw-` on our own skills, scripts in English, project paths in English and configurable in `gw.json`; `gw-update` renames and the hooks accept both names during `0.x` | done |
| A9 | `schemaVersion` in `gw.json` and its migration in `gw-update` (A3.2) | done |
| D11 | Conventional Commits on the first line (`fix(B1): …`); `version.py` suggests the bump | done |
| D12 | `Refs: <id>` trailer required by `commit-msg` (except merges), checked against this roadmap | done |
| D15 | Optional `Agent:` trailer, with no model name | done |
| D16 | Subagent branches `agent/<id>-…`; `merge-branch.sh` copies `Refs:` | done |
| E2 | Private-data check in `pre-push` (list in `.claude/gw.local.json`); CI, only keys and emails | done (`8ffc4f5`) |
| E3 | Published harvests anonymised (`private-project-1`) | done (`d11153f`) |
| D3 | Review of the already published harvests with E2's check | done (`0cb929b`) |
| E1 | Audit of `AGENTS.md` and `CLAUDE.md`, with a line-cap check | done (`d0dfed3`, `e02859e`) |
| E6 | Each `REVIEW.md` rule names its check or says "judgement" | done |
| D18 | `scripts/ci-status.py`: Actions status of a branch or commit (private-project-2 P6) | done (`32e7f8f`) |
| D19 | `ciPython` key: Python versions of the CI template matrix (private-project-2 P7) | done (`364966d`) |
| D20 | `ciIgnore` key: foreign CI statuses that do not block the merge (private-project-1 P1) | done (`b2dd04c`) |
| D21 | No agent signatures in PRs, issues and comments; warning on a `noreply@anthropic.com` `user.email` (private-project-1 P2) | done (`84580cc`) |
| E17 | The check in one command with a summary and trimmed output (INS P12, WMF P4) | done (`bb1f47a`) |
| D22 | `handoff.py own-row --staged`: the own row checked at commit time (INS P9) | done (`08bc6b6`) |
| D23 | `handoff.py set-row` (private-project-1 P7) | done (`0403f2b`) |
| D24 | `reviewed.sh` warns of code not reviewed since the last mark (private-project-1 P6) | done (`e93a941`) |
| D25 | `red-without-fix.sh --fix-at <commit>`; build red versus assertion red (private-project-1 P5) | done (`4c6527f`) |
| D26 | `doctor.py` warns of worktrees already merged (INS P10) | done (`e3a7789`) |
| D27 | `doctor.py` warns of `cd <folder> && …` without `worktreeLinks` (private-project-1 P8) | done (`b8926e7`) |
| D28 | `doctor.py` warns of an absolute `core.hooksPath` to the main checkout's `.githooks` (retro `0.4.2` P3) | done (`204c735`) |
| D29 | `related-tests.sh` with deleted files (private-project-1 P11) | done (`a4798a0`) |
| D30 | `version.py`: every path quoted in the new CHANGELOG entry exists (retro `0.4.3` R1) | done (`785062f`) |
| D31 | `commit-msg` requires `Siguiente:`, also in `merge-branch.sh` merges; `GW_NO_NEXT=1` escape (retro `0.4.2` P4) | done (`7561ebf`) |
| B14 | `recover.py --state` warns when the compaction budget is exceeded (private-project-1 P1) | done (`0.5.0`, `e1f312f`) |
| D40 | Warning about remote branches with work outside the protected one (WMF P1, private-project-1 P4) | done (`0.5.0`, `e1f312f`) |
| B15 | Warning about a subagent launched without `model` (portal P1) | done (`0.5.0`, `bdaef9d`) |
| E19 | The check fails on a `TestCase` after `unittest.main()` (private-project-1 P2) | done (`0.5.0`, `a4ab81c`) |
| — | What [`pending.md`](records/pending.md) marks `0.5` | split into D18-D31 and E17 |

## `0.5.1` — patch

| Id | Task | Status |
|---|---|---|
| D6 | `worktree.baseRef: "head"` in the `settings.json` the workflow installs (from `0.4.4`) | pending |
| — | Retro `0.4.2` P5: the `pre-commit` QUOTED rule without false positives in `.md` (from `0.4.4`) | pending |
| E20 | `check.sh`: fixed log `.git/gw/check-<sha>.log`, lock with its pid and a final line with the sections that failed; `merge-branch.sh` uses it and records the green (retro `0.5.0` R1) | pending |
| D44 | Marking as reviewed costs no extra check: the `pre-push` takes as green a commit that only adds the review mark to an already green one, or branch and `main` go up in a single `git push` (user, 2026-11-04: pushing `0.5.0` ran three nearly identical checks) | pending |
| D41 | The `Stop` hook says in one line, without asking to push, that a check or a push is running (retro `0.5.0` R5; depends on E20) | pending |
| D45 | `apply.py --update` does not remove the project's own CI steps: why the `.gw-new` did not save the portal's `check.yml` in the move to `0.5.0`, with its test (`0.5.1` harvest, portal P2) | pending |
| B17 | `gw-orchestrate-dealer`: a subagent that writes in the background always works in a worktree, even a single one (`0.5.1` harvest, image-generator P1) | pending |
| E23 | The check cache is invalidated when an ignored file the check reads changes (`.claude/gw.local.json`), or the reused green says so (`0.5.1` harvest, portal P3) | pending |
| D46 | After the name migration (A8), `apply.py --update` or `doctor.py` list uses of old paths in the project's own files (`0.5.1` harvest, portal P1) | pending |
| D47 | The `pre-push` that stops private data says the commits are not pushed yet and offers `--amend` or `rebase -i` only over them (`0.5.1` harvest, portal P4) | pending |
| E24 | What is tested with a double also gets a smoke test with the real thing: a note in `patterns.md` and a `(judgement)` rule in `REVIEW.md` (`0.5.1` harvest, world-maker-fantasy P3) | pending |

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
| B10 | The `gw-selector` recommends the main session's model and effort | pending |
| B11 | Model and effort per agent (Claude Code levers) | pending |
| E21 | `scripts/related-tests.py <files>`: the tests of a change, cited in the `gw-orchestrate-dealer` brief; in `REVIEW.md`, a script that commits is tested with the hooks installed (retro `0.5.0` R2) | pending |
| B16 | `gw-orchestrate-dealer`: the approved findings of a `/code-review` are dealt out to subagents by group of files (retro `0.5.0` R3) | pending |
| D42 | `gw-orchestrate-dealer`: a `scratchpad/<id>/` folder per agent, check the worktree base and stop with `TaskStop` (retro `0.5.0` R4) | pending |
| E22 | `check.sh` also runs the tests with the oldest Python available, or warns if there is none (retro `0.5.0` R6) | pending |
| B18 | Review by blocks on a long branch: `/code-review` of the new diff at each closed block, in `gw-selector` and the `AGENTS.md` template (`0.5.1` harvest, world-maker-fantasy P1) | pending |
| D48 | `handoff.py next-id <prefix>`: the next free id looking at the remote branches before numbering, with `free_id` (`0.5.1` harvest, world-maker-fantasy P2) | pending |
| D43 | Commit and review size: warn, without blocking, about a commit of more than ~400 changed lines (LOC); the review unit is the block or task of ~1000 lines, reviewed when it closes (B18), and the PR to `main` adds up already-reviewed blocks. Paired docs, the installed copies under `.claude/gw/` and generated files do not count; the thresholds, in `.claude/gw.json` (user, 2026-11-04) | pending |
| D49 | The `pre-push` of a branch other than `main` requires only the related tests (`related-tests.sh`); the full check moves to the push to `main` and to environment changes. The GitHub CI keeps running in full on every push, without blocking, and is checked at each block close with `ci-status.py`; absorbs part of D44 (user, 2026-11-04) | pending |
| D50 | Traceable commits: `feat`/`fix` commits (and a large `refactor`) carry `Técnica:` (the decision and what was discarded) and `Problemas:` (what failed and how it was solved, or «ninguno») in the body. The `commit-msg` checks they are there, with the types in `.claude/gw.json`; `REVIEW.md` asks for their quality as a judgement rule and the retro goes over it. `docs`, `WIP` and the review mark are exempt (user, 2026-11-04) | pending |

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
| — | What [`pending.md`](records/pending.md) marks `0.7` | pending |

## `0.8` "Front end and other agents"

| Id | Task | State |
|---|---|---|
| E4 | Install profiles (minimal/core/full, `core` by default) in `gw-init` and `gw-update` | pending |
| E5 | Front-end tests following the research | pending |
| E7 | Front-end testing guide in `docs/en/patterns.md` and a config template | pending |
| E9-E16 | The front-end checks decided in [`E-quality.md`](design/E-quality.md) (screenshots, when they run, tokens, preprocessors, accessibility, baselines, no paid services, matrix) | pending |
| D7 | `AGENTS.md` readable without `@include`; skills also in `.agents/skills` (opencode, Codex) | pending |
| B9 | Non-Anthropic models through opencode | pending |
| — | What [`pending.md`](records/pending.md) marks `0.8` | pending |

## `0.9` "Stable"

| Id | Task | State |
|---|---|---|
| E8 | Full documentation review, by subagents | pending |
| G2 | Versioned JSON output in the scripts the MMC uses | pending |
| — | What [`pending.md`](records/pending.md) marks `0.9` | pending |

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
| B12 | "Scouts" pattern in `gw-orchestrate-dealer`, measured before and after | Ledger |
| C9 | `modes.freeze <folder>` | C7 |
| G10 | Multi-project MMC | `1.0` |
| — | OpenTelemetry as an option for B1 | B1 |
| — | Harvest of the private repos (R3) | Read access |
