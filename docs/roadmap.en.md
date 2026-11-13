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
  git, E quality, G Management Center (MMC), H roadmap, I lifecycle and authority ([`I-lifecycle.md`](design/I-lifecycle.md)).
- A new task takes the next free number of its block (`handoff.py next-id <letter>`, which also looks at the other
  branches); a number is never reused, not even a dropped task's. Block A's
  tasks that come from its sections rather than a question start at `A7` (its questions go up to `A-6`).
- Questions that only decided something (for example D1, D2 or D4) are not tasks and are not listed.
- States: `hecho` (done), `en curso` (in progress), `pendiente` (pending). When a task closes, its row names the
  commit.
- Scripts and hooks read the ids from the Spanish version, [`roadmap.md`](roadmap.md); this file translates it.

## Version rule

Only the latest published minor gets patches; new features go to the next minor (H14, plan §7) not yet under way: with `0.6` already being built, a
harvest's go to `0.7` (user, 2026-11-05). Work moves through
`0.x`, where a minor may break: **everything that breaks goes into `0.5`**, so projects migrate once. `1.0` is the
MMC: each patch leaves what it touches configurable (thresholds, paths, behaviours) so the MMC can edit it (G4;
user, 2026-11-04). At most one release a day (A-6).

## `0.4.4` — patch (not released)

The user decided on 2026-11-03 to release `0.5.0` directly: its fixes ship in it and what is pending moves to
`0.5.1`.

| Id | Task | State |
|---|---|---|
| D6 | `worktree.baseRef: "head"` in the `settings.json` the workflow installs | done in `0.5.1` |
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
| D6 | `worktree.baseRef: "head"` in the `settings.json` the workflow installs (from `0.4.4`) | done |
| E25 | Retro `0.4.2` P5: the `pre-commit` QUOTED rule without false positives in `.md` (from `0.4.4`) | done |
| E20 | `check.sh`: fixed log `.git/gw/check-<sha>.log`, lock with its pid and a final line with the sections that failed; `merge-branch.sh` uses it and records the green (retro `0.5.0` R1) | done |
| D44 | Marking as reviewed costs no extra check: the `pre-push` takes as green a commit that only adds the review mark to an already green one, or branch and `main` go up in a single `git push` (user, 2026-11-04: pushing `0.5.0` ran three nearly identical checks) | done |
| D41 | The `Stop` hook says in one line, without asking to push, that a check or a push is running (retro `0.5.0` R5; depends on E20) | done |
| D45 | `apply.py --update` does not remove the project's own CI steps: why the `.gw-new` did not save the portal's `check.yml` in the move to `0.5.0`, with its test (`0.5.1` harvest, portal P2) | done |
| B17 | `gw-orchestrate-dealer`: a subagent that writes in the background always works in a worktree, even a single one (`0.5.1` harvest, image-generator P1) | done |
| E23 | The check cache is invalidated when an ignored file the check reads changes (`.claude/gw.local.json`), or the reused green says so (`0.5.1` harvest, portal P3) | done |
| D46 | After the name migration (A8), `apply.py --update` or `doctor.py` list uses of old paths in the project's own files (`0.5.1` harvest, portal P1) | done |
| D47 | The `pre-push` that stops private data says the commits are not pushed yet and offers `--amend` or `rebase -i` only over them (`0.5.1` harvest, portal P4) | done |
| E24 | What is tested with a double also gets a smoke test with the real thing: a note in `patterns.md` and a `(judgement)` rule in `REVIEW.md` (`0.5.1` harvest, world-maker-fantasy P3) | done |
| D51 | `apply.py --update` does not seed the log template at the destination of a folder it moves (with `log` inside it, the log was lost when moving to `0.5`), with its test (`0.5.1` closing harvest, world-maker-fantasy P1) | done |
| D52 | `apply.py` decides whether to keep an old script by its whole path (`.claude/gw/scripts/<name>`), not by the same name in another path, with its test (`0.5.1` closing harvest, world-maker-fantasy P2) | done |
| E26 | `red-without-fix.sh` does not look for test code in text and data files (`.md`, `.json`, `.yml`, `.properties`, `.txt`, `.csv`): prose matched `it(`, with its test (`0.5.1` closing harvest, private-project-1 P1) | done |

## `0.5.2` — patch

| Id | Task | Status |
|---|---|---|
| B20 | `measure.py` measures a subagent's log (`subagents/agent-*.jsonl`, every line with `isSidechain`), with its test (`0.6` harvest, image-generator P1) | done |
| D57 | `harvest.py` follows renames (`-M`) and does not repeat the ideas of a moved file; a cut idea says "… (truncated)" (`0.6` harvest, image-generator P2) | done |
| D58 | The log template only explains `logRows` when it is on; `handoff.py close-row` warns and exits 1 when it is off, like `set-row` (`0.6` harvest, image-generator P3) | done |
| D59 | `commitNext: true` by default in `templates/gw.json`, as the `AGENTS.md` template asks (`0.6` harvest, image-generator P4) | done |
| D60 | The `AGENTS.md` templates name `handoff.py set-row` and `close-row` for the branch's own log row (`0.6` harvest, private-project-1 P2) | done |
| D64 | `gw-selector`: the model line keeps the session and the subagents apart and gives the current one (`Session: <recommended> (current: <X>; /model to change it) · Subagents: <rung> · Skill: <y>`); when the session orchestrates with `gw-orchestrate-dealer`, its model is that of the riskiest row it deals out, medium at least (user, 2026-11-05) | done |
| B21 | Start-up context and compaction-loop guard: after a `/clear` or a compaction, `measure.py` reads the first turn's usage from the log (`input` + `cache_read` + `cache_creation`) and compares it with the **auto-compaction cut-off** (key in `.claude/gw.json`; the model's by default), not with the window. `SessionStart` warns above 25 % and alarms above 50 % (keys); if start-up passes the threshold again after a compaction, it is a loop: alarm and stop, with the "Compaction budget". The warning names the culprit with a deterministic breakdown (log, `AGENTS.md`/`CLAUDE.md`, hook output, skills and tools, rest of the system) and the command that fixes it. Real case: a project with a 140k cut-off looped because re-reading the context took 70 %; here, ~82k of 200k after `/clear` with the log at ~9k (user, 2026-11-05) | done |
| D65 | Archive the log: a total size cap for `docs/handoff.md` (key in `.claude/gw.json`) that `handoff.py check` warns about and B21 uses as a culprit; `handoff.py archive` moves the "Pending" items and minor findings of already published versions to `docs/records/handoff-archive.md` (not read at start), leaving one line with the link; after a compaction, `recover.py` and `SessionStart` re-read only the state and the next step (user, 2026-11-05) | done |
| D69 | `hotfix` type in `commitFormat` and in `version.py` (counts as a patch), with its test, so projects on `0.5` accept the type before the task record (C11) ([`I-lifecycle.md`](design/I-lifecycle.md) Q11; user, 2026-11-08) | done |
| D66 | Each version reviews the documentation for people (`README.md` ↔ `README.es.md`, `docs/es/` ↔ `docs/en/`, roadmap) against its CHANGELOG before the push to `main` (`AGENTS.md`); `version.py --release` fails if a file in `releaseDocs` (a `.claude/gw.json` key; default `[]`, here both READMEs) does not name the version being released. Real case: `0.5.1` shipped with the README at "Status: `0.4.3`" (user, 2026-11-06) | done |
| D70 | `measure.py --since` picks the right session, not the newest log (`0.6` closing harvest, private-project-1 P2) | done (2026-11-11) |
| D71 | `handoff.py close-row` and `set-row` take the branch the same way (`0.6` closing harvest, private-project-1 P3) | done (2026-11-11) |
| D72 | The `gw-orchestrate-dealer` brief says who pushes (on the work branch, the subagent; in a worktree, nobody) and what to do with the commit (leave it uncommitted, or commit it with its log row); the main session checks `git status -sb` on return (`0.6` closing harvest, image-generator P2, world-maker P1) | done (2026-11-11) |
| D73 | `gw-update` ends by opening the PR from the update branch to the protected one (`0.6` closing harvest, instalador P1) | done (2026-11-11) |
| D74 | `related-tests.sh` prints the file count and a temp file with the full command, not the whole list (`0.6` closing harvest, world-maker P2) | done (2026-11-11) |
| D75 | Closing step of a test round: call the project's script that stops what it started (servers, models, sleep inhibitors) (`0.6` closing harvest, world-maker P7) | done (2026-11-11) |
| D88 | The `Stop` hook does not ask to push while background subagents run (extends D41); first check here how world-maker detects them (`0.6` closing harvest, world-maker P4) | done (2026-11-11) |
| B22 | `measure.py` shows the `action` of Artifact calls in HEAVIEST RESULTS (`0.6` closing harvest, portal P4) | done (2026-11-11) |
| B23 | `prototype` publishes the Artifact (with its `quickstart`) from a subagent that returns only the URL (`0.6` closing harvest, portal P3) | done (2026-11-11) |
| B24 | The phase 1 review starts after `/clear` or in a clean subagent (`AGENTS.md`, `gw-selector`) (`0.6` closing harvest, portal P2) | done (2026-11-11) |
| B25 | `gw-scout-updates` with 2 subagents (`0.6` closing harvest, private-project-1 P4) | done (2026-11-11) |
| D76 | `check-green.sh` lock: the same pid updates sha and log, a `check.lock.steal` without pid does not block, another user's process is treated as in `before-stop.py`; `before-stop.py` compares `check.sh`'s full sha with HEAD (`0.6` closing harvest, instalador `0.5.1` review, findings 1-4) | done (2026-11-11) |
| D77 | `merge-branch.sh` validates `check` and `checkWrapper` before merging (`0.6` closing harvest, instalador `0.5.1` review, finding 5) | done (2026-11-11) |
| D78 | `pre-push`: rechecks the green cache after waiting for the lock; with the same tree on a protected ref and a branch, the branch is checked too; `lock_wait` local (`0.6` closing harvest, instalador `0.5.1` review, findings 6-8) | done (2026-11-11) |
| D79 | `private-check.py amend_advice`: no `rebase -i` onto a tag or `HEAD`, no `git add -A`, no unused `cfg` (`0.6` closing harvest, instalador `0.5.1` review, findings 11 and 14) | done (2026-11-11) |
| E38 | `pre-commit`: `PROSE_ASSIGN` catches a one-word capitalised quoted secret in a `.md`; `md_prose_dropped` without one process per line (`0.6` closing harvest, instalador `0.5.1` review, findings 12-13) | done (2026-11-11) |
| E39 | `check.sh` without `--quiet` keeps TTY and colours (E17 regression; reproduced with a test first) (`0.6` closing harvest, instalador `0.5.1` review, finding 10) | done (2026-11-11) |
| E40 | Pruning of `.git/gw` `check-<sha>.log` files: the last `checkLogKeep` (20) are kept (`0.6` closing harvest, instalador `0.5.1` review, finding 9) | done (2026-11-11) |

## `0.6` "Measure"

| Id | Task | State |
|---|---|---|
| H16 | `0.6` harvest (`gw-harvest`) and its proposals, to the user | done (B20, D57-D60 to `0.5.2`; D61-D63 to `0.7`) |
| H17 | User notes (SDD, DDD, TDD, exploration, task record, done per environment) and four external references, split into proposals: [`2026-11-08-notes-and-references.md`](proposals/2026-11-08-notes-and-references.md); all 13 and the 5 questions approved (user, 2026-11-08); the design that joins them, [`I-lifecycle.md`](design/I-lifecycle.md), open until its `grilling` | in progress |
| H18 | `0.6` closing harvest (`gw-harvest`) before releasing it: fixes to the next `0.5` patch; evolutions, split across the versions (user, 2026-11-11) | done (2026-11-11; 28 proposals and 14 findings of the instalador `0.5.1` review: D70-D79, D88, B22-B25 and E38-E40 to `0.5.2`; B26-B29, D82, D84-D86 and E43 to `0.6`; D80, D81, D83, D87 and E41 to `0.7`; E42 to `0.8`; portal P6 discarded) |
| H19 | `0.6.0` harvest (`gw-harvest`) before releasing it (user, 2026-11-13: fixes to `0.6.0`; evolutions to `0.7` and `0.8`) | done (2026-11-13; 12 proposals: D90-D93 and B30 to `0.6`; E48, D94-D96, E49 and B31 to `0.7`; E50 to `0.8`) |
| A10 | One-page A4 workflow presentation sheets: for whoever contracts development, `docs/es/mkt-workflow.md` ↔ `docs/en/mkt-workflow.md` (what it solves, how work runs, what it guarantees), and for teams that install it, `docs/es/mkt-adoption.md` ↔ `docs/en/mkt-adoption.md` (user, 2026-11-09), with its HTML and final PDF generated from the `.md` by a script so they do not drift; reviewed on each version (D66) (user, 2026-11-06) | done (`scripts/mkt-sheet.py`, portal style) |
| B1 | `Stop` hook that reads the session logs | done (`scripts/metrics.py record`, key `metrics`) |
| B2 | `docs/metrics/ledger.jsonl` in the repo | done (`merge=union` in `.gitattributes`; `apply.py` does not set it in projects yet) |
| B3 | What is stored: tokens by model and type, date, branch, `Refs`, subagent; prices in a dated table | done (2026-11-09; fields with B1, `metrics.prices` and `metrics.py price`) |
| B4 | Reports by period: `metrics.py report --period …` and the `gw-metrics` skill | done (2026-11-09; `metrics.reports`, `--write`) |
| B5 | Comparisons: `metrics.py compare` | done (2026-11-09; previous period or `--against`) |
| B6 | Warning at `SessionStart` when a model spends 1.5× its average | done (2026-11-09; `metrics.alert`, today and yesterday) |
| B7 | `models.disabled` in `gw.json`, with its hook | done (2026-11-09; `subagent-cap.py` denies, `models.py`) |
| B8 | Quality signals next to spend (the deterministic table, under "Later") | done (2026-11-09; `metrics.py quality`, `Findings`/`Retries` trailers, `metrics.quality`) |
| B10 | The `gw-selector` recommends the main session's model and effort | done (2026-11-09; effort column, line `Session: <model> <effort> (current: …)` and `sessionEffort` in `selector.cases`) |
| B11 | Model and effort per agent (Claude Code levers) | done (2026-11-09; `models.agentFields` in `subagent-cap.py`, `models.checkLevers` in `doctor.py`, rule in `gw-selector` and `gw-orchestrate-dealer`) |
| E21 | `scripts/tests-for.py <files>` (key `testMap`; not `related-tests.py`: it clashed with `related-tests.sh` and its test): the tests of a change, cited in the `gw-orchestrate-dealer` brief; in `REVIEW.md`, a script that commits is tested with the hooks installed (retro `0.5.0` R2) | done (2026-11-09) |
| B16 | `gw-orchestrate-dealer`: the approved findings of a `/code-review` are dealt out to subagents by group of files (retro `0.5.0` R3) | done (2026-11-10; rule «Approved review findings are dealt by group of files») |
| D42 | `gw-orchestrate-dealer`: a `scratchpad/<id>/` folder per agent, check the worktree base and stop with `TaskStop` (retro `0.5.0` R4) | done (2026-11-10; `{scratch}/<id>-<topic>/` folder, like the branch; `{head}` in the brief) |
| E22 | `tests/check.sh` also compiles everything and runs the tests of the change on the oldest Python available (3.8+, older than `python3`) (`tests/old-python.sh` with `tests-for.py`; the hook suites only when they changed), or warns if there is none (retro `0.5.0` R6) | done (2026-11-10) |
| B18 | Review by blocks on a long branch: `/code-review` of the new diff at each closed block, in `gw-selector` and the `AGENTS.md` template (`0.5.1` harvest, world-maker-fantasy P1) | done (2026-11-10; row «Closing a block or phase» and phase 1 of the templates and of `AGENTS.md`) |
| D48 | `handoff.py next-id <prefix>`: the next free id looking at the remote branches before numbering, with `free_id` (`0.5.1` harvest, world-maker-fantasy P2) | done (2026-11-10; reads the work tree, the index and every local and remote branch; `--fetch`; `clash` now suggests ids without a dash right) |
| D43 | Commit and review size: warn, without blocking, about a commit of more than ~400 changed lines (LOC); the review unit is the block or task of ~1000 lines, reviewed when it closes (B18), and the PR to `main` adds up already-reviewed blocks. Paired docs, the installed copies under `.claude/gw/` and generated files do not count; the thresholds, in `.claude/gw.json` (user, 2026-11-04) | done (2026-11-10; `change-size.py` from the `commit-msg` hook, `changeSize` key; the block starts after the last commit with `Findings:`) |
| D49 | The `pre-push` of a branch other than `main` requires only the related tests (`related-tests.sh`); the full check moves to the push to `main` and to environment changes. The GitHub CI keeps running in full on every push, without blocking, and is checked at each block close with `ci-status.py`; absorbs part of D44 (user, 2026-11-04) | done (2026-11-10; keys `branchCheck` and `fullCheckPaths`, `config.py push-scope`; without `relatedTests`, the full one) |
| D50 | Traceable commits: `feat`/`fix` commits (and a large `refactor`) carry `Técnica:` (the decision and what was discarded) and `Problemas:` (what failed and how it was solved, or «ninguno») in the body. The `commit-msg` checks they are there, with the types in `.claude/gw.json`; `REVIEW.md` asks for their quality as a judgement rule and the retro goes over it. `docs`, `WIP` and the review mark are exempt (user, 2026-11-04). **Absorbed by C11** (user, 2026-11-08): the reasoning goes to the task record and the commit only summarises | absorbed by C11 |
| D53 | `ownedFiles` in `.claude/gw.json`: workflow files the project made its own; `apply.py --check` does not report them as drifted and `doctor.py` does not recommend `/gw-update` for them (`0.5.1` closing harvest, world-maker-fantasy P3) | done (2026-11-10; `fnmatch` patterns, `config.owned`; warning if a `.gw-new` is left) |
| D54 | `ciOnPush` in `.claude/gw.json`: `check.yml` runs on every push or only on PRs, without editing it (`0.5.1` closing harvest, world-maker-fantasy P4) | done (2026-11-10; `branches-ignore: ['**']` when applied; hint in `ci-status.py`) |
| B19 | `gw-update` deals the reconciliation of each `.gw-new` to a subagent that returns the drift table; the `/code-review` of the update branch leaves out identical workflow copies (`0.5.1` closing harvest, world-maker-fantasy P5) | done (2026-11-10; skill steps 3-5: "drift · upstream · decision" table from a light subagent, `/code-review` without identical copies) |
| E27 | `shellcheckVersion` in `.claude/gw.json`: CI installs that version and `tests/shellcheck.sh` warns, with the command that installs it, if the local one differs (`0.5.1` retro R1) | done (2026-11-11; CI installs it with `pip install shellcheck-py==X.Y.Z.*`; in CI another version fails) |
| D55 | `roadmap.py show <id>` and `roadmap.py done <id>`: see or mark a roadmap row in both languages without reading it whole (`0.5.1` retro R4) | done (2026-11-11; `scripts/roadmap.py`, key `roadmapFiles` (the reserved `roadmap` stays boolean); marks both languages or neither) |
| D56 | `ci-status.py --failed`: for each red job, only the failed step and its error lines, capped by a key, with the URL of the whole log (`0.5.1` retro R5) | done (2026-11-11; `--failed`: the step from the jobs API and, from the log, its `Run …` header to its last `##[error]` line, without the folded command; cap `ciFailedLines` (40) or `--lines`) |
| B26 | Warning when the log or a record over `wholeReadWarnBytes` (20000) is read whole (`0.6` closing harvest, private-project-1 P1) | done (2026-11-11) |
| B27 | Trivial diffs reviewed without a subagent; phase 1 fixes go to `sonnet` (`0.6` closing harvest, private-project-1 P7) | done (2026-11-11) |
| B28 | Light subagent type (`gw-worker`, in `.claude/agents/`) with only the brief's tools; `gw-init` creates it and the dealer brief names it (`0.6` closing harvest, private-project-3 P1) | done (2026-11-11) |
| B29 | `measure.py` measures the previous session of the same branch when the current one has fewer than `measure.minCalls` (5) calls (after `/clear`) (`0.6` closing harvest, world-maker P5) | done (2026-11-11) |
| D82 | Files copied unchanged from the workflow (`vendored`) stay out of the phase 1 `/code-review` (next to D53 and B19) (`0.6` closing harvest, instalador P2) | done (2026-11-11) |
| D84 | `templates/github/check.yml` reads the Node and Rust directories from `.claude/gw.json` and uses `Swatinem/rust-cache` (`0.6` closing harvest, instalador P5) | done (2026-11-11) |
| D85 | `recover.py --state` warns of an overdue review (`changeSize.block` threshold) (`0.6` closing harvest, world-maker P3) | done (2026-11-11) |
| D86 | `merge-branch.sh` recognises a conflict in the log and gives the command to solve it, with its test (`0.6` closing harvest, portal P5) | done (2026-11-11) |
| E43 | `doctor.py` warns of folders with `test_*.py` that no check command runs; excluded folders configurable (`0.6` closing harvest, instalador P3) | done (2026-11-11) |
| E44 | The check also runs `version.py --release` on `version/*` branches (key `releaseCheckBranches`), not only in the `pre-push` to `main` (`0.5.2` retro R2) | done (2026-11-13; in `scripts/check.sh`, not in the `pre-push`: a push halfway through a version is not blocked) |
| D81 | `scripts/backport.sh <sha>...`: cherry-pick in topological order (`-m 1 -x`), log and roadmap take the patch's version, empty picks skipped, stops on a code conflict and checks with `git cherry`; also brings the branch's harvest files; in the patch guide and `docs/agent-map.md` (`0.6` closing harvest, image-generator P1; `0.5.2` retro R3) | done (2026-11-13) |
| D89 | `handoff.py`: `published_version` uses the highest tag also when the workflow repo has a `plugin.json`, so `archive` does not run ahead of an unpublished version (`0.5.2` retro R4) | done (2026-11-13) |
| E45 | Fast check: `scripts/test-run.py` runs the Python suite in parallel, one test class per process, the slowest first, across `testJobs` processes (one per core by default), and the E22 pass runs alongside the main one; same tests locally and in CI; target, the full check in 10-15 min (user, 2026-11-12: it took 50-80 min) | done (2026-11-12) |
| E46 | The most expensive test files per `test-run.py --times` set up their test repos once per class, with a clean state for each test (follows E45): `Snapshot` in `tests/test_hooks.py` (`build()` once, a copy of the folder at the same path for each test) in the three `Base` classes, `Hook` and `Doctor`; the suite, from 556 s to 352 s on 4 cores | done (2026-11-12) |
| E47 | The `pre-push` asks for the full check only for the `.claude/gw.json` keys that change what the check runs; the rest get the change's tests (follows E45): `config.py push-scope --commits` compares each new commit's keys with its parents and only those outside `fullCheckSkipKeys` count (new; by default, the ones no check script reads); a broken or missing config on either side, full | done (2026-11-12) |
| A13 | Review of everything done up to `0.6` so that `.claude/gw.json` is as complete as possible: each threshold, path, warning or behaviour still fixed in the code becomes a key that can be turned on or configured, with its default, its entry in `config.py`, the schema and `docs/en/config.md` (rule "Everything configurable"; user, 2026-11-12) | done (2026-11-13) |
| D90 | `handoff.py closed` gives the command that fixes it (`handoff.py done '<id>: …'`) (`0.6.0` harvest, world-maker P1) | pending |
| D91 | The `merge-branch.sh` examples (`AGENTS.md` templates, `gw-orchestrate-dealer`) carry the `Siguiente:` trailer `commitNext` asks for (`0.6.0` harvest, installer P2) | pending |
| D92 | The `gw-orchestrate-dealer` brief tells the subagent not to answer until its background work ends (`0.6.0` harvest, image-generator P3) | pending |
| D93 | `gw-orchestrate-dealer`: when applying a document from another repo, the subagent returns each point with its literal text and path, not a summary (`0.6.0` harvest, portal P1) | pending |
| B30 | Phase 2 of the `AGENTS.md` templates and `gw-opt-ai` (`disable-model-invocation`) agree on who launches it (`0.6.0` harvest, image-generator P1) | pending |

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
| D61 | `handoff.py preflight`: what the `pre-push` checks in the log (the "Updated" date, ids clashing with `main`), without pushing; in the template's `check` (`0.6` harvest, private-project-1 P1) | pending |
| D62 | The `pre-push` warns, without blocking, when the branch's last CI is red (`ci-status.py`, when `gh` is there) (`0.6` harvest, image-generator P5) | pending |
| D63 | `templates/github/check.yml` with `workflow_call`: a `release.yml` calls it with `uses:` and `needs:` instead of copying its steps; the workflow's own too (`0.6` harvest, image-generator P6) | pending |
| A11 | The four working modes in the plan, `AGENTS.md` and `gw-selector`: SDD always (task record), DDD with a domain, TDD with testable behaviour, bounded exploration (H17 P2; user, 2026-11-08) | pending |
| C11 | Task record (`docs/tasks/<id>.md`, `taskRecord`): SDD, acceptance criteria, planned files and a decision log per agent; required for `feat`/`fix`/`hotfix` with code, checked by the `commit-msg`; `close-row` requires the boxes; absorbs D50 (H17 P1; user, 2026-11-08) | pending |
| C12 | Exploration branch `spike/<topic>` with no record and no `Refs:`, which the `pre-push` and `merge-branch.sh` refuse to merge into a working branch (H17 P2) | pending |
| C13 | Frozen scope (`scopeGuard`): warning or block when touching a file outside the record's `Files`, `pre-commit` as fallback, new requirement = new task, deviation log for the retro (H17 P3) | pending |
| D68 | CHANGELOG fragments per branch (`changelog.d/`), folded by `merge-branch.sh` or `version.py --release` (H17 P10) | pending |
| E32 | Read `permissions.deny` for secrets and a `PreToolUse` hook on `cat`/`grep` of those files, with a test; in `docs/en/`, what goes out to the provider (H17 P6) | pending |
| E33 | Review contract with anchors in `REVIEW.md`: `path:line | severity | anchor | problem. fix.`; no anchor, an observation (H17 P7) | pending |
| E35 | Flaky test ledger (`flaky`): the check records what fails and passes on retry and proposes a fix after N times (H17 P12) | pending |
| A12 | Configurable languages in a `languages` block of `.claude/gw.json`: `code` (code, names and comments; replaces A8's fixed rule), `docs.primary` and `docs.others` (internal docs, log, roadmap and commits; the `docs/es` ↔ `docs/en` pairing reads them), `public.primary` and `public.others` (README, release, posts) and `ui` (today `visibleLanguages`); the agent language (the one user and agent speak) goes per user in `~/.claude/gw.json`, identified by `git config user.email`, with the docs primary as fallback; `language` and `visibleLanguages` migrate with `apply.py --update`; the MMC edits it in `1.1` (user, 2026-11-08) | pending |
| — | What [`pending.md`](records/pending.md) marks `0.7` | pending |
| D80 | Automatic warning of a stale `gw-scout-updates` seal (`0.6` closing harvest, private-project-1 P5) | pending |
| D83 | `apply.py --update` adds the names its migration renames to the project's `staleRefs` (extends D46) (`0.6` closing harvest, instalador P4) | pending |
| D87 | `gw-init` offers a dual licence: MIT for code and CC BY-NC-SA 4.0 for content, with the third-party note (`0.6` closing harvest, world-maker P6) | pending |
| E41 | The `pre-commit` rejects an author in `authorDeny` (empty by default in projects; Claude in this repo); changes the `AGENTS.md` line saying no hook checks the author (`0.6` closing harvest, private-project-1 P6) | pending |
| E48 | `red-without-fix.sh` reverts only the fix inside the test's file (`--patch <diff>` or `--lines A-B`): inline tests in Rust and others (`0.6.0` harvest, installer P1) | pending |
| D94 | `scripts/push.sh <branch>`: retries at 2, 4, 8 and 16 s and success only if `git ls-remote` matches `HEAD`; `AGENTS.md` points to it (`0.6.0` harvest, image-generator P4) | pending |
| D95 | `handoff.py add-pending` and `add-decision`: add to the log without reading it (`0.6.0` harvest, installer P3) | pending |
| D96 | Long log cells: `handoff.py` moves a row's closed items to "Done", or a second cap that fails (new key) (`0.6.0` harvest, image-generator P2) | pending |
| E49 | `gw-init` with `agentSignatures: false` writes the "no signatures" rule into `CLAUDE.md` against the attribution reminder (`0.6.0` harvest, image-generator P5) | pending |
| B31 | Warning when the context nears the window with the compaction budget spent (`recover.py --state` or `Stop`), before the compaction (`0.6.0` harvest, image-generator P7) | pending |

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
| E42 | `gw-seo` skill (SEO and link previews for static sites) brought from the portal: no portal paths, English names, tests in the check, es/en docs and its source's MIT LICENSE (`0.6` closing harvest, portal P1) | pending |
| E50 | `PreToolUse` hook on `Read` that warns, without blocking, when reading loose screenshots and suggests a contact sheet (the project's command in a key) (`0.6.0` harvest, image-generator P6) | pending |

## `0.9` "Stable"

| Id | Task | State |
|---|---|---|
| E8 | Full documentation review, by subagents | pending |
| E28 | Security review: hooks and scripts (inputs, paths, `eval`), `settings.json` permissions, CI and secrets; ideas from [`cloudflare/security-audit-skill`](https://github.com/cloudflare/security-audit-skill), read by a subagent, its licence checked before copying anything (user, 2026-11-05) | pending |
| E29 | Anonymisation review: private data in the history and the docs, and whether `private-check` and its `EXCEPTIONS` are still enough (user, 2026-11-05) | pending |
| E30 | Configurable-values review: thresholds, paths and behaviours still fixed in code move to `.claude/gw.json` and `docs/en/config.md` ("Everything configurable" rule, G4; user, 2026-11-05) | pending |
| E31 | Refactoring and upkeep of the `.md` files: duplicates, one fact in one place, sizes and stale text, with `writing-for-agents` (user, 2026-11-05) | pending |
| G2 | Versioned JSON output in the scripts the MMC uses | pending |
| E34 | `scripts/audit.py`: overlaps and duplicates across `AGENTS.md`, skills and `docs/`, with each datum's owner and the tokens it saves; used by `gw-opt-tokens`, E31 and the MMC (H17 P9) | pending |
| E36 | Behaviour tests for the skills (a couple of cases per skill, run by hand before each version) (H17 P13) | pending |
| E37 | Repo citations: `docs/design` and `docs/research` keep only public repos with a link and the user's private projects become "pilot project A/B"; the rule in one line of `AGENTS.md` and the `privateNames` key of `.claude/gw.json` checked by `names-check.py` ([`I-lifecycle.md`](design/I-lifecycle.md) Q8 and Q12; user, 2026-11-08) | pending |
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
| G11 | Instructions rendered from the config: the sources (`templates/`, `skills/`) carry both branches of each switch (`<!-- gw:if key -->…<!-- gw:else -->…<!-- gw:end -->`) and `apply.py` leaves only the one that applies in the installed copy; changing a key (an MMC button) re-renders what it affects and `doctor.py` warns when a copy does not match the config. Only behaviour switches (booleans and enums); documents for people keep both branches. First: a trial on one switch (B11's restricted mode) and a measure of the saving; decide what the plugin's skills do (Phase 9), since they are not rendered per project (user, 2026-11-11) | pending |

## `1.2` — MMC 3: profiles, environments and roles

| Id | Task | State |
|---|---|---|
| G5 | Layered profiles | pending |
| G8 | Environments and roles in the MMC | pending |
| D9 | Configurable (`environments` in `gw.json`) and new environments | pending |
| D10 | `rc` tags on `uat` | pending |
| D17 | Roles, with the git user check per environment (a warning layer; authority comes from branch protection; reopened in [`I-lifecycle.md`](design/I-lifecycle.md)) | pending |
| D67 | Done per environment and approvals: `environments[].done/approvers/requires`, `promote.py` (same sha, `Approved-by: <role> <user>` trailer, tag), destination `pre-push` that requires it; merging outside the development environment is done by a person with a role (H17 P4; user, 2026-11-08) | pending |
| I1 | `riskPaths`: risky paths that require a rollback plan in the record and a human approver in any environment | pending |
| I2 | Project declarations for `prod` (`environments[].requires`: rollback, observability, smoke) in `docs/records/declarations/`, dated and expiring | pending |

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
