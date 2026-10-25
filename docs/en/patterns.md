# Optional patterns

> [Español](../es/patrones.md)

Ways of working the workflow allows but does not impose. None is needed to apply it ([apply](apply.md)); adopt them
when the project asks. They all rest on the same ground: what is not pushed does not exist, the log says where things
stood, and a script, not an opinion, decides whether something may be pushed.

## Weekly scheduled task

A session that starts by itself every week (a Claude Code "scheduled task") for repeatable work: updating
dependencies, checking broken links, running `scout-updates`, tidying the log. The workflow **does not ship** the
concrete prompt: each project writes its own.

How it is set up, generically:

1. **Every firing is a fresh session** with the complete instruction (it cannot assume an earlier conversation): what
   to do, on which branch, what to check and when to stop.
2. **It starts like any session**: reads the log, `git fetch`, brings in the protected branch and runs
   `python3 .claude/gw/scripts/doctor.py` and the `check`. If something is red before it touches anything, it notes
   that in the log and stops.
3. **It works on its own branch** (`claude/weekly-<date>`), with commits and pushes as usual and the log up to date.
4. **To the protected branch, per the configuration** ([config](config.md)):
   - `pushToProtected: pr`: it opens a pull request; the PR hook and CI stand guard and a person decides.
   - `direct`: it may push to the protected branch **only if the review mark covers the code** (`pre-push` requires it
     and fails closed). If the task changes code without review, it does not push: it leaves the branch with its log
     for a person to review. A `content`-only change needs no mark (that is why `content` holds no scripts nor
     instructions for agents).
5. **It ends with a short report** in the log: what it did, what it left pending and the next step.

Authorisation: a task that pushes to the protected branch with nobody present deserves to be written as a rule in
`AGENTS.md`, so it is on record who allowed it.

## Two accounts relaying

Two accounts (or two people, or a local session and a cloud one) work the same project in turns and sometimes at the
same time.

- **Each session, its own branch.** Two sessions at once never push to the same one. If the log's branch is already
  in use, create `claude/<topic>` from it and write its row in the log.
- **Row-based log** (`"logRows": true`): each branch writes only in its "Current task · `<branch>`" row, at most 600
  characters. `pre-push` rejects touching another branch's row or a shared one; for a shared one (e.g. adding your
  branch to "Working branches"), `BITACORA_COMPARTIDA=1 git push`.
- **Merge, never rebase**, at the start of every task (`git fetch origin <protected>` and `git merge
  origin/<protected>`): branches are pushed. Their work returns to the main branch by `git merge` before the PR.
- **On stop**, the `Stop` hook (`antes-de-parar.py`) does not let a session finish with unpushed commits or with
  changes the log does not mention; if it cannot check (no git, no config), it warns instead of blocking.
- **On touching the workflow's configuration**, the `PreToolUse` hook `guardia-config.py` asks the person before
  `.claude/settings.json`, `.claude/gw.json`, `.githooks/` or `.claude/gw/scripts/` are edited (with `Edit`, `Write` or
  a `Bash` command that writes there); if it cannot read the event it asks too. To regenerate the applied copy:
  `python3 scripts/aplicar.py .`.
- **When dealing work to subagents**, the `PreToolUse` hook `tope-subagentes.py` counts the session's `Agent`/`Task`
  calls and, at `subagentCap` (30 by default) and every 10 after, asks the person to check they are not looping
  (`opt-tokens`); it never blocks.
- **On start**, the new session reads the log and checks that the last commit matches what it says; it does not ask
  where things stood. After a `/clear` or compaction, `recuperar.py --estado` reminds it.
- When the branch closes, `bitacora.py close-row <branch>` leaves its row as "merged, branch finished" so the
  protected branch does not inherit a stale "Next".
- **A short log, with or without `logRows`:** `bitacora.py check --strict` fails if a cell of the state table passes
  800 characters or if "Done (last 5)" has more than 5 items, badly numbered or glued on one line (without
  `--strict` it only prints `WARNING:`). `bitacora.py done "text"` adds the `1.` item with the date, renumbers and
  drops the extra ones, leaving the rest of the file alone.

## A local session that cannot create PRs

Some environments (a laptop without `gh`, a console) let the session work and push branches but not create the PR.
Split it like this:

1. The local session finishes the work and passes review (`/code-review`, and a `retro` if configured). Then it
   writes the PR description with the `pr` skill into `docs/registros/pr/<branch>.md`.
2. In its log row it leaves **"PR ready"** with the title, and pushes **everything in the last commit** of the
   branch.
3. A **cloud session** (with a GitHub tool) checks that nothing comes after that commit (`git log
   <commit>..origin/<branch>` is empty), runs `bash .claude/gw/scripts/revisado.sh` to leave the mark of the same
   commit, creates the PR with that description, and follows CI and, when the person confirms, the merge.

The PR hook blocks creating or merging without the mark of the same commit, so a slip (something pushed after "PR
ready") shows up as a block, not as unreviewed code.

## Social content

Two skills prepare, **without publishing**, posts about the project: `gw-media-content` proposes up to 10 (post type, hook,
networks, facts with their source) and `gw-media-content-now` produces one piece in a dated folder: one file per channel
and language, plus the images. Starting networks: X, Reddit, LinkedIn and Discord; the project may declare others
(*extra channels*). Per-network limits live in `reglas.json`, marked `P` (verified), `S` (per the source) or `NV` (not
verified: the skill says so when a proposal leans on one). The person publishes; no skill does.

They need Python 3 and git for the figures (`cifras.py`). Rendering images (`render.mjs`) also needs Node with Playwright
and ImageMagick with WebP; `comprobar.py` runs without them, and **CI does not cover the real render** (its tests use a
stand-in except where Chromium is present). If the project has the skill's note or folder, `doctor.py` warns about
whatever is missing (`media tools`).

Without a project note the defaults apply (and it is said once). To change them, `.claude/gw/gw-media-content.md`, one
`key: value` line per item (the keys are those of the table in `skills/gw-media-content/nota.md`, in English); the
workflow neither creates nor overwrites it. An *extra channel* is declared with `límite: N` (checked with
`--limite <channel>=N`) or with `formato: propio` and `plantilla: <path>` (its file is consumed by another system;
checked with `--formato-propio <channel>`). A generic example:

```
Folder: docs/difusion
Languages: es, en
Channels: x, reddit, linkedin, discord
Extra channels:
- mastodon: límite: 500; tono: cercano
- portal: formato: propio; plantilla: docs/difusion/portal.json
Palette: --fondo #101418; --acento #4cc38a
Screenshots: start the app (npm run dev), open /panel, capture the window at 1280x720
Task prefixes: INS,FLU   (passed to comprobar.py --prefijos-tarea)
Reddit: r/example, rules pasted by the person on 2026-10-25: "no self-promotion more than once a month; tag [Project]"
```

## Harvesting improvements back

The workflow learns from the projects that use it. There are two halves:

- **The project pushes.** A `retro` that finds a **general** improvement (to a skill, script, template or `AGENTS.md`
  rule) does not patch the local copy, which the next update would overwrite: it proposes it to the workflow, as an
  issue or PR on this repo, or leaves it in the retro file under a `## For Galivelop-workflow` heading (or
  `## Para Galivelop-workflow`).
- **The workflow pulls.** From this repo, the `gw-harvest` skill walks the connected projects that have
  `.claude/gw.json`. The mechanical part is `python3 scripts/recoger.py <project>...` (edited workflow copies, new
  skills, retro sections, commits since the last harvest); the agent only decides what is general and writes
  `docs/propuestas/YYYY-MM-DD-<repo>.md`. **It never applies anything without confirmation**: what is approved goes in
  as a normal change with a CHANGELOG entry and a new version ([contributing](contributing.md)).

Projects are read, never modified, from the session that harvests.
