"""scripts/ci-local.py, the local run of the project's GitHub CI (INS P3, second part): the YAML subset reader, the
${{ }} evaluator and the matrix as units; then whole runs against temporary repos (test_hooks.Project) with a
workflow of plain `run:` steps, which say what ran, what not, what is not covered, the exit code and the record.
"""
import importlib.util
import json
import os
import platform
import shutil
import tempfile
import unittest
from pathlib import Path

from test_hooks import ROOT, Project

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
        # E71: neither GitHub's own variable nor an actionlint installed here (the CI installs one) changes these tests
        self.p.env.pop("GITHUB_ACTIONS", None)
        self.p.env["PATH"] = os.pathsep.join(d for d in self.p.env.get("PATH", os.defpath).split(os.pathsep)
                                             if not os.path.isfile(os.path.join(d, "actionlint")))

    def workflow(self, body, name="ci.yml", commit=True):
        self.p.write(f".github/workflows/{name}", body)
        if commit:
            self.p.commit("workflow")

    def ci(self, *args):
        return self.p.run("python3", ".claude/gw/scripts/ci-local.py", *args)

    def log(self):
        return (self.p.work / "docs" / "records" / "ci-local.md").read_text()

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
        code, out = self.ci("--record")
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

    def template(self):
        text = (ROOT / "templates" / "github" / "check.yml").read_text().replace("{{ciPushIgnore}}", "main").replace("{{ciLedgerPath}}", '"l.jsonl"')
        self.workflow(text.replace("runs-on: ubuntu-latest", f"runs-on: {HOST}"), name="check.yml")  # also on macOS

    def test_the_ci_template_with_a_matrix_from_an_expression_runs_its_check_job_once(self):
        self.template()
        code, out = self.ci()
        self.assertIn("matrix from expression: run once locally", out)
        self.assertIn("== job check.yml / check", out)
        self.assertIn("== job check.yml / versions", out)
        self.assertIn("Check", out)
        self.assertEqual(code, 0, out)

    def test_the_ci_template_check_job_failing_is_red_not_skipped(self):
        self.template()
        self.p.write("check.sh", "exit 7\n")
        self.p.commit("failing check")
        code, out = self.ci()
        self.assertEqual(code, 1, out)
        self.assertIn("red:", out)

    def gw_ci_workflow(self, step):
        self.workflow(f"on: [pull_request]\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: {step}\n")

    def test_a_dir_a_green_run_writes_is_removed(self):  # D160
        self.gw_ci_workflow("mkdir -p .gw-ci && echo x > .gw-ci/pre-commit")
        code, out = self.ci("--record")
        self.assertEqual(code, 0, out)
        self.assertFalse((self.p.work / ".gw-ci").exists(), out)

    def test_a_dir_a_red_run_writes_is_removed(self):  # D160
        self.gw_ci_workflow("mkdir -p .gw-ci && exit 1")
        code, out = self.ci("--record")
        self.assertEqual(code, 1, out)
        self.assertIn("red:", out)
        self.assertFalse((self.p.work / ".gw-ci").exists(), out)

    def test_a_dir_the_run_writes_leaves_the_next_record_without_uncommitted_changes(self):  # D160
        self.gw_ci_workflow("mkdir .gw-ci")
        code, out = self.ci("--record")
        self.assertEqual(code, 0, out)
        self.p.git("add", "-A")
        self.p.commit("log")
        code, out = self.ci("--record")
        self.assertEqual(code, 0, out)
        self.assertNotIn("uncommitted changes", self.log().strip().splitlines()[-1])

    def test_a_dir_that_was_already_there_is_left(self):  # D160
        (self.p.work / ".gw-ci").mkdir()
        (self.p.work / ".gw-ci" / "keep").write_text("1")
        self.workflow(f"on: [pull_request]\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: true\n")
        self.ci()
        self.assertTrue((self.p.work / ".gw-ci" / "keep").is_file())

    def test_a_job_it_cannot_evaluate_forbids_the_green(self):
        self.workflow("""on: [pull_request]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
  b:
    needs: a
    if: ${{ needs.a.outputs.x == 'y' }}
    runs-on: ubuntu-latest
    steps:
      - run: echo never
""".replace("ubuntu-latest", HOST))
        code, out = self.ci()
        self.assertEqual(code, 1, out)
        self.assertIn("not green: a job could not be evaluated, so it did not run: ci.yml / b", out)

    def test_other_os_jobs_stay_listed_and_do_not_forbid_the_green(self):
        self.workflow(f"""on: [pull_request]
jobs:
  a:
    runs-on: {HOST}
    steps:
      - run: echo ok
  b:
    runs-on: {OTHER}
    steps:
      - run: echo elsewhere
""")
        code, out = self.ci()
        self.assertEqual(code, 0, out)
        self.assertIn(f"runs on {OTHER}", out)

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
        code, out = self.ci("--record")
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
        code, out = self.ci("--record")
        self.assertEqual(code, 0, out)
        self.assertIn(f"`{self.p.sha()[:12]}` (uncommitted changes) · green", self.log())
        self.assertIn("the PR hook will not take this line", out)

    def test_old_apuntar_option_warns_with_the_new_name_and_records(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: 'true'\n")
        code, out = self.ci("--apuntar")
        self.assertEqual(code, 0, out)
        self.assertIn("ci-local: warning: --apuntar is deprecated and will stop working in 1.0; use --record", out)
        self.assertIn("· green", self.log())

    def test_the_log_itself_does_not_make_the_tree_dirty(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: 'true'\n")
        self.ci("--record")
        code, out = self.ci("--record")
        self.assertEqual(code, 0, out)
        self.assertNotIn("uncommitted", self.log())
        self.assertEqual(self.log().count("· green"), 2)

    SECRETS = ("GITHUB_TOKEN", "GH_TOKEN", "ANTHROPIC_API_KEY", "AWS_SECRET_ACCESS_KEY")

    def test_steps_get_a_minimal_environment_without_the_shells_tokens(self):  # E28 D4
        for name in self.SECRETS:
            self.p.env[name] = "leak"  # gw-allow-secret: a fake token
        self.p.env.update(LC_ALL="C", MY_TOOL_HOME="/opt/tool")
        checks = "\n".join(f'          test -z "${{{n}:-}}"' for n in self.SECRETS + ("MY_TOOL_HOME",))
        self.workflow(f"""on: pull_request
env:
  FROM_WORKFLOW: w
jobs:
  j:
    runs-on: {HOST}
    steps:
      - env:
          FROM_STEP: s
        run: |
{checks}
          test -n "$PATH" && test -n "$HOME" && test "$LC_ALL" = C
          test "$FROM_WORKFLOW-$FROM_STEP" = w-s && test "$CI" = true && test -n "$GITHUB_SHA"
""")
        code, out = self.ci()
        self.assertEqual(code, 0, out)
        self.assertIn("green (1 step run", out)

    def test_ci_local_pass_env_lets_the_named_variables_through_and_only_them(self):  # E28 D4
        self.p.env.update(MY_TOOL_HOME="/opt/tool", GH_TOKEN="leak")  # gw-allow-secret: a fake token
        self.set_config(ciLocalPassEnv=["MY_TOOL_HOME"])
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n"
                      '      - run: test "$MY_TOOL_HOME" = /opt/tool && test -z "${GH_TOKEN:-}"\n')
        code, out = self.ci()
        self.assertEqual(code, 0, out)
        self.set_config(ciLocalPassEnv=["NOT A NAME"])
        code, out = self.ci()
        self.assertEqual(code, 2, out)
        self.assertIn("ciLocalPassEnv", out)

    def test_a_working_directory_outside_the_repo_is_refused_with_the_reason(self):  # E28 D4
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (self.p.work / "inside").mkdir()
        os.symlink(outside, self.p.work / "away")
        os.symlink(self.p.work / "inside", self.p.work / "here")
        for wd in ("..", str(outside), "away", "docs/../.."):
            with self.subTest(wd=wd):
                self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n"
                              f"      - working-directory: '{wd}'\n        run: touch ran-here\n", commit=False)
                code, out = self.ci()
                self.assertEqual(code, 1, out)
                self.assertIn(f"working-directory {wd} is outside the repository, so it is not run", out)
                self.assertFalse((outside / "ran-here").exists())
                self.assertFalse((self.p.work.parent / "ran-here").exists())
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n"
                      "      - working-directory: here\n        run: touch ran-here\n", commit=False)
        code, out = self.ci()  # a link that stays inside the repo still runs
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "inside" / "ran-here").exists())

    def test_record_refuses_a_symlinked_log_or_a_log_folder_outside_the_repo(self):  # E28 B3
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        target = outside / "victim.md"
        target.write_text("keep\n")
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: 'true'\n")
        log = self.p.work / "docs" / "records" / "ci-local.md"
        log.parent.mkdir(parents=True, exist_ok=True)
        for link in (target, outside / "missing.md"):  # to a file, and dangling
            with self.subTest(link=link.name):
                if os.path.lexists(log):
                    os.remove(log)
                os.symlink(link, log)
                code, out = self.ci("--record")
                self.assertEqual(code, 2, out)
                self.assertIn("docs/records/ci-local.md is a symbolic link, so nothing was recorded", out)
                self.assertEqual(target.read_text(), "keep\n")
                self.assertFalse((outside / "missing.md").exists())
        os.remove(log)
        shutil.rmtree(self.p.work / "docs" / "records")
        os.symlink(outside, self.p.work / "docs" / "records")
        code, out = self.ci("--record")
        self.assertEqual(code, 2, out)
        self.assertIn("the folder of docs/records/ci-local.md is outside the repository", out)
        self.assertFalse((outside / "ci-local.md").exists())

    def test_nothing_ran_is_not_green(self):
        self.workflow(f"on: pull_request\njobs:\n  j:\n    runs-on: {OTHER}\n    steps:\n      - run: 'true'\n")
        code, out = self.ci("--record")
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

    def set_config(self, **keys):
        path = self.p.work / ".claude" / "gw.json"
        config = json.loads(path.read_text())
        config.update(keys)
        path.write_text(json.dumps(config))
        self.p.commit("config")

    SYSTEM = (f"on: [pull_request]\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n"
              "      - run: apt-get update >/dev/null 2>&1 || true\n      - run: echo foo-install\n")

    def test_system_package_steps_are_left_out_by_default_and_by_the_ci_system_commands_key(self):
        self.workflow(self.SYSTEM)
        code, out = self.ci()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("not run (system packages"), 1, out)
        self.set_config(ciSystemCommands=[])  # none left out: the apt-get line runs
        code, out = self.ci()
        self.assertNotIn("not run (system packages", out)
        self.set_config(ciSystemCommands=["apt-get", "brew"])  # a subset of the package managers
        code, out = self.ci()
        self.assertEqual(out.count("not run (system packages"), 1, out)

    def test_ci_system_commands_only_accept_package_managers_and_a_skipped_non_install_is_not_green(self):
        self.workflow(self.SYSTEM)
        for bad in ("bash", "echo"):
            with self.subTest(bad=bad):
                self.set_config(ciSystemCommands=[bad])
                code, out = self.ci()
                self.assertEqual(code, 2, out)
                self.assertIn("ciSystemCommands[0]: must be one of", out)
        self.workflow(f"on: [pull_request]\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n"
                      "      - run: echo ok\n      - run: sudo bash tests/check.sh\n")
        self.set_config(ciSystemCommands=["sudo"])
        code, out = self.ci()
        self.assertNotEqual(code, 0, out)
        self.assertIn("not green", out)
        self.assertIn("skipped as a system command but it installs nothing", out)

    def test_ci_system_commands_validates_in_the_config(self):
        self.workflow(self.SYSTEM)
        self.set_config(ciSystemCommands=["a b"])
        code, out = self.ci()
        self.assertEqual(code, 2, out)
        self.assertIn("ciSystemCommands", out)

    SLOW = f"on: [pull_request]\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: sleep 20\n"

    def test_step_timeout_defaults_to_none_applies_to_steps_without_their_own_and_loses_to_theirs(self):
        self.workflow(self.SLOW.replace("sleep 20", "sleep 2"))
        code, out = self.ci()
        self.assertEqual(code, 0, out)  # no default limit
        self.workflow(self.SLOW)
        self.set_config(ciStepTimeout=0.02)  # 1.2 s
        code, out = self.ci()
        self.assertEqual(code, 1, out)
        self.assertIn("timed out after 0.02 min", out)
        self.workflow(self.SLOW.replace("- run: sleep 20", "- run: sleep 2\n        timeout-minutes: 1"))
        code, out = self.ci()
        self.assertEqual(code, 0, out)  # the step's own timeout-minutes wins over the key

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
        code, out = self.ci("--plan", "--record")
        self.assertEqual(code, 2, out)
        self.assertIn("--plan runs nothing", out)


class Validate(unittest.TestCase):
    """--validate (E51): every workflow file parses; a broken one fails with file, line and reason."""
    setUp, workflow, ci, set_config = Runs.setUp, Runs.workflow, Runs.ci, Runs.set_config
    GOOD = f"on: pull_request\njobs:\n  j:\n    runs-on: {HOST}\n    steps:\n      - run: 'true'\n"

    def test_real_workflows_of_this_repo_pass(self):
        for f in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
            ci.load_yaml(f.read_text(encoding="utf-8"))

    def test_valid_files_pass_with_both_extensions(self):
        self.workflow(self.GOOD)
        self.workflow(self.GOOD, name="b.yaml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("2 workflow file(s) checked, 0 invalid", out)

    def test_no_dir_or_empty_dir_passes(self):
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("0 workflow file(s)", out)
        (self.p.work / ".github" / "workflows").mkdir(parents=True)
        (self.p.work / ".github" / "workflows" / "notes.txt").write_text("a: b: c\n")  # not a workflow file
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)

    def test_unquoted_colon_in_a_name_fails_with_file_and_line(self):
        self.workflow("name: a: b\non: push\njobs: {}\n", name="bad.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn(".github/workflows/bad.yml: line 1:", out)
        self.assertIn("ci-local.py --validate", out)
        self.assertIn("mapping values are not allowed", out)
        self.assertIn("1 invalid", out)

    def test_step_name_with_colon_and_space_fails(self):
        self.workflow(self.GOOD.replace("- run: 'true'", "- name: Run: tests\n        run: 'true'"), name="s.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("s.yml: line", out)
        self.assertIn("mapping values are not allowed", out)

    def test_anchors_tags_and_aliases_before_values_are_valid(self):
        for body in ("d: &x\n  b: 1\n", "d:\n  - &x\n    b: 1\n", "d: &x {b: 1}\n", "d: !!map\n  b: 1\n",
                     "d: &x\n  b: 1\ne:\n  <<: *x\n", "d: &x plain\ne: *x\n"):
            self.workflow("on: push\njobs: {}\n" + body, name="a.yml")
            code, out = self.ci("--validate")
            self.assertEqual(code, 0, f"{body!r}: {out}")
        self.workflow("on: push\nname: &x a: b\n", name="a.yml")  # a property does not excuse a ': ' in the value
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("mapping values are not allowed", out)

    def test_tab_indentation_and_bad_indentation_fail(self):
        self.workflow("on: push\njobs:\n\tj: 1\n", name="tab.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("tab in indentation", out)
        self.workflow("on: push\njobs:\n    j:\n      a: 1\n   b: 2\n", name="ind.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("ind.yml: line", out)
        self.assertIn("bad indentation", out)

    def test_empty_file_and_non_mapping_fail(self):
        self.workflow("", name="empty.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("empty.yml: the file is empty", out)
        self.workflow("- a\n- b\n", name="list.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("list.yml: not a mapping at the top level", out)

    def test_non_utf8_fails_closed(self):
        self.p.write(".github/workflows/bin.yml", "on: push\n")
        (self.p.work / ".github" / "workflows" / "bin.yml").write_bytes(b"on: push\nname: \xff\xfe\n")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("bin.yml:", out)
        self.assertIn("codec", out)

    def test_key_off_says_so_and_passes(self):
        self.workflow("name: a: b\n", name="bad.yml")
        self.set_config(ciYamlCheck=False)
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("workflow YAML check is off (ciYamlCheck", out)
        self.assertNotIn("bad.yml", out)

    def test_bad_key_value_is_a_config_error(self):
        self.set_config(ciYamlCheck="no")
        code, out = self.ci("--validate")
        self.assertEqual(code, 2, out)
        self.assertIn("ciYamlCheck", out)

    def test_key_is_in_schema_and_template_and_check_list(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]
        self.assertIs(schema["ciYamlCheck"]["default"], True)
        tpl = json.loads((ROOT / "templates" / "gw.json").read_text())
        self.assertIs(tpl["ciYamlCheck"], True)
        self.assertIn("python3 .claude/gw/scripts/ci-local.py --validate", tpl["check"])


class Actionlint(unittest.TestCase):
    """E71: --validate also runs `actionlint -shellcheck=` over valid workflows (`ciActionlint`, `actionlintVersion`);
    a fake actionlint on PATH records its arguments and answers as told."""
    setUp_runs, workflow, ci, set_config = Runs.setUp, Runs.workflow, Runs.ci, Runs.set_config
    GOOD = Validate.GOOD
    FAKE = """#!/bin/sh
if [ "$1" = -version ]; then echo "${FAKE_VERSION:-1.7.12}"; echo "installed by pip"; exit 0; fi
[ -z "${FAKE_SLEEP:-}" ] || sleep "$FAKE_SLEEP"
echo "$@" >> "$FAKE_LOG"
[ -z "${FAKE_FAIL:-}" ] || { echo "$FAKE_FAIL"; exit 1; }
"""

    def setUp(self):
        self.setUp_runs()
        self.bin = self.tmp / "fakebin"
        self.bin.mkdir()
        self.calls = self.tmp / "actionlint-calls"
        self.p.env["FAKE_LOG"] = str(self.calls)

    def install(self):
        (self.bin / "actionlint").write_text(self.FAKE)
        (self.bin / "actionlint").chmod(0o755)
        self.p.env["PATH"] = str(self.bin) + os.pathsep + self.p.env["PATH"]

    def called(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def test_installed_runs_over_every_workflow_without_shellcheck(self):
        self.install()
        self.workflow(self.GOOD)
        self.workflow(self.GOOD, name="b.yaml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        [args] = self.called()
        self.assertEqual(args.split(), ["-shellcheck=", "-pyflakes=", ".github/workflows/b.yaml", ".github/workflows/ci.yml"])
        self.assertIn("actionlint: 2 workflow file(s) clean", out)

    def test_a_v_prefixed_version_matches_without_warning(self):
        self.install()
        self.p.env["FAKE_VERSION"] = "v1.7.12"
        self.workflow(self.GOOD)
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertNotIn("warning: actionlint", out)
        self.assertEqual(len(self.called()), 1)

    def test_a_hung_actionlint_times_out_failing_in_require_and_warning_in_auto(self):
        self.install()
        self.p.env["FAKE_SLEEP"] = "5"
        self.workflow(self.GOOD)
        self.set_config(ciStepTimeout=0.01)  # minutes: 0.6 s
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("actionlint timed out after 0.01 min (ciStepTimeout", out)
        self.set_config(ciStepTimeout=0.01, ciActionlint="require")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("actionlint timed out after 0.01 min (ciStepTimeout", out)

    def test_its_findings_fail_with_the_fix(self):
        self.install()
        self.p.env["FAKE_FAIL"] = ".github/workflows/ci.yml:3:5: unexpected key \"job\" [syntax-check]"
        self.workflow(self.GOOD)
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn('ci.yml:3:5: unexpected key "job"', out)
        self.assertIn("actionlint found errors", out)
        self.assertIn("ci-local.py --validate", out)

    def test_invalid_yaml_does_not_run_it(self):
        self.install()
        self.workflow("name: a: b\n", name="bad.yml")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.called(), [])

    def test_no_workflow_does_not_run_it(self):
        self.install()
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.called(), [])
        self.assertNotIn("actionlint", out)

    def test_missing_warns_with_the_pinned_install_in_auto_and_fails_in_require(self):
        self.workflow(self.GOOD)
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("warning: actionlint is not installed", out)
        self.assertIn('pip install "actionlint-py==1.7.12.*"', out)
        self.set_config(ciActionlint="require")
        code, out = self.ci("--validate")
        self.assertEqual(code, 1, out)
        self.assertIn("actionlint is not installed and ciActionlint is require", out)
        self.assertIn('pip install "actionlint-py==1.7.12.*"', out)
        self.set_config(actionlintVersion="")
        code, out = self.ci("--validate")
        self.assertIn('pip install actionlint-py', out)
        self.assertNotIn("==", out)

    def test_off_does_not_run_it(self):
        self.install()
        self.p.env["FAKE_FAIL"] = "boom"
        self.workflow(self.GOOD)
        self.set_config(ciActionlint="off")
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.called(), [])
        self.assertIn("actionlint is off (ciActionlint", out)

    def test_another_version_warns_and_still_runs(self):
        self.install()
        self.p.env["FAKE_VERSION"] = "1.6.0"
        self.workflow(self.GOOD)
        code, out = self.ci("--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("warning: actionlint 1.6.0 here, but actionlintVersion is 1.7.12", out)
        self.assertIn('pip install "actionlint-py==1.7.12.*"', out)
        self.assertEqual(len(self.called()), 1)
        self.set_config(actionlintVersion="")
        code, out = self.ci("--validate")
        self.assertNotIn("warning: actionlint", out)

    def test_bad_values_are_config_errors(self):
        self.workflow(self.GOOD)
        for key, value in (("ciActionlint", "yes"), ("actionlintVersion", "1.7")):
            self.set_config(**{key: value})
            code, out = self.ci("--validate")
            self.assertEqual(code, 2, out)
            self.assertIn(key, out)
            self.set_config(ciActionlint="auto", actionlintVersion="1.7.12")

    def test_keys_are_in_schema_and_template(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]
        self.assertEqual(schema["ciActionlint"]["default"], "auto")
        self.assertEqual(schema["ciActionlint"]["enum"], ["auto", "require", "off"])
        self.assertEqual(schema["actionlintVersion"]["default"], "1.7.12")
        tpl = json.loads((ROOT / "templates" / "gw.json").read_text())
        self.assertEqual((tpl["ciActionlint"], tpl["actionlintVersion"]), ("auto", "1.7.12"))

    def test_the_ci_template_installs_the_pinned_version_only_on_github(self):
        text = (ROOT / "templates" / "github" / "check.yml").read_text()
        step = text.split("- name: Install actionlint", 1)[1].split("- name:", 1)[0]
        self.assertIn('[ "${GITHUB_ACTIONS:-}" = true ]', step)
        self.assertIn("config.py get actionlintVersion", step)
        self.assertIn("config.py get ciActionlint", step)
        self.assertIn('"$RUNNER_TEMP/actionlint"', step)
        self.assertIn("GITHUB_PATH", step)
        # B50: only the binary on PATH, never the venv's bin/ (its python3 has no PyYAML).
        self.assertIn('echo "$RUNNER_TEMP/actionlint-bin" >> "$GITHUB_PATH"', step)
        self.assertNotIn('actionlint/bin" >> "$GITHUB_PATH"', step)
        self.assertLess(text.index("- name: Install actionlint"), text.index("- name: Check\n"))


if __name__ == "__main__":
    unittest.main()
