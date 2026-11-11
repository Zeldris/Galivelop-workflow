#!/usr/bin/env bash
# Runs shellcheck over the shell scripts it is given (comprobar.sh passes the repo's, without the applied copy).
# Without shellcheck: a warning on a person's machine, a failure in CI and in a cloud session, where nothing else
# would run it. With `shellcheckVersion` in .claude/gw.json (E27), a different local version is a warning with the
# command that installs the pinned one (a failure in CI, which installs it). Usage: bash tests/shellcheck.sh FILE...
# Compatible with bash 3.2.
set -uo pipefail
if (($# == 0)); then exit 0; fi
if command -v shellcheck >/dev/null 2>&1; then
  root="$(cd "$(dirname "$0")/.." && pwd)" || { echo "shellcheck.sh: cannot find the repo root"; exit 1; }
  config="$root/scripts/config.py"
  if ! python3 "$config" --root "$root" validate >/dev/null; then
    echo "shellcheck.sh: .claude/gw.json does not load; fix it: python3 scripts/config.py validate"; exit 1
  fi
  want="$(python3 "$config" --root "$root" get shellcheckVersion 2>/dev/null)" || want=""   # absent: not pinned
  if [[ -n "$want" ]]; then
    have="$(shellcheck --version | sed -n 's/^version: *//p')"
    if [[ "$have" != "$want" ]]; then
      fix="pip install \"shellcheck-py==$want.*\""
      if [[ "${CI:-}" == "true" ]]; then
        echo "shellcheck ${have:-?} in CI, but shellcheckVersion is $want; the workflow must install it: $fix"; exit 1
      fi
      echo "warning: shellcheck ${have:-?} here, but CI runs $want (shellcheckVersion); its warnings may differ: $fix"
    fi
  fi
  shellcheck "$@"
elif [[ "${CI:-}" == "true" ]]; then
  echo "shellcheck is missing in CI; install it (apt-get install shellcheck / brew install shellcheck)"; exit 1
elif [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]]; then
  echo "shellcheck is missing in this cloud session, and the check needs it; install it: pip install shellcheck-py"
  exit 1
else
  echo "warning: shellcheck not installed locally; CI will run it (or: pip install shellcheck-py)"
fi
