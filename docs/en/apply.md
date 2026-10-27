# Applying the workflow to a project (guide for the agent)

> [Español](../es/aplicar.md)

This is the guide an AI agent follows to apply Galivelop-workflow to a project, **new** (recommended) or **existing**
(its own section, below). What needs judgement is decided by the agent with the person; the rest is done by a script
(`scripts/aplicar.py`) and checked by another (`scripts/doctor.py`). In Claude Code, the `/gw-init` skill is a thin
wrapper over this guide.

The result lives **in the project's repo** (scripts, skills, hooks, templates), so it also works in cloud sessions,
which do not load plugins declared in the repo.

## 0. Before starting

1. The project is cloned and is a git repo (`git init` if it is new).
2. This repo, the workflow's, is cloned next to the project, or the person has added it to the session. From here on
   it is `<workflow>`. **It is read by a subagent** (`orchestrate-dealer`), which returns the step-1 table and the
   conflicts with the project, with paths; the main session only decides. **Clone the latest published tag, not the
   default branch** (which may not be `main` and may be an old version): `git ls-remote --tags <url>` to see it and
   `git clone --branch vX.Y.Z <url>`. In the cloud, keep the workflow repo from
   becoming a working folder of the session (it would load its `CLAUDE.md` and skills): if it is public, a plain
   `git clone`; if it is added with `add_repo`, do not register it as a root, and check the path it returns with `ls`
   (it may come lowercased and not exist).
3. **The session is opened with the project as its working folder.** Opened elsewhere, it does not load
   `.claude/settings.json` (nor the hooks). If it is not, ask the person to reopen it from the project.
4. `git status` is clean in the project, or the person knows what is unpushed. Generated files (`__pycache__/`,
   `node_modules/`, `target/`, build output) are in `.gitignore`: running the check must not dirty the tree.
5. git has an identity for commits (`git config user.name` and `user.email`); set it if it is a fresh machine.
6. `python3` 3.8 or later, `git` and `bash` are available (on Windows, Git Bash or WSL: see
   [troubleshooting](troubleshooting.md)).
7. **The `.gitignore` does not ignore what is about to be copied.** A `.gitignore` with `.claude/*` also ignores
   `.claude/gw*` (`.claude/gw/` and `.claude/gw.json`), and a commit would leave the scripts and the config out.
   Before copying, add the exceptions below that line (`!.claude/gw/`, `!.claude/gw.json`, `!.claude/settings.json`,
   `!.claude/skills/`) and check with `git check-ignore -v <path>` that none is still ignored. `doctor.py` reports it
   as a `FAIL` (`ignored`) with the exact lines if forgotten.

Done when: `python3 <workflow>/scripts/aplicar.py --help` and `git -C <project> status` run without error.

## 1. Decide what needs judgement

Collect these facts **before** running anything. They all go into `.claude/gw.json` (every key is in
[config](config.md)).

| Fact | How it is decided |
|---|---|
| Language (`language`: `es` or `en`) | The person's and the project docs'; it drives the templates and the replies |
| Log path (`log`) | Default `docs/traspaso.md` (es) or `docs/handoff.md` (en); the project's own if it already has one |
| Install command(s) (`install`) | Inferred (below); empty if there are no dependencies |
| Check command(s) (`check`) | Inferred (below); **at least one**, it is what `pre-push` and CI run |
| Protected branch (`protectedBranch`) | The one that deploys or publishes: `git symbolic-ref --short refs/remotes/origin/HEAD`; if that fails (a fresh or local remote), `git remote show origin \| sed -n 's/.*HEAD branch: //p'`; otherwise ask the person |
| Pushing to it (`pushToProtected`) | `direct` if people push straight to it; `pr` if it only takes pull requests |
| Content (`content`) | Regexes for what is **not** code and needs no `/code-review`: docs, data, texts |
| Required retro (`requireRetro`) | Ask: "`/retro` on every push to the protected branch, or only on big changes?". Every push: `--require-retro true` (`revisado.sh` will not mark without a decided retro on the branch); otherwise `false` |
| Visible languages and design references (`visibleLanguages`, `designReferences`) | Only if the project has them: `--visible-language` and `--design-reference`, one flag per value |
| Optional skills | `opt-ai` (local AI models) and `scout-updates` (update scouting); only if the person asks |

**Inferring `install` and `check`.** Read the build file and propose commands that really exist:

| File | `install` | `check` (the most complete one there is) |
|---|---|---|
| `package.json` | `npm ci` (or `pnpm i --frozen-lockfile`, `yarn --frozen-lockfile` per the lockfile) | the `check` script, or `lint` + `test`: `npm run check` |
| `pyproject.toml` | `pip install -e .[dev]` or `uv sync` | `pytest`, plus `ruff check .` if configured |
| `Cargo.toml` | (empty) | `cargo clippy -- -D warnings` and `cargo test` |
| `pom.xml` | (empty) | `mvn -q verify` |
| `go.mod` | (empty) | `go vet ./...` and `go test ./...` |
| `Makefile` | (empty) | `make check` or `make test`, if the target exists (`make -n check`) |

Rules:

- Read the build file's scripts and **run the `check` command once** to see that it works and how long it takes. A
  command that does not exist or does not pass is found late and gets in the way of every push.
- **When unsure, ask the person**; do not invent a command. With several candidates, offer them numbered.
- A project with no tests: `check` can be a linter or a `bash -n`; say so and note it as debt in the log. A `bash -n` checks only the first file (the rest are arguments): one command per file, or `for f in …; do bash -n "$f"; done` (`doctor.py` warns about it). If you put `doctor.py` in `check`, in CI (`CI=true`) an unset `hooks-path` is a `WARN` and does not break the run: CI has no git hooks installed; locally it stays a `FAIL`.
- If the project has an agent map (`docs/mapa-agente.md`, or the one `agentMap.path` declares), add `--check-command "python3 .claude/gw/scripts/mapa-agente.py"`: it checks that every path the map cites exists. With no map it exits 0 and does no harm; with short prefixes (`b/` for `backend/src/`), set `agentMap.prefixes` ([`config.md`](config.md)).
- The copied skills bring their tests next to their scripts: they are discovered with `python3 -m unittest discover -s <skill>/scripts` (the workflow repo's check does it for each one).
- `content` is proposed by reading the tree: `^docs/`, `^public/`… (in JSON the backslash is doubled). **What is
  `content` goes up without a mark:** do not put scripts there, nor what an agent reads as instructions (an
  `AGENTS.md` in a subfolder, a prompt template). When in doubt, put less: what counts as code gets reviewed. The
  `.md` files of the copied skills (`^\.claude/skills/.*\.md$`) are reviewed in the workflow repo and are in the
  template's default `content`; keep them there (their scripts, no). The scripts in
  `.claude/gw/` do **not** go in `content`: they are the hooks that guard the branch, and a change to them is reviewed
  like any code.

Done when: every row of the table has an answer (or a question put to the person), and `check` has run once.

## 2. Apply

From the project root or giving it as the argument; the flags come from `--help`. `--check-command`, `--install` and
`--content` **repeat**: one flag per command or regex (two checks = two `--check-command`). Without `--content`, the
template's default applies (`^docs/`, the root `.md` files that are documentation and the copied skills' `.md`):

```bash
python3 <workflow>/scripts/aplicar.py <project> --dry-run --init --language en \
  --log docs/handoff.md --install "npm ci" --check-command "npm run lint" --check-command "npm test" \
  --protected-branch main --push-to-protected direct
```

`--dry-run` prints the plan without writing. When it is the one you want, repeat the same command **without**
`--dry-run`.

Options: `--review-mark PATH` (default `docs/registros/revisado.txt`), `--with opt-ai` and `--with scout-updates`.
`--init` writes `.claude/gw.json` only when it does not exist, validates it and applies as usual.

What it does (full detail in `--help`): copies `scripts/` to `.claude/gw/scripts/`, the skills to `.claude/skills/`,
the git hooks to `.githooks/`, the CI to `.github/workflows/comprobar.yml`; **merges** the Claude Code hooks and
`CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` into `.claude/settings.json`, removing nothing; creates `AGENTS.md`,
`CLAUDE.md`, `REVIEW.md`, `GLOSSARY.md` and the log when missing; and sets `core.hooksPath=.githooks` when nothing
else owns it. **It never commits.** It is idempotent: running it twice changes nothing.

**Personal notes.** If the person keeps notes in `~/.claude/gw/notas/` (or in the folder of `GW_NOTAS_PERSONALES`),
`aplicar.py` creates the missing ones in `.claude/gw/` and leaves alone those the project already has with other
content ([config](config.md#personal-notes)); `--sin-notas-personales` skips them for one run.

**The scripts under `.claude/gw/scripts/` are not edited in the project.** They are tested in the workflow's repo
(their tests live there) and `--update` overwrites them. If one fails or lacks something, the change goes to the
workflow as a proposal, with the `gw-harvest` skill (`scripts/recoger.py`). The `REVIEW.md` rule "every script change
has its test" applies to the project's **own** scripts.

**Claude Code auto mode.** The auto-mode classifier may ask for permission when editing `.claude/settings.json`,
`.claude/gw/scripts/` and `.githooks/`, and the failure shows up halfway through the application. `aplicar.py` says so
right before writing them. **Ask the person for permission first** before launching it (or have them run it in their
own terminal with the same command) instead of retrying blindly; after a refusal, `git status` and `git diff`
before repeating.

Done when: the command ends without error and you know what was created, what was updated and what was left as
`*.gw-nuevo`.

## 3. Review every `*.gw-nuevo` with the person

When a file already exists and is the project's (an `AGENTS.md`, a `CLAUDE.md` without the `galivelop-workflow`
marker), `aplicar.py` **does not touch it**: it leaves `<file>.gw-nuevo` next to it with the proposal.

```bash
git -C <project> ls-files --others --exclude-standard | grep '\.gw-nuevo$'
```

For each one:

1. Show the person what the proposal brings that the file lacks (`git diff --no-index <file> <file>.gw-nuevo`).
2. **`AGENTS.md` and `CLAUDE.md`: merge by hand**, block by block. The project's rules stay; the workflow's blocks
   are added (session start, hand-offs, checking, commits, branches). `CLAUDE.md` ends up with `@AGENTS.md` plus
   what is Claude's own. Keep the `<!-- galivelop-workflow vX.Y.Z -->` marker on the first line.
3. Other files: accept the whole proposal (`mv <file>.gw-nuevo <file>`) only if the person confirms.
4. Delete the `.gw-nuevo` when done. `aplicar.py --check` counts it as a difference while it exists.

Also fill in the log's placeholders (at least branch, phase and next step; the other sections can stay as they come
until there is something to write) and add the project's own rules to the "Project rules" sections of `REVIEW.md`
and `AGENTS.md` and its terms to `GLOSSARY.md`: the workflow never writes those files again.

**A `REVIEW.md` or `GLOSSARY.md` that already existed:** `aplicar.py` leaves it alone, but prints how it differs from
the template while it lacks the current version's marker. Bring over by hand what it misses (for instance the
"bash 3.2", "brought from another repo: this repo's contracts" and "visible languages" rules of `REVIEW.md`) and put
`<!-- galivelop-workflow vX.Y.Z -->` on its first line; from then on the diff is no longer printed.

Done when: no `*.gw-nuevo` is left, no `REVIEW.md`/`GLOSSARY.md` diff is printed, and the log has a next-step line.

## 4. Check with `doctor.py`

```bash
python3 <project>/.claude/gw/scripts/doctor.py
```

It prints `OK`, `WARN` or `FAIL` per check, and with each problem the command that fixes it. Repeat (fix, run again)
until **no `FAIL` is left**; explain the `WARN`s to the person (what each means is in
[troubleshooting](troubleshooting.md)). With `--json` the output is machine-readable.

It also reports `FAIL` if `AGENTS.md`, `CLAUDE.md` or a `SKILL.md` holds invisible or bidirectional characters (a hidden
instruction is an injection; the line carries the command that removes them) and warns when `AGENTS.md`/`CLAUDE.md`
run past 150 lines (`FAIL` from 250).

Done when: `doctor.py` exits 0.

## 5. Commit and push

`aplicar.py` ended by printing a suggested commit:

```bash
git add -A && git commit -m "Galivelop-workflow v0.1.0 workflow" -m "Next: <next concrete step>"
```

Replace the last line with the real concrete step (the one the log declares) and add any attribution lines the
project asks for in the same final block. The commit already goes through the new `pre-commit` (it refuses secrets
and, for agents, the `protectedPaths`) and, with `logRows`, through `commit-msg` (it checks the staged log with `bitacora.py check`); if it stops, read its message. Then `git push -u origin <branch>`: the new `pre-push` runs the `check` on
the commit being pushed; if it fails, fix it and push again (never with `--no-verify`, except a red `WIP:`).

If the project has CI, check that the `Comprobar` workflow passes. Node, Python and Java are set up on their own when
`package.json`, `pyproject.toml`/`requirements*.txt` or `pom.xml`/`build.gradle*` exist; another toolchain
(rust-toolchain…) must be added, as the header of `comprobar.yml` says.

Done when: the push went through, `doctor.py` is still green and the log says what comes next. Remember the warning in step 6: until a new session, the PR guard is not active.

## 6. Prove the protection works

**Warning:** a `.claude/settings.json` created mid-session is not loaded until the next one. In the session that
applies the workflow the `PreToolUse` hook (the PR guard) is **not active**: until you open a new session from the
project, check the mark by hand before creating or merging a PR (`bash .claude/gw/scripts/revisado.sh`).

On the working branch, commit a small code change and try to push it straight to the protected branch, as a dry
run (`pre-push` runs all the same, nothing is pushed even if it passed, and Claude Code's auto mode does not block it
as it blocks the real push to the protected branch):

```bash
git push --dry-run origin HEAD:<protectedBranch>
```

With either `pushToProtected` it **must be refused**, for one of two reasons: "the pushed commit has no review mark"
(there is no mark) or "code changed after the review mark" (there is a mark, with code after it). With `pr`, the same
check also happens when the pull request is created or merged. Then drop the test commit
(`git reset --hard HEAD~1`, only if it was not pushed anywhere). The normal way in is `/code-review`, fixes,
`bash .claude/gw/scripts/revisado.sh` and the push.

Done when: the dry run was refused for one of those two reasons and the test commit is gone.

## Existing projects

Everything above applies; these are the points that change.

**A hook manager already installed (husky, lefthook, pre-commit…).** `aplicar.py` does not overwrite
`core.hooksPath` when another manager owns it, and `doctor.py` and the session-start warning say so. **Chain, do not
overwrite.** Add as the last line of the manager's `pre-push`, `pre-commit` and `commit-msg` (with `<hook>` the file's name):

```bash
"$(git rev-parse --show-toplevel)/.githooks/<hook>" "$@" || exit 1
```

The workflow's `pre-push` reads git's ref lines from standard input: if the manager does not forward them (in
lefthook, `use_stdin: true`), it cannot tell what is being pushed. Check with a real push: it must print
`pre-push: pushing N commit(s)`.

**An existing `CLAUDE.md` or `AGENTS.md`.** Merge by hand (step 3). If there is only a `CLAUDE.md` holding Claude's
own bits, keep that text and move the shared rules to `AGENTS.md`. If the project already has a different rule for
something the workflow covers (branches, commit messages), **the project's wins**: note the difference in the merge.

**A red check or lint on adoption.** Do not block the first push or switch the check off. Two ways:

1. Fix it first, as a task of its own, if it is small.
2. If it is large debt, open a **debt task** in the log and make `check` look **only at what changes while that task
   stays open**: e.g. a script that runs the linter on `git diff --name-only origin/<protected branch>...HEAD`. When
   the debt is closed, `check` goes back to checking everything. New code comes out clean without blocking the rest.

**A log that already exists.** If the project has one, set it as `log` (it is what the whole workflow reads) and add
by hand what the template has and it lacks: current state with a next step, recent work, pending items and how to
check the state. `doctor.py` requires a "Next step" (or "Siguiente paso") line.

**Existing CI.** `comprobar.yml` is one more workflow; if the project already runs its check, keep one of the two to
avoid duplicating it, but keep the step that runs the base branch's `pre-commit` over the PR. That step works as a
standalone piece in an existing CI: copy only the "Base branch's pre-commit over the pull request" step of
`comprobar.yml` (it needs `fetch-depth: 0`); it runs `bash .githooks/pre-commit --rango <base>..HEAD` with the base
branch's `pre-commit`, so a PR cannot weaken the review that checks it. If CI installs differently, set `ciInstall` in
the config; `doctor.py` does not suggest `comprobar.yml` when another workflow already runs the `check`.

**A protected branch with several people.** `pre-push` asks for the mark on every direct push with code; with
`pushToProtected: pr`, the `PreToolUse` hook also asks for it when pull requests are created and merged. Choose by
how code already reaches it today.

**Migrating from an earlier copy of the workflow.** On top of the above:

- **Many `.gw-nuevo` proposals are normal** (a hand-made copy gave 17): every skill or script the project touched
  comes out as a proposal. Merge them one at a time: the workflow's version goes in whole and the project's own part
  (language, paths, local rules) goes to `.claude/gw/<skill>.md`, which the workflow never overwrites.
- **Files of a skill the workflow replaces** (for instance the bench and `evals` of a project-made `scout-updates`):
  `aplicar.py` does not delete them, it lists them as "no longer in the workflow (kept)". Move them to a folder of the
  project (e.g. `tools/scout/`) or `git rm` them if nothing uses them; do not leave them inside `.claude/skills/`.
- **Old hooks in `.claude/settings.json`.** `aplicar.py` merges the new ones without removing anything, and warns
  ("also runs '…'") about a `SessionStart`, `PreToolUse` or `Stop` entry that runs a workflow script from outside
  `.claude/gw/scripts/`; so does `doctor.py`. Delete it by hand, or it runs twice.
- **`recuperar.py` on the command line**, to get back what a compaction or a `/clear` dropped:
  `python3 .claude/gw/scripts/recuperar.py --estado` (the log, `git status` and the last commits) and
  `--buscar TEXT` (matching session fragments, printed as data after a header line, with control characters
  stripped; `--max N`, `--ancho N`, `--sesion PATH`). `--estado` stops at 9,500 characters, at a whole line, and says so.
- **`install` by hand.** `session-start.sh` runs it only in the cloud and only when the `install`/`setup` commands or
  the lockfiles change. To force it, delete the stamp (`rm "$(git rev-parse --git-path gw-install.sha)"`) and open the
  session again, or run the config's `install` commands yourself.

## What the agent leaves alone

- Does not register as session roots the repos it only reads (the workflow's included): their same-name skills would
  shadow the project's ([troubleshooting](troubleshooting.md)).
- `aplicar.py --update` and overwriting project files happen only when the person asks.
- `install` and `check` are never invented: if the agent cannot run them, it asks.
- Commit and push come after `doctor.py` shows no `FAIL`.
- The protected branch gets pushes only with the person's confirmation.
- A hook is never skipped with `git push --no-verify` or by pointing `core.hooksPath` elsewhere.
- Files the workflow reports it no longer has are reported to the person, not deleted.
- Other repos are read, never edited: the workflow's repo is read from the project session, never changed.
- Another project's `.claude/settings.json` is never copied: `aplicar.py` merges it.
