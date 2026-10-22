"""scripts/version.py: markers in sync with plugin.json, and a bump that moves them all."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(root, *args):
    return subprocess.run(["python3", str(root / "scripts" / "version.py"), *args], capture_output=True, text=True)


class Version(unittest.TestCase):
    def test_this_repo_markers_match_plugin_json(self):
        r = run(ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_bump_moves_every_marker_and_adds_a_changelog_entry(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for rel in ("scripts", "skills", "templates", "schema", ".claude-plugin"):
                shutil.copytree(ROOT / rel, tmp / rel)
            (tmp / ".claude").mkdir()
            shutil.copy(ROOT / ".claude" / "gw.json", tmp / ".claude" / "gw.json")
            shutil.copy(ROOT / "CHANGELOG.md", tmp / "CHANGELOG.md")
            r = run(tmp, "9.8.7")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(run(tmp).returncode, 0, run(tmp).stdout)
            self.assertIn('"version": "9.8.7"', (tmp / ".claude-plugin" / "plugin.json").read_text())
            self.assertIn("## [9.8.7] - Unreleased", (tmp / "CHANGELOG.md").read_text())
            self.assertIn('version: "9.8.7"', (tmp / "skills" / "selector" / "SKILL.md").read_text())
            self.assertIn("galivelop-workflow v9.8.7", (tmp / "scripts" / "config.py").read_text())
        finally:
            shutil.rmtree(tmp)

    def test_not_semver_is_refused(self):
        self.assertEqual(run(ROOT, "1.2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
