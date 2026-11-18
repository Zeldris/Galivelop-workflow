# The workflow from opencode and Codex

[Español](../es/other-agents.md)

The workflow is built for Claude Code, but its written part also works in other coding agents. This page says what
works outside Claude Code and what does not (B9, D7).

## What works

- **`AGENTS.md`:** opencode and Codex read it at start. The workflow's one makes sense without `@include` (only
  `CLAUDE.md` does `@AGENTS.md`), so the rules arrive whole.
- **Skills:** `apply.py` also copies the skills into `.agents/skills` (key `agentsSkillsDir`, [config](config.md)),
  where opencode looks for them. Codex uses its own folder (`~/.codex/skills`, per design D-7 in
  `docs/design/D-git.md`): copy them there by hand if you want them.
- **Git hooks** (`.githooks`): they belong to git, not to Claude Code, so `pre-commit`, `commit-msg` and `pre-push`
  check every commit and push the same.
- **Scripts:** `handoff.py`, `recover.py`, `check.sh`, `task.py` and the rest are run by hand or by the agent.

## What does not work

- **Claude Code hooks** (`.claude/settings.json`): the `SessionStart` that shows the hand-off log, the `Stop` that
  warns of unpushed work and the permission guards do not run. At start, read `docs/handoff.md` and run
  `python3 .claude/gw/scripts/recover.py --state`; before stopping, `git status` and push.
- **Subagents** with a `model` and `effort` per brief (`gw-orchestrate-dealer`): they depend on Claude Code's Agent
  tool.
- **Token ledger:** `metrics.py record` reads Claude Code's transcripts; opencode's and Codex's spend is not recorded
  yet (it goes to a `1.x`).

## Models outside Anthropic

Claude Code only launches Claude models. GPT, Gemini, DeepSeek and the rest are used from opencode or another tool
that supports them, never as the workflow's subagents. `gw-selector` may recommend them for a session in that tool.
Their prices can go as data in `metrics.prices` (a table with its `since` and `source`), but the ledger will have no
rows of theirs until those tools' spend is read.
