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

    def test_not_a_git_repo_fails(self):
        plain = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(cli(plain, "validate").returncode, 2)
        finally:
            shutil.rmtree(plain)


if __name__ == "__main__":
    unittest.main()
