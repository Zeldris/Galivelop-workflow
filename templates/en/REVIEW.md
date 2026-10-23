<!-- galivelop-workflow v0.4.0 -->
# Review guide

What the reviewer (`/code-review`, or any agent reviewing a diff) checks in every diff of {{project}}, besides the
usual bugs. The mechanical part is already done by the check ({{check}}) and the git hooks; this is what needs
judgement. The project fills it in; the workflow never overwrites it once it exists.

## One fact, one place

- A fact that already lives somewhere (a config file, a data file, a constant) is not repeated by hand in code,
  docs or the README; if it must be repeated, every copy changes in the same commit.
- The workflow's settings live only in `.claude/gw.json` and only `.claude/gw/scripts/config.py` reads them.

## Hooks and scripts

- The repo root comes from the script's own path (`$(dirname "$0")`) or `git rev-parse --show-toplevel`, never from
  `$CLAUDE_PROJECT_DIR` or the current directory: a session may start outside the repo.
- A push hook checks **the commit being pushed**, not the working copy.
- Hooks **fail closed** when a fact is missing (a commit the clone lacks, an API that does not answer), with the
  command that fixes it.
- Shell scripts run on bash 3.2 (macOS): no `mapfile`, no associative arrays.
- A fixed-name folder in a shared directory (`$TMPDIR`, `/tmp`) is per user, created with mode 700 and refused if it
  already exists as a symlink or owned by another user; single files use `mktemp`.
- Every change to a hook or script comes with its test case; a case that expects a failure checks the reason, not
  only the exit code. The scripts under `.claude/gw/scripts/` are tested in the workflow's repo and are not edited here
  (a change goes to the workflow as a proposal, with `gw-harvest`); this rule applies to the project's own scripts.

## Brought from another repo: adapt to this repo's contracts

- Code, scripts or rules brought from another repository are checked against **this** repo, not the original:
  formats, paths, file extensions, naming patterns, constants, configuration keys and task ids.
- What comes from a project that ships another way (straight to the protected branch, or by pull request) is
  adapted to how this one ships to `{{protectedBranch}}`.
- A table or example in a guide that a script reads is read by that script in a test.

## Visible languages

- If `.claude/gw.json` declares `visibleLanguages`, every new text a user sees exists in each of those languages
  (labels, alternative texts, page titles, messages), and a translation is a real one, not the same text.

## Project rules

<!-- The project fills this in: what is never published, domain rules, accessibility, performance, security. -->
