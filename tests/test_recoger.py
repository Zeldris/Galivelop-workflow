"""scripts/recoger.py against a temporary project repository."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "recoger.py"


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


def git(repo, *args):
    return run("git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args)


class Recoger(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "proj"
        self.state = self.tmp / "estado.json"
        (self.repo / ".claude" / "skills").mkdir(parents=True)
        git(self.tmp, "init", "-q", str(self.repo))
        # A copy of a workflow skill with an extra line, and a skill born in the project.
        ours = (ROOT / "skills" / "grilling" / "SKILL.md").read_text()
        (self.repo / ".claude/skills/grilling").mkdir()
        (self.repo / ".claude/skills/grilling/SKILL.md").write_text(ours + "\nA local improvement.\n")
        (self.repo / ".claude/skills/local-skill").mkdir()
        (self.repo / ".claude/skills/local-skill/SKILL.md").write_text(
            "---\nname: local-skill\ndescription: Born here.\n---\nBody\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "one")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def harvest(self):
        out = run("python3", str(SCRIPT), "--json", "--state", str(self.state), str(self.repo))
        return json.loads(out)[0]

    def test_first_harvest_reports_changed_and_new_skills(self):
        r = self.harvest()
        self.assertEqual([s["skill"] for s in r["skills_changed"]], ["grilling"])
        self.assertEqual(r["skills_changed"][0]["added"], 2)
        self.assertEqual([s["skill"] for s in r["skills_new"]], ["local-skill"])
        self.assertIn("retro", r["skills_missing"])

    def test_after_update_state_only_new_work_is_reported(self):
        run("python3", str(SCRIPT), "--update-state", "--state", str(self.state), str(self.repo))
        self.assertEqual(self.harvest()["history"], "nothing new since the last harvest")
        retro = self.repo / "docs" / "retro-2026-01-01-x.md"
        retro.parent.mkdir()
        retro.write_text("# Retro\n\n## For Galivelop-workflow\n\nCheck shallow clones.\n\n## Other\n\nlocal\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "two")
        r = self.harvest()
        self.assertEqual(len(r["commits"]), 1)
        self.assertEqual(r["skills_changed"], [], "unchanged files since the last harvest are not reported")
        self.assertEqual(r["retros"], ["docs/retro-2026-01-01-x.md"])
        self.assertEqual(r["ideas"][0]["text"], "Check shallow clones.")

    def test_a_clone_behind_its_remote_branch_is_flagged(self):
        origin = self.tmp / "origin.git"
        git(self.tmp, "init", "-q", "--bare", str(origin))
        git(self.repo, "remote", "add", "origin", str(origin))
        git(self.repo, "push", "-q", "-u", "origin", "HEAD:refs/heads/main")
        git(self.repo, "branch", "-q", "--set-upstream-to=origin/main")
        other = self.tmp / "other"
        git(self.tmp, "clone", "-q", "-b", "main", str(origin), str(other))
        (other / "new.txt").write_text("x\n")
        git(other, "add", "-A")
        git(other, "commit", "-qm", "newer")
        git(other, "push", "-q", "origin", "HEAD:main")
        git(self.repo, "fetch", "-q", "origin")
        r = self.harvest()
        self.assertEqual(r["behind"], {"ref": "origin/main", "commits": 1})
        out = run("python3", str(SCRIPT), "--state", str(self.state), str(self.repo))
        self.assertIn("1 commit(s) behind `origin/main`", out)

    def test_up_to_date_clone_is_not_flagged(self):
        self.assertIsNone(self.harvest()["behind"])

    def test_unknown_last_commit_falls_back_to_full_scan(self):
        self.state.write_text(json.dumps({"proj": "0" * 40}))
        r = self.harvest()
        self.assertIn("not in this clone", r["history"])
        self.assertTrue(r["skills_changed"])


if __name__ == "__main__":
    unittest.main()
