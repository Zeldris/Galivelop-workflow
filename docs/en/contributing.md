# Changing the workflow

> [Español](../es/contribuir.md)

How Galivelop-workflow itself is modified. This repo **is worked on with its own workflow**: if a rule gets in the way
here, it gets in the way in every project. Read [`AGENTS.md`](../../AGENTS.md) and the log
([`docs/traspaso.md`](../traspaso.md)) first; the plan is [`docs/plan.en.md`](../plan.en.md).

## The cycle of a change

1. **Start from the working branch** the log names, with `main` brought in (`git fetch origin main` and
   `git merge origin/main`).
2. **Edit the sources**: `scripts/`, `skills/`, `templates/`, `schema/`, `docs/`. Never hand-edit the applied copy
   (`.claude/gw/`, `.claude/skills/`, `.githooks/`, `.claude/settings.json`): it is generated.
3. **Refresh this repo's copy**:

   ```bash
   python3 scripts/aplicar.py .
   python3 scripts/aplicar.py --check .      # must exit 0
   ```

   Without this, `tests/comprobar.sh` fails ("workflow copy in sync"): the copy has to be identical to the sources.
4. **Add the test case** (below) and run the check:

   ```bash
   bash scripts/check.sh      # runs bash tests/comprobar.sh and records the green: pre-push does not repeat it
   ```

5. **CHANGELOG entry**, **log**, commit and push, in the same commit (below).

## Tests for every change

- **Every change to a hook or script comes with its case in the tests** (`tests/test_*.py`, which build a temporary
  git repo): `test_ganchos.py`, `test_revision_main.py`, `test_doctor.py`, `test_aplicar.py`… A new check in
  `doctor.py` is a new case in `test_doctor.py`.
- **A new test must fail without its fix.** Check with the fix still uncommitted:

  ```bash
  bash scripts/rojo-sin-arreglo.sh "python3 -m unittest tests.test_doctor.Class.test_case" scripts/doctor.py
  ```

  Options: `--fails-with REGEX` (the failure without the fix must print REGEX, so it does not fail for another
  reason) and `--ran-one REGEX` (the run with the fix must print exactly one line matching REGEX, the one your
  runner prints per test, e.g. `'^ok '`: it fails if the filter matches nothing or runs more than one test).

- A new or changed **skill** passes `tests/test_skills.py` (name = folder, `description` 1 to 1024 characters,
  `license`, `compatibility`, `metadata.version`, under 200 lines). It is written in **English**, applying the
  `writing-for-agents` skill.
- **Templates:** `tests/test_plantillas.py` applies the workflow to an empty repo, checks the expected result and that
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

`0.4` is the last `0.x` minor (plan §7): a harvest sends fixes to a `0.4.x` patch and notes new features for `1.0.0` and later.

Each version has an entry in [`CHANGELOG.md`](../../CHANGELOG.md) with `### ES` and `### EN`, both with the same
content; the check fails when `plugin.json`'s version has no entry. When the version goes up, **every** skill's
`metadata.version` (`test_skills.py` requires it) and the `# galivelop-workflow vX.Y.Z` headers of scripts and templates move with it, and projects
pick it up with `/gw-update`. They are not edited by hand: `python3 scripts/version.py X.Y.Z` moves them all and
leaves the CHANGELOG entry to fill in; without an argument it checks none was left behind.

**Every change to a copyable file** (`scripts/`, `skills/`, `templates/`, `schema/`) between two releases **bumps the
version**, a patch at least: a project that copied in between would see "local edits" it never made.
`python3 scripts/version.py --release` checks it against the last `vX.Y.Z` tag reachable from the commit (it needs the
tags: `git fetch --tags origin`), and this repo's `check` runs it on every push to `main` (`GW_PUSH_PROTECTED`).

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
each is a file in `docs/propuestas/` that the person approves; the approved one is done with this same cycle.
