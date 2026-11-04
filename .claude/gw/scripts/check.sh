#!/usr/bin/env bash
# galivelop-workflow v0.5.0
# Runs the project's `check` (every command of .claude/gw.json, prefixed by `checkWrapper` exactly as the pre-push
# does) at the repo root with GW_PUSH_PROTECTED=false, stopping at the first failure, then prints a summary (each
# command, ok/FAILED, seconds) and ends with one line `CHECK <ok|FAILED>: <what failed>`.
# The output of every command always goes to a log: <git common dir>/gw/check-<sha>.log (<sha> = HEAD, plus -dirty
# when the work tree has changes; GW_CHECK_LOG overrides the path, a relative one is taken from the current
# directory), also shown live unless --quiet (-q, or GW_CHECK_QUIET=1/true/yes): then only the last GW_CHECK_TAIL
# lines (default 40) of the command that fails are shown, with the log path. The log of a run is never deleted by
# the scripts. A lock <git common dir>/gw/check.lock (the pid and sha of the run) keeps two checks from running at
# once: a second one waits up to `checkLockWait` seconds (.claude/gw.json, default 0 = no wait) and then exits 3
# saying which pid/sha runs; a lock whose pid no longer exists is discarded; Ctrl-C or a kill releases it.
# When it all passes and the work tree did not change during the run, it records the tree it would commit (see
# check-green.sh), so the next push of that same tree skips the check. GW_CHECK_CACHE=0 leaves the cache alone.
#   bash scripts/check.sh [--quiet|-q]
# Bash 3.2 compatible. Root from this script's path, never from $CLAUDE_PROJECT_DIR or the current directory.
set -uo pipefail
orig_pwd="$PWD"
quiet=""
case "${GW_CHECK_QUIET:-}" in 1|true|yes) quiet=1 ;; esac
case "${1:-}" in
  --quiet|-q) quiet=1; shift ;;
esac
[ "$#" -eq 0 ] || { echo "check: unexpected argument '$1'; usage: bash $0 [--quiet|-q]" >&2; exit 2; }
tail_lines="${GW_CHECK_TAIL:-40}"
case "$tail_lines" in ''|*[!0-9]*) tail_lines=40 ;; esac
here="$(cd "$(dirname "$0")" && pwd)"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE  # git exports GIT_DIR to hooks, also in a linked worktree
root="$(unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE; git -C "$here" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "check: $here is not inside a git repository; reinstall the workflow: /gw-update" >&2; exit 1; }
cd "$root" || exit 1
if [ -d "$root/.claude/gw/scripts" ]; then scripts="$root/.claude/gw/scripts"; else scripts="$root/scripts"; fi
config="$scripts/config.py"
helper="$scripts/check-green.sh"
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

# --- the log and the lock live in <git common dir>/gw (shared by linked worktrees)
common="$(git rev-parse --git-common-dir 2>/dev/null)" && common="$(cd "$common" 2>/dev/null && pwd)" || common=""
[ -n "$common" ] || fail "cannot find the git dir; run it inside the repository, or set GW_CHECK_LOG to a writable file outside the work tree"
gwdir="$common/gw"
mkdir -p "$gwdir" 2>/dev/null || fail "cannot create $gwdir; make the git dir writable, e.g. chmod u+w $common"
sha="$(git rev-parse --short=12 HEAD 2>/dev/null)" || sha="nohead"
[ -z "$(git status --porcelain 2>/dev/null | head -n 1)" ] || sha="$sha-dirty"
log="${GW_CHECK_LOG:-$gwdir/check-$sha.log}"
case "$log" in /*) ;; *) log="$orig_pwd/$log" ;; esac
case "$log" in
  "$root"/.git/*) ;;  # inside the git dir: not part of the tree
  "$root"/*)
    git check-ignore -q -- "$log" 2>/dev/null ||
      fail "the log $log is inside the work tree and would change it; set GW_CHECK_LOG to a path outside the work tree or git-ignored, e.g. GW_CHECK_LOG=$gwdir/check.log" ;;
esac

lock="$gwdir/check.lock"
lock_wait="$(python3 "$config" --root "$root" get checkLockWait 2>/dev/null)" || lock_wait=0
case "$lock_wait" in ''|*[!0-9]*) lock_wait=0 ;; esac
have_lock=""
child=""
release() { [ -z "$have_lock" ] || rm -rf "$lock"; have_lock=""; }
trap 'release' EXIT
trap 'release; exit 130' INT
trap 'release; exit 143' TERM
deadline=$((SECONDS + lock_wait))
while :; do
  if mkdir "$lock" 2>/dev/null; then
    have_lock=1
    printf '%s\n' "$$" > "$lock/pid"
    printf '%s\n' "$sha" > "$lock/sha"
    break
  fi
  holder="$(cat "$lock/pid" 2>/dev/null)"
  if [ -z "$holder" ]; then  # the holder is between mkdir and writing its pid: give it a moment
    sleep 1
    holder="$(cat "$lock/pid" 2>/dev/null)"
  fi
  case "$holder" in ''|*[!0-9]*) holder="" ;; esac
  if [ -z "$holder" ] || ! kill -0 "$holder" 2>/dev/null; then  # orphan: its process is gone
    echo "check: discarding a stale lock (pid ${holder:-unknown} is not running)" >&2
    rm -rf "$lock"
    continue
  fi
  other="$(cat "$lock/sha" 2>/dev/null)"
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "CHECK FAILED: not run, another check is running (pid $holder, sha ${other:-unknown}); wait for it and read its log $gwdir/check-${other:-unknown}.log, or raise checkLockWait in .claude/gw.json to wait for it (kill $holder stops it)" >&2
    exit 3
  fi
  sleep 2
done

: > "$log" 2>/dev/null || fail "cannot write the log $log; set GW_CHECK_LOG to a writable file"
echo "check: log: $log"
summary=""
failed_cmd=""
failed_section=""
while IFS= read -r cmd; do
  [ -n "$cmd" ] || continue
  [ -z "$wrapper" ] || cmd="$wrapper bash -c '$(printf '%s' "$cmd" | sed "s/'/'\\\\''/g")'"
  echo "check: running '$cmd'"
  start=$SECONDS
  printf '== %s\n' "$cmd" >> "$log"
  offset="$(wc -c < "$log" | tr -d ' ')"
  if [ -n "$quiet" ]; then
    GW_PUSH_PROTECTED=false bash -c "$cmd" < /dev/null >> "$log" 2>&1
    rc=$?
  else
    # live output, also into the log; stdout and stderr stay on their own streams (two fifos, two tees)
    fifos="$(mktemp -d "${TMPDIR:-/tmp}/gw-check-fifo.XXXXXX")" && mkfifo "$fifos/out" "$fifos/err" || fail "cannot create a fifo in ${TMPDIR:-/tmp}; free space or set TMPDIR to a writable folder"
    tee -a "$log" < "$fifos/out" &
    tee_out=$!
    tee -a "$log" >&2 < "$fifos/err" &
    tee_err=$!
    GW_PUSH_PROTECTED=false bash -c "$cmd" < /dev/null > "$fifos/out" 2> "$fifos/err"
    rc=$?
    wait "$tee_out" "$tee_err"
    rm -rf "$fifos"
  fi
  secs=$((SECONDS - start))
  if [ "$rc" -eq 0 ]; then
    summary="$summary  ok      ${secs}s  $cmd
"
  else
    summary="$summary  FAILED  ${secs}s  $cmd (exit $rc)
"
    failed_cmd="$cmd"
    failed_section="$(tail -c +"$((offset + 1))" "$log" | grep '^== ' | tail -n 1)"
    break
  fi
done <<<"$checks"

echo "check: summary"
printf '%s' "$summary"
if [ -n "$failed_cmd" ]; then
  if [ -n "$quiet" ]; then
    echo "check: last $tail_lines lines of the failed command:"
    tail -c +"$((offset + 1))" "$log" | tail -n "$tail_lines"
  fi
  echo "check: full output: $log"
  echo "check: failed: '$failed_cmd'; fix it and run the whole check again: bash $0" >&2
  echo "CHECK FAILED: $failed_cmd${failed_section:+ [$failed_section]}" | tee -a "$log"
  exit 1
fi

finish_ok() {  # finish_ok <message>: the CHECK line is always the last one
  echo "$1"
  echo "CHECK ok: nothing failed" | tee -a "$log"
  exit 0
}
if [ -z "$key" ]; then
  if [ "${GW_CHECK_CACHE:-}" = "0" ]; then
    finish_ok "check: all green (not recorded for the pre-push: the cache is off; to record it: bash $0)"
  else
    finish_ok "check: all green (not recorded for the pre-push: the cache is unavailable, see above; after fixing it: bash $0)"
  fi
fi
tree_after="$(bash "$helper" worktree-tree 2>/dev/null)" || tree_after=""
if [ "$tree_after" != "$tree_before" ]; then
  finish_ok "check: all green, but the work tree changed during the run (${tree_before:0:7} -> ${tree_after:0:7}); not recorded, so the next push runs the check again. To record it: bash $0"
fi
bash "$helper" add "$key" < /dev/null
if bash "$helper" has "$key" > /dev/null 2>&1; then
  finish_ok "check: all green on tree ${tree_before:0:7}; the next push of this same tree will skip the check (to run it anyway: GW_CHECK_CACHE=0 git push)"
else
  finish_ok "check: all green, but it could not be recorded (see above); the next push will run the check again"
fi
