"""scripts/merge-main.py (E65): brings origin/<protectedBranch> in without losing the metrics ledger. Temporary
projects with a bare origin; every failing case checks the reason, not only the exit code."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "merge-main.py"
LEDGER = "docs/metrics/ledger.jsonl"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e")


class MergeMain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-merge-main-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origin, self.work, self.other = self.tmp / "origin.git", self.tmp / "work", self.tmp / "other"
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        for d in (self.work, self.other):
            self.git(self.tmp, "clone", "-q", str(self.origin), str(d))
            self.git(d, "checkout", "-q", "-b", "main")
        self.put(self.work, ".claude/gw.json", json.dumps(self.config()))
        self.put(self.work, "a.txt", "a\n")
        self.put(self.work, LEDGER, '{"n":1}\n')
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "-qm", "base\n\nRefs: E1")
        self.git(self.work, "push", "-q", "origin", "main")
        self.git(self.work, "checkout", "-q", "-b", "work")
        self.git(self.other, "pull", "-q", "origin", "main")

    def config(self, **extra):
        cfg = {"version": "0.8.1", "schemaVersion": 1, "language": "es", "log": "docs/log.md",
               "protectedBranch": "main", "pushToProtected": "direct", "check": ["true"],
               "reviewMark": "docs/revisado.txt", "content": ["^docs/"]}
        cfg.update(extra)
        return cfg

    def git(self, cwd, *args):
        res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=ENV)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def put(self, repo, rel, text):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def upstream(self, rel="b.txt", text="b\n"):
        self.put(self.other, rel, text)
        self.git(self.other, "add", "-A")
        self.git(self.other, "commit", "-qm", "up")
        self.git(self.other, "push", "-q", "origin", "main")

    def run_it(self, *args):
        res = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.work), *args], capture_output=True,
                             text=True, env=ENV)
        return res.returncode, res.stdout + res.stderr

    def subjects(self):
        return self.git(self.work, "log", "--format=%s").splitlines()

    def test_e28_protected_branch_as_an_option_runs_nothing(self):  # A1: "--upload-pack=<cmd>" ran <cmd>
        marker = self.tmp / "pwned"
        for value in (f"--upload-pack=touch {marker};", "-x"):
            self.put(self.work, ".claude/gw.json", json.dumps(self.config(protectedBranch=value)))
            code, out = self.run_it()
            self.assertEqual(code, 2, out)
            self.assertIn("protectedBranch", out)
            self.assertIn("must be a git branch name", out)
            self.assertIn("validate", out)
            self.assertFalse(marker.exists(), out)

    def test_e28_fetch_updates_origin_main_with_a_narrow_fetch_refspec(self):  # A1: explicit refspec
        self.git(self.work, "config", "remote.origin.fetch", "+refs/heads/work:refs/remotes/origin/work")
        self.upstream()
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertTrue((self.work / "b.txt").is_file(), out)

    def test_clean_tree_merges(self):
        self.upstream()
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertTrue((self.work / "b.txt").is_file())
        self.assertFalse(any(s.startswith("chore") for s in self.subjects()))

    def test_only_ledger_dirty_is_committed_then_merged(self):
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertIn("committed " + LEDGER, out)
        self.assertEqual((self.work / LEDGER).read_text(), '{"n":1}\n{"n":2}\n')
        self.assertEqual(self.git(self.work, "status", "--porcelain"), "")
        self.assertTrue((self.work / "b.txt").is_file())
        msg = self.git(self.work, "log", "--format=%B", "-n", "2", "--skip=1")
        self.assertIn("chore(E1): ", msg)
        self.assertIn("Refs: E1", msg)
        self.assertIn("Siguiente: Fusionar origin/main", msg)

    def test_the_trailer_word_follows_languages_docs_primary_of_a_schema_2_config(self):
        for primary, word in (("es", "Siguiente: Fusionar"), ("gl", "Next: Merge")):
            with self.subTest(primary=primary):
                cfg = self.config(schemaVersion=2, languages={"docs": {"primary": primary}})
                del cfg["language"]
                self.put(self.work, ".claude/gw.json", json.dumps(cfg))
                self.git(self.work, "add", "-A")
                self.git(self.work, "commit", "-qm", "schema 2\n\nRefs: E1")
                self.upstream(f"b-{primary}.txt")
                self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n' + primary + "\n")
                code, out = self.run_it()
                self.assertEqual(code, 0, out)
                msg = self.git(self.work, "log", "--format=%B", "-n", "2", "--skip=1")
                self.assertIn(word, msg)

    def message_ok(self, rev="HEAD"):
        """The commit message at `rev` passes the real commit-message.py rules of the project's config."""
        msg = self.tmp / "msg.txt"
        msg.write_text(self.git(self.work, "log", "-1", "--format=%B", rev), encoding="utf-8")
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / "commit-message.py"), "--root", str(self.work),
                              str(msg)], capture_output=True, text=True, env=ENV)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def strict(self, **extra):
        self.put(self.work, ".claude/gw.json", json.dumps(self.config(commitRefs=True, commitNext=True, taskId="[A-H]\\d+", refsSources=["docs/log.md"], **extra)))
        self.put(self.work, "docs/log.md", "| E1 | task |\n- E9: other\n")
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "-qm", "strict\n\nRefs: E1")

    def test_ledger_commit_passes_the_commit_msg_rules(self):
        self.strict()
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it("--refs", "E9")
        self.assertEqual(code, 0, out)
        self.message_ok("HEAD^")

    def test_id_comes_from_the_branch_not_from_a_merge_commit(self):
        self.strict()
        self.upstream()
        self.run_it()  # a merge commit is now HEAD
        self.assertEqual(self.git(self.work, "log", "-1", "--format=%P").count(" "), 1)
        self.upstream("c.txt", "c\n")
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertIn("chore(E1)", " ".join(self.subjects()))

    def test_spike_branch_commits_without_scope_or_refs(self):
        self.strict()
        self.git(self.work, "checkout", "-q", "-b", "spike/idea")
        self.git(self.work, "commit", "-q", "--allow-empty", "-m", "no refs")
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        msg = self.git(self.work, "log", "--format=%B", "-n", "1", "--skip=1")
        self.assertTrue(msg.startswith("chore: "), msg)
        self.assertNotIn("Refs:", msg)
        self.assertIn("Siguiente:", msg)
        self.message_ok("HEAD^")

    def test_commit_ledger_false_treats_it_as_dirty(self):
        self.put(self.work, ".claude/gw.json", json.dumps(self.config(metrics={"commitLedger": False})))
        self.git(self.work, "commit", "-qam", "cfg")
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        head = self.git(self.work, "rev-parse", "HEAD")
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("uncommitted changes besides the ledger: " + LEDGER, out)
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD"), head)

    def test_nothing_to_merge_commits_nothing(self):
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        head = self.git(self.work, "rev-parse", "HEAD")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertIn("Already up to date", out)
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD"), head)
        self.assertIn(LEDGER, self.git(self.work, "status", "--porcelain"))

    def test_root_in_a_subdirectory(self):
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        res = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.work / "docs")], capture_output=True,
                             text=True, env=ENV)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue((self.work / "b.txt").is_file())

    def test_refs_option_names_the_id(self):
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it("--refs", "E9")
        self.assertEqual(code, 0, out)
        self.assertIn("Refs: E9", self.git(self.work, "log", "-1", "--format=%B", "HEAD^"))

    def test_ledger_and_other_file_dirty_refuses(self):
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        self.put(self.work, "a.txt", "changed\n")
        head = self.git(self.work, "rev-parse", "HEAD")
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("uncommitted changes besides the ledger: a.txt", out)
        self.assertIn("git stash", out)
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD"), head)
        self.assertFalse((self.work / "b.txt").exists())

    def test_untracked_file_counts_as_dirty(self):
        self.put(self.work, "new.txt", "x\n")
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("new.txt", out)

    def test_no_ledger_file_at_all(self):
        self.upstream()
        self.git(self.work, "rm", "-q", LEDGER)
        self.git(self.work, "commit", "-qm", "rm ledger")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertTrue((self.work / "b.txt").is_file())

    def test_conflict_passes_status_through_and_keeps_ledger_commit(self):
        self.upstream("a.txt", "theirs\n")
        self.put(self.work, "a.txt", "mine\n")
        self.git(self.work, "commit", "-qam", "mine")
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it("--refs", "E1")
        self.assertEqual(code, 1, out)
        self.assertIn("CONFLICT", out)
        self.assertIn("chore(E1)", " ".join(self.subjects()))
        self.assertEqual(self.git(self.work, "show", "HEAD:" + LEDGER), '{"n":1}\n{"n":2}\n')

    def test_missing_config_fails_closed(self):
        (self.work / ".claude" / "gw.json").unlink()
        code, out = self.run_it()
        self.assertEqual(code, 2)
        self.assertIn("cannot read the config", out)
        self.assertIn("not found", out)

    def test_missing_protected_branch_fails_closed(self):
        self.put(self.work, ".claude/gw.json", json.dumps(self.config(protectedBranch="")))
        code, out = self.run_it()
        self.assertEqual(code, 2)
        self.assertIn("$.protectedBranch: must not be empty", out)

    def test_fetch_failure_fails_with_reason(self):
        self.git(self.work, "remote", "set-url", "origin", str(self.tmp / "nowhere.git"))
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("git fetch origin main failed", out)

    def test_ledger_without_task_id_asks_for_refs(self):
        self.git(self.work, "checkout", "-q", "--orphan", "fresh")  # a history with no Refs: at all
        self.git(self.work, "commit", "-q", "--allow-empty", "-m", "no refs")
        self.upstream()
        self.put(self.work, LEDGER, '{"n":1}\n{"n":2}\n')
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("--refs <id>", out)


if __name__ == "__main__":
    unittest.main()
