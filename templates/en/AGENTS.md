<!-- galivelop-workflow v0.1.0 -->
# {{project}} — instructions for agents

This project is worked on in hand-offs: a session can end at any moment (tokens, container, account switch) and the
next one has to carry on **without losing anything and without asking where things were**. Everything in this file
exists for that. The workflow is Galivelop-workflow v{{version}}; its scripts live in `.claude/gw/scripts/`, its
skills in `.claude/skills/` and its settings in `.claude/gw.json` (read only by `.claude/gw/scripts/config.py`).

## At the start of every session

1. Read the log, `{{log}}`: branch, task in progress, what is pending and the next step.
2. `git fetch origin <branch>` and check that the last commit matches what the log says.
3. Check the state is green before touching anything: {{check}}.
4. Carry on with the log's **next step**, unless the user asks for something else.
5. At the start of every task, bring in the protected branch: `git fetch origin {{protectedBranch}}` and, if it brings
   commits, `git merge origin/{{protectedBranch}}` (merge, never rebase: branches are pushed). If the conflict touches
   the same logic on both sides, stop and ask the user.
6. **The session is opened with the repo as its working folder.** Opened anywhere else (a folder holding several
   repos, the home folder), it does not load `.claude/settings.json`: no compaction limit, no start hook, no guard on
   the protected branch. If that happens, tell the user so they reopen it from the repo; meanwhile run
   `git config core.hooksPath .githooks` before the first commit, and before pushing to `{{protectedBranch}}` or
   creating or merging a pull request, check by hand what that guard checks: the review mark of the same commit and
   a green CI.

## Hand-offs: commit and push all the time

Each session may run in a throwaway container: **what is not pushed does not exist** for the next one.

- Commit + push at every stable point (check green). **Never more than 30-45 minutes of work without pushing.**
  Big tasks are split into small steps, each with its own commit.
- **The log is updated in the same commit** as the work it describes, not at the end of the session.
- **The state lives in the files, not in the conversation**: the plan says what is implemented, the log what is being
  done. A half-done task says what is done and what is missing.
- If you have to stop with something half-done or red: commit anyway with `WIP:` at the start of the message and, in
  the log, what fails and why. Never leave work only on the local machine.
- Push to the working branch (`git push -u origin <branch>`); if it fails because of the network, retry after 2, 4,
  8 and 16 s.
- **After an interrupted or rejected call, run `git status` and `git diff` before repeating it**: the change may
  already be saved, or even pushed, and repeating it duplicates it.
- If the user says stop, stop: push what there is, leave the log up to date and do nothing else.
- **When a phase closes** (or a large task), with the log up to date, recommend `/clear` before the next one: a long context is
  almost all the spend, and the log is enough to resume.
- **When each block or phase closes, look at the CI of the last push.** A CI that does not start (no quota, no
  runners) counts as red: tell the user and treat nothing as checked by CI.

## Checking

- **The project's check:** {{check}}. `.githooks/pre-push` runs it on the commit being pushed, and CI
  (`.github/workflows/comprobar.yml`) on every push outside `{{protectedBranch}}` and on every pull request.
- **What can be checked is checked by a script**, not by an agent: skills and guides only decide what needs
  judgement. If a rule keeps being broken, it becomes a check.
- **What depends on a particular machine is not declared tested by tests** (another operating system, a device, the
  user's own computer): it is written down as pending in the plan, with who checks it and where.
- A new test must fail without its fix: `bash .claude/gw/scripts/rojo-sin-arreglo.sh "<test command>" <fix-file>...`.
- A test that expects a failure checks **the reason** (the message or the cause), not only the exit code: otherwise
  it also passes when it fails for another reason.
- `python3 .claude/gw/scripts/doctor.py` says whether the workflow is set up right, with the command that fixes each
  problem.

## Commit messages

- First line: what changes, in the project's language, with the ids of the tasks touched.
- Body: what was done, what is left of that task if it is not closed, and the state of the check.
- **Last line: `Next: <next concrete step>`**, in the same final block as any attribution lines.

## Branches and `{{protectedBranch}}`

- Work on the branch the log names (or the one the session was given, written into the log at once).
- **One branch per session**: two sessions at the same time never push to the same branch. If the log's branch is in
  use by another session, create `claude/<topic>` from it and write only in your own part of the log. Your work goes
  back by `git merge` before going to `{{protectedBranch}}`.
- Merge, never rebase: branches are pushed.
- **To `{{protectedBranch}}` only when the user confirms**, and it is written into the log. Depending on
  `pushToProtected` in `.claude/gw.json`, the work goes straight to it (`direct`: `.githooks/pre-push` asks for the
  review mark) or by pull request (`pr`: a Claude Code hook asks for the mark before creating or merging it; a direct
  push still needs it).
- **Merged only with CI green**, also when the user says "merge directly": that skips waiting for more reviews, never
  the CI nor the retro presented to the user.
- A subagent's branch comes back with `bash .claude/gw/scripts/fusionar.sh <branch> "<message>"`, which runs the check
  and cleans up its worktree.

## Before going to `{{protectedBranch}}`: three phases

Never on work that is already merged.

1. **Code:** `git fetch origin {{protectedBranch}}`, then a review of the diff against `origin/{{protectedBranch}}`
   with every finding (in Claude Code, `/code-review --max-findings all`), with the criteria of `REVIEW.md`. Fixes
   committed and pushed. Only code needs review: what matches `content` in `.claude/gw.json` is content.
2. **Environment:** the `opt-tokens` skill, then `retro` (plus `opt-ai` if there were measurements with a local AI
   model). Their proposals are **presented to the user**; what they confirm is applied on the branch. A retro written
   without presenting it does not count.
3. **Close:** if phase 2 brought code, review only those commits and their fixes; then
   `bash .claude/gw/scripts/revisado.sh` (writes the review mark, `{{reviewMark}}`, and commits it) and `git push`;
   for a pull request, its description with the `pr` skill. Only then push to `{{protectedBranch}}` or create the
   pull request. Without the mark of the same commit, the hooks refuse it.

## Subagents

**Dealing work to subagents is authorised:** multi-step work is dealt to clean-context subagents with the
`orchestrate-dealer` skill (and the models the `selector` skill picks) without asking each time; the main session
plans, decides and reviews. This line is the authorisation the agent's own instructions ask for.

- Each subagent gets a brief: goal, paths, constraints, the check to run and what to report back.
- Other repositories are read through a subagent that returns a summary with paths, never modified from here.

## Project rules

<!-- The project fills this in: stack, how to run it, what must never be done, domain rules, where each thing lives.
     Keep it short; a rule that can be checked becomes a script. -->

- Install: {{install}}.
- _(to fill in)_
