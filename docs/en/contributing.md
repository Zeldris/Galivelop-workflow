# Changing the workflow

> [Español](../es/contributing.md)

How Galivelop-workflow itself is modified. This repo **is worked on with its own workflow**: if a rule gets in the way
here, it gets in the way in every project. Read [`AGENTS.md`](../../AGENTS.md) and the log
([`docs/handoff.md`](../handoff.md)) first; the plan is [`docs/plan.en.md`](../plan.en.md).

## The cycle of a change

1. **Start from the working branch** the log names, with `main` brought in (`git fetch origin main` and
   `git merge origin/main`).
2. **Edit the sources**: `scripts/`, `skills/`, `templates/`, `schema/`, `docs/`. Never hand-edit the applied copy
   (`.claude/gw/`, `.claude/skills/`, `.githooks/`, `.claude/settings.json`): it is generated.
3. **Refresh this repo's copy**:

   ```bash
   python3 scripts/apply.py .
   python3 scripts/apply.py --check .      # must exit 0
   ```

   Without this, `tests/check.sh` fails ("workflow copy in sync"): the copy has to be identical to the sources.
4. **Add the test case** (below) and run the check:

   ```bash
   bash scripts/check.sh      # runs bash tests/check.sh and records the green: pre-push does not repeat it
   ```

5. **CHANGELOG entry**, **log**, commit and push, in the same commit (below).

## Tests for every change

- **Every change to a hook or script comes with its case in the tests** (`tests/test_*.py`, which build a temporary
  git repo): `test_hooks.py`, `test_review_before_main.py`, `test_doctor.py`, `test_apply.py`… A new check in
  `doctor.py` is a new case in `test_doctor.py`.
- **A new test must fail without its fix.** Check with the fix still uncommitted:

  ```bash
  bash scripts/red-without-fix.sh "python3 -m unittest tests.test_doctor.Class.test_case" scripts/doctor.py
  ```

  Options: `--fails-with REGEX` (the failure without the fix must print REGEX, so it does not fail for another
  reason) and `--ran-one REGEX` (the run with the fix must print exactly one line matching REGEX, the one your
  runner prints per test, e.g. `'^ok '`: it fails if the filter matches nothing or runs more than one test).
  If the fix is already committed, `--fix-at COMMIT` runs the "without the fix" step with the fix files as they were
  at `COMMIT^`. The red must be an assertion red: if the test fails without the fix only because it cannot load
  (syntax, import, compile or collection error) the script reports it (with the line that
  matched) without changing the exit status; `--reject-compile-red` makes it exit 1, unless `--fails-with REGEX` is
  given (`--compile-re REGEX` replaces the list of load errors).

- A new or changed **skill** passes `tests/test_skills.py` (name = folder, `description` 1 to 1024 characters,
  `license`, `compatibility`, `metadata.version`, under 200 lines). It is written in **English**, applying the
  `writing-for-agents` skill.
- **Templates:** `tests/test_templates.py` applies the workflow to an empty repo, checks the expected result and that
  repeating it changes nothing.
- **bash 3.2** (macOS): no `mapfile`, no associative arrays. CI runs on Linux and macOS.

## Repo rules (summary of `AGENTS.md`)

- **Hooks and scripts:** the root comes from the script's path or `git rev-parse --show-toplevel`, never from
  `$CLAUDE_PROJECT_DIR` or the current directory; a push hook checks **the commit being pushed**; they **fail closed**
  when data is missing; every message is in English and carries the command that fixes the failure.
- **One fact, one place:** the version only in `.claude-plugin/plugin.json`; the project config is read only by
  `scripts/config.py`.
- **Languages:** human documentation in Spanish and English, **paired** (`docs/es/` ↔ `docs/en/`, `README.md` ↔
  `README.es.md`, with the link to the pair in the first lines); `SKILL.md` in English only.
- **What can be checked is done by a script**, not an agent; skills and guides decide only what needs judgement.
- **Other repos are read, never modified** from here; they are read with a subagent that returns a summary with paths.
- **Quality first:** a token saving that worsens the result is not a saving.

## Version and CHANGELOG

The version follows [SemVer](https://semver.org/) and lives **only** in `.claude-plugin/plugin.json`:

| Change | Bumps |
|---|---|
| The config or a template changes in a way that requires touching projects already using it | **major** |
| A new skill or hook, or a compatible improvement | **minor** |
| Fixes | **patch** |

Only the latest published minor gets patches (plan §7): a harvest sends fixes to its next patch (`0.5.x` today) and new features to the next minor not yet under way (`0.7` today, with `0.6` being built), following the [roadmap](../roadmap.en.md).

To split a patch off the minor's branch, from the patch branch: `bash scripts/backport.sh [--from <branch>] <sha>...` applies the commits with `cherry-pick -x` (oldest first; `-m 1` for merges), resolves with the patch's version any conflict that is only in the log or the roadmap, skips the ones that end empty and finally checks that every sha is in the patch; on a code conflict it stops and says what to do and which shas remain. With `--from` it also brings, in a commit of its own, the harvest files the branch has and the patch lacks (`version.py --release` requires them); with no shas, `--from` brings just those, and `--refs <id>` sets the `Refs:` id of that commit when the patch branch's `commit-msg` accepts none of the brought commits' ids.

Each version has an entry in [`CHANGELOG.md`](../../CHANGELOG.md) with `### ES` and `### EN`, both with the same
content; the check fails when `plugin.json`'s version has no entry. When the version goes up, **every** skill's
`metadata.version` (`test_skills.py` requires it) and the `# galivelop-workflow vX.Y.Z` headers of scripts and templates move with it, and projects
pick it up with `/gw-update`. They are not edited by hand: `python3 scripts/version.py X.Y.Z` moves them all and
leaves the CHANGELOG entry to fill in; without an argument it checks none was left behind.

**Every change to a copyable file** (`scripts/`, `skills/`, `templates/`, `schema/`) between two releases **bumps the
version**, a patch at least: a project that copied in between would see "local edits" it never made.
`python3 scripts/version.py --release` checks it against the last `vX.Y.Z` tag reachable from the commit (it needs the
tags: `git fetch --tags origin`), and this repo's `check` runs it on every push to `main` (`GW_PUSH_PROTECTED`) and in `bash scripts/check.sh` on a `version/*` branch (`releaseCheckBranches`). `python3 scripts/version.py --suggest` suggests the bump from the non-merge commits since that
tag (`feat` → minor, `fix` and `perf` → patch, `!` or `BREAKING CHANGE:` → major, minor in `0.x`) and warns when
`plugin.json` does not match; it only suggests (exit 0) and `--release` prints the same as a warning.
`--release` also requires every repo path quoted in backticks in the new CHANGELOG entry (`docs/…`, `scripts/…`, `CHANGELOG.md`…; read from
`HEAD`, not the working tree) to exist in the tree being released, to have existed in the history (an old name, "antes X") or to be ignored by
git (`.claude/gw.local.json`); a token counts as a path when it starts with a top-level directory (of `HEAD` or the history), ends in a file
extension or in `/`, or is a root document by name. Paths with placeholders (`vX.Y.Z`, `<…>`, `*`, `YYYY-MM-DD`, `NNN`, `…`) are skipped. Paths of
the project that installs the flow go without backticks, or with the full path in this repo (`skills/gw-media-content/scripts/figures.py`).

**Releasing a version:** on `main` (with the three phases done), the CHANGELOG entry dated instead of
"Unreleased", and the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`. The `release.yml` workflow checks that the tag,
`plugin.json` and the markers agree and that the version went up, runs the check and creates the release with that entry.

## Commit, log and `main`

- **Commit and push at every stable point**, never more than 30-45 minutes without pushing; **the log in the same
  commit**.
- Message in Spanish; first line with the phase (`Fase 4: …`); body with what was done, what is left and the state of
  the tests; **last line `Siguiente: <next concrete step>`**, in the same final block as the attribution.
- If you must stop with something red: commit with `WIP:` at the start and, in the log, what fails and why.
- **To `main` only with the person's confirmation**, and `/code-review` of the diff against `origin/main` first. `main`
  is the latest published version, the one other projects install.
- **When each phase closes**, stop and report what is done and what the next phase is.

## Proposals from projects

Improvements arriving from projects come in through `gw-harvest` ([patterns](patterns.md#harvesting-improvements-back)):
each is a file in `docs/proposals/` that the person approves; the approved one is done with this same cycle.
