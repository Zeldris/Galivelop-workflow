# Configuration: `.claude/gw.json`

> [Español](../es/config.md)

Everything that varies between projects, and nothing else. Only `scripts/config.py` reads it (one fact, one place);
every other script asks it for keys. It is validated against [`schema/gw.schema.json`](../../schema/gw.schema.json):
an unknown or misspelled key is an error, and the scripts **fail closed** (exit 2) with the command that checks it:

```bash
python3 .claude/gw/scripts/config.py validate     # is it valid?
python3 .claude/gw/scripts/config.py get check    # a key's value (with its default)
```

The full, commentable example is [`templates/gw.json`](../../templates/gw.json); `aplicar.py --init` fills it from
flags ([apply](apply.md)). Lists are JSON arrays. Regexes use Python syntax and, in JSON, the backslash is doubled
(`"\\.md$"`).

## Required keys

| Key | What it is | Default | Example | Read by |
|---|---|---|---|---|
| `version` | Workflow version the project was applied with (`X.Y.Z`). Bumped by hand after `/gw-update` | (none) | `"0.1.0"` | `session-start.sh` and `doctor.py` (warn when the copy differs), `aplicar.py` |
| `language` | Language of templates and replies: `es` or `en` | (none) | `"en"` | `aplicar.py` (which templates it copies), `revisado.sh` (message language) |
| `log` | Path of the hand-off log, from the repo root | (none; `--init` sets `docs/traspaso.md` for es and `docs/handoff.md` for en) | `"docs/handoff.md"` | `recuperar.py`, `doctor.py`, `prepush-ramas.sh`, `aplicar.py` |
| `protectedBranch` | The branch that takes only reviewed code | (none) | `"main"` | `pre-push`, `revision-antes-de-main.sh`, `revisado.sh`, `fusionar.sh`, templates and CI |
| `pushToProtected` | How code reaches it: `direct` (pushed straight) or `pr` (by pull request: the `PreToolUse` hook also guards PR creation and merging). In both, `pre-push` requires the review mark on every direct push that brings code | (none) | `"pr"` | `pre-push`, `revision-antes-de-main.sh` |
| `check` | Commands run **in order** on the commit being pushed; all must pass. At least one | (none) | `["npm run check"]` | `pre-push`, `fusionar.sh`, `doctor.py`, CI |
| `reviewMark` | Committed file holding the reviewed commit's sha | (none; `--init` sets `docs/registros/revisado.txt`) | `"docs/registros/revisado.txt"` | `revisado.sh` (writes it), `es-codigo.sh`, `pre-push`, `revision-antes-de-main.sh` |
| `content` | Regexes (on repo-relative paths) of what **is content, not code**: it needs no `/code-review` (no scripts, nor what an agent reads as instructions: it goes up without a mark) | (none; may be `[]`, then everything is code; `--init` sets `^docs/`, the root documentation `.md` files (their translations too, `README.es.md`, and `CHANGELOG.md`) and the `.md` files under `.claude/skills/`) | `["^docs/", "^README\\.md$"]` | `es-codigo.sh`, and through it `pre-push` and `revision-antes-de-main.sh` |

## Optional keys

| Key | What it is | Default | Example | Read by |
|---|---|---|---|---|
| `$schema` | Path or URL of the schema, for the editor | – | `"gw/schema/gw.schema.json"` | the editor |
| `visibleLanguages` | Languages every user-visible text must exist in | `[]` | `["es", "gl", "en"]` | `REVIEW.md` (applied by `/code-review` and agents) |
| `logRows` | Log with **one row per branch**, at most 600 characters: each branch writes only in its own | `false` | `true` | `bitacora.py`, `prepush-ramas.sh`, `recuperar.py` |
| `install` | Commands that install dependencies (in the cloud and CI) | `[]` | `["npm ci"]` | `session-start.sh` (cloud only, when the lockfile changed), CI, `doctor.py` |
| `ciInstall` | Install commands for CI only: the CI template runs these instead of `install`. Without the key, CI runs `install`; with `[]`, it installs nothing. It is left out of `templates/gw.json` on purpose (a copied `[]` would switch CI installs off) | no key (CI uses `install`) | `["npm ci --ignore-scripts"]` | CI (`comprobar.yml`) |
| `setup` | Commands that run in the cloud **after** `install`, one after another in the same start-up hook (`SessionStart` hooks run in parallel, so the order lives here): a build, a data seed. They rerun when `install` reruns (a lockfile or the list changed). If one fails or passes `GW_COMMAND_TIMEOUT` seconds (900 by default), the hook reports it with the command to run by hand and stops; the next session retries. The CI template does not run `setup` The limit is enforced by a bash watchdog (no `timeout` needed, so it works on stock macOS): the command runs in its own process group and, past the limit, the whole group gets TERM and, a few seconds later, KILL. A process that detaches itself from the group (`setsid`, a daemon) can survive. | `[]` | `["cargo build"]` | `session-start.sh`, `doctor.py` |
| `requireRetro` | `revisado.sh` requires a `retro` with the person's decision on the branch before marking; reads the whole `**Status:**` paragraph and accepts applied, rejected, deferred, decided or approved; `revisado.sh --footer "Siguiente: …"` adds that line to the mark commit; untracked files do not count as changes | `false` (in `templates/gw.json` too; `--init --require-retro true` turns it on) | `true` | `revisado.sh`, `retro` skill |
| `roadmap` | Reserved for the optional milestones module; no script reads it yet | `false` | `false` | (nobody yet) |
| `selector` | `{ "cases": [ { "case", "skill", "sessionModel", "subagentModel" } ] }`: the project's own rows for the `selector` | no rows | `{"cases": [{"case": "Data migration", "skill": "orchestrate-dealer", "sessionModel": "Opus"}]}` | `selector` skill |
| `logSections` | Headings of the log sections `recuperar.py --estado` puts back after a compaction or `/clear` (without `logRows`) | `[]`: the first section and the one named "Pendiente"/"Pending" | `["Current state", "Pending"]` | `recuperar.py` |
| `designReferences` | Products, frameworks or standards each design proposal is contrasted with | `[]` | `["WCAG 2.2", "Material Design 3"]` | `grilling` and `selector` skills |
| `protectedPaths` | Path prefixes an agent (`CLAUDECODE=1`) may not commit: other people's drafts | `[]` | `["docs/drafts/"]` | `.githooks/pre-commit` |
| `staleRefs` | Case-insensitive regexes that must not appear in `docs/` or the READMEs: a renamed task, a removed phase. Also accepts `{ "patterns": [...], "skip": [globs] }`: `skip` lists files or folders (repo paths; `*` stays inside a folder, `**` crosses, a trailing `/` is the whole folder) that are not read, besides the log and `.claude/`, which are always skipped (e.g. `retro-*.md`, which quote old paths). A glob that matches nothing does nothing The globs support only `*`, `**` and `?` (no brackets, no gitignore semantics): `*` and `?` do not cross folders, `**` does; an entry without wildcards (`docs/registros`, with or without a trailing `/`) is that file or that folder and everything under it, and `docs/**` also matches `docs`; a leading `/` is ignored. | `[]` | `["old phase 9"]` or `{"patterns": ["phase 9"], "skip": ["docs/records/retro-*.md"]}` | `enlaces-md.py` |
| `linkRoots` | Folders (relative, no `..`) whose Markdown writes relative links from the repo root instead of from its own folder (e.g. a saved PR description); `enlaces-md.py` resolves them that way. `.` is the whole repo A leading `/` resolves from the repo root; a link that leaves the repo is reported, not looked up on the disk. | `[]` | `["docs/prs"]` | `enlaces-md.py` |
| `scoutDir` | Folder (relative, no `..`) where `scout-updates` keeps its memory: `architecture.md`, `proposals.md` and the reports. | `.claude/gw/scout` | `"docs/scout"` | `scout-updates` (`compare.py`) |
| `checkWrapper` | Prefix of every `check` and `relatedTests` command (e.g. `docker compose run --rm app`): it always runs `<prefix> bash -c '<command>'` (with `cd <cwd> &&` inside when the entry has `cwd`), so it also covers a compound command (`a && b`). The CI template does not apply `checkWrapper`: it is for the local host (e.g. a sandbox); CI runners do not need it. | `""` (no prefix) | `"docker compose run --rm app"` | `pre-push`, `tests-relacionados.sh` |
| `relatedTests` | `{ "fast": [...], "slow": [...] }`: tests of what changed. Each entry is a command (string) or `{ "command", "paths", "cwd" }`: `paths` is a regex filtering the changed files and `cwd` a folder the command runs from (`{files}` is relative to it). `fast` runs on every push; `slow` only when some changed file (in its scope) still exists; `{files}` is replaced by the changed files | no commands | `{"fast": [{"command": "npx vitest related {files}", "paths": "\\.tsx?$", "cwd": "web"}], "slow": []}` | `tests-relacionados.sh` (called by `pre-push`) |
| `worktreeLinks` | Paths (relative, no `..`) of the main checkout that `pre-push` links into the temporary worktree where `check` runs; missing ones are skipped and a path of the commit is never overwritten | `["node_modules", ".venv"]` | `["node_modules", "backend/node_modules", ".env"]` | `pre-push` |
| `worktreeDir` | Folder (absolute, or relative to the repo root) under which `pre-push` creates its temporary worktrees, for a sandbox that cannot see `$TMPDIR` (e.g. Flatpak); a relative one should be in `.gitignore` and outside `.git/` | `""` (`${TMPDIR:-/tmp}`) | `".cache/gw-worktrees"` | `pre-push` |
| `plan` | Plan or roadmap files or folders where tasks are ticked or struck through | `[]` | `["docs/roadmap.md"]` | `bitacora.py` |
| `taskId` | Regex of the project's task ids | `[A-Z]{2,5}-\\d+` | `"(INS\|FLU)-\\d+"` (capturing groups are treated as non-capturing) | `bitacora.py` |

## Notes

- **`check` is a list of commands**, not a single script: each runs with `bash -c` at the root of the commit being
  pushed. One that does not exist is caught by `doctor.py` before a push fails. The `pre-push` passes them
  `GW_PUSH_PROTECTED=true` when the push goes to the protected branch (`false` otherwise; unset outside the hook), so a
  command can run only before `main`, e.g. `[ "${GW_PUSH_PROTECTED:-}" != true ] || <command>`.
- **`check` runs in a temporary worktree** when the working copy is not clean (or the push is not what it holds): it
  lives in `${TMPDIR:-/tmp}/gw-pre-push-wt-<repo id>/wt.XXXXXX.d` (or under `worktreeDir`), never inside `.git/`
  (jest and similar tools ignore any path with a `/.git/` segment), and is removed on every exit (also on Ctrl-C or
  `kill`). If a push dies unable to clean up, the next one removes the orphaned worktrees older than 24 h whose process
  is gone; two pushes at once do not step on each other. What is linked from the main checkout is set by `worktreeLinks`. A failing command's log
  is kept (`full log: <path>`); when it passes, it is deleted.
- **`pushToProtected`** says how code reaches the protected branch today. A direct push that brings code always needs
  the mark in `pre-push`, with `direct` and with `pr`; with `pr`, the PR hook also asks for it when the pull request
  is created or merged. The config is read from the pushed commit, not the working copy; for the protected branch,
  `content` and `reviewMark` come from its remote tip (from what is pushed only while it has no config yet, with a
  warning), and the branch is protected if either of them or the working copy says so: a commit cannot relax the
  rule that judges it.
- **`content` and the mark.** A change touching only `content` files needs no review; any other does. `revisado.sh`
  writes the reviewed commit to `reviewMark`, and the mark must be an ancestor of what is pushed with no code after it.
  `.claude/gw.json`, `.claude/settings.json`, `.claude/gw/` and `.githooks/` are always code, whatever `content` says.
  To see how a path is classified and why: `bash .claude/gw/scripts/es-codigo.sh --explicar <path>...`.
- **`logRows`** goes with the row-based log template (``| **Current task · `branch`** | … |``); the push checks that
  each branch writes only in its own row, that every "Task in progress" row names its branch, and that each task
  closed in the plan is recorded in "Done": struck through there, or named on a line that starts with a date (an
  unstruck bullet is not enough).
- After changing the workflow version, bump `version` by hand (`/gw-update` does it): `doctor.py` compares that number
  with the copied headers.
