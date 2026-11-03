"""related-tests.sh with deleted files (D29): a push that only deletes still runs the related tests."""
import json
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

    def test_deletion_only_push_runs_slow_and_gets_deleted_paths(self):
        rel = {"fast": [{"command": "echo \"fast:{files}\" >> out.log", "paths": "\\.py$"}],
               "slow": ["echo \"slow:{files}\" >> out.log"]}
        code, out, lines = self.run_with(rel, ("src/gone.py", "my gone.py"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["fast:src/gone.py 'my gone.py'", "slow:src/gone.py 'my gone.py'"])
        self.assertIn("the push only deletes files", out)

    def test_deletion_only_respects_paths(self):
        rel = {"fast": [{"command": "echo md >> out.log", "paths": "\\.md$"}], "slow": []}
        code, out, lines = self.run_with(rel, ("src/gone.py",))
        self.assertEqual((code, lines), (0, []), out)

    def test_mixed_push_ignores_deleted_files(self):
        rel = {"fast": ["echo \"fast:{files}\" >> out.log"], "slow": []}
        code, out, lines = self.run_with(rel, ("src/gone.py", "src/a.py"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["fast:src/a.py"])
        self.assertNotIn("only deletes", out)

    def test_empty_list_is_not_a_deletion(self):
        rel = {"fast": ["echo fast >> out.log"], "slow": ["echo slow >> out.log"]}
        code, out, lines = self.run_with(rel, ())
        self.assertEqual((code, lines), (0, ["fast"]), out)
        self.assertNotIn("only deletes", out)

    def test_deletion_only_failure_names_the_command(self):
        code, out, _ = self.run_with({"fast": [], "slow": ["exit 3"]}, ("src/gone.py",))
        self.assertEqual(code, 1, out)
        self.assertIn("related-tests: failed (slow): exit 3", out)


if __name__ == "__main__":
    unittest.main()
