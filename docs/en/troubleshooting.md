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
| `hooks-path` (FAIL) | `core.hooksPath` is unset: the workflow's git hooks do not run. With `CI=true` (GitHub Actions) it is a `WARN`: CI has no hooks installed | `git config core.hooksPath .githooks` |
| `hooks-path` (WARN) | Another manager owns it (husky, lefthook…): the workflow's hooks run only if chained | Add to the manager's `pre-push`, `pre-commit` and `commit-msg`: `"$(git rev-parse --show-toplevel)/.githooks/<hook>" "$@" \|\| exit 1` |
| `githook pre-push` / `pre-commit` / `commit-msg` (FAIL) | The file is missing or not executable | `/gw-update`; or `chmod +x .githooks/<hook>` (on Windows, `git update-index --chmod=+x .githooks/<hook>`) |
| `githook …` (WARN) | A version different from `.claude/gw.json`'s | `/gw-update` |
| `log` (FAIL) | The log does not exist, or has no "Next step" / "Siguiente paso" line | Create it with `/gw-update`; add the line to the file named by `log` |
| `log` (OK/FAIL) | "Siguientes pasos" / "Next steps" in the plural also counts as a next-step line | — |
| `glossary` (WARN) | The same `**Term**:` appears twice in `GLOSSARY.md` | Merge the entries into one |
| `ignored` (FAIL) | Git ignores a workflow file, or the `reviewMark` file: a commit would leave it out | Add `!<path>` to `.gitignore` and check `git check-ignore -v <path>` |
| `settings <event>` (WARN) | A hook command runs a workflow script (recognised by its `# galivelop-workflow v…` header) from outside `.claude/gw/scripts/`; a project's own script with the same name does not warn | Delete that entry from `.claude/settings.json` |
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
| `compaction` (WARN) | Cloud session without `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in its environment: it starts in `/home/user` (often with several repos), does not load `.claude/settings.json` and the context grows with no cap | Add `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` to the cloud environment's variables (environment menu → Edit); new sessions get it |
| `skill tests` (WARN) | A `.claude/skills/*/scripts/*.py` has no `test_<name>.py` next to it (`__init__.py`, `test_*.py` files and subfolders do not count) | Write `scripts/test_<name>.py`; the warning gives the path, and `python3 -m unittest discover -s <scripts> -p 'test_*.py'` runs it |
| `media tools` (WARN) | Only if the project uses `gw-media-content` (`.claude/gw/gw-media-content.md` exists, or the folder it names, `docs/difusion` by default): `node`, Playwright (from the current folder or `GW_PLAYWRIGHT_DIR`) or ImageMagick with WebP (`magick` or `convert` with WEBP in `-list format`) is missing | `apt install imagemagick webp` / `brew install imagemagick webp`; in the project, `npm i -D playwright && npx playwright install chromium` |
| `ci access` (WARN) | `origin` is on GitHub (https or ssh) but the agent cannot read the CI state: no `gh` on `PATH` (or `gh auth status` fails) and neither `GITHUB_TOKEN` nor `GH_TOKEN` is set. `AGENTS.md` asks to look at the CI of the last push when each block closes. It reads the machine running doctor; the token is never printed | Install GitHub CLI and run `gh auth login`, or `export GITHUB_TOKEN=<token>` |

## Pushing (`pre-push`)

`pre-push` says which commits it pushes, or that there is nothing new (did you forget `git commit`?). When it rejects
the push, the last line is the command that fixes it.

While it runs it keeps the marker `gw-push-en-curso` (its pid and, per ref it pushes, the local sha and the
branch) in git's common dir (`git rev-parse --git-common-dir`) and removes it when it ends, also if it fails or is
interrupted; the `Stop` hook uses it only not to tell an agent to push again the `HEAD` that is already being pushed
(a marker of another branch or of an older commit does not silence it). A marker left by a `kill -9` is ignored after
an hour or with a dead pid; it can be deleted by hand.

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
closed**: if it cannot check, it blocks and says why. It only looks at calls to the PR tools and commands with the word
`gh` followed by `pr` or `pulls` ("github" and "projects" do not count). A direct push to the protected branch is guarded by `pre-push`, in both `pushToProtected` modes.

| Block | Cause | Fix |
|---|---|---|
| `Blocked: … has no review mark` / `… not an ancestor` / `code changed after the review mark` | The PR brings code the review mark of the **same commit** does not cover | `/code-review` of the diff, push the fixes, `bash .claude/gw/scripts/revisado.sh`, `git push` |
| `Blocked: CI of PR #N is not green` / `could not verify CI` | CI did not pass or could not be read | Wait for or fix CI; authentication: `gh auth login` or `export GITHUB_TOKEN=…` |
| `cannot read PR #N` / `cannot query origin` | No network or no credential | Authenticate and retry; it blocks because it could not check |
| `the PR head … is not in this clone` | Shallow clone or branch not fetched | `git fetch --deepen=200 origin <branch>` |
| `no open PR for <branch>` / `without a PR number` | Merging with no number and no open PR for the branch | Pass the number: `gh pr merge <number>` |
| `PR #N of <repo> is closed` / `already merged` | The PR is no longer open: there is nothing to guard | `gh pr view <number> -R <repo>`; reopen it if it should go on |
| `requireRetro is on and the branch adds no retro-*.md…` (from `revisado.sh`) | With `requireRetro`, the branch lacks a new retro whose `**Status:**` paragraph (up to the first blank line) has a whole word among `aplicad*`, `rechazad*`, `aplazad*`, `decidid*`, `aprobad*` (or `applied`, `rejected`, `deferred`, `decided`, `approved`) and no `pendiente`/`pending`/`sin decidir`/`aún no`/`not yet` | `/retro`, present it, apply what is approved, record the status in that form and run `revisado.sh` again |
| `revisado: the tree has uncommitted changes to tracked files…` / `HEAD is not what origin/<branch> has` / `the branch does not include the latest origin/<protected>` | The mark is only written over what is pushed and up to date; untracked files do not count, modified ones do | Commit and push; `git merge origin/<protected>`; review again and mark. If a `commit-msg` hook demands the `Siguiente:` line: `bash .claude/gw/scripts/revisado.sh --footer "Siguiente: …"` |
| `es-codigo: content regex "…" is invalid` / `the classification failed (exit N), not because of a content regex` | A `content` regex does not compile (the reason is printed), or something else failed (python3, closed pipe) | Fix the regex: `python3 .claude/gw/scripts/config.py validate`; otherwise `python3 --version` and retry |
| `python3 is missing, so this PR call cannot be checked` / `the check could not run… Check python3 3.8+` | `python3` is missing (or crashed) and the command creates or merges a PR; other commands, `gh pr view` included, pass | Install Python 3.8 or later: `python3 --version` |

**Multi-repo (cloud) session.** It loads no project hooks. Before creating or merging a PR to the protected branch,
check by hand what that hook would check: the `revisado.sh` mark of the same commit and a green CI, and run
`git config core.hooksPath .githooks` before the first commit.

## Session opened outside the repo

If Claude Code is opened in another folder (the one holding several repos, the home folder), it does not load the
project's `.claude/settings.json`: no compaction limit, no start hook, no PR guard. `doctor.py` detects it
("the newest session transcript is in …"); `session-start.sh` only warns ("this session was started in …") when it is
loaded, that is, when the session is opened in a subfolder of the repo, not outside it. Fix: reopen from the
repo (`cd <repo> && claude`). Meanwhile: `git config core.hooksPath .githooks` and a manual check before pushing to
the protected branch.

Opened outside the repo, the warning from `session-start.sh` **cannot appear**, because the hook is not loaded
either; the reliable check is `python3 .claude/gw/scripts/doctor.py`. Without compaction the context grows without a cap and is
almost all the spend: when each phase closes, log up to date and `/clear`.

**In the cloud** the session always starts in `/home/user`, so reopening from the repo is not possible: the
compaction cap goes in the cloud environment's variables (`CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`; `doctor.py` warns
when it is missing), and after a compaction run `python3 .claude/gw/scripts/recuperar.py --estado` by hand.

## Skills with the same name in several repos of the session

If other repos are added to the session and registered as roots (in the cloud, `register_repo_root`), their
`.claude/skills/` come in too, and a same-name skill from another repo (`retro`, `selector`…) may shadow the
project's. Fix: repos that are only read are **not registered**; cloning them and reading them with a subagent is
enough. If they already are, invoke the project's skill and check the path it shows when it loads (`Base directory`).

Applying the workflow in the cloud, the same goes for the workflow repo: clone it with `git clone` if it is public,
or, if it is added with `add_repo`, do not register it as a root and check with `ls` the path it returns (it may
come lowercased and not exist).

## Claude Code auto mode

The auto-mode classifier may ask for permission, or refuse, when editing `.claude/settings.json`, `.claude/gw/scripts/`
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
