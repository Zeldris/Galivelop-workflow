# Configuration: `.claude/gw.json`

> [Español](../es/config.md)

Everything that varies between projects, and nothing else. Only `scripts/config.py` reads it (one fact, one place);
every other script asks it for keys. It is validated against [`schema/gw.schema.json`](../../schema/gw.schema.json):
an unknown or misspelled key is an error, and the scripts **fail closed** (exit 2) with the command that checks it:

```bash
python3 .claude/gw/scripts/config.py validate     # is it valid?
python3 .claude/gw/scripts/config.py get check    # a key's value (with its default)
```

The full, commentable example is [`templates/gw.json`](../../templates/gw.json); `apply.py --init` fills it from
flags ([apply](apply.md)). Lists are JSON arrays. Regexes use Python syntax and, in JSON, the backslash is doubled
(`"\\.md$"`).

## Required keys

| Key | What it is | Default | Example | Read by |
|---|---|---|---|---|
| `version` | Workflow version the project was applied with (`X.Y.Z`). Bumped by hand after `/gw-update` | (none) | `"0.1.0"` | `session-start.sh` and `doctor.py` (warn when the copy differs), `apply.py` |
| `language` | Language of templates and replies: `es` or `en` | (none) | `"en"` | `apply.py` (which templates it copies), `reviewed.sh` (message language) |
| `log` | Path of the hand-off log, from the repo root | `docs/handoff.md`; if it does not exist and `docs/traspaso.md` does (a 0.4 project), that one (`doctor.py` warns: `/gw-update`) | `"docs/handoff.md"` | `recover.py`, `doctor.py`, `prepush-branches.sh`, `apply.py` |
| `protectedBranch` | The branch that takes only reviewed code | (none) | `"main"` | `pre-push`, `review-before-main.sh`, `reviewed.sh`, `merge-branch.sh`, templates and CI |
| `pushToProtected` | How code reaches it: `direct` (pushed straight) or `pr` (by pull request: the `PreToolUse` hook also guards PR creation and merging). In both, `pre-push` requires the review mark on every direct push that brings code | (none) | `"pr"` | `pre-push`, `review-before-main.sh` |
| `check` | Commands run **in order** on the commit being pushed; all must pass. At least one | (none) | `["npm run check"]` | `pre-push`, `merge-branch.sh`, `doctor.py`, CI |
| `reviewMark` | Committed file holding the reviewed commit's sha | `docs/records/reviewed.txt`; if it does not exist and `docs/registros/revisado.txt` does, that one | `"docs/records/reviewed.txt"` | `reviewed.sh` (writes it), `is-code.sh`, `pre-push`, `review-before-main.sh` |
| `recordsDir` | Folder (relative, no `..`, no trailing `/`) where the skills leave their reports: `retro-*.md`, those of `gw-opt-tokens` and `gw-opt-ai`, release texts | `docs/records`; if it does not exist and `docs/registros` does, that one | `"docs/reports"` | `retro`, `gw-opt-tokens`, `gw-opt-ai` (read `config.py get recordsDir`) |
| `proposalsDir` | Folder (relative, no `..`, no trailing `/`) where `gw-harvest` writes its `# Harvest` files and `state.json`; `version.py --release` requires a new one per version | `docs/proposals`; if it does not exist and `docs/propuestas` does, that one | `"docs/ideas"` | `gw-harvest`, `harvest.py`, `version.py` |
| `content` | Regexes (on repo-relative paths) of what **is content, not code**: it needs no `/code-review` (no scripts, nor what an agent reads as instructions: it goes up without a mark) | (none; may be `[]`, then everything is code; `--init` sets `^docs/`, the root documentation `.md` files (their translations too, `README.es.md`, and `CHANGELOG.md`) and the `.md` files under `.claude/skills/`) | `["^docs/", "^README\\.md$"]` | `is-code.sh`, and through it `pre-push` and `review-before-main.sh` |

## Optional keys

| Key | What it is | Default | Example | Read by |
|---|---|---|---|---|
| `$schema` | Path or URL of the schema, for the editor | – | `"gw/schema/gw.schema.json"` | the editor |
| `schemaVersion` | Version of this file's format (an integer). Absent means 0 (written before 0.5). Optional during `0.x`; `apply.py --init` and `/gw-update` write it | `0` | `1` | `config.py` (migrates in memory), `apply.py` (writes the migration), `doctor.py` (warns when old) |
| `visibleLanguages` | Languages every user-visible text must exist in | `[]` | `["es", "gl", "en"]` | `REVIEW.md` (applied by `/code-review` and agents) |
| `keepLegacyPaths` | With `true`, the project keeps its old Spanish paths (`docs/traspaso.md`, `docs/registros/`, `docs/propuestas/`), written explicitly in this file, and `apply.py` plans no move of them. `apply.py --keep-paths` writes it; setting it to `true` by hand does the same | `false` | `true` | `scripts/apply.py` |
| `logRows` | Log with **one row per branch**, at most 600 characters: each branch writes only in its own | `false` | `true` | `handoff.py`, `prepush-branches.sh`, `recover.py` |
| `install` | Commands that install dependencies (in the cloud and CI) | `[]` | `["npm ci"]` | `session-start.sh` (cloud only, when the lockfile changed), CI, `doctor.py` |
| `ciInstall` | Install commands for CI only: the CI template runs these instead of `install`. Without the key, CI runs `install`; with `[]`, it installs nothing. It is left out of `templates/gw.json` on purpose (a copied `[]` would switch CI installs off) | no key (CI uses `install`) | `["npm ci --ignore-scripts"]` | CI (`check.yml`) |
| `ciPython` | Python versions of the CI template, as a matrix (one job per version). Quoted strings without spaces (`"3"`, `"pypy3.10"`, `"3.13-dev"` are fine) (`"3.10"`, not `3.10`, which JSON reads as a number), no repeats, at least one; `[]` is an error: without the key, one job with `"3.x"`. With the key, the job is named `check (<version>)` (without it, `check`, also for `["3.x"]`): the protected branch's required checks and `ciIgnore` go by name and must be adjusted. If the project has no `pyproject.toml` or `requirements*.txt` at its root, one `check` job with `"3.x"` runs (setup-python is skipped and N equal jobs would only spend quota). A leading job of the template reads them from `gw.json` when CI runs, so the template stays untouched. It is left out of `templates/gw.json` on purpose (copying it would pin versions nobody chose) | no key (`"3.x"`) | `["3.10", "3.13"]` | CI (`check.yml`) |
| `setup` | Commands that run in the cloud **after** `install`, one after another in the same start-up hook (`SessionStart` hooks run in parallel, so the order lives here): a build, a data seed. They rerun when `install` reruns (a lockfile or the list changed). If one fails or passes `GW_COMMAND_TIMEOUT` seconds (900 by default), the hook reports it with the command to run by hand and stops; the next session retries. The CI template does not run `setup` The limit is enforced by a bash watchdog (no `timeout` needed, so it works on stock macOS): the command runs in its own process group and, past the limit, the whole group gets TERM and, a few seconds later, KILL. A process that detaches itself from the group (`setsid`, a daemon) can survive. | `[]` | `["cargo build"]` | `session-start.sh`, `doctor.py` |
| `requireRetro` | `reviewed.sh` requires a `retro` with the person's decision on the branch before marking; reads the whole `**Status:**` paragraph and accepts applied, rejected, deferred, decided or approved; `reviewed.sh --footer "Siguiente: …"` adds that line to the mark commit; untracked files do not count as changes; with the person away, the retro stays `**Status:** pending` (`reviewed.sh` refuses it) and the work stops there: their decision is the only missing step | `false` (in `templates/gw.json` too; `--init --require-retro true` turns it on) | `true` | `reviewed.sh`, `retro` skill |
| `agentSignatures` | With `false`, the `commit-msg` hook rejects a message that carries an agent signature: a `Co-Authored-By:` with `noreply@anthropic.com` or naming Claude Code, Opus, Sonnet, Haiku or Fable (case-insensitive), `Claude-Session:`, or a line that starts (after any emoji) with "Generated with/by [Claude Code" or with a `claude.ai/code/session` link; a human co-author (even one called Claude) and a body that only quotes those texts pass. It ignores comment lines (`core.commentString` or `core.commentChar`) and whatever follows the scissors line of `git commit --verbose`; it also checks a merge and is skipped during a rebase. The `PreToolUse` hook `scripts/agent-signatures.py` applies the same, at column 0 only (an indented line or one inside a ``` or ~~~ code block is a quote and passes), plus a line that starts with a `claude.ai/code/session` link, to the text the agent publishes on GitHub: the title and body (`title`, `body`, `message`, `commit_title`, `commit_message`, `commitHeadline`, `commitBody`) of the tools of any MCP server with `github` in its name (`create_pull_request`, `update_pull_request`, `merge_pull_request`, `enable_pr_auto_merge`, `add_issue_comment`, `update_issue_comment`, `issue_write`, `add_reply_to_pull_request_comment`, `add_comment_to_pending_review`, `pull_request_review_write`, `push_files`, `create_or_update_file`), and in Bash `gh pr create\|edit\|comment\|review\|merge`, `gh issue create\|comment\|edit`, `gh release create\|edit` and `gh api` (`--title`/`-t`, `--subject`, `--body`/`-b`, `--notes`/`-n`, also pasted as `-bTEXT`; the content of `--body-file`/`-F`/`--notes-file`; the `key=value` of `-f`/`-F`/`--field`/`--raw-field`; with a file `-` the whole command is read, heredoc included); it blocks the call with the reason and the fix. With the key absent or `true` it does nothing. Also, `session-start.sh` warns (without blocking) when `git config user.email` is `noreply@anthropic.com` with `false` | `true` (in `templates/gw.json` too; `--init --agent-signatures false` sets it to `false`) | `false` | `templates/githooks/commit-msg` |
| `commitFormat` | `"free"` (any first line) or `"conventional"`: the `commit-msg` hook requires `type(scope)!: text` (types `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`; scope and `!` optional; a space after the colon). A leading `WIP: ` and the lines git writes itself (`fixup! `, `squash! `, `amend! `, `Revert "`, `Reapply "`, `Merge `) pass. Not checked while a merge, revert or cherry-pick is being concluded, nor in a rebase | `"free"` | `"conventional"` | `scripts/commit-message.py`, `templates/githooks/commit-msg` |
| `commitRefs` | With `true`, the `commit-msg` hook requires, in the trailer block (the last paragraph, only `Key: value` lines), a `Refs: <id>` with one or several ids separated by commas (`Refs: D11, D12`; the line may repeat), and each id must open an entry (table row `\| D11 \|` or list item `- D11 …`, with or without `[ ]`, bold or strike-through) with the shape of `taskId` in one of `refsSources`, **read from the index** (a commit that adds the id may cite it; an unstaged change does not count). Same exceptions as `commitFormat`. Also, an `Agent: <skill>` trailer is optional and, with `agentSignatures: false`, must not name a model or provider (the value is split at anything that is not a letter or digit; a piece fails if it is `claude`, `anthropic`, `opus`, `sonnet`, `haiku`, `fable`, `gpt`, `chatgpt`, `openai`, `gemini`, `llama`, `mistral`, `qwen` or `deepseek`, or matches `gpt<digit>…`, `o<digits>` or `<digits>o`) | `false` | `true` | `scripts/commit-message.py` |
| `commitNext` | With `true`, the `commit-msg` hook requires a non-empty next-step trailer in the trailer block: `Siguiente:` with `language: "es"`, `Next:` with `en` (and any other language). A `WIP:` commit needs it too. `fixup! `, `squash! `, `amend! `, `Revert "`, `Reapply "` and `Merge ` lines pass, and it is not checked while a merge, revert or cherry-pick is in progress or during a rebase; `merge-branch.sh` requires it in its merge message and stops before merging. For a legitimate message without it: `GW_NO_NEXT=1 git commit …` (the error says so). It does not worsen the `core.commentChar=auto` case: comment lines are dropped before the trailers are read | `false` (also in `templates/gw.json`) | `true` | `scripts/commit-message.py`, `scripts/merge-branch.sh` |
| `refsSources` | Files or folders (a folder counts for its tracked `.md` files) where the valid `Refs:` ids live | `[]`: those of `plan` plus `log` | `["docs/roadmap.md"]` | `scripts/commit-message.py` |
| `ciLocalLog` | Markdown file (relative to the root, no `..`) where `ci-local.py --record` writes one line each time the GitHub CI runs locally. When a PR's CI did not start (no CI, or not started for billing), `review-before-main.sh` accepts the newest green line whose commit is an ancestor of the PR head, with only content after it and made on a clean tree; the protected branch's config decides. Never code for `is-code.sh` | `docs/records/ci-local.md`; if it does not exist and `docs/registros/ci-local.md` does, that one | `"ci/local.md"` | `ci-local.py`, `review-before-main.sh`, `is-code.sh` |
| `ciLocalWorkflows` | Workflows (paths relative to the root) that `ci-local.py` runs, whatever their triggers. Empty: every `.github/workflows/*.yml\|yaml` the event triggers | `[]` | `[".github/workflows/ci.yml"]` | `ci-local.py` |
| `ciIgnore` | Names of foreign CI checks (a check-run name or a commit status context, e.g. a deploy) that do not block the merge nor count as the project's CI. An exact name, or with `*` for any text (`vercel*`); case matters; no regex. An ignored one is only set aside: it never turns a red or pending check of the project into green, and a commit where only ignored checks reported counts as no CI. The protected branch's config decides. If the protected branch has no `gw.json` yet, the PR head's counts. A broad pattern (`deploy-*`) also sets aside a job of your own with that name. | `[]` | `["Vercel", "deploy-*"]` | `ci-status.py`, `review-before-main.sh` |
| `roadmap` | Reserved for the optional milestones module; no script reads it yet | `false` | `false` | (nobody yet) |
| `selector` | `{ "cases": [ { "case", "skill", "sessionModel", "subagentModel" } ] }`: the project's own rows for the `gw-selector` | no rows | `{"cases": [{"case": "Data migration", "skill": "gw-orchestrate-dealer", "sessionModel": "Opus"}]}` | `selector` skill |
| `logSections` | Headings of the log sections `recover.py --state` puts back after a compaction or `/clear` (without `logRows`) | `[]`: the first section and the one named "Pendiente"/"Pending" | `["Current state", "Pending"]` | `recover.py` |
| `designReferences` | Products, frameworks or standards each design proposal is contrasted with | `[]` | `["WCAG 2.2", "Material Design 3"]` | `grilling` and `gw-selector` skills |
| `protectedPaths` | Path prefixes an agent (`CLAUDECODE=1`) may not commit: other people's drafts | `[]` | `["docs/drafts/"]` | `.githooks/pre-commit` |
| `staleRefs` | Case-insensitive regexes that must not appear in `docs/` or the READMEs: a renamed task, a removed phase. Also accepts `{ "patterns": [...], "skip": [globs] }`: `skip` lists files or folders (repo paths; `*` stays inside a folder, `**` crosses, a trailing `/` is the whole folder) that are not read, besides the log and `.claude/`, which are always skipped (e.g. `retro-*.md`, which quote old paths). A glob that matches nothing does nothing The globs support only `*`, `**` and `?` (no brackets, no gitignore semantics): `*` and `?` do not cross folders, `**` does; an entry without wildcards (`docs/registros`, with or without a trailing `/`) is that file or that folder and everything under it, and `docs/**` also matches `docs`; a leading `/` is ignored. | `[]` | `["old phase 9"]` or `{"patterns": ["phase 9"], "skip": ["docs/records/retro-*.md"]}` | `md-links.py` |
| `linkRoots` | Folders (relative, no `..`) whose Markdown writes relative links from the repo root instead of from its own folder (e.g. a saved PR description); `md-links.py` resolves them that way. `.` is the whole repo A leading `/` resolves from the repo root; a link that leaves the repo is reported, not looked up on the disk. | `[]` | `["docs/prs"]` | `md-links.py` |
| `agentMap` | `{ "path", "prefixes", "roots" }`: the agent map that `agent-map.py` checks. `path` is the file (relative, no `..`; without the key, `docs/agent-map.md`, and if that one is missing the script says so and exits 0; a declared `path` that does not exist is an error). `prefixes` maps a short prefix to its real folder (`{"b/": "backend/src/"}`: `` `b/a.ts#f` `` is looked up in `backend/src/a.ts`). `roots` lists top-level folders that count as a path even when they no longer exist (so a deleted or renamed folder is reported instead of passing as plain text). A path in the map (`` `path` ``, `` `path#name` `` or a Markdown link) must exist, and `name` must be defined in that file. | `{}` (map at `docs/agent-map.md`, no prefixes or roots) | `{"path": "docs/map.md", "prefixes": {"b/": "backend/src/"}, "roots": ["backend"]}` | `agent-map.py` |
| `scoutDir` | Folder (relative, no `..`) where `gw-scout-updates` keeps its memory: `architecture.md`, `proposals.md` and the reports. | `.claude/gw/scout` | `"docs/scout"` | `gw-scout-updates` (`compare.py`) |
| `checkWrapper` | Prefix of every `check` and `relatedTests` command (e.g. `docker compose run --rm app`): it always runs `<prefix> bash -c '<command>'` (with `cd <cwd> &&` inside when the entry has `cwd`), so it also covers a compound command (`a && b`). The CI template does not apply `checkWrapper`: it is for the local host (e.g. a sandbox); CI runners do not need it. | `""` (no prefix) | `"docker compose run --rm app"` | `pre-push`, `related-tests.sh` |
| `relatedTests` | `{ "fast": [...], "slow": [...] }`: tests of what changed. Each entry is a command (string) or `{ "command", "paths", "cwd" }`: `paths` is a regex filtering the changed files and `cwd` a folder the command runs from (`{files}` is relative to it). `fast` runs on every push; `slow` only when some changed file (in its scope) still exists or some file was deleted; `{files}` is replaced by the changed files that exist (never by deleted paths). Deleted files are decided per entry: if an entry's scope (`paths`/`cwd`) matches no existing file but matches a deleted one, it is skipped when its command uses `{files}` (with a note) and runs when it does not | no commands | `{"fast": [{"command": "npx vitest related {files}", "paths": "\\.tsx?$", "cwd": "web"}], "slow": []}` | `related-tests.sh` (called by `pre-push` and `merge-branch.sh`) |
| `worktreeLinks` | Paths (relative, no `..`) of the main checkout that `pre-push` links into the temporary worktree where `check` runs; missing ones are skipped and a path of the commit is never overwritten | `["node_modules", ".venv"]` | `["node_modules", "backend/node_modules", ".env"]` | `pre-push` |
| `worktreeDir` | Folder (absolute, or relative to the repo root) under which `pre-push` creates its temporary worktrees, for a sandbox that cannot see `$TMPDIR` (e.g. Flatpak); a relative one should be in `.gitignore` and outside `.git/` | `""` (`${TMPDIR:-/tmp}`) | `".cache/gw-worktrees"` | `pre-push` |
| `plan` | Plan or roadmap files or folders where tasks are ticked or struck through | `[]` | `["docs/roadmap.md"]` | `handoff.py` |
| `taskId` | Regex of the project's task ids | `[A-Z]{2,5}-\\d+` | `"(INS\|FLU)-\\d+"` (capturing groups are treated as non-capturing) | `handoff.py` |
| `subagentCap` | Integer ≥ 1: subagents (`Agent`/`Task` calls) a session launches before the `PreToolUse` hook `subagent-cap.py` asks the person to check they are not looping, and again every 10 (it never blocks). If the config cannot be read, the default applies | `30` | `50` | `subagent-cap.py` |
| `instructionLines` | `{ "warn", "fail" }`, integers ≥ 1 with `warn` ≤ `fail`: line limit of `AGENTS.md` and `CLAUDE.md` (every session loads them whole). `doctor.py` warns above `warn` and fails above `fail`; a missing part takes its default | `{"warn": 150, "fail": 250}` | `{"warn": 200, "fail": 300}` | `doctor.py` |
| `privateCheck` | Private-data check (E2) in `pre-push` and in `--all`: `emails` (look for addresses) and `allowEmails` (addresses that may be published; `noreply@…`, `git@…`, `…@users.noreply.github.com` and the `example` domains already pass). `false` turns it off. Private names go in `.claude/gw.local.json` (`{"privateNames": [...], "allowEmails": [...], "anonymize": {"<name>": "private-project-N"}}`), which is never pushed: `pre-commit` refuses it, `apply.py` puts it in `.gitignore` and `config.py local` validates it; without it, names are not checked (with a notice). `anonymize` (E3) gives each name's public alias (any spelling; it counts as `privateNames`, no need to repeat it): `harvest.py` prints it and records it in the state instead of the name, and refuses to print a project with a private name that has no alias | `{"emails": true, "allowEmails": []}` | `{"allowEmails": ["me@example.com"]}` | `private-check.py` (`pre-push`, `tests/check.sh`) |

**English paths and compatibility (A8, 0.x).** `log`, `reviewMark`, `recordsDir`, `proposalsDir` and `ciLocalLog` are no longer required: when absent from `gw.json` they take the English default, unless that does not exist and the old Spanish name does (one path, key by key), which is used until you move the file; `doctor.py` warns and `/gw-update` fixes it. An explicit value in `gw.json` always wins. `config.py` is the only one that resolves it (with `--rev`, it looks at the requested commit).


## Notes

- **`check` is a list of commands**, not a single script: each runs with `bash -c` at the root of the commit being
  pushed. One that does not exist is caught by `doctor.py` before a push fails. The `pre-push` passes them
  `GW_PUSH_PROTECTED=true` when the push goes to the protected branch (`false` otherwise; unset outside the hook), so a
  command can run only before `main`, e.g. `[ "${GW_PUSH_PROTECTED:-}" != true ] || <command>`.
- **`check` runs in a temporary worktree** when the working copy is not clean (or the push is not what it holds): it
  lives in `${TMPDIR:-/tmp}/gw-pre-push-wt-<uid>-<repo id>/wt.XXXXXX.d` (or under `worktreeDir`; the folder is mode 700, and a symlink in its place is refused), never inside `.git/`
  (jest and similar tools ignore any path with a `/.git/` segment), and is removed on every exit (also on Ctrl-C or
  `kill`). If a push dies unable to clean up, the next one removes the orphaned worktrees older than 24 h whose process
  is gone; two pushes at once do not step on each other. After changing `worktreeDir`, the old folder is no longer cleaned: delete it by hand. What is linked from the main checkout is set by `worktreeLinks`. A failing command's log
  is kept (`full log: <path>`); when it passes, it is deleted.
- **`pre-push` does not repeat a `check` that already passed.** The key is the pushed commit's tree, the `check`
  commands and `checkWrapper`; it is recorded in `<git common dir>/gw-check-green` (linked worktrees share it),
  expires after 24 h and keeps the last 50. If the key is there, `pre-push` says `check already green on this tree…`
  and skips the `check` (`relatedTests` still run); otherwise it runs the `check` and, when green, records it (if it
  ran in the working copy itself, only when it left it clean). The earlier way to record it is `bash
  .claude/gw/scripts/check.sh` (`scripts/check.sh` in this repo): it runs the `check` on the working copy and, if it
  passes and the tree (what `git add -A` would commit) did not change during the run, records the green, so the push
  does not repeat it. At the end it prints a summary (each command, `ok`/`FAILED` and seconds); the commands' output
  stays live, as always. With `--quiet` (`-q`, or `GW_CHECK_QUIET=1`/`true`/`yes`) the whole output goes to `<git
  dir>/gw-check.log` (`GW_CHECK_LOG` changes the path; a relative one counts from the current directory and cannot
  fall inside the working copy unless git ignores it) and only the last `GW_CHECK_TAIL` lines (40) of the command that
  fails and the log path are shown. A `check` run by hand (e.g. `bash tests/check.sh`) records nothing. Limits: a push
  to the protected branch never reads nor writes the cache; nothing is recorded with `assume-unchanged` or
  `skip-worktree` entries (sparse checkout) or a submodule with changes; any failure of the cache only means the
  `check` runs; `check.sh` runs with the working copy's ignored files (`.env`, generated ones), whereas a push with a
  dirty working copy used to check in a clean worktree. `GW_CHECK_CACHE=0` turns it off (`GW_CHECK_CACHE=0 git push`
  runs the `check` even if it is recorded).
- **`pushToProtected`** says how code reaches the protected branch today. A direct push that brings code always needs
  the mark in `pre-push`, with `direct` and with `pr`; with `pr`, the PR hook also asks for it when the pull request
  is created or merged. The config is read from the pushed commit, not the working copy; for the protected branch,
  `content` and `reviewMark` come from its remote tip (from what is pushed only while it has no config yet, with a
  warning), and the branch is protected if either of them or the working copy says so: a commit cannot relax the
  rule that judges it.
- **`content` and the mark.** A change touching only `content` files needs no review; any other does. `reviewed.sh`
  writes the reviewed commit to `reviewMark`, and the mark must be an ancestor of what is pushed with no code after it.
  Before marking it warns (without blocking) which code files changed since the previous mark (or since the fork from
  the protected branch when there is no valid mark), so fixes made after the review do not arrive unreviewed; only what the branch itself changed counts, not what came in by merging the protected branch.
  `.claude/gw.json`, `.claude/settings.json`, `.claude/gw/` and `.githooks/` are always code, whatever `content` says.
  To see how a path is classified and why: `bash .claude/gw/scripts/is-code.sh --explain <path>...`.
- **`logRows`** goes with the row-based log template (``| **Current task · `branch`** | … |``); the push checks that
  each branch writes only in its own row, that every "Task in progress" row names its branch, and that each task
  closed in the plan is recorded in "Done": struck through there, or named on a line that starts with a date (an
  unstruck bullet is not enough). That last rule is also checked by `pre-commit`, on the staged log, so a closure is
  recorded in the same commit (not with an `--amend` before the push). With `plan`, the push also refuses a task id
  the branch opens that `origin/<protectedBranch>` uses for another task (or a new merge that kept both under one id),
  and warns when it clashes with another remote branch (`handoff.py clash`); the `pre-commit` of a conflicted merge
  checks it earlier.
- After changing the workflow version, bump `version` by hand (`/gw-update` does it): `doctor.py` compares that number
  with the copied headers.
- `schemaVersion` is not the workflow version but that of the `gw.json` format, and it only goes up when the format
  changes. An old project is never silently broken: `config.py` migrates in memory a `schemaVersion` older than the
  workflow's (or an absent one, which counts as 0), so every reader sees the current shape, also when reading another
  commit's config (`--rev`); `doctor.py` warns and `/gw-update` (`apply.py`) writes the migration to the file, in one
  write together with any path change, and `apply.py --check` counts it as pending. A **newer** one than the
  workflow's fails closed (exit 2) in every reader: update the workflow (`/gw-update`, or
  fetch the latest `vX.Y.Z` tag of the workflow clone and check it out, as step 1 of `/gw-update` does). The
  migrations live in `MIGRATIONS` in `scripts/config.py`.

## Personal notes

If you have notes that should reach every project where you apply the workflow, keep them **outside any repo**, in
`~/.claude/gw/notas/` (another folder through the `GW_PERSONAL_NOTES` environment variable). `apply.py` carries
them to `<project>/.claude/gw/<name>`:

- Only regular files directly in that folder, named `[A-Za-z0-9][A-Za-z0-9._-]*`; subfolders, symlinks and hidden
  files are ignored. If the folder does not exist, nothing happens and nothing is said.
- A note missing in the project is created (reported as a "personal note"). An identical one: nothing. One that
  **differs** is never overwritten and gets no `.gw-new` (the project may have adapted it on purpose): one line
  with `diff <source> <target>` is printed on every run. `--check` **does not fail** for a missing note (it only says
  "would create personal note …") or for a differing one.
- A note is skipped with a `WARNING` and the order to rename it when its name ends in `.gw-new` (`doctor.py` takes
  it for a pending proposal), when it is the name of a workflow file in `.claude/gw/` (compared ignoring case and
  even if that file is not installed: `gw-opt-tokens.md`, `gw-opt-ai.md`, `gw-scout-updates.md`, `scripts`, `schema`…) or
  when its target is not a regular file. A notes folder that is unreadable or is a file, and a note that cannot be
  read, warn too (an absent folder does not).
- They are never applied to the workflow's own repo: nothing personal goes into it. `--no-personal-notes` skips
  them for one run. A relative `GW_PERSONAL_NOTES` is resolved from the folder where the command is launched.
