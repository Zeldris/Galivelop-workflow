<!-- galivelop-workflow v0.4.2 -->
@AGENTS.md

## Claude Code only

- Reply in the project's language (`{{language}}`).
- At the start of every task, say in one line which skill and which model the case calls for, with the `selector`
  skill. The session's model is the person's choice; subagents get the cheapest model that does the job well.
- Before going to `{{protectedBranch}}`: `/code-review --max-findings all` of the diff against
  `origin/{{protectedBranch}}`, with the criteria in `REVIEW.md` (phase 1 of the three in `AGENTS.md`).
- Mechanical work goes to subagents with cheap models (`orchestrate-dealer`); the main session plans, decides and
  reviews.
- **Compaction:** `.claude/settings.json` sets the auto-compaction window. After a compaction or a `/clear`, the
  start hook runs `python3 .claude/gw/scripts/recuperar.py --estado`, which puts back the log's state and the last
  commits; a detail that was lost is searched with `python3 .claude/gw/scripts/recuperar.py --buscar "<text>"`.
  What must survive goes into `{{log}}`.
- **Auto mode** may ask for permission to edit `.claude/settings.json`, `.claude/gw/scripts/` and `.githooks/`: ask the
  person before touching them, or let them run the change themselves.
