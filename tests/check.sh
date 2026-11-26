#!/usr/bin/env bash
# The repo's check: what pre-push and CI run. Usage: bash tests/check.sh
# Compatible with bash 3.2 (macOS default): no mapfile, no associative arrays.
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
fail=0
# Each section that fails is named once, at the end, as `FAILED: <section>`: scripts/check.sh reads those lines
# for its last line `CHECK FAILED: … (failed: <sections>)`.
current=""
failed=""
section() { current="$1"; echo "== $1"; }
bad() {
  fail=1
  case "
$failed
" in *"
$current
"*) ;; *) failed="${failed:+$failed
}$current" ;; esac
}

# The applied copy (.claude/, .githooks/) is checked byte for byte against its source by the sync step below, so
# the linters and compilers only look at the sources.
copies=(':!.claude/' ':!.githooks/')

# B59: test_harvest.py runs harvest.py on this repo, which needs the full history; a shallow clone would fail it only
# after the whole check (~50 min), so stop here, in seconds. CI clones with fetch-depth: 0.
if [[ "$(git rev-parse --is-shallow-repository 2>/dev/null)" == "true" ]]; then
  echo "check: $root is a shallow clone and tests/test_harvest.py needs the full history; run: git fetch --unshallow origin" >&2
  echo "FAILED: shallow clone"
  echo "CHECK FAILED"
  exit 1
fi

section "workflow copy in sync (.claude/gw, .claude/skills, .githooks, .claude/settings.json)"
python3 scripts/apply.py --check . || bad

section "workflow YAML valid (ciYamlCheck, E51)"
python3 scripts/ci-local.py --validate || bad

section "shell scripts"
scripts="$(git ls-files -- '*.sh' 'templates/githooks/*' "${copies[@]}")"
if [[ -n "$scripts" ]]; then
  files=()
  while IFS= read -r f; do bash -n "$f" || bad; files+=("$f"); done <<<"$scripts"
  bash tests/shellcheck.sh "${files[@]}" || bad
fi

section "markdown links and stale references"
python3 scripts/md-links.py || bad

section "names in English (A8)"
python3 scripts/names-check.py || bad

section "private data: keys and e-mails (E2)"
python3 scripts/private-check.py --all --no-names || bad

section "agent map paths"
python3 scripts/agent-map.py || bad

section "presentation sheets (A10)"
python3 scripts/mkt-sheet.py check || bad

section "roadmap parity (same ids in every language, D105)"
python3 scripts/roadmap.py check || bad

section "hand-off log (state-table cells, Done section, Updated date, task-id clash with origin/main, D61)"
python3 scripts/handoff.py preflight --strict || bad  # one pass: preflight runs the check (--strict) and the clash

# E22 runs alongside the main suite (E45): its output is printed in its own section once both end.
e22_out="$(mktemp "${TMPDIR:-/tmp}/gw-check-e22.XXXXXX")" || exit 1
trap 'kill "${e22_pid:-}" 2>/dev/null; rm -f "$e22_out"' EXIT
# `&` in a script makes the job ignore SIGINT and SIGQUIT, and a hook started by the tests could not trap them (its
# interrupt tests would fail): the subshell restores them before exec.
( trap - INT QUIT; exec bash tests/old-python.sh ) >"$e22_out" 2>&1 &
e22_pid=$!

section "python"
if [[ -n "$(git ls-files -- '*.py' "${copies[@]}")" ]]; then
  git ls-files -z -- '*.py' "${copies[@]}" | xargs -0 python3 -m py_compile || bad
fi
python3 scripts/tests-after-main.py || bad  # a TestCase after unittest.main() never runs
# tests/ and every skills/<name>/scripts with tests, each folder on its own, one class per process (E45, testJobs).
python3 scripts/test-run.py --times 5 || bad

section "python (oldest available, E22)"
wait "$e22_pid" || bad
cat "$e22_out"

if ((fail)); then
  while IFS= read -r f; do echo "FAILED: $f"; done <<<"$failed"
  echo "CHECK FAILED"
  exit 1
fi
echo "CHECK OK"
