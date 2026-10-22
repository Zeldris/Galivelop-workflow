#!/usr/bin/env bash
# The repo's check: what pre-push and CI run. Usage: bash tests/comprobar.sh
# Compatible with bash 3.2 (macOS default): no mapfile, no associative arrays.
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
fail=0

# The applied copy (.claude/, .githooks/) is checked byte for byte against its source by the sync step below, so
# the linters and compilers only look at the sources.
copies=(':!.claude/' ':!.githooks/')

echo "== workflow copy in sync (.claude/gw, .claude/skills, .githooks, .claude/settings.json)"
python3 scripts/aplicar.py --check . || fail=1

echo "== shell scripts"
scripts="$(git ls-files -- '*.sh' 'templates/githooks/*' "${copies[@]}")"
if [[ -n "$scripts" ]]; then
  while IFS= read -r f; do bash -n "$f" || fail=1; done <<<"$scripts"
  if command -v shellcheck >/dev/null 2>&1; then
    git ls-files -z -- '*.sh' 'templates/githooks/*' "${copies[@]}" | xargs -0 shellcheck || fail=1
  elif [[ "${CI:-}" == "true" ]]; then
    echo "shellcheck is missing in CI; install it (apt-get install shellcheck / brew install shellcheck)"; fail=1
  else
    echo "warning: shellcheck not installed locally; CI will run it"
  fi
fi

echo "== markdown links and stale references"
python3 scripts/enlaces-md.py || fail=1

echo "== python"
if [[ -n "$(git ls-files -- '*.py' "${copies[@]}")" ]]; then
  git ls-files -z -- '*.py' "${copies[@]}" | xargs -0 python3 -m py_compile || fail=1
fi
python3 -m unittest discover -s tests -p 'test_*.py' || fail=1
# Tests bundled with skills (skills/<name>/scripts/test_*.py), each folder on its own.
for d in skills/*/scripts; do
  if [[ -n "$(git ls-files "$d/test_*.py")" ]]; then
    python3 -m unittest discover -s "$d" -p 'test_*.py' || fail=1
  fi
done

if ((fail)); then echo "CHECK FAILED"; exit 1; fi
echo "CHECK OK"
