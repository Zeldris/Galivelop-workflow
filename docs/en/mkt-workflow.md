# How Galivelop works with AI agents

[Español](../es/mkt-workflow.md)

Galivelop builds software with coding agents (Claude Code) following **Galivelop-workflow**: its own public,
versioned method, where the rules do not rely on the agent's good will but on **automatic checks that enforce
them**.

## What it solves for your project

- **Continuity.** An AI session can stop at any time; the work is not lost. Everything is pushed to the repository
  at every stable point, with a log that says where it stands and what comes next.
- **Quality.** Nothing reaches the published version without a code review, green tests and your confirmation.
- **Controlled cost.** Each task uses the AI model it calls for, and the spend is measured instead of guessed.
- **Traceability.** Every change can be followed from the plan's task to the commit that made it.

## How the work runs

1. **Plan and tasks.** The work is split into tasks with an id, in a plan you can read.
2. **Work on a branch.** The agent works away from the published version and pushes often, with the log updated in
   the same commit.
3. **Continuous checking.** Every push runs the project's check (tests, format, private data) on the exact code
   being pushed.
4. **Review before release.** Code review, a process retrospective and a review mark tied to that code.
5. **Release with your approval.** The published version only changes when you confirm it.

## What it guarantees, and how

| Guarantee | What enforces it |
|---|---|
| Nothing is lost between sessions | Constant pushes; a hook does not let a session end with unpushed work |
| Nothing unreviewed is released | A review mark tied to the commit; without it, the push is rejected |
| Tests really prove something | A new test has to fail without its fix |
| No keys or private data leak | A secrets check on every commit and every push |
| A CI that does not start is not green | It counts as red and you are told |
| Every change is traceable | Commit format with the task id and the next step |

## What you get

Your repository, with its full history and the log; the plan with the state of each task; and every version with its
list of changes. The method is public: you can review it at
[github.com/Zeldris/Galivelop-workflow](https://github.com/Zeldris/Galivelop-workflow).
