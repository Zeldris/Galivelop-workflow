#!/usr/bin/env bash
# galivelop-workflow v0.1.0
# The tests of what changes, in the push. Called by .githooks/pre-push as:   tests-relacionados.sh <changed-files-file>
# (one repo-relative path per line; git's ref lines on stdin are ignored). Reads relatedTests of .claude/gw.json:
#   fast  commands that run on every push; one whose text has {files} runs only if some changed file still exists
#   slow  commands that run only when some changed file still exists (e.g. foo.ts -> foo.integration.test.ts)
# {files} is replaced by the existing changed files, each shell-quoted. Fast ones go first; the first failure stops
# the run (exit 1). A no-op when relatedTests is absent or empty. Fails closed on an invalid config.
# Bash 3.2 compatible. Root from this script's path, never from $CLAUDE_PROJECT_DIR or the current directory.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ "$#" -lt 1 ]; then echo "tests-relacionados: usage: tests-relacionados.sh <changed-files-file>" >&2; exit 2; fi
list="$1"
root="$(git -C "$here" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "tests-relacionados: $here is not inside a git repository; reinstall the workflow: /gw-update" >&2; exit 2; }
cd "$root" || exit 2
config="$here/config.py"
python3 "$config" --root "$root" validate > /dev/null || {
  echo "tests-relacionados: the config is invalid; fix it: python3 $config --root $root validate" >&2; exit 1; }
fast="$(python3 "$config" --root "$root" get relatedTests.fast 2>/dev/null || true)"
slow="$(python3 "$config" --root "$root" get relatedTests.slow 2>/dev/null || true)"
[ -n "$fast$slow" ] || exit 0

quoted=""
count=0
if [ -f "$list" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] && [ -f "$f" ] || continue
    quoted="$quoted $(printf '%q' "$f")"
    count=$((count + 1))
  done < "$list"
fi
quoted="${quoted# }"

expand() {  # expand <command>: replaces every {files}
  local rest="$1" out=""
  while [[ "$rest" == *"{files}"* ]]; do
    out="$out${rest%%"{files}"*}$quoted"
    rest="${rest#*"{files}"}"
  done
  printf '%s' "$out$rest"
}
run() {  # run <kind> <commands>
  local kind="$1" cmd full
  while IFS= read -r cmd; do
    [ -n "$cmd" ] || continue
    if [ "$count" -eq 0 ]; then
      case "$kind" in slow) continue ;; fast) case "$cmd" in *"{files}"*) continue ;; esac ;; esac
    fi
    full="$(expand "$cmd")"
    echo "pre-push: related tests ($kind): $full"
    bash -c "$full" < /dev/null || {
      echo "tests-relacionados: failed ($kind): $full; fix it and run it again: $full" >&2; exit 1; }
  done <<<"$2"
}
run fast "$fast"
run slow "$slow"
exit 0
