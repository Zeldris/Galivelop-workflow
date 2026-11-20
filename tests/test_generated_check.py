"""scripts/generated-check.py (E72): each `generated` entry of .claude/gw.json is regenerated and its paths must not
change. Every failing case checks the reason in the output, not only the exit code.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

SCRIPT = "generated-check.py"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-generated-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        gw = self.work / ".claude" / "gw"
        (gw / "scripts").mkdir(parents=True)
        (gw / "schema").mkdir()
        for name in (SCRIPT, "config.py"):
            shutil.copy2(ROOT / "scripts" / name, gw / "scripts" / name)
        shutil.copy2(ROOT / "schema" / "gw.schema.json", gw / "schema" / "gw.schema.json")
        subprocess.run(["git", "init", "-q", str(self.work)], check=True)
        # the generator: gen/<name> is src/<name> in upper case
        self.write("tools/gen.sh", "set -e\nmkdir -p gen\nfor f in src/*.txt; do tr a-z A-Z < \"$f\" > gen/$(basename \"$f\"); done\n")
        self.write("src/a.txt", "alpha\n")
        self.write("gen/a.txt", "ALPHA\n")

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def config(self, generated, **extra):
        cfg = dict(BASE_CONFIG, **extra)
        if generated is not None:
            cfg["generated"] = generated
        self.write(".claude/gw.json", json.dumps(cfg))

    def run_it(self, *args, cwd=None):
        r = subprocess.run([sys.executable, str(self.work / ".claude" / "gw" / "scripts" / SCRIPT), *args],
                           cwd=cwd or self.work, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout + r.stderr


class Generated(Base):
    def test_absent_or_empty_key_does_nothing(self):
        for value in (None, []):
            self.config(value)
            code, out = self.run_it()
            self.assertEqual(code, 0, out)
            self.assertIn("nothing to regenerate", out)

    def test_up_to_date_output_passes(self):
        self.config([{"command": "bash tools/gen.sh", "paths": ["gen"]}])
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertIn("up to date", out)
        self.assertIn("bash tools/gen.sh", out)

    def test_stale_output_fails_naming_the_command_and_the_file(self):
        self.write("src/a.txt", "beta\n")
        self.config([{"command": "bash tools/gen.sh", "paths": ["gen"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("gen/a.txt", out)
        self.assertIn("'bash tools/gen.sh'", out)
        self.assertIn("stale", out)
        self.assertIn("git add -- gen", out)
        self.assertEqual((self.work / "gen" / "a.txt").read_text(), "BETA\n")  # regenerated: ready to commit

    def test_new_and_deleted_files_count_as_changes(self):
        self.write("src/b.txt", "bee\n")
        self.write("gen/old.txt", "OLD\n")
        self.config([{"command": "rm -f gen/old.txt; bash tools/gen.sh", "paths": ["gen"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("added: gen/b.txt", out)
        self.assertIn("removed: gen/old.txt", out)

    def test_a_single_file_path_is_compared(self):
        self.write("gen/a.txt", "stale\n")
        self.config([{"command": "bash tools/gen.sh", "paths": ["gen/a.txt"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("changed: gen/a.txt", out)

    def test_suggested_git_add_quotes_each_path(self):
        self.write("src/a.txt", "beta\n")
        self.config([{"command": "bash tools/gen.sh; echo x > 'my gen.txt'", "paths": ["gen", "my gen.txt"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("git add -- gen 'my gen.txt'", out)

    def test_in_a_temporary_worktree_it_says_to_run_the_command_in_the_working_copy(self):
        base = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(self.work)]
        self.config([{"command": "bash tools/gen.sh", "paths": ["gen"]}])
        subprocess.run(base + ["add", "-A"], check=True)
        subprocess.run(base + ["commit", "-q", "-m", "x"], check=True)
        wt = self.tmp / "wt"
        subprocess.run(base + ["worktree", "add", "-q", "--detach", str(wt)], check=True)
        (wt / "src" / "a.txt").write_text("beta\n")
        r = subprocess.run([sys.executable, str(wt / ".claude" / "gw" / "scripts" / SCRIPT)], cwd=wt,
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 1, out)
        self.assertIn("run `bash tools/gen.sh` in your working copy, then git add -- gen", out)
        self.assertNotIn("commit them", out)

    def test_a_symlinked_subfolder_is_followed_and_a_loop_ends(self):
        self.write("real/x.txt", "old\n")
        (self.work / "gen" / "sub").symlink_to(self.work / "real", target_is_directory=True)
        (self.work / "real" / "loop").symlink_to(self.work / "real", target_is_directory=True)
        self.config([{"command": "bash tools/gen.sh; echo new > real/x.txt", "paths": ["gen"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("changed: gen/sub/x.txt", out)

    def test_a_dirty_tree_regenerated_to_the_same_content_passes(self):
        """The comparison is with the files on disk before the command, not with HEAD: uncommitted work whose
        generated files are already regenerated passes."""
        self.config([{"command": "bash tools/gen.sh", "paths": ["gen"]}])
        self.write("src/a.txt", "gamma\n")
        self.write("gen/a.txt", "GAMMA\n")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)

    def test_failing_command_fails_with_its_exit_code(self):
        self.config([{"command": "exit 3", "paths": ["gen"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("'exit 3' failed (exit 3)", out)

    def test_every_entry_runs_and_each_failure_is_named(self):
        self.write("src/a.txt", "delta\n")
        self.config([{"command": "exit 4", "paths": ["x"]}, {"command": "bash tools/gen.sh", "paths": ["gen"]}])
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("'exit 4' failed", out)
        self.assertIn("changed: gen/a.txt", out)

    def test_runs_at_the_repo_root_from_a_subfolder(self):
        self.config([{"command": "bash tools/gen.sh", "paths": ["gen"]}])
        code, out = self.run_it(cwd=self.work / "src")
        self.assertEqual(code, 0, out)

    def test_path_outside_the_repo_is_a_config_error(self):
        for bad in ("../elsewhere", "/etc", "gen/../../x"):
            self.config([{"command": "true", "paths": [bad]}])
            code, out = self.run_it()
            self.assertEqual(code, 2, out)
            self.assertIn("outside the repository", out)
            self.assertIn(bad, out)

    def test_invalid_shape_is_rejected_by_the_config(self):
        for bad in ([{"command": "true"}], [{"command": "", "paths": ["gen"]}], [{"command": "true", "paths": []}],
                    "bash tools/gen.sh"):
            self.config(bad)
            code, out = self.run_it()
            self.assertEqual(code, 2, out)
            self.assertIn("generated", out)
            self.assertIn("config.py", out)


if __name__ == "__main__":
    unittest.main()
