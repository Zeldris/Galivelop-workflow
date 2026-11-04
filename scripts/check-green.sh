#!/usr/bin/env bash
# galivelop-workflow v0.5.0
# Cache of "the project's `check` already passed": lets the pre-push (and scripts/check.sh) skip a check that already
# ran green on the same tree with the same commands and wrapper, less than 24 h ago. One line per success,
# "<epoch> <key>", in <git common dir>/gw-check-green (shared by linked worktrees), the last 50 kept.
#   printf '%s\n' "$checks" | bash check-green.sh key <tree-sha> <wrapper>   # prints the key
#   bash check-green.sh worktree-tree   # the tree the working copy would commit after `git add -A` (real index untouched);
#                                       # fails when that tree may not be what a check sees (assume-unchanged or
#                                       # skip-worktree entries, sparse checkout, a modified submodule)
#   bash check-green.sh has <key>       # exit 0 and the age in minutes if recorded < 24 h ago; any problem is a miss (1)
#   bash check-green.sh add <key>       # records the key now; best effort (a write failure warns and exits 0)
#   bash check-green.sh lock-acquire <owner-pid> <sha> <wait-seconds> <log>
#                                       # takes <git common dir>/gw/check.lock for <owner-pid> (E20), a symlink whose target
#                                       # is "pid|process start|sha|log" (so the take is atomic and the owner verifiable);
#                                       # exit 0 taken, 3 another live check holds it (names pid/sha/log) after waiting
#                                       # <wait-seconds>, 1 cannot. A lock whose process is gone, or whose pid now belongs
#                                       # to another process (different start time), is discarded.
#   bash check-green.sh lock-release <owner-pid>   # removes the lock only if <owner-pid> owns it
# GW_CHECK_CACHE=0 makes `has` always miss. Bash 3.2 compatible. Root from this script's path, never from the cwd.
set -uo pipefail
TTL_SECONDS=86400  # a recorded success older than this is a miss
KEEP_LINES=50      # lines the cache file keeps
FORMAT="gw-check-cache 1"
here="$(cd "$(dirname "$0")" && pwd)"
# Git exports GIT_DIR (and friends) to hooks, also in a linked worktree; with GIT_DIR set `rev-parse --show-toplevel`
# answers $here, not the repo root.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
root="$(unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE; git -C "$here" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "check-green: $here is not inside a git repository; reinstall the workflow: /gw-update" >&2; exit 1; }
cd "$root" || exit 1

usage() {
  echo "check-green: $1; usage: bash $0 key <tree-sha> <wrapper> | worktree-tree | has <key> | add <key> | lock-acquire <pid> <sha> <wait> <log> | lock-release <pid>" >&2
  exit 2
}
valid_key() {  # a git object name: 40 (sha-1) or 64 (sha-256) lowercase hex digits
  case "$1" in *[!0-9a-f]*) return 1 ;; esac
  [ "${#1}" -eq 40 ] || [ "${#1}" -eq 64 ]
}
cache_file() {  # absolute path of the cache file, or fail
  local common
  common="$(git rev-parse --git-common-dir 2>/dev/null)" && common="$(cd "$common" 2>/dev/null && pwd)" && [ -n "$common" ] || return 1
  printf '%s/gw-check-green\n' "$common"
}

cmd_key() {
  [ "$#" -ge 1 ] || usage "key needs a tree sha"
  local tree="$1" wrapper="${2:-}" commands
  commands="$(cat)"
  # Every part is on its own labelled line, so a change in any of them changes the key.
  printf '%s\ntree %s\nwrapper %s\ncommands\n%s\n' "$FORMAT" "$tree" "$wrapper" "$commands" | git hash-object --stdin
}

hidden_entry() {  # the first index entry git does not compare with the disk (assume-unchanged, skip-worktree), or fail
  local listing
  listing="$(git ls-files -v 2>/dev/null)" || return 1
  # `ls-files -v` tags assume-unchanged entries with a lowercase letter and skip-worktree ones (sparse checkout) with S.
  printf '%s\n' "$listing" | { LC_ALL=C grep -m 1 '^[a-zS] ' || true; } | cut -c 3-
}
dirty_submodule() {  # the first submodule (gitlink) with new commits or changes inside, or fail
  local rec path
  git ls-files -s -z 2>/dev/null | while IFS= read -r -d '' rec; do
    case "$rec" in 160000\ *) ;; *) continue ;; esac
    path="${rec#*$'\t'}"
    if [ -n "$(git status --porcelain --ignore-submodules=none -- "$path" 2>/dev/null)" ]; then
      printf '%s\n' "$path"
      break
    fi
  done
}

tmp_add=""   # the temp file of add, global for the same reason
tmp_tree=""  # the temp dir of worktree-tree: global, because the EXIT trap runs after the function is gone
cmd_worktree_tree() {
  local tmp idx hidden sub
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/gw-check-tree.XXXXXX")" || {
    echo "check-green: cannot create a temp dir in ${TMPDIR:-/tmp}; free space and retry: bash $0 worktree-tree" >&2; return 1; }
  tmp_tree="$tmp"
  trap 'rm -rf "$tmp_tree"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP
  idx="$(git rev-parse --git-path index 2>/dev/null)" || {
    echo "check-green: cannot locate the git index; check the repository: git rev-parse --git-path index" >&2; return 1; }
  # No index yet (a repo with no add or commit): an index file that does not exist is an empty one for git.
  if [ -f "$idx" ]; then
    # -p keeps the index's mtime: git re-reads the files changed in the same second it was written (racy git); a
    # newer copy would trust their size and mtime and stage the old content.
    cp -p "$idx" "$tmp/index" || {
      echo "check-green: cannot copy the git index $idx; check permissions and space: cp -p $idx $tmp/index" >&2; return 1; }
  fi
  GIT_INDEX_FILE="$tmp/index" git add -A >/dev/null 2>&1 || {
    echo "check-green: cannot stage a copy of the work tree; reproduce it with: git add -A --dry-run" >&2; return 1; }
  # The tree must be what a check of the work tree sees: git add -A skips the files git does not look at (the
  # copy keeps the real index's flags).
  hidden="$(GIT_INDEX_FILE="$tmp/index" hidden_entry)" || {
    echo "check-green: cannot list the index entries; check the repository: git ls-files -v" >&2; return 1; }
  if [ -n "$hidden" ]; then
    echo "check-green: '$hidden' is assume-unchanged or skip-worktree (sparse checkout?), so the staged tree may not be what the check sees; clear the flags to use the cache: git update-index --no-assume-unchanged --no-skip-worktree -- '$hidden'" >&2
    return 1
  fi
  sub="$(dirty_submodule)"
  if [ -n "$sub" ]; then
    echo "check-green: submodule '$sub' has new commits or changes inside, so the staged tree may not be what the check sees; commit or discard them to use the cache: git -C '$sub' status" >&2
    return 1
  fi
  GIT_INDEX_FILE="$tmp/index" git write-tree 2>/dev/null || {
    echo "check-green: cannot write the tree of the work tree; reproduce it with: git add -A --dry-run && git write-tree" >&2; return 1; }
}

cmd_has() {
  [ "$#" -eq 1 ] || usage "has needs a key"
  [ "${GW_CHECK_CACHE:-}" != "0" ] || return 1
  valid_key "$1" || return 1
  local file now epoch k age found=""
  file="$(cache_file)" || return 1
  [ -f "$file" ] || return 1
  now="$(date +%s)" || return 1
  case "$now" in '' | *[!0-9]*) return 1 ;; esac
  while read -r epoch k _rest; do  # the newest line for the key wins
    [ "${k:-}" = "$1" ] || continue
    case "$epoch" in '' | *[!0-9]*) continue ;; esac
    found="$epoch"
  done 2>/dev/null < "$file"
  [ -n "$found" ] || return 1
  age=$((now - found))
  [ "$age" -ge 0 ] && [ "$age" -lt "$TTL_SECONDS" ] || return 1  # in the future (clock change) or too old
  echo $((age / 60))
}

cmd_add() {
  [ "$#" -eq 1 ] || usage "add needs a key"
  valid_key "$1" || usage "'$1' is not a git object name"
  local file now tmp
  file="$(cache_file)" || { echo "check-green: warning: cannot locate the git dir, check not recorded; check the repository: git rev-parse --git-common-dir" >&2; return 0; }
  now="$(date +%s)" || { echo "check-green: warning: cannot read the clock, check not recorded; check it: date +%s" >&2; return 0; }
  [ ! -d "$file" ] || { echo "check-green: warning: $file is a directory, check not recorded; remove it: rm -r $file" >&2; return 0; }
  tmp="$(mktemp "$file.XXXXXX" 2>/dev/null)" || { echo "check-green: warning: cannot write next to $file, check not recorded; make its folder writable: ls -ld ${file%/*}" >&2; return 0; }
  tmp_add="$tmp"
  trap 'rm -f "$tmp_add"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP
  if {
    if [ -f "$file" ]; then  # drop older lines of the same key, keep the last KEEP_LINES - 1
      awk -v key="$1" '$2 != key' "$file" 2>/dev/null | tail -n $((KEEP_LINES - 1))
    fi
    printf '%s %s\n' "$now" "$1"
  } > "$tmp" 2>/dev/null && mv -f "$tmp" "$file" 2>/dev/null; then
    :
  else
    rm -f "$tmp"
    echo "check-green: warning: cannot update $file, check not recorded; free space or fix its permissions: ls -l $file" >&2
  fi
  return 0
}

lock_file() {  # absolute path of the lock, creating <git common dir>/gw, or fail
  local common
  common="$(git rev-parse --git-common-dir 2>/dev/null)" && common="$(cd "$common" 2>/dev/null && pwd)" && [ -n "$common" ] || return 1
  mkdir -p "$common/gw" 2>/dev/null || return 1
  printf '%s/gw/check.lock\n' "$common"
}
proc_start() {  # the start time of a process as ps prints it ("?" if ps cannot tell but the process exists); empty if gone
  local out
  out="$(LC_ALL=C ps -o lstart= -p "$1" 2>/dev/null | sed 's/^ *//; s/ *$//; s/  */ /g')"
  if [ -z "$out" ] && kill -0 "$1" 2>/dev/null; then out="?"; fi
  printf '%s\n' "$out"
}
proc_is() {  # proc_is <pid> <start>: that very process is still running (not gone, not a zombie, not a reused pid)
  local st
  st="$(LC_ALL=C ps -o stat= -p "$1" 2>/dev/null | tr -d ' ')"
  case "$st" in Z*) return 1 ;; esac
  [ -n "$2" ] && [ "$(proc_start "$1")" = "$2" ]
}

cmd_lock_acquire() {
  [ "$#" -eq 4 ] || usage "lock-acquire needs <owner-pid> <sha> <wait-seconds> <log>"
  local owner="$1" sha="$2" wait="$3" log="$4" lock mine cur pid rest start osha olog tmp moved deadline announced="" vanished=0
  case "$owner$wait" in ''|*[!0-9]*) usage "lock-acquire: pid and wait must be numbers" ;; esac
  lock="$(lock_file)" || { echo "check-green: cannot create <git common dir>/gw for the lock; make the git dir writable, e.g. chmod u+w \"\$(git rev-parse --git-common-dir)\"" >&2; return 1; }
  mine="$owner|$(proc_start "$owner")|$sha|$log"
  deadline=$((SECONDS + wait))
  while :; do
    ln -s "$mine" "$lock" 2>/dev/null && return 0
    cur="$(readlink "$lock" 2>/dev/null)"
    if [ -z "$cur" ]; then
      if [ -e "$lock" ] || [ -L "$lock" ]; then  # an old-format lock (a directory) or an empty one
        echo "check-green: removing a lock in an old format: $lock" >&2
        rm -rf "$lock"
        continue
      fi
      vanished=$((vanished + 1))  # it went away between ln and readlink: try again, but not forever if ln cannot work
      [ "$vanished" -lt 5 ] || { echo "check-green: cannot create the lock $lock; make its folder writable: chmod u+w $(dirname "$lock")" >&2; return 1; }
      continue
    fi
    [ "${cur%%|*}" != "$owner" ] || return 0  # already ours (a hook that checks several refs)
    pid="${cur%%|*}"; rest="${cur#*|}"; start="${rest%%|*}"; rest="${rest#*|}"; osha="${rest%%|*}"; olog="${rest#*|}"
    if ! proc_is "$pid" "$start"; then  # orphan: take it aside first, and only drop it if it is still the one we judged
      tmp="$lock.stale.$owner"
      if mv "$lock" "$tmp" 2>/dev/null; then
        moved="$(readlink "$tmp" 2>/dev/null)"
        if [ "$moved" = "$cur" ]; then
          echo "check: discarding a stale lock (pid $pid is not running as the same process)" >&2
          rm -f "$tmp"
        else  # somebody took it between our read and the move: give it back
          ln -s "$moved" "$lock" 2>/dev/null
          rm -f "$tmp"
        fi
      fi
      continue
    fi
    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "CHECK FAILED: not run, another check is running (pid $pid, sha ${osha:-unknown}); wait for it and read its log ${olog:--}, or raise checkLockWait in .claude/gw.json to wait for it. If pid $pid is not a check (check: ps -p $pid -o command=), remove the lock: rm $lock" >&2
      return 3
    fi
    [ -n "$announced" ] || echo "check: waiting for the check of pid $pid (sha ${osha:-unknown}) to end (up to ${wait}s)" >&2
    announced=1
    sleep 1
  done
}
cmd_lock_release() {
  [ "$#" -eq 1 ] || usage "lock-release needs <owner-pid>"
  local lock cur
  lock="$(lock_file)" || return 0
  cur="$(readlink "$lock" 2>/dev/null)"
  case "$cur" in "$1|"*) rm -f "$lock" ;; esac
  return 0
}

sub="${1:-}"
[ "$#" -eq 0 ] || shift
case "$sub" in
  key) cmd_key "$@" ;;
  worktree-tree) cmd_worktree_tree ;;
  has) cmd_has "$@" ;;
  add) cmd_add "$@" ;;
  lock-acquire) cmd_lock_acquire "$@" ;;
  lock-release) cmd_lock_release "$@" ;;
  *) usage "unknown subcommand '$sub'" ;;
esac
