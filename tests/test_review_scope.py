"""scripts/review-scope.py (D82) and apply.py --vendored: the phase 1 review leaves out unchanged workflow copies. Every
failing case checks the message, not only the exit code."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_apply import Fixture, ROOT

sys.dont_write_bytecode = True
HOOK = ".githooks/pre-push"
SCRIPT = ".claude/gw/scripts/change-size.py"


class ScopeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-review-scope-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.assertEqual(self.p.run_apply()[0], 0)
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "base")
        self.p.run("git", "checkout", "-q", "-b", "work")

    def commit(self):
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "work")

    def scope(self, *args):
        return self.p.run("python3", str(self.p.work / ".claude/gw/scripts/review-scope.py"), "--base", "main",
                          "--workflow", str(ROOT), *args)

    def listed(self, *args):
        code, out = self.scope(*args)
        self.assertEqual(code, 0, out)
        return [l for l in out.splitlines() if not l.startswith("review-scope:")]



class ReviewScope(ScopeBase):
    def test_no_vendored_files_lists_the_whole_diff(self):
        self.p.write("src/a.py", "a\n")
        self.p.write("docs/b.md", "b\n")
        self.commit()
        self.assertEqual(self.listed(), ["docs/b.md", "src/a.py"])

    def test_vendored_files_are_left_out(self):
        self.p.write("src/a.py", "a\n")
        self.p.write(HOOK, (self.p.work / HOOK).read_text())  # same bytes: not a change at all
        self.p.write(".claude/gw/scripts/extra.py", "x\n")  # a file the workflow does not ship: the project's own
        self.commit()
        self.assertEqual(self.listed(), [".claude/gw/scripts/extra.py", "src/a.py"])

    def test_all_vendored_prints_nothing_and_says_how_many(self):
        # the whole workflow copy arrives in one branch: the diff is its project's files plus unchanged copies only
        tmp = Path(tempfile.mkdtemp(prefix="gw-review-scope-all-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        q = Fixture(tmp)
        q.run("git", "add", "-A")
        q.run("git", "commit", "-qm", "base")
        q.run("git", "checkout", "-q", "-b", "work")
        self.assertEqual(q.run_apply()[0], 0)
        q.run("git", "add", "-A")
        q.run("git", "commit", "-qm", "work")
        code, out = q.run("python3", str(q.work / ".claude/gw/scripts/review-scope.py"), "--base", "main",
                          "--workflow", str(ROOT))
        self.assertEqual(code, 0, out)
        shown = [l for l in out.splitlines() if not l.startswith("review-scope:")]
        # what stays is the project's to fill in (templates, config): never a script, skill or hook copy
        self.assertFalse([l for l in shown if l.startswith((".claude/gw/scripts/", ".claude/skills/", ".githooks/"))], shown)
        self.assertIn("vendored file(s) left out of", out)

    def test_a_vendored_file_edited_locally_is_still_reviewed(self):
        (self.p.work / SCRIPT).write_text((self.p.work / SCRIPT).read_text() + "# local\n")
        self.p.write(HOOK, (self.p.work / HOOK).read_text())
        self.commit()
        self.assertEqual(self.listed(), [SCRIPT])

    def test_a_renamed_vendored_copy_is_listed_by_its_new_path(self):
        (self.p.work / "tools").mkdir()
        self.p.run("git", "mv", HOOK, "tools/pre-push")
        self.commit()
        self.assertEqual(self.listed(), [HOOK, "tools/pre-push"])

    def test_all_flag_lists_everything(self):
        self.p.write("src/a.py", "a\n")
        (self.p.work / SCRIPT).write_text((self.p.work / SCRIPT).read_text() + "# local\n")
        self.commit()
        self.assertEqual(self.listed("--all"), [SCRIPT, "src/a.py"])

    def bare(self, *args):
        return self.p.run("python3", str(self.p.work / ".claude/gw/scripts/review-scope.py"), "--base", "main", *args)

    def test_a_project_without_a_workflow_fails_closed_with_the_clone_command(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        code, out = self.bare()
        self.assertEqual(code, 2, out)
        self.assertIn("no workflow copy at v", out)
        self.assertIn("git clone --branch v", out)
        self.assertIn("--workflow <DIR>", out)
        self.assertNotIn("src/a.py", out)

    def test_the_trivial_path_fails_closed_too(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        code, out = self.bare("--trivial")
        self.assertEqual(code, 2, out)
        self.assertIn("git clone --branch v", out)

    def test_all_needs_no_workflow(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        code, out = self.bare("--all")
        self.assertEqual(code, 0, out)
        self.assertIn("src/a.py", out)

    def test_the_env_var_gives_the_workflow(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        self.p.env["GW_WORKFLOW"] = str(ROOT)
        code, out = self.bare()
        self.assertEqual(code, 0, out)
        self.assertIn("src/a.py", out)

    def test_a_sibling_clone_at_the_project_version_is_found(self):  # D132
        sib = self.p.work.parent / "Galivelop-workflow"
        shutil.copytree(ROOT, sib, ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__", "node_modules"))
        self.addCleanup(shutil.rmtree, sib, True)
        self.p.write("src/a.py", "a\n")
        self.commit()
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        plug = sib / ".claude-plugin/plugin.json"
        data = json.loads(plug.read_text())
        data["version"] = cfg["version"]
        plug.write_text(json.dumps(data))
        code, out = self.bare()
        self.assertEqual(code, 0, out)
        self.assertIn("src/a.py", out)
        data["version"] = "0.0.1"  # another version: not accepted, and the message says which one it is
        plug.write_text(json.dumps(data))
        code, out = self.bare()
        self.assertEqual(code, 2, out)
        self.assertIn("is at v0.0.1", out)

    def test_the_workflow_repo_itself_is_its_own_copy(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        wf = self.tmp / "wf"
        shutil.copytree(ROOT, wf, ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__", "node_modules"))
        (wf / ".claude").mkdir()
        shutil.copy(ROOT / ".claude/gw.json", wf / ".claude/gw.json")
        for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "base"], ["checkout", "-q", "-b", "w"]):
            self.p.run("git", "-C", str(wf), *args)
        (wf / "x.py").write_text("x\n")
        self.p.run("git", "-C", str(wf), "add", "-A")
        self.p.run("git", "-C", str(wf), "commit", "-qm", "w")
        code, out = self.p.run("python3", str(wf / "scripts/review-scope.py"), "--base", "main", cwd=str(wf))
        self.assertEqual(code, 0, out)
        self.assertIn("x.py", out)

    def fake_wf(self, name="galivelop-workflow", version=None, repository=None):
        wf = self.tmp / "fake-wf"
        shutil.copytree(ROOT / "scripts", wf / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "skills", wf / "skills")
        shutil.copytree(ROOT / "schema", wf / "schema")
        (wf / ".claude-plugin").mkdir()
        data = {"name": name, "version": version or json.loads((self.p.work / ".claude/gw.json").read_text())["version"]}
        if repository:
            data["repository"] = repository
        (wf / ".claude-plugin/plugin.json").write_text(json.dumps(data))
        return wf

    def set_cfg(self, **kv):
        path = self.p.work / ".claude/gw.json"
        cfg = json.loads(path.read_text())
        cfg.update(kv)
        cfg = {k: v for k, v in cfg.items() if v is not None}
        path.write_text(json.dumps(cfg))
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "cfg")

    def test_an_explicit_workflow_that_is_not_the_workflow_is_an_error(self):  # D132
        self.commit()
        code, out = self.bare("--workflow", str(self.p.work))  # a project: has scripts/apply.py, skills/, another name
        self.assertEqual(code, 2, out)
        self.assertIn("--workflow", out)
        self.assertIn("is not the galivelop-workflow repo", out)
        self.assertIn("--workflow <DIR>", out)
        code, out = self.bare("--workflow", str(self.tmp / "nowhere"))
        self.assertEqual(code, 2, out)
        self.assertIn("is not the galivelop-workflow repo", out)

    def test_a_wrong_env_var_is_an_error_too(self):  # D132
        self.commit()
        self.p.env["GW_WORKFLOW"] = str(self.tmp / "nowhere")
        code, out = self.bare()
        self.assertEqual(code, 2, out)
        self.assertIn("GW_WORKFLOW", out)
        self.assertIn("is not the galivelop-workflow repo", out)

    def test_a_workflow_at_another_version_warns(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        wf = self.fake_wf(version="0.0.1", repository="https://example.test/wf")
        code, out = self.bare("--workflow", str(wf), "--all")
        self.assertEqual(code, 0, out)  # --all never looks for the workflow
        code, out = self.bare("--workflow", str(wf))
        self.assertIn("warning", out)
        self.assertIn("is at v0.0.1", out)
        self.assertIn("https://example.test/wf", out)  # the URL comes from the workflow's plugin.json

    def test_a_gw_json_without_version_fails_closed(self):  # D132: the config loader refuses it before the lookup
        self.p.write("src/a.py", "a\n")
        self.commit()
        self.set_cfg(version=None)
        code, out = self.bare()
        self.assertEqual(code, 2, out)
        self.assertIn("missing required key 'version'", out)
        self.assertNotIn("vNone", out)

    def test_workflow_dir_without_version_never_matches_none_with_none(self):  # D132
        import importlib.util
        spec = importlib.util.spec_from_file_location("rs", ROOT / "scripts/review-scope.py")
        rs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rs)
        rs.HERE = self.tmp / "not-the-workflow"  # the script's own repo must not answer in this test
        sib = self.tmp / "Galivelop-workflow"
        shutil.copytree(ROOT, sib, ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__", "node_modules"))
        plug = sib / ".claude-plugin/plugin.json"
        data = json.loads(plug.read_text())
        data.pop("version", None)
        plug.write_text(json.dumps(data))
        proj = self.tmp / "proj"
        proj.mkdir()
        with self.assertRaises(rs.ScopeError) as cm:
            rs.workflow_dir(None, proj, {})
        self.assertIn('has no "version"', str(cm.exception))
        self.assertIn("git clone --depth 1", str(cm.exception))
        self.assertNotIn("vNone", str(cm.exception))

    def test_the_clone_path_and_the_url_come_from_gw_json(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        self.set_cfg(workflowClone="../elsewhere", workflowRepository="https://example.test/own.git")
        code, out = self.bare()
        self.assertEqual(code, 2, out)
        self.assertIn("https://example.test/own.git", out)
        shutil.copytree(ROOT, self.p.work.parent / "elsewhere", ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__", "node_modules"))
        self.addCleanup(shutil.rmtree, self.p.work.parent / "elsewhere", True)
        code, out = self.bare()
        self.assertEqual(code, 0, out)

    def test_a_project_copy_is_not_taken_for_the_workflow(self):  # D132
        self.p.write("src/a.py", "a\n")
        self.commit()
        # the project holds scripts/apply.py and skills/ (a vendored layout) but its plugin.json is not the workflow's
        (self.p.work / "scripts").mkdir(exist_ok=True)
        (self.p.work / "scripts/apply.py").write_text("raise SystemExit('must not run')\n")
        (self.p.work / "skills").mkdir(exist_ok=True)
        code, out = self.bare()
        self.assertEqual(code, 2, out)
        self.assertIn("no workflow copy at v", out)
        self.assertNotIn("must not run", out)

    def test_a_base_that_is_not_a_commit_fails_with_the_fix(self):
        code, out = self.scope("--base", "nope")
        self.assertEqual(code, 2)
        self.assertIn("is not a commit", out)


class Trivial(ScopeBase):
    """B27: --trivial."""

    def setUp(self):
        super().setUp()
        self.p.write(".claude/gw.json", (self.p.work / ".claude/gw.json").read_text())
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "gw")
        self.p.run("git", "branch", "-f", "main", "HEAD")

    def limit(self, n):
        import json
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        cfg["reviewTrivialLines"] = n
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "limit")
        self.p.run("git", "branch", "-f", "main", "HEAD")

    def code(self, n):
        self.p.write("src/a.py", "".join(f"x{i} = {i}\n" for i in range(n)))
        self.commit()

    def test_no_code_is_trivial_whatever_its_size(self):
        self.limit(0)
        self.p.write("docs/b.md", "".join(f"l{i}\n" for i in range(500)))
        self.commit()
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)
        self.assertIn("no code in the review scope", out)

    def test_small_code_diff_is_trivial(self):
        self.code(5)
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)
        self.assertIn("5 changed code line(s), at most reviewTrivialLines=30", out)

    def test_at_the_threshold_is_trivial_and_one_over_is_not(self):
        self.limit(10)
        self.code(10)
        self.assertEqual(self.scope("--trivial")[0], 0)
        self.code(11)
        code, out = self.scope("--trivial")
        self.assertEqual(code, 1, out)
        self.assertIn("not trivial: 1 code file(s), 11 changed line(s), reviewTrivialLines=10", out)

    def test_zero_turns_the_line_limit_off(self):
        self.limit(0)
        self.code(1)
        code, out = self.scope("--trivial")
        self.assertEqual(code, 1, out)
        self.assertIn("reviewTrivialLines=0", out)

    def stamped_base(self, version, n=0):
        """src/a.py with a version header and N real lines, on main when called first, on the branch after."""
        self.p.write("src/a.py", f"# galivelop-workflow v{version}\n" + "".join(f"x{i} = {i}\n" for i in range(n)))

    def test_a_diff_of_only_version_headers_is_trivial(self):  # B45
        self.limit(1)
        self.stamped_base("0.8.0", 20)
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "base file")
        self.p.run("git", "branch", "-f", "main", "HEAD")
        self.stamped_base("0.8.1", 20)
        self.commit()
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)
        self.assertIn("0 changed code line(s) (2 version-stamp line(s) not counted), at most reviewTrivialLines=1", out)

    def test_headers_plus_a_real_change_over_the_limit_is_not_trivial(self):  # B45
        self.limit(10)
        self.stamped_base("0.8.0", 20)
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "base file")
        self.p.run("git", "branch", "-f", "main", "HEAD")
        self.stamped_base("0.8.1", 40)  # 20 real lines more, plus the header
        self.commit()
        code, out = self.scope("--trivial")
        self.assertEqual(code, 1, out)
        self.assertIn("not trivial: 1 code file(s), 20 changed line(s) (2 version-stamp line(s) not counted), "
                      "reviewTrivialLines=10", out)

    def test_skip_stamps_off_counts_the_stamp_lines(self):
        self.limit(1)
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        cfg["scopeGuard"] = {"mode": "warn", "skipStamps": False}
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.stamped_base("0.8.0", 20)
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "base file")
        self.p.run("git", "branch", "-f", "main", "HEAD")
        self.stamped_base("0.8.1", 20)
        self.commit()
        code, out = self.scope("--trivial")
        self.assertEqual(code, 1, out)
        self.assertIn("not trivial: 1 code file(s), 2 changed line(s), reviewTrivialLines=1", out)

    def test_bracket_paths_are_literal_in_the_trivial_diff(self):
        self.limit(25)
        self.p.write("app/[id].py", "# galivelop-workflow v0.8.0\n" + "".join(f"x{i} = {i}\n" for i in range(20)))
        self.p.write("app/i.py", "")
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "base files")
        self.p.run("git", "branch", "-f", "main", "HEAD")
        self.p.write("app/[id].py", "# galivelop-workflow v0.8.1\n" + "".join(f"x{i} = {i}\n" for i in range(20)))
        self.p.write("app/i.py", "".join(f"y{i} = {i}\n" for i in range(20)))
        self.commit()
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)  # a glob would count i.py twice (40 lines)
        self.assertIn("20 changed code line(s) (2 version-stamp line(s) not counted)", out)

    def test_an_empty_scope_is_trivial(self):
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)


class Vendored(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-vendored-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.p.run_apply()

    def test_lists_unchanged_copies_and_not_edited_or_template_ones(self):
        (self.p.work / SCRIPT).write_text((self.p.work / SCRIPT).read_text() + "# local\n")
        code, out = self.p.run_apply("--vendored")
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertIn(HOOK, lines)
        self.assertNotIn(SCRIPT, lines)
        self.assertNotIn("AGENTS.md", lines)
        self.assertEqual(self.p.read(SCRIPT).splitlines()[-1], "# local", "it writes nothing")

    def test_init_and_vendored_together_write_nothing(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-vendored-init-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        q = Fixture(tmp)
        (q.work / ".claude/gw.json").unlink()
        code, out = q.run_apply("--init", "--vendored", "--check-command", "true")
        self.assertEqual(code, 2, out)
        self.assertIn("--init writes files", out)
        self.assertFalse((q.work / ".claude/gw.json").exists())

    def test_an_owned_file_is_not_vendored(self):
        self.p.write(".claude/gw.json", (self.p.work / ".claude/gw.json").read_text().replace(
            "{", '{"ownedFiles": [".githooks/pre-push"],', 1))
        code, out = self.p.run_apply("--vendored")
        self.assertEqual(code, 0, out)
        self.assertNotIn(HOOK, out.splitlines())


if __name__ == "__main__":
    unittest.main()
