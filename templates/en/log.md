<!-- galivelop-workflow v0.4.2 -->
# Log (hand-off)

> Read it whole at the start of every session. What is not pushed does not exist: commit + push at every stable
> point, with this log updated in the same commit. The workflow never overwrites it once it exists.

## Current state

| Field | Value |
|---|---|
| **Branch** | _(working branch)_ |
| **Phase / task** | _(phase and task in progress; with the branch heading for `{{protectedBranch}}`, which of the phases before it are done: "1 done (`<commit>`), 2 pending")_ |
| **Last stable point** | _(last commit with the check green, and what it brought)_ |
| **Next step** | _(the next concrete step, so the next session needs to ask nothing)_ |
| **Check** | {{check}}: _(green / red, and what fails)_ |

With `logRows` in `.claude/gw.json`, each branch writes only in its own row of this table, at most 600 characters,
shaped as ``| **Current task · `<branch>`** | task, phases before `{{protectedBranch}}`, what is missing and the next step |``; the push checks it.

## For the next release

_(what goes to `{{protectedBranch}}` next, and what it is waiting for)_

## Done (last 5)

1. _(date — what was closed, in two lines at most: the detail is in the commit; the oldest entry goes when there are
   more than 5, the history is in git)_

## Pending

- _(decisions of the person that block something, known problems, ideas not yet planned)_

## Check the state

- Last commits: `git fetch origin <branch> && git log --oneline -5 origin/<branch>`.
- The check: {{check}}.
- Workflow set up right: `python3 .claude/gw/scripts/doctor.py`.
- Log state as a new session gets it: `python3 .claude/gw/scripts/recuperar.py --estado`.
