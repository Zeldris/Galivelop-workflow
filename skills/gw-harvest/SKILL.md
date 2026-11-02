---
name: gw-harvest
description: Collect, as proposals, what projects using Galivelop-workflow changed or invented (edited workflow skills and scripts, new skills, ideas in their retros) since the last harvest. Use when, from the Galivelop-workflow repo, the user asks to harvest, review or gather improvements from connected projects, and at the start of every new workflow version (AGENTS.md; `version.py --release` checks it).
disable-model-invocation: true
license: MIT
compatibility: Run in the Galivelop-workflow repo with the project repos cloned locally; git and python3.
metadata:
  version: "0.4.3"
  source: "Galivelop workshop"
---

# gw-harvest

If `.claude/gw/gw-harvest.md` exists in the project, read it first: it holds what is specific to the project.

The workflow learns from the projects that use it. `retro` pushes general ideas from a project; this skill pulls
them, plus anything a project changed in its copy of the workflow. **It proposes; it never applies.**

## Steps

1. **Pick the projects.** The projects the user names (or those added to the session), cloned locally. Projects are read-only: never commit, push, edit files or rewrite history in them (updating a dedicated,
   clean clone with fetch + fast-forward is allowed: it is how you see their latest state), and do not register them
   as session roots (their same-name skills would shadow this repo's).
   **Clone them read-only into a scratch folder** outside the session's working directory. A private project may be
   added with `add_repo` (read access) so the clone works, but never registered (`register_repo_root`): a registered
   project loads its `CLAUDE.md`, `AGENTS.md` and skill list into every call of the session (~17 % of a harvest
   session's input in one measure).
   **Bring each clone up to date first** (`git -C <project> fetch && git -C <project> merge --ff-only @{upstream}`):
   `harvest.py` harvests the clone's `HEAD` and warns when it is behind or diverged from its upstream, or has none.
   `<proposalsDir>` is the config's `proposalsDir`: `python3 scripts/config.py get proposalsDir` (default `docs/proposals`).

2. **Run the mechanical part** from this repo:

   ```bash
   python3 scripts/harvest.py <project-path> [<project-path> ...]
   ```

   It lists, per project and since the last harvest (`<proposalsDir>/state.json`): workflow skills whose body
   differs, skills born in the project, copied workflow scripts that differ, retro files, the
   `## For Galivelop-workflow` sections of every changed `.md` (pilot notes too, not only retros), the lines there that
   start with "Propuesta para el flujo" / "Proposal for the workflow" (how projects note requests in their hand-off
   log), and the commits. A copy equal to an earlier workflow commit is listed apart
   as an older copy: the project's stale text, never a proposal. If it reports missing history, deepen the clone as
   it says and run it again.
   **Private projects come out anonymized.** With `anonymize` in this repo's `.claude/gw.local.json`
   (`{"<name>": "private-project-N"}`, never committed), the report, the diff and the state carry the alias instead
   of the name, so paths in the report name the alias, not your clone: run the commands on the path you passed. If
   it refuses a project ("private names with no alias", exit 1), ask the user for the alias, have it added to
   `anonymize` and run it again; never work from the clone's raw files around it.
3. **Look at the findings with one subagent per project, all in parallel** (one message with several Agent calls),
   each returning a short summary with paths per finding, never whole files in the main session. For a changed
   skill, `python3 scripts/harvest.py --diff <skill> <project-path>` gives the diff.
4. **Classify each finding**:
   - **General**: would help any project (a fix, a clearer rule, a missing check, a reusable skill) → proposal.
   - **Project-specific**: domain wording, stack commands, local paths → note it as "stays in the project".
   - **Already here**: the workflow has it in a newer form → note it, no proposal.
5. **Write the proposals** in `<proposalsDir>/YYYY-MM-DD-<repo-name>.md` using the template below, in the
   workflow repo's language for human docs. `<repo-name>` is the name part of the id the report prints (the alias for
   a private project), and the text uses that alias too, including what subagents summarized from the clone. Before
   committing the file, run `python3 scripts/private-check.py --all`; it must pass. One file per project and harvest; projects with nothing new go as one line
   each in another project's file, or in one file of their own when no project brings anything (every version needs
   a `# Harvest` file added since the last tag: `python3 scripts/version.py --release`).
6. **Present them to the user**, most valuable first, and wait. What the user approves becomes a normal change in
   this repo: the piece updated, a CHANGELOG entry and a version bump (patch, minor or major per plan §7).
7. **Record the harvest** once the proposals file is committed:
   `python3 scripts/harvest.py --update-state <project-path> ...`, then commit `<proposalsDir>/state.json` in the
   same commit as the proposals.

## Proposal template

```markdown
# Harvest <repo> — YYYY-MM-DD

From `<last>` to `<head>` (`scripts/harvest.py`).

## P1. <short title>

- **Source:** `<path>` @ `<commit>` (<skill | script | retro | new skill>)
- **What changes:** <one or two sentences>
- **Why it is general:** <the problem it solves for any project>
- **Version bump:** patch | minor | major
- **Status:** proposed

## Stays in the project

- `<path>`: <why it is project-specific>
```

## Rules

- A proposal cites the exact source path and commit; never paraphrase without a source.
- A project's local edit to a copied workflow file is a signal, not a patch: propose the general version here so the
  next update reaches every project.
- Don't harvest secrets, personal data or private names into this repo: a private project is its
  `private-project-N` alias everywhere here (file names, text, commit messages).
