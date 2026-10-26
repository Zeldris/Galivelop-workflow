#!/usr/bin/env bash
# galivelop-workflow v0.4.1
# Runs the project's `check` (every command of .claude/gw.json, prefixed by `checkWrapper` exactly as the pre-push does)
# at the repo root with GW_PUSH_PROTECTED=false, output streamed, stopping at the first failure. When it all passes and
# the work tree did not change during the run, it records the tree it would commit (see check-verde.sh), so the next
# push of that same tree skips the check. GW_CHECK_CACHE=0 leaves the cache alone.
#   bash scripts/check.sh
# Bash 3.2 compatible. Root from this script's path, never from $CLAUDE_PROJECT_DIR or the current directory.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE  # git exports GIT_DIR to hooks, also in a linked worktree
root="$(unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE; git -C "$here" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "check: $here is not inside a git repository; reinstall the workflow: /gw-update" >&2; exit 1; }
cd "$root" || exit 1
if [ -d "$root/.claude/gw/scripts" ]; then scripts="$root/.claude/gw/scripts"; else scripts="$root/scripts"; fi
config="$scripts/config.py"
helper="$scripts/check-verde.sh"
fail() {  # fail <message>: the message ends with the command that fixes it
  echo "check: $1" >&2
  exit 1
}
[ -f "$config" ] || fail "the workflow scripts are missing ($config); reinstall them: /gw-update"
checks="$(python3 "$config" --root "$root" get check)" || fail "cannot read 'check' from .claude/gw.json; fix the config: python3 $config --root $root validate"
wrapper="$(python3 "$config" --root "$root" get checkWrapper)" || fail "cannot read 'checkWrapper' from .claude/gw.json; fix the config: python3 $config --root $root validate"

key=""
tree_before=""
if [ "${GW_CHECK_CACHE:-}" != "0" ] && [ -f "$helper" ]; then  # any failure of the cache only means no recording
  # Its reason for not giving a tree (a skip-worktree entry, a modified submodule) goes to stderr: the check still runs.
  tree_before="$(bash "$helper" worktree-tree)" || tree_before=""
  if [ -n "$tree_before" ]; then
    key="$(printf '%s\n' "$checks" | bash "$helper" key "$tree_before" "$wrapper" 2>/dev/null)" || key=""
  fi
fi

while IFS= read -r cmd; do
  [ -n "$cmd" ] || continue
  [ -z "$wrapper" ] || cmd="$wrapper bash -c '$(printf '%s' "$cmd" | sed "s/'/'\\\\''/g")'"
  echo "check: running '$cmd'"
  if ! GW_PUSH_PROTECTED=false bash -c "$cmd" < /dev/null; then
    fail "failed: '$cmd'; fix it and run the whole check again: bash $0"
  fi
done <<<"$checks"

if [ -z "$key" ]; then
  if [ "${GW_CHECK_CACHE:-}" = "0" ]; then
    echo "check: all green (not recorded for the pre-push: the cache is off; to record it: bash $0)"
  else
    echo "check: all green (not recorded for the pre-push: the cache is unavailable, see above; after fixing it: bash $0)"
  fi
  exit 0
fi
tree_after="$(bash "$helper" worktree-tree 2>/dev/null)" || tree_after=""
if [ "$tree_after" != "$tree_before" ]; then
  echo "check: all green, but the work tree changed during the run (${tree_before:0:7} -> ${tree_after:0:7}); not recorded, so the next push runs the check again. To record it: bash $0"
  exit 0
fi
bash "$helper" add "$key" < /dev/null
if bash "$helper" has "$key" > /dev/null 2>&1; then
  echo "check: all green on tree ${tree_before:0:7}; the next push of this same tree will skip the check (to run it anyway: GW_CHECK_CACHE=0 git push)"
else
  echo "check: all green, but it could not be recorded (see above); the next push will run the check again"
fi
