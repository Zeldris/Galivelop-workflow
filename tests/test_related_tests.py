"""related-tests.sh with deleted files (D29): a push that only deletes still runs the related tests."""
import json
import pathlib
import re
import sys
import unittest

from test_utils import Base

sys.dont_write_bytecode = True


class RelatedDeleted(Base):
    def run_with(self, related, changed, present=("src/a.py",)):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["relatedTests"] = related
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(cfg))
        for f in present:
            self.p.write(f, "x\n")
        listing = self.tmp / "changed"
        listing.write_text("".join(f + "\n" for f in changed))
        (self.p.work / "out.log").write_text("")
        self.p.git("add", "-A"); self.p.git("commit", "-q", "--no-verify", "--allow-empty", "-m", "related setup")
        code, out = self.p.script("related-tests.sh", str(listing), stdin="refs/heads/x 1 refs/heads/x 2\n")
        return code, out, (self.p.work / "out.log").read_text().splitlines()

    def test_deletion_only_push_files_entry_skipped_and_slow_runs(self):
        rel = {"fast": [{"command": "echo \"fast:{files}\" >> out.log", "paths": "\\.py$"},
                        {"command": "echo scoped >> out.log", "paths": "\\.py$"}],
               "slow": ["echo slow >> out.log"]}
        code, out, lines = self.run_with(rel, ("src/gone.py", "my gone.py"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["scoped", "slow"])
        self.assertIn("skipped (fast): echo \"fast:{files}\" >> out.log", out)

    def test_files_command_never_gets_nonexistent_paths(self):
        rel = {"fast": [{"command": "test -e {files}", "paths": "\\.py$"}], "slow": []}
        code, out, _ = self.run_with(rel, ("src/gone.py",))
        self.assertEqual(code, 0, out)
        self.assertIn("skipped (fast): test -e {files}", out)
        self.assertNotIn("failed", out)

    def test_deletion_only_respects_paths(self):
        rel = {"fast": [{"command": "echo md >> out.log", "paths": "\\.md$"}], "slow": []}
        code, out, lines = self.run_with(rel, ("src/gone.py",))
        self.assertEqual((code, lines), (0, []), out)

    def test_mixed_push_decides_per_entry(self):
        rel = {"fast": [{"command": "echo \"py:{files}\" >> out.log", "paths": "\\.py$"},
                        {"command": "echo pynofiles >> out.log", "paths": "\\.py$"},
                        {"command": "echo \"md:{files}\" >> out.log", "paths": "\\.md$"}], "slow": []}
        code, out, lines = self.run_with(rel, ("src/gone.py", "docs/handoff.md"), present=("docs/handoff.md",))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["pynofiles", "md:docs/handoff.md"])

    def test_mixed_push_files_entry_matching_existing_ignores_deleted(self):
        rel = {"fast": ["echo \"fast:{files}\" >> out.log"], "slow": []}
        code, out, lines = self.run_with(rel, ("src/gone.py", "src/a.py"))
        self.assertEqual((code, lines), (0, ["fast:src/a.py"]), out)
        self.assertNotIn("skipped", out)

    def test_cwd_entry_with_deleted_file_in_its_folder(self):
        rel = {"fast": [{"command": "pwd >> ../out.log", "cwd": "web"},
                        {"command": "echo \"f:{files}\" >> ../out.log", "cwd": "web"}], "slow": []}
        (self.p.work / "web").mkdir(exist_ok=True)
        code, out, lines = self.run_with(rel, ("web/gone.ts",), present=("web/keep.txt",))
        self.assertEqual(code, 0, out)
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].endswith("/web"), lines)
        self.assertIn("skipped (fast): echo \"f:{files}\"", out)

    def test_cwd_entry_ignores_deleted_file_outside_its_folder(self):
        rel = {"fast": [{"command": "echo web >> ../out.log", "cwd": "web", "paths": "\\.ts$"}], "slow": []}
        code, out, lines = self.run_with(rel, ("api/gone.ts",))
        self.assertEqual((code, lines), (0, []), out)

    def test_modified_then_deleted_in_range_counts_as_deleted(self):
        # The list names the file once (it was modified and then deleted in the pushed range); it is gone at HEAD.
        rel = {"fast": [{"command": "echo \"f:{files}\" >> out.log", "paths": "\\.py$"},
                        {"command": "echo nofiles >> out.log", "paths": "\\.py$"}], "slow": ["echo slow >> out.log"]}
        self.p.write("src/tmp.py", "1\n"); self.p.git("add", "-A"); self.p.git("commit", "-q", "--no-verify", "-m", "add")
        self.p.write("src/tmp.py", "2\n"); self.p.git("commit", "-qam", "edit", "--no-verify")
        self.p.git("rm", "-q", "src/tmp.py"); self.p.git("commit", "-q", "--no-verify", "-m", "rm")
        code, out, lines = self.run_with(rel, ("src/tmp.py",), present=())
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["nofiles", "slow"])
        self.assertIn("skipped (fast)", out)

    def test_empty_list_is_not_a_deletion(self):
        rel = {"fast": ["echo fast >> out.log"], "slow": ["echo slow >> out.log"]}
        code, out, lines = self.run_with(rel, ())
        self.assertEqual((code, lines), (0, ["fast"]), out)
        self.assertNotIn("skipped", out)

    def test_deletion_only_failure_names_the_command(self):
        code, out, _ = self.run_with({"fast": [], "slow": ["exit 3"]}, ("src/gone.py",))
        self.assertEqual(code, 1, out)
        self.assertIn("related-tests: failed (slow): exit 3", out)

    def test_many_files_print_a_count_and_a_temp_file_not_the_list(self):  # D74
        files = tuple(f"src/m{i}.py" for i in range(3))
        rel = {"fast": [{"command": "echo {files} >> out.log; exit 4", "paths": "\\.py$"}], "slow": []}
        code, out, _ = self.run_with(rel, files, present=files)
        self.assertEqual(code, 1, out)
        self.assertIn("related tests (fast): 3 files; the full command is in ", out)
        self.assertNotIn("m1.py", out)
        m = re.search(r"the full command is in (\S+)", out)
        self.assertIn("m1.py", pathlib.Path(m.group(1)).read_text())  # failed: kept, holds the whole command
        self.assertIn(f"run it again: bash {m.group(1)}", out)

    def test_one_file_command_is_still_printed_whole(self):  # D74
        rel = {"fast": [{"command": "echo {files} >> out.log; exit 4", "paths": "\\.py$"}], "slow": []}
        code, out, _ = self.run_with(rel, ("src/a.py",))
        self.assertEqual(code, 1, out)
        self.assertIn("src/a.py", out)
        self.assertNotIn("files; the full command", out)


if __name__ == "__main__":
    unittest.main()
