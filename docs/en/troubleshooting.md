# Known problems

> [Español](../es/problemas.md)

What to do when something in the workflow does not work. Script messages are in English and end with the command that
fixes the failure; here they are grouped by origin so you can find them by what you see. To start, almost always:

```bash
python3 .claude/gw/scripts/doctor.py
```

## Claude Code hooks

| Symptom | Cause | Fix |
|---|---|---|
| A hook does not run | Invalid JSON in `.claude/settings.json`, event or matcher misspelled (they are case-sensitive: `bash` ≠ `Bash`), wrong settings file, session not restarted | `/hooks` shows what is loaded; `python3 -m json.tool .claude/settings.json`; restart the session |
| "Nothing happens" with exit 0 | A hook that exits 0 with no output is neither seen nor blocks nor approves | To block, exit 2 with the reason on `stderr` (as the workflow's hooks do); to debug, write to a log |
| A hook does not block | It is on `PostToolUse` or `SessionStart`, which cannot block | Put it on `PreToolUse` |
| Project hooks do not run in the cloud | The session has **several repos**: it loads no repo's `.claude/settings.json` hooks | One session, one repo; if you must mix, run by hand what the hook would do (see below) |
| The plugin does not show up in the cloud | The cloud ignores the repo's `extraKnownMarketplaces` and `enabledPlugins` | That is why the workflow is **copied** into the repo (`aplicar.py`), not dependent on the plugin |
| A private marketplace fails locally | No non-interactive git credential | `gh auth login && gh auth setup-git`, or SSH with an agent |
| A script cannot find the repo | The cloud starts in `/home/user`; neither `$CLAUDE_PROJECT_DIR` nor the current directory is the root | The workflow's scripts already take the root from their own path or `git rev-parse --show-toplevel`; do the same in yours |

## `doctor.py`: every `FAIL` and `WARN`

| Check | What it says | Fix |
|---|---|---|
| `config` (FAIL) | `.claude/gw.json` is missing, not JSON, or breaks the schema (unknown key, empty value…) | `python3 .claude/gw/scripts/config.py validate` names the line; keys in [config](config.md); if missing, apply the workflow ([apply](apply.md)) |
| `hooks-path` (FAIL) | `core.hooksPath` is unset: the workflow's git hooks do not run | `git config core.hooksPath .githooks` |
| `hooks-path` (WARN) | Another manager owns it (husky, lefthook…): the workflow's hooks run only if chained | Add to the manager's `pre-push` and `pre-commit`: `"$(git rev-parse --show-toplevel)/.githooks/<hook>" "$@" \|\| exit 1` |
| `githook pre-push` / `pre-commit` (FAIL) | The file is missing or not executable | `/gw-update`; or `chmod +x .githooks/<hook>` (on Windows, `git update-index --chmod=+x .githooks/<hook>`) |
| `githook …` (WARN) | A version different from `.claude/gw.json`'s | `/gw-update` |
| `log` (FAIL) | The log does not exist, or has no "Next step" / "Siguiente paso" line | Create it with `/gw-update`; add the line to the file named by `log` |
| `check command` (FAIL) | The first word of a `check` command is neither on `PATH` nor a file in the repo | Install that tool or fix `check` in `.claude/gw.json` |
| `install command` (WARN) | The same for `install` | Same |
| `ci` (WARN) | No workflow under `.github/workflows` | `mkdir -p .github/workflows && cp <workflow>/templates/github/comprobar.yml .github/workflows/` |
| `settings` (FAIL) | `.claude/settings.json` is missing or invalid JSON | `/gw-update`; fix it and check with `python3 -m json.tool` |
| `settings SessionStart` (FAIL) | An entry with no `matcher` runs on every start, resume, `clear` and `compact`; or one with `compact` runs something other than `recuperar.py --estado` | Give it `"matcher": "startup\|resume\|clear"`; move that command to an entry without `compact` |
| `settings <event>` (FAIL) | A hook command points to a file that does not exist | `/gw-update` restores the scripts; or fix the command |
| `settings PreToolUse` (FAIL) | The hook guarding PR creation and merging (`revision-antes-de-main.sh`) is missing | Add it from `templates/claude/settings.json` (`/gw-update`) |
| `agents` (FAIL) | Neither `AGENTS.md` nor `CLAUDE.md` exists | `/gw-init` |
| `agents` (WARN) | Neither mentions `orchestrate-dealer`: the session may not deal work to subagents | Add to `AGENTS.md`: "Multi-step work is dealt to subagents (skill `orchestrate-dealer`); the main session plans, decides and reviews." |
| `skills` (WARN) | Copied skills at a version different from `gw.json`'s | `/gw-update` |
| `session` (WARN) | The newest session was opened outside the repo and may not have loaded `.claude/settings.json` | Reopen Claude Code from the repo: `cd <repo> && claude` |

## Pushing (`pre-push`)

`pre-push` says which commits it pushes, or that there is nothing new (did you forget `git commit`?). When it rejects
the push, the last line is the command that fixes it.

| Message | Cause | Fix |
|---|---|---|
| `check failed on <sha>: '<command>'` | A `check` command fails **on the commit being pushed** (not your working copy); the full log is at the path it prints | Reproduce with the same command, fix, commit and push; `--no-verify` only for a red `WIP:` commit |
| `the push adds *.rej / *.orig leftovers` | Leftovers of a patch or merge | `git rm -- <file> && git commit` |
| `the push has conflict markers` | `<<<<<<<` or `>>>>>>>` left in what is pushed | Resolve and `git commit -a` |
| `the pushed commit has no review mark` / `the review mark … is not an ancestor` / `code changed after the review mark` | Direct push to the protected branch with unreviewed code | `/code-review` of the diff against `origin/<protected>`, push the fixes, then `bash .claude/gw/scripts/revisado.sh && git push` |
| `…this clone is shallow…` / `is not a commit in this clone` | Shallow clone (typical in the cloud): the mark or the remote branch lies beyond its history | `git fetch --deepen=200 origin <branch>` and repeat |
| `the remote <branch> is at <sha>, which this clone does not have` | The latest commit of the protected branch is missing | The `git fetch` command it prints |
| `cannot read '<key>' from .claude/gw.json` | Invalid config | `python3 .claude/gw/scripts/config.py validate` |
| `the workflow scripts are missing` | `.claude/gw/scripts/` is missing | `/gw-update` |
| `prepush-ramas.sh refused the push` | With `logRows`: another branch's log row, too long, or tasks closed but not moved to "Done" | What it prints; for a shared row: `BITACORA_COMPARTIDA=1 git push` |
| `the related tests failed` | The `relatedTests` fail | Fix them or adjust the key |
| `pre-push` does not run | `core.hooksPath` unset or another manager's; no execute bit (Windows) | `git config core.hooksPath .githooks`; `git update-index --chmod=+x .githooks/pre-push` |

## Creating or merging a PR (`revision-antes-de-main.sh`)

The `PreToolUse` hook that guards `create_pull_request`, `merge_pull_request` and `gh pr create|merge`. It **fails
closed**: if it cannot check, it blocks and says why. A direct push to the protected branch is guarded by `pre-push`, in both `pushToProtected` modes.

| Block | Cause | Fix |
|---|---|---|
| `Blocked: … has no review mark` / `… not an ancestor` / `code changed after the review mark` | The PR brings code the review mark of the **same commit** does not cover | `/code-review` of the diff, push the fixes, `bash .claude/gw/scripts/revisado.sh`, `git push` |
| `Blocked: CI of PR #N is not green` / `could not verify CI` | CI did not pass or could not be read | Wait for or fix CI; authentication: `gh auth login` or `export GITHUB_TOKEN=…` |
| `cannot read PR #N` / `cannot query origin` | No network or no credential | Authenticate and retry; it blocks because it could not check |
| `the PR head … is not in this clone` | Shallow clone or branch not fetched | `git fetch --deepen=200 origin <branch>` |
| `no open PR for <branch>` / `without a PR number` | Merging with no number and no open PR for the branch | Pass the number: `gh pr merge <number>` |
| `requireRetro is on and the branch adds no retro-*.md…` (from `revisado.sh`) | With `requireRetro`, a retro with the person's decision is missing | `/retro`, present it, apply what is approved, record the status and run `revisado.sh` again |
| `revisado: the tree has uncommitted…` / `HEAD is not what origin/<branch> has` / `the branch does not include the latest origin/<protected>` | The mark is only written over what is pushed and up to date | Commit and push; `git merge origin/<protected>`; review again and mark |
| `the check could not run… Install python3 3.8+` | `python3` is missing | Install Python 3.8 or later |

**Multi-repo (cloud) session.** It loads no project hooks. Before creating or merging a PR to the protected branch,
check by hand what that hook would check: the `revisado.sh` mark of the same commit and a green CI, and run
`git config core.hooksPath .githooks` before the first commit.

## Session opened outside the repo

If Claude Code is opened in another folder (the one holding several repos, the home folder), it does not load the
project's `.claude/settings.json`: no compaction limit, no start hook, no PR guard. `session-start.sh` and
`doctor.py` warn ("the newest session transcript is in …" / "this session was started in …"). Fix: reopen from the
repo (`cd <repo> && claude`). Meanwhile: `git config core.hooksPath .githooks` and a manual check before pushing to
the protected branch.

## Claude Code auto mode

The auto-mode classifier may ask for permission, or refuse, when editing `.claude/settings.json`, `.claude/hooks/`
and `.githooks/`: exactly what `/gw-init` and `/gw-update` write, so the failure shows up halfway through the
application. `aplicar.py` prints a note ("Claude Code's auto mode may ask for permission…").

- **Ask the person for permission first** before running `aplicar.py`, or have the person run it in their own
  terminal: `python3 <workflow>/scripts/aplicar.py <project>`.
- After a refused or interrupted call, `git status` and `git diff` before repeating it: half may have been written.
- It is idempotent: repeating it completes what is missing.

## Hook managers, clones and systems

| Symptom | Cause | Fix |
|---|---|---|
| "another hook manager installed hooks" warning at start | Own hooks in `.git/hooks`, or another manager's `core.hooksPath` | The warning carries the chaining line; see [apply](apply.md#existing-projects) |
| "The mark is not an ancestor" for no reason | Shallow clone | `git fetch --deepen=200 origin <branch>` |
| A script fails only on macOS | macOS `bash` is 3.2: no `mapfile`, no associative arrays | Write for bash 3.2 (CI also runs on macOS) |
| Odd failures on Windows | CRLF line endings in scripts; symbolic links | `.gitattributes` with `*.sh text eol=lf` (and `*.py`, `.githooks/*`); use **Git Bash or WSL**, not `cmd` or PowerShell; no symbolic links |
| `CLAUDE.md` exists and `AGENTS.md` is not read | Claude reads `AGENTS.md` only when there is no `CLAUDE.md` | `@AGENTS.md` in `CLAUDE.md` (the template does it) |
| `install` commands fail at start | `session-start.sh` runs them only in the cloud and when the lockfile changed | The warning gives the log and the command to run them by hand |
| `aplicar.py --check` exits 1 | The copy differs from the workflow, a `*.gw-nuevo` is pending, or a file the workflow no longer has | Read what it prints; `/gw-update`; resolve and delete the `*.gw-nuevo` |

If a failure is not here, write it down: `/retro` collects it in its "For Galivelop-workflow" section and it reaches
this file ([patterns](patterns.md#harvesting-improvements-back)).
