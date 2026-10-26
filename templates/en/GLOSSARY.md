<!-- galivelop-workflow v0.4.1 -->
# Glossary

Vocabulary of {{project}}. The workflow's terms come first; the project adds its own domain terms below and keeps
them up to date (skill `domain-modeling`). The workflow never overwrites this file once it exists.

## Workflow terms

- **Log**: `{{log}}`, the state of the work for the next session: branch, task in progress, next step, check.
- **Hand-off**: one session ending and another carrying on from the log, without asking where things were.
- **Stable point**: a state with the check green, committed and pushed.
- **Check**: the project's commands that must pass on every pushed commit: {{check}}.
- **`WIP:` commit**: a commit pushed with something half-done or red; the log says what fails and why.
- **Protected branch**: `{{protectedBranch}}`, what is published; it only receives reviewed work, with the person's
  confirmation.
- **Review mark**: `{{reviewMark}}`, the committed file holding the sha of the last reviewed commit; the hooks
  accept code up to it.
- **Content vs code**: content (what matches `content` in `.claude/gw.json`) needs no code review; everything else
  is code.
- **Subagent brief**: what a subagent receives: goal, paths, constraints, the check to run and what to report back.
- **Retro**: the session retrospective before going to the protected branch; its proposals are presented to the
  person, and what they confirm is applied on the branch.
- **Proposal (`.gw-nuevo`)**: a workflow file the update could not apply without losing local changes; merged by
  hand, then deleted.

## Project terms

<!-- **Term**: definition, and where it lives in the code. -->
