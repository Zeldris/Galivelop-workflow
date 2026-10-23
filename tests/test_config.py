"""scripts/config.py: validation, defaults, CLI and failing closed."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "config.py"
VALID = {"version": "0.1.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main",
         "pushToProtected": "pr", "check": ["make check", "make lint"], "reviewMark": "docs/reviewed.txt",
         "content": ["^docs/"]}


def cli(root, *args):
    return subprocess.run(["python3", str(SCRIPT), "--root", str(root), *args], capture_output=True, text=True)


class Config(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, data):
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(data))

    def test_this_repo_config_is_valid(self):
        self.assertEqual(cli(ROOT, "validate").returncode, 0)

    def test_get_list_scalar_bool_and_default(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "check").stdout.splitlines(), ["make check", "make lint"])
        self.assertEqual(cli(self.tmp, "get", "log").stdout.strip(), "docs/log.md")
        self.assertEqual(cli(self.tmp, "get", "requireRetro").stdout.strip(), "false")
        self.assertEqual(cli(self.tmp, "get", "install", "--json").stdout.strip(), "[]")

    def test_check_wrapper_and_worktree_links_defaults_and_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "checkWrapper").stdout, "\n")
        self.assertEqual(cli(self.tmp, "get", "worktreeLinks").stdout.splitlines(), ["node_modules", ".venv"])
        self.write(dict(VALID, checkWrapper="tools/qa/host.sh", worktreeLinks=["backend/node_modules", ".env"]))
        self.assertEqual(cli(self.tmp, "get", "checkWrapper").stdout.strip(), "tools/qa/host.sh")
        self.assertEqual(cli(self.tmp, "get", "worktreeLinks").stdout.splitlines(), ["backend/node_modules", ".env"])
        self.write(dict(VALID, worktreeLinks=[]))
        self.assertEqual(cli(self.tmp, "get", "worktreeLinks", "--json").stdout.strip(), "[]")

    def test_worktree_links_must_stay_inside_the_repo(self):
        for bad in ("/etc", "../x", "a/../b", "a/..", ".."):
            self.write(dict(VALID, worktreeLinks=[bad]))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("worktreeLinks[0]", r.stderr)
            self.assertIn("does not match", r.stderr)
        self.write(dict(VALID, worktreeLinks=["..hidden", "a..b/c"]))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)

    def test_related_tests_entries_are_strings_or_objects(self):
        ok = {"fast": ["npx vitest", {"command": "npm test {files}", "paths": "^app/", "cwd": "app"}], "slow": []}
        self.write(dict(VALID, relatedTests=ok))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.write(dict(VALID, relatedTests={"fast": [5]}))
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("relatedTests.fast[0]: matches none of the allowed forms", r.stderr)

    def test_related_picks_the_commands_that_apply(self):
        entries = ["echo always", {"command": "run {files}", "paths": "\\.ts$", "cwd": "app"}]
        self.write(dict(VALID, relatedTests={"fast": entries}, checkWrapper="w.sh"))
        r = subprocess.run(["python3", str(SCRIPT), "--root", str(self.tmp), "related", "--kind", "fast"],
                           input="app/a b.ts\nsrc/x.py\n", capture_output=True, text=True)
        self.assertEqual(r.stdout.split("\0")[:-1],
                         ["w.sh echo always", "w.sh bash -c 'cd app && run '\"'\"'a b.ts'\"'\"''"])

    def test_missing_config_fails_closed(self):
        r = cli(self.tmp, "get", "check")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not found", r.stderr)

    def test_invalid_config_names_every_problem(self):
        bad = dict(VALID, pushToProtected="sometimes", chek=["x"], check=[])
        del bad["log"]
        self.write(bad)
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        for fragment in ("pushToProtected", "unknown key 'chek'", "missing required key 'log'", "at least 1"):
            self.assertIn(fragment, r.stderr)

    def test_broken_json_reports_the_line(self):
        (self.tmp / ".claude" / "gw.json").write_text('{\n "version": "0.1.0",\n}')
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertRegex(r.stderr, r"invalid JSON at line [23]")

    def test_unknown_key_in_get_fails(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "nope").returncode, 2)

    def test_rev_reads_the_config_of_that_commit(self):
        git = ["git", "-C", str(self.tmp), "-c", "user.name=T", "-c", "user.email=t@example.com",
               "-c", "commit.gpgsign=false"]
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "no config"], check=True)
        self.write(VALID)
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-q", "-m", "config"], check=True)
        self.write(dict(VALID, protectedBranch="trunk"))  # the working tree says otherwise
        self.assertEqual(cli(self.tmp, "get", "protectedBranch").stdout.strip(), "trunk")
        r = cli(self.tmp, "--rev", "HEAD", "get", "protectedBranch")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "main"), r.stderr)
        self.assertEqual(cli(self.tmp, "--rev", "HEAD", "get", "requireRetro").stdout.strip(), "false")
        r = cli(self.tmp, "--rev", "HEAD~1", "get", "protectedBranch")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not in commit HEAD~1", r.stderr)
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        (self.tmp / ".claude" / "gw.json").write_text("{}")
        subprocess.run([*git, "commit", "-q", "-am", "broken"], check=True)
        self.assertEqual(cli(self.tmp, "--rev", "HEAD", "validate").returncode, 2)

    def test_not_a_git_repo_fails(self):
        plain = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(cli(plain, "validate").returncode, 2)
        finally:
            shutil.rmtree(plain)


class NonCapturing(unittest.TestCase):
    def test_groups_become_non_capturing_and_the_rest_is_left_alone(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import config
        cases = {r"(INS|FLU)-\d+": r"(?:INS|FLU)-\d+", r"\(x\)(a|b)": r"\(x\)(?:a|b)", r"[(]a(b)": r"[(]a(?:b)",
                 r"(?:a)(?P<n>c)": r"(?:a)(?:c)", r"[^]()](z)": r"[^]()](?:z)", r"(?i)a(b)": r"(?i)a(?:b)",
                 r"[A-Z]{2,5}-\d+[a-z]?": r"[A-Z]{2,5}-\d+[a-z]?"}
        for src, want in cases.items():
            self.assertEqual(config.non_capturing(src), want)
        with self.assertRaises(config.ConfigError) as ctx:
            config.non_capturing(r"(a)\1")
        self.assertIn("back-reference", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
