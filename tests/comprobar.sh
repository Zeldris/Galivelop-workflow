#!/usr/bin/env bash
# The repo's check: what pre-push and CI run. Usage: bash tests/comprobar.sh
# Compatible with bash 3.2 (macOS default): no mapfile, no associative arrays.
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
fail=0

echo "== shell scripts"
scripts="$(git ls-files '*.sh' '.githooks/*')"
if [[ -n "$scripts" ]]; then
  while IFS= read -r f; do bash -n "$f" || fail=1; done <<<"$scripts"
  if command -v shellcheck >/dev/null 2>&1; then
    git ls-files -z '*.sh' '.githooks/*' | xargs -0 shellcheck || fail=1
  elif [[ "${CI:-}" == "true" ]]; then
    echo "shellcheck is missing in CI; install it (apt-get install shellcheck / brew install shellcheck)"; fail=1
  else
    echo "warning: shellcheck not installed locally; CI will run it"
  fi
fi

echo "== python"
if [[ -n "$(git ls-files '*.py')" ]]; then
  git ls-files -z '*.py' | xargs -0 python3 -m py_compile || fail=1
fi
python3 -m unittest discover -s tests -p 'test_*.py' || fail=1

if ((fail)); then echo "CHECK FAILED"; exit 1; fi
echo "CHECK OK"
