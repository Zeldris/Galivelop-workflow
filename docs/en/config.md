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
| `content` | Regexes (on repo-relative paths) of what **is content, not code**: it needs no `/code-review` (no scripts, nor what an agent reads as instructions: it goes up without a mark) | (none; may be `[]`, then everything is code; `--init` sets `^docs/`, the root documentation `.md` files and the `.md` files under `.claude/skills/`) | `["^docs/", "^README\\.md$"]` | `es-codigo.sh`, and through it `pre-push` and `revision-antes-de-main.sh` |

## Optional keys

| Key | What it is | Default | Example | Read by |
|---|---|---|---|---|
| `$schema` | Path or URL of the schema, for the editor | – | `"gw/schema/gw.schema.json"` | the editor |
| `visibleLanguages` | Languages every user-visible text must exist in | `[]` | `["es", "gl", "en"]` | `REVIEW.md` (applied by `/code-review` and agents) |
| `logRows` | Log with **one row per branch**, at most 600 characters: each branch writes only in its own | `false` | `true` | `bitacora.py`, `prepush-ramas.sh`, `recuperar.py` |
| `install` | Commands that install dependencies (in the cloud and CI) | `[]` | `["npm ci"]` | `session-start.sh` (cloud only, when the lockfile changed), CI, `doctor.py` |
| `requireRetro` | `revisado.sh` requires a `retro` with the person's decision on the branch before marking | `false` (but `templates/gw.json`, and so `aplicar.py --init`, sets it to `true`) | `true` | `revisado.sh`, `retro` skill |
| `roadmap` | Reserved for the optional milestones module; no script reads it yet | `false` | `false` | (nobody yet) |
| `selector` | `{ "cases": [ { "case", "skill", "sessionModel", "subagentModel" } ] }`: the project's own rows for the `selector` | no rows | `{"cases": [{"case": "Data migration", "skill": "orchestrate-dealer", "sessionModel": "Opus"}]}` | `selector` skill |
| `designReferences` | Products, frameworks or standards each design proposal is contrasted with | `[]` | `["WCAG 2.2", "Material Design 3"]` | `grilling` and `selector` skills |
| `protectedPaths` | Path prefixes an agent (`CLAUDECODE=1`) may not commit: other people's drafts | `[]` | `["docs/drafts/"]` | `.githooks/pre-commit` |
| `staleRefs` | Case-insensitive regexes that must not appear in `docs/` or the READMEs: a renamed task, a removed phase | `[]` | `["old phase 9"]` | `enlaces-md.py` |
| `relatedTests` | `{ "fast": [...], "slow": [...] }`: tests of what changed. `fast` runs on every push; `slow` only when some changed file still exists; `{files}` is replaced by the changed files | no commands | `{"fast": ["npx vitest related {files}"], "slow": []}` | `tests-relacionados.sh` (called by `pre-push`) |
| `plan` | Plan or roadmap files or folders where tasks are ticked or struck through | `[]` | `["docs/roadmap.md"]` | `bitacora.py` |
| `taskId` | Regex of the project's task ids | `[A-Z]{2,5}-\\d+` | `"INS-\\d+"` | `bitacora.py` |

## Notes

- **`check` is a list of commands**, not a single script: each runs with `bash -c` at the root of the commit being
  pushed. One that does not exist is caught by `doctor.py` before a push fails.
- **`pushToProtected`** says how code reaches the protected branch today. A direct push that brings code always needs
  the mark in `pre-push`, with `direct` and with `pr`; with `pr`, the PR hook also asks for it when the pull request
  is created or merged. The config is read from the pushed commit, not the working copy; for the protected branch,
  `content` and `reviewMark` come from its remote tip (from what is pushed only while it has no config yet, with a
  warning), and the branch is protected if either of them or the working copy says so: a commit cannot relax the
  rule that judges it.
- **`content` and the mark.** A change touching only `content` files needs no review; any other does. `revisado.sh`
  writes the reviewed commit to `reviewMark`, and the mark must be an ancestor of what is pushed with no code after it.
  `.claude/gw.json`, `.claude/settings.json`, `.claude/gw/` and `.githooks/` are always code, whatever `content` says.
- **`logRows`** goes with the row-based log template (``| **Current task · `branch`** | … |``); the push checks that
  each branch writes only in its own row.
- After changing the workflow version, bump `version` by hand (`/gw-update` does it): `doctor.py` compares that number
  with the copied headers.
