#!/usr/bin/env bash
# Runs shellcheck over the shell scripts it is given (comprobar.sh passes the repo's, without the applied copy).
# Without shellcheck: a warning on a person's machine, a failure in CI and in a cloud session, where nothing else
# would run it. Usage: bash tests/shellcheck.sh FILE... Compatible with bash 3.2.
set -uo pipefail
if (($# == 0)); then exit 0; fi
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$@"
elif [[ "${CI:-}" == "true" ]]; then
  echo "shellcheck is missing in CI; install it (apt-get install shellcheck / brew install shellcheck)"; exit 1
elif [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]]; then
  echo "shellcheck is missing in this cloud session, and the check needs it; install it: pip install shellcheck-py"
  exit 1
else
  echo "warning: shellcheck not installed locally; CI will run it (or: pip install shellcheck-py)"
fi
