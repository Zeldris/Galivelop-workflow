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

section "workflow copy in sync (.claude/gw, .claude/skills, .githooks, .claude/settings.json)"
python3 scripts/apply.py --check . || bad

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

section "hand-off log (state-table cells, Done section)"
python3 scripts/handoff.py check --strict || bad

section "python"
if [[ -n "$(git ls-files -- '*.py' "${copies[@]}")" ]]; then
  git ls-files -z -- '*.py' "${copies[@]}" | xargs -0 python3 -m py_compile || bad
fi
python3 scripts/tests-after-main.py || bad  # a TestCase after unittest.main() never runs
python3 -m unittest discover -s tests -p 'test_*.py' || bad
# Tests bundled with skills (skills/<name>/scripts/test_*.py), each folder on its own.
for d in skills/*/scripts; do
  if [[ -n "$(git ls-files "$d/test_*.py")" ]]; then
    python3 -m unittest discover -s "$d" -p 'test_*.py' || bad
  fi
done

if ((fail)); then
  while IFS= read -r f; do echo "FAILED: $f"; done <<<"$failed"
  echo "CHECK FAILED"
  exit 1
fi
echo "CHECK OK"
