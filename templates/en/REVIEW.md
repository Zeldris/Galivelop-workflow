<!-- galivelop-workflow v0.5.0 -->
# Review guide

What the reviewer (`/code-review`, or any agent reviewing a diff) checks in every diff of {{project}}, besides the
usual bugs. The mechanical part is already done by the check ({{check}}) and the git hooks; this is what needs
judgement. Each rule ends in `(check: …)`, naming what enforces it, or in `(judgement)` when there is no check; a
mechanical rule marked `(judgement)` asks for its check. The project fills it in; the workflow never overwrites it
once it exists.

## How to report

- Before reporting a finding, try to refute it: look for the code, test or hook that already covers it. Only what
  survives is reported, with its path and line. (judgement)
- Findings are also written to a file outside the tree (the scratchpad, or `"$(git rev-parse --git-dir)/review.md"`),
  not only to the conversation: a compaction or a handover loses them, and that file feeds the fix briefs and the
  minor findings logged as pending. (judgement)
- A fact that expires (a version, a price, a quota, a limit of an outside service) written in the diff carries its
  date and source; if not, it is a finding. (judgement)
- The review ends with one verdict of three: `SHIP` (nothing to fix), `SHIP WITH FIXES` (there are fixes, none blocks)
  or `DO NOT SHIP` (something serious or breaking). (judgement)

## One fact, one place

- A fact that already lives somewhere (a config file, a data file, a constant) is not repeated by hand in code,
  docs or the README; if it must be repeated, every copy changes in the same commit. (judgement)
- The workflow's settings live only in `.claude/gw.json` and only `.claude/gw/scripts/config.py` reads them. (judgement)

## Hooks and scripts

- The repo root comes from the script's own path (`$(dirname "$0")`) or `git rev-parse --show-toplevel`, never from
  `$CLAUDE_PROJECT_DIR` or the current directory: a session may start outside the repo. (judgement)
- A push hook checks **the commit being pushed**, not the working copy. (judgement)
- Hooks **fail closed** when a fact is missing (a commit the clone lacks, an API that does not answer), with the
  command that fixes it. Reasoned exception: the path keys (`log`, `reviewMark`, `recordsDir`, `proposalsDir`,
  `ciLocalLog`) are optional with an English default, so an absent one is not a missing fact. (judgement)
- Shell scripts run on bash 3.2 (macOS): no `mapfile`, no associative arrays. (judgement)
- A fixed-name folder in a shared directory (`$TMPDIR`, `/tmp`) is per user, created with mode 700 and refused if it
  already exists as a symlink or owned by another user; single files use `mktemp`. (judgement)
- Every change to a hook or script comes with its test case; a case that expects a failure checks the reason, not
  only the exit code. It applies to the project's own scripts. (judgement)
- The scripts under `.claude/gw/scripts/` are tested in the workflow's repo and are not edited here: a change goes
  to the workflow as a proposal, with `gw-harvest` (check: `config-guard.py` asks before they are edited). (judgement)
- A hook that asks or blocks is reviewed by **trying to get around it**: wrappers whose options take a value
  (`sudo -u X`, `sudo -uX`, `env -u X`, `nice -n 5`, `timeout 5`, `xargs -I{}`), the destination of copiers (`cp`,
  `install`, `rsync`, `dd of=`, `-t DIR`), an ancestor of the protected folder and a relative path or one with `..`;
  and the usual false positives (reading or copying **from** the folder, `git restore --staged`). Each form, its case.
  (judgement)
- `pkill -f <pattern>` (and `pgrep -f`) also matches the command that launches it when the pattern is in it
  (`bash -c "… pkill -f server"`), and kills it: use a pidfile, `pgrep -x` or a pattern that does not match itself
  (`[s]erver`). (judgement)
- A runbook or brief that a scheduled task follows (a session with nobody watching) is reviewed as code, even if it
  matches `content`: what it says runs as it is. (judgement)

## Brought from another repo: adapt to this repo's contracts

- Code, scripts or rules brought from another repository are checked against **this** repo, not the original:
  formats, paths, file extensions, naming patterns, constants, configuration keys and task ids. (judgement)
- What comes from a project that ships another way (straight to the protected branch, or by pull request) is
  adapted to how this one ships to `{{protectedBranch}}`. (judgement)
- A table or example in a guide that a script reads is read by that script in a test. (judgement)

## Visible languages

- If `.claude/gw.json` declares `visibleLanguages`, every new text a user sees exists in each of those languages
  (labels, alternative texts, page titles, messages), and a translation is a real one, not the same text. (judgement)

## Project rules

<!-- The project fills this in: what is never published, domain rules, accessibility, performance, security. -->
