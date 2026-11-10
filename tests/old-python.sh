#!/usr/bin/env bash
# E22 (retro 0.5.0 R6): what fails only on an older Python. Finds the oldest Python on PATH that is older than
# `python3` and not older than the supported floor (3.8, README "Requirements"), compiles every Python source of the
# repo with it and runs the tests of the change with it (scripts/tests-for.py: the full suite takes too long to run
# twice; the hook suites only when they changed). No older Python: a warning, not a failure (CI covers its own
# version).
#   bash tests/old-python.sh [FILE...]
# The change is FILE... when given; otherwise every file that differs from the upstream of the branch (what a push
# sends) or, without one, from the merge base with origin/<protectedBranch>; no base at all: only the compile step.
# GW_OLD_PYTHONS: the commands to try (default python3.8 … python3.<current minor - 1>); GW_OLD_PYTHONS=off skips.
# Compatible with bash 3.2. Root from this script's path.
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
floor=8
slow="tests/test_hooks.py tests/test_reviewed.py"
version() { "$1" -c 'import sys; print("%d %d" % sys.version_info[:2])' 2>/dev/null; }
read -r major current <<<"$(version python3)" || { echo "old-python: python3 does not run; install Python 3.8+" >&2; exit 1; }
[ "$major" = 3 ] || { echo "old-python: python3 is not Python 3; install Python 3.8+" >&2; exit 1; }
candidates="${GW_OLD_PYTHONS-}"
if [ "$candidates" = off ]; then echo "old-python: skipped (GW_OLD_PYTHONS=off)"; exit 0; fi
if [ -z "$candidates" ]; then
  n=$floor
  while [ "$n" -lt "$current" ]; do candidates="$candidates python3.$n"; n=$((n + 1)); done
fi
old=""
old_minor=""
for c in $candidates; do
  command -v "$c" >/dev/null 2>&1 || continue
  read -r m n <<<"$(version "$c")" || continue
  [ "$m" = 3 ] && [ "$n" -ge "$floor" ] && [ "$n" -lt "$current" ] || continue
  if [ -z "$old_minor" ] || [ "$n" -lt "$old_minor" ]; then old="$c"; old_minor="$n"; fi
done
if [ -z "$old" ]; then
  echo "warning: no Python older than 3.$current (and 3.$floor or later) on PATH, so the tests ran on 3.$current only;" \
    "install one to test what breaks on an older Python (e.g. apt-get install python3.$floor, pyenv install 3.$floor)"
  exit 0
fi
echo "old-python: $old (3.$old_minor)"
fail=0
# compile(), not py_compile: no __pycache__ left behind for the older version.
git ls-files -z -- '*.py' ':!.claude/' ':!.githooks/' | xargs -0 "$old" -B -c '
import sys
bad = 0
for f in sys.argv[1:]:
    try:
        with open(f, "rb") as fh:
            compile(fh.read(), f, "exec")
    except SyntaxError as e:
        print("%s:%s: %s" % (f, e.lineno, e.msg)); bad = 1
sys.exit(bad)' || fail=1
changed=""
if [ "$#" -gt 0 ]; then
  changed="$(printf '%s\n' "$@")"
else
  base=""
  if upstream="$(git rev-parse -q --verify '@{upstream}' 2>/dev/null)"; then
    base="$upstream"
  else
    protected="$(python3 -B scripts/config.py --root "$root" get protectedBranch 2>/dev/null)" || protected=""
    if [ -n "$protected" ]; then base="$(git merge-base HEAD "origin/$protected" 2>/dev/null)" || base=""; fi
  fi
  if [ -z "$base" ]; then
    echo "old-python: no upstream and no origin/<protectedBranch> to diff against, so only the compile step ran"
    exit "$fail"
  fi
  changed="$( (git diff --name-only "$base" --; git ls-files --others --exclude-standard) | sort -u)"
fi
tests=""
if [ -n "$changed" ]; then
  list=()
  while IFS= read -r f; do list+=("$f"); done <<<"$changed"
  tests="$(python3 -B scripts/tests-for.py "${list[@]}")" || exit 1
fi
# The hook suites start the hooks through `python3`, so on the older Python they would mostly re-run the current
# one, for minutes: they run only when they changed themselves.
kept=""
while IFS= read -r t; do
  [ -n "$t" ] || continue
  case " $slow " in
    *" $t "*) printf '%s\n' "$changed" | grep -qxF "$t" || continue ;;
  esac
  kept="${kept:+$kept
}$t"
done <<<"$tests"
tests="$kept"
if [ -z "$tests" ]; then
  echo "old-python: the change calls for no tests"
  exit "$fail"
fi
files=()
while IFS= read -r f; do files+=("$f"); done <<<"$tests"
echo "old-python: ${#files[@]} test file(s) of the change"
PYTHONPATH=tests "$old" -B -m unittest "${files[@]}" || fail=1
exit "$fail"
