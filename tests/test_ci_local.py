"""scripts/ci-local.py, the local run of the project's GitHub CI (INS P3, second part): the YAML subset reader, the
${{ }} evaluator and the matrix as units; then whole runs against temporary repos (test_ganchos.Project) with a
workflow of plain `run:` steps, which say what ran, what not, what is not covered, the exit code and the record.
"""
import importlib.util
import json
import platform
import shutil
import tempfile
import unittest
from pathlib import Path

from test_ganchos import ROOT, Project

spec = importlib.util.spec_from_file_location("ci_local", ROOT / "scripts" / "ci-local.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

HOST = {"Linux": "ubuntu-latest", "Darwin": "macos-latest"}.get(platform.system(), "ubuntu-latest")
OTHER = "macos-latest" if HOST.startswith("ubuntu") else "ubuntu-latest"


class Yaml(unittest.TestCase):
    def test_workflow_shapes(self):
        doc = ci.load_yaml("""
name: CI   # a comment
on:
  push:
    branches-ignore: [main, 'release/**']
  pull_request:
env:
  A: "x # not a comment"
  B: 'it''s'
jobs:
  check:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        include:
          - os: ubuntu-latest
            extra: yes
    steps:
      - uses: actions/checkout@v4
      - name: Two lines
        run: |
          echo one
            echo indented
          echo two
      - run: >-
          folded
          text
      - run: echo plain
        if: github.event_name == 'pull_request'
""")
        self.assertEqual(doc["on"]["push"]["branches-ignore"], ["main", "release/**"])
        self.assertIsNone(doc["on"]["pull_request"])
        self.assertEqual(doc["env"], {"A": "x # not a comment", "B": "it's"})
        job = doc["jobs"]["check"]
        self.assertEqual(job["strategy"]["matrix"]["include"], [{"os": "ubuntu-latest", "extra": "yes"}])
        steps = job["steps"]
        self.assertEqual(steps[0], {"uses": "actions/checkout@v4"})
        self.assertEqual(steps[1]["run"], "echo one\n  echo indented\necho two\n")
        self.assertEqual(steps[2]["run"], "folded text")
        self.assertEqual(steps[3], {"run": "echo plain", "if": "github.event_name == 'pull_request'"})

    def test_flow_over_lines_and_scalars(self):
        doc = ci.load_yaml("a: [one,\n  two]\nb: {x: 1, y: [true, null]}\nc: -1\nd: '3'\n")
        self.assertEqual(doc, {"a": ["one", "two"], "b": {"x": 1, "y": [True, None]}, "c": -1, "d": "3"})

    def test_errors_are_yaml_errors_with_the_line(self):
        with self.assertRaisesRegex(ci.YamlError, "line 3: bad indentation"):
            ci.load_yaml("a:\n   b: 1\n  c: 2\n")
        with self.assertRaisesRegex(ci.YamlError, "a collection as a key"):
            ci.load_yaml("on: [{{protectedBranch}}]\n")
        with self.assertRaisesRegex(ci.YamlError, "unclosed"):
            ci.load_yaml("a: [one, two\n")


class Expressions(unittest.TestCase):
    def ev(self, text, matrix=None, env=None, status=None):
        run = ci.Run.__new__(ci.Run)
        run.root, run.os, run.tmp = ROOT, "Linux", "/tmp"
        run.github = {"event_name": "pull_request", "base_ref": "main"}
        return run.evaluator(matrix or {}, env or {}, status or {"success": True, "failure": False})(text)

    def test_operators_and_contexts(self):
        self.assertIs(self.ev("github.event_name == 'PULL_REQUEST'"), True)  # strings compare without case
        self.assertIs(self.ev("runner.os != 'Linux' || matrix.os == 'ubuntu'", {"os": "ubuntu"}), True)
        self.assertEqual(self.ev("matrix.missing && 'a' || 'b'"), "b")
        self.assertIs(self.ev("!(1 < 2)"), False)
        self.assertIs(self.ev("env.A == ''"), True)  # a missing env var is null, equal to ''
        self.assertEqual(self.ev("format('{0}-{1}', 'a', 2)"), "a-2")
        self.assertIs(self.ev("startsWith('Abc', 'a')"), True)
        self.assertIs(self.ev("contains(github['base_ref'], 'AI')"), True)
        self.assertEqual(self.ev("hashFiles('no/such/*.lock')"), "")
        self.assertRegex(self.ev("hashFiles('scripts/ci-local.py')"), r"^[0-9a-f]{64}$")

    def test_what_is_not_local_is_unknown(self):
        for text in ("secrets.TOKEN", "steps.x.outputs.y", "needs.a.result", "fromJSON('[]')", "github.nope"):
            with self.subTest(text), self.assertRaises(ci.Unknown):
                self.ev(text)

    def test_condition_adds_success_unless_a_status_function(self):
        failed = {"success": False, "failure": True}
        ev = lambda status: lambda t: self.ev(t, status=status)  # noqa: E731
        self.assertFalse(ci.condition("true", ev(failed), failed))
        self.assertTrue(ci.condition("${{ always() }}", ev(failed), failed))
        self.assertTrue(ci.condition("failure()", ev(failed), failed))
        self.assertFalse(ci.condition(None, ev(failed), failed))


class Matrix(unittest.TestCase):
    def test_include_and_exclude_like_github(self):
        combos = ci.matrix_combos({"matrix": {
            "os": ["a", "b"], "py": [1, 2],
            "exclude": [{"os": "b", "py": 2}],
            "include": [{"os": "a", "extra": "x"}, {"os": "c", "py": 3}, {"py": 1, "os": "a", "fast": True}]}}, None)
        self.assertEqual(combos, [{"os": "a", "py": 1, "extra": "x", "fast": True}, {"os": "a", "py": 2, "extra": "x"},
                                  {"os": "b", "py": 1}, {"os": "c", "py": 3}])

    def test_matrix_from_an_expression_is_not_covered(self):
        with self.assertRaisesRegex(ci.Unknown, "expression"):
            ci.matrix_combos({"matrix": "${{ fromJSON(needs.a.outputs.m) }}"}, None)

    def test_runs_on(self):
        self.assertTrue(ci.runs_here("ubuntu-22.04", "Linux"))
        self.assertTrue(ci.runs_here(["self-hosted", "linux"], "Linux"))
        self.assertFalse(ci.runs_here("macos-14", "Linux"))
        self.assertFalse(ci.runs_here(["self-hosted", "windows"], "Linux"))
        self.assertTrue(ci.runs_here("macos-latest", "macOS"))


class Runs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.p = Project(self.tmp)
        shutil.copy2(ROOT / "scripts" / "ci-local.py", self.p.work / ".claude" / "gw" / "scripts" / "ci-local.py")
        self.p.git("checkout", "-q", "-b", "feature")

    def workflow(self, body, name="ci.yml", commit=True):
        self.p.write(f".github/workflows/{name}", body)
        if commit:
            self.p.commit("workflow")

    def ci(self, *args):
        return self.p.run("python3", ".claude/gw/scripts/ci-local.py", *args)

    def log(self):
        return (self.p.work / "docs" / "registros" / "ci-local.md").read_text()

    def test_green_run_records_what_it_did_not_cover(self):
        self.workflow(f"""on: [pull_request]
env:
  GREETING: hi
jobs:
  build:
    runs-on: ${{{{ matrix.os }}}}
    strategy:
      matrix:
        os: [{HOST}, {OTHER}]
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get install -y foo
      - name: Env and context
        working-directory: docs
        env:
          WHO: ${{{{ matrix.os }}}}
        run: |
          test "$GREETING-$WHO" = "hi-{HOST}"
          test "$CI" = true && test "$GITHUB_BASE_REF" = main && test "$GITHUB_EVENT_NAME" = pull_request
          test -f notes.md
          echo "SET_LATER=yes" >> "$GITHUB_ENV"
      - run: test "$SET_LATER" = yes
      - if: github.event_name == 'push'
        run: exit 1
      - run: echo ${{{{ secrets.TOKEN }}}}
""")
        code, out = self.ci("--apuntar")
        self.assertEqual(code, 0, out)
        self.assertIn("not run (uses: actions/checkout@v4", out)
        self.assertIn("not run (system packages", out)
        log = self.log()
        self.assertTrue(log.startswith("# CI run locally\n"), log)
        line = log.strip().splitlines()[-1]
        self.assertRegex(line, r"^- \d{4}-\d\d-\d\d · `" + self.p.sha()[:12] + r"` · green \(2 steps run, "
                               r"event pull_request\); not run: 2 setup steps; not covered: ")
        self.assertIn(f"ci.yml / build ({OTHER}) (runs on {OTHER})", line)
        self.assertIn("› echo ${{ secrets.TOKEN }} (the context secrets is not available locally)", line)

    def test_a_failing_step_stops_the_job_but_always_runs(self):
        self.workflow(f"""on: pull_request
jobs:
  first:
    runs-on: {HOST}
    steps:
      - run: exit 3
        name: Breaks
      - run: touch ran-after-failure
      - if: always()
        run: touch ran-always
  second:
    needs: first
    runs-on: {HOST}
    steps:
      - run: touch ran-second
""")
        code, out = self.ci("--apuntar")
        self.assertEqual(code, 1, out)
        self.assertTrue((self.p.work / "ran-always").exists())
        self.assertFalse((self.p.work / "ran-after-failure").exists())
        self.assertFalse((self.p.work / "ran-second").exists(), "a job whose need failed is skipped")
        self.assertIn("· red: ci.yml / first › Breaks (exit 3)", self.log())

    def test_continue_on_error_and_pipefail(self):
        self.workflow(f"""on: pull_request
jobs:
  j:
    runs-on: {HOST}
    steps:
      - run: exit 1
        continue-on-error: true
      - shell: bash
        run: false | true
""")
        code, out = self.ci()
        self.assertEqual(code, 1, out)
        self.assertIn("j › false | true (exit 1)", out)
        self.assertIn("continue-on-error", out)

    def test_uncommitted_changes_are_marked(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: 'true'\n")
        self.p.write("src/new.py", "x = 1\n")
        code, out = self.ci("--apuntar")
        self.assertEqual(code, 0, out)
        self.assertIn(f"`{self.p.sha()[:12]}` (uncommitted changes) · green", self.log())
        self.assertIn("the PR hook will not take this line", out)

    def test_the_log_itself_does_not_make_the_tree_dirty(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: 'true'\n")
        self.ci("--apuntar")
        code, out = self.ci("--apuntar")
        self.assertEqual(code, 0, out)
        self.assertNotIn("uncommitted", self.log())
        self.assertEqual(self.log().count("· green"), 2)

    def test_nothing_ran_is_not_green(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {OTHER}\n    steps:\n      - run: 'true'\n")
        code, out = self.ci("--apuntar")
        self.assertEqual(code, 1, out)
        self.assertIn("· not green: no step ran; not covered: ci.yml / j (runs on", self.log())

    def test_triggers_and_the_listed_workflows(self):
        self.workflow(f"on:\n  push:\n    branches: [main]\njobs:\n  j:\n    runs-on: {HOST}\n"
                      "    steps:\n      - run: 'true'\n")
        code, out = self.ci()
        self.assertEqual(code, 2, out)
        self.assertIn("no workflow in .github/workflows runs on pull_request", out)
        self.assertIn("ciLocalWorkflows", out)
        code, out = self.ci("--event", "push")  # pushing feature, not main
        self.assertEqual(code, 2, out)
        config = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        config["ciLocalWorkflows"] = [".github/workflows/ci.yml"]
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(config))
        code, out = self.ci()
        self.assertEqual(code, 0, out)
        config["ciLocalWorkflows"] = [".github/workflows/gone.yml"]
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(config))
        code, out = self.ci()
        self.assertEqual(code, 2, out)
        self.assertIn(".github/workflows/gone.yml (ciLocalWorkflows) does not exist", out)

    def test_paths_filter(self):
        self.workflow(f"on:\n  pull_request:\n    paths: ['src/**']\njobs:\n  j:\n    runs-on: {HOST}\n"
                      "    steps:\n      - run: 'true'\n")
        self.p.git("fetch", "-q", "origin")
        code, out = self.ci()
        self.assertEqual(code, 2, out)
        self.p.write("src/a.py", "a = 1\n")
        self.p.commit("code")
        code, out = self.ci()
        self.assertEqual(code, 0, out)

    def test_a_workflow_it_cannot_read_is_not_covered(self):
        self.workflow("on: pull_request\njobs:\n  j:\n    a: 1\n   b: 2\n")
        code, out = self.ci()
        self.assertEqual(code, 1, out)
        self.assertIn("not covered: .github/workflows/ci.yml (cannot read it: line 5", out)
        self.workflow("on: pull_request\njobs:\n  j:\n    a: 1\n  b: 2\n")
        code, out = self.ci()
        self.assertEqual(code, 1, out)
        self.assertIn("not covered: .github/workflows/ci.yml (not a workflow: job b is not a mapping)", out)

    def test_plan_runs_nothing(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: touch made\n")
        code, out = self.ci("--plan")
        self.assertEqual(code, 0, out)
        self.assertIn("would run in .", out)
        self.assertFalse((self.p.work / "made").exists())
        code, out = self.ci("--plan", "--apuntar")
        self.assertEqual(code, 2, out)
        self.assertIn("--plan runs nothing", out)


if __name__ == "__main__":
    unittest.main()
