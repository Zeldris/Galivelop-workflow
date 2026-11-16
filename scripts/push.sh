#!/usr/bin/env bash
# galivelop-workflow v0.7.1
# Pushes a branch with retries and says "pushed" only when the remote really has the commit (D94).
#   bash push.sh [<branch>]     (default: the current branch)
#  - Runs `git push -u origin <branch>`; its output is shown and also classified when it fails.
#  - A transient failure (network, timeouts, RPC, early EOF, HTTP 5xx) is retried after each delay of `pushRetryDelays`
#    (seconds; default 2, 4, 8, 16). Anything else (a hook rejection, non-fast-forward, 403, authentication) fails at
#    once, with the reason and the command that fixes it.
#  - Success = `git ls-remote origin refs/heads/<branch>` equals the local commit of the branch (HEAD when it is the
#    current one). Exit 0 only then, also when the push exited non-zero but the remote already has it; a push that
#    said OK with a different remote is a failure.
#  - Exit 0 pushed; 1 push failed; 2 usage or a missing datum (no branch, detached HEAD without argument, no origin,
#    unreadable config), all before pushing.
# Bash 3.2 compatible. Root from this script's path, never from $CLAUDE_PROJECT_DIR or the current directory.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
die() { echo "push: $1" >&2; exit "${2:-2}"; }
[ $# -le 1 ] || die "usage: bash $0 [<branch>]"
# Git exports GIT_DIR (and friends) to hooks; with it set `rev-parse --show-toplevel` answers $here, not the root.
root="$(unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE; git -C "$here" rev-parse --show-toplevel 2>/dev/null)" || {
  die "$here is not inside a git repository; reinstall the workflow: /gw-update"; }
cd "$root" || exit 2
config="$here/config.py"

branch="${1:-}"
if [ -z "$branch" ]; then
  branch="$(git symbolic-ref --short -q HEAD)" || branch=""
  [ -n "$branch" ] || die "detached HEAD and no branch given; check out the branch or pass it: bash $0 <branch>"
fi
want="$(git rev-parse --verify -q "refs/heads/$branch^{commit}")" || want=""
[ -n "$want" ] || die "there is no local branch '$branch'; create it or pass an existing one: bash $0 <branch>"
git remote get-url origin >/dev/null 2>&1 || die "the repository has no remote 'origin'; add it: git remote add origin <url>"
delays="$(python3 "$config" --root "$root" get pushRetryDelays 2>/dev/null)" || {
  die "cannot read pushRetryDelays; fix the config: python3 $config --root $root validate"; }
out="$(mktemp "${TMPDIR:-/tmp}/gw-push.XXXXXX")" || die "cannot create a temp file; free space and retry"
trap 'rm -f "$out"' EXIT

remote_sha() {  # the sha of the branch on origin; empty when absent; non-zero when ls-remote fails
  local line
  line="$(git ls-remote origin "refs/heads/$branch")" || return 1
  printf '%s\n' "$line" | awk 'NR==1 {print $1}'
}
remote_has() { local got; got="$(remote_sha 2>/dev/null)" && [ "$got" = "$want" ]; }

# Not transient even if the text also looks like it (a hook's own output, an HTTP 403 page).
permanent='non-fast-forward|fetch first|\[rejected\]|\[remote rejected\]|pre-push|hook declined|error: 40[0-9]|HTTP/?[0-9.]* 40[0-9]|Authentication failed|Permission denied|could not read Username|protected branch'
transient='Could not resolve host|Connection (reset|refused|timed out)|Operation timed out|RPC failed|early EOF|unexpected disconnect|remote end hung up|error: 5[0-9][0-9]|HTTP/?[0-9.]* 5[0-9][0-9]|HTTP code 5[0-9][0-9]'

attempt=0
rest="$delays"
while :; do
  attempt=$((attempt + 1))
  git push -u origin "$branch" 2>&1 | tee "$out"
  code="${PIPESTATUS[0]}"
  if remote_has; then
    echo "push: ok: origin/$branch is at $want"
    exit 0
  fi
  if [ "$code" -eq 0 ]; then
    die "git push said OK but origin/$branch is not at $want (remote: $(remote_sha 2>/dev/null || echo unreadable)); check the remote and retry: git ls-remote origin refs/heads/$branch && bash $0 $branch" 1
  fi
  if grep -Eiq "$permanent" "$out" || ! grep -Eiq "$transient" "$out"; then
    echo "push: failed and not retrying: the error is not a transient network one (read the git output above)." >&2
    if grep -Eiq 'non-fast-forward|fetch first|\[rejected\]' "$out"; then
      echo "push: the remote has commits you lack; bring them in and push again: git fetch origin $branch && git merge --no-edit origin/$branch && bash $0 $branch" >&2
    elif grep -Eiq 'error: 40[0-9]|HTTP/?[0-9.]* 40[0-9]|Authentication failed|Permission denied|could not read Username' "$out"; then
      echo "push: access was refused; check the credentials or permissions for origin: git remote -v" >&2
    else
      echo "push: a hook or the remote rejected it; read its output above, fix that and run again: bash $0 $branch" >&2
    fi
    exit 1
  fi
  delay="$(printf '%s\n' "$rest" | sed -n 1p)"
  if [ -z "$delay" ]; then
    die "transient failure and the $attempt attempt(s) are used up (pushRetryDelays); check the network and run again: bash $0 $branch" 1
  fi
  rest="$(printf '%s\n' "$rest" | sed 1d)"
  echo "push: transient failure (attempt $attempt); retrying in ${delay}s" >&2
  sleep "$delay"
done
