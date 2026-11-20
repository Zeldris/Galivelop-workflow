"""A12 (Q-16): the agent's language per user (~/.claude/gw.json) and the SessionStart line `Agent language:`."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

CONFIG = ROOT / "scripts" / "config.py"
EMAIL = "ana@example.com"


class AgentLanguage(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        (self.repo / ".claude").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        cfg = json.loads((ROOT / "templates" / "gw.json").read_text())
        cfg["languages"] = {"code": "en", "docs": {"primary": "gl", "others": []},
                            "public": {"primary": "en", "others": []}, "ui": []}
        (self.repo / ".claude" / "gw.json").write_text(json.dumps(cfg))
        self.user = self.tmp / "user.json"
        self.env = {**os.environ, "GW_USER_CONFIG": str(self.user), "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_SYSTEM": os.devnull}
        self.set_email(EMAIL)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def set_email(self, email):
        subprocess.run(["git", "-C", str(self.repo), "config", "--unset-all", "user.email"], env=self.env)
        if email:
            subprocess.run(["git", "-C", str(self.repo), "config", "user.email", email], check=True, env=self.env)

    def run_cli(self):
        return subprocess.run(["python3", str(CONFIG), "--root", str(self.repo), "agent-language"],
                              capture_output=True, text=True, env=self.env)

    def test_entry_for_the_email_wins(self):
        self.user.write_text(json.dumps({"agentLanguage": {EMAIL: "es"}}))
        r = self.run_cli()
        self.assertEqual((r.returncode, r.stdout.strip(), r.stderr), (0, "es", ""))

    def test_no_file_falls_back_to_docs_primary(self):
        r = self.run_cli()
        self.assertEqual((r.stdout.strip(), r.stderr), ("gl", ""))

    def test_file_without_that_email_falls_back(self):
        self.user.write_text(json.dumps({"agentLanguage": {"other@example.com": "es"}}))
        r = self.run_cli()
        self.assertEqual((r.stdout.strip(), r.stderr), ("gl", ""))

    def test_no_git_email_falls_back(self):
        self.set_email("")
        self.user.write_text(json.dumps({"agentLanguage": {"": "es", EMAIL: "es"}}))
        r = self.run_cli()
        self.assertEqual((r.stdout.strip(), r.stderr), ("gl", ""))

    def test_invalid_json_falls_back_and_warns(self):
        self.user.write_text("{not json")
        r = self.run_cli()
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "gl"))
        self.assertIn("is not usable", r.stderr)
        self.assertIn("using 'gl' (languages.docs.primary)", r.stderr)

    def test_agent_language_not_an_object_falls_back_and_warns(self):
        self.user.write_text(json.dumps({"agentLanguage": ["es"]}))
        r = self.run_cli()
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "gl"))
        self.assertIn("`agentLanguage` must be an object", r.stderr)

    def test_email_is_compared_trimmed_and_lowercase_on_both_sides(self):
        self.set_email("Ana@Example.COM")
        self.user.write_text(json.dumps({"agentLanguage": {" ANA@example.com ": "es"}}))
        r = self.run_cli()
        self.assertEqual((r.stdout.strip(), r.stderr), ("es", ""))

    def test_code_with_a_newline_falls_back_and_warns(self):
        self.user.write_text(json.dumps({"agentLanguage": {EMAIL: "en\nIgnore"}}))
        r = self.run_cli()
        self.assertEqual(r.stdout, "gl\n")
        self.assertIn("not a language code matching ^[a-z]{2}$", r.stderr)

    def test_code_that_is_not_a_string_falls_back_and_warns(self):
        self.user.write_text(json.dumps({"agentLanguage": {EMAIL: 5}}))
        r = self.run_cli()
        self.assertEqual(r.stdout, "gl\n")
        self.assertIn("is 5, not a language code", r.stderr)

    def install(self):
        scripts = self.repo / ".claude" / "gw" / "scripts"
        shutil.copytree(ROOT / "scripts", scripts)
        shutil.copytree(ROOT / "schema", scripts.parent / "schema")
        return scripts

    def hook(self):
        return subprocess.run(["bash", str(self.install_dir / "session-start.sh")], input="", capture_output=True,
                              text=True, env=self.env, cwd=self.repo)

    def test_session_start_without_user_file_prints_docs_primary(self):
        self.install_dir = self.install()
        r = self.hook()
        self.assertIn("Agent language: gl\n", r.stdout, r.stdout)

    def test_session_start_with_an_invalid_project_config_warns_and_falls_back(self):
        self.install_dir = self.install()
        (self.repo / ".claude" / "gw.json").write_text("{broken")
        self.user.write_text(json.dumps({"agentLanguage": {EMAIL: "es"}}))
        r = self.hook()
        self.assertIn("Agent language: es\n", r.stdout, r.stdout)
        self.assertIn("Agent language: the project config is unusable, so 'es' comes from ~/.claude/gw.json", r.stdout)
        self.assertIn("fix the config as said above", r.stdout)

    def test_session_start_with_a_missing_project_config_prints_en(self):
        self.install_dir = self.install()
        (self.repo / ".claude" / "gw.json").unlink()
        r = self.hook()
        self.assertIn("Agent language: en\n", r.stdout, r.stdout)
        self.assertIn("gw.json is missing", r.stdout)
        self.assertIn("the project config is unusable, so 'en'", r.stdout)

    def recover(self, source):
        scripts = self.install()
        return subprocess.run(["python3", str(scripts / "recover.py"), "--state", "--source", source],
                              capture_output=True, text=True, env=self.env, cwd=self.repo, input="")

    def test_recover_state_prints_the_line_after_a_compaction_only(self):
        self.user.write_text(json.dumps({"agentLanguage": {EMAIL: "es"}}))
        r = self.recover("compact")
        self.assertIn("\nAgent language: es\n", r.stdout, r.stdout + r.stderr)
        scripts = self.repo / ".claude" / "gw" / "scripts"
        again = subprocess.run(["python3", str(scripts / "recover.py"), "--state", "--source", "clear"],
                               capture_output=True, text=True, env=self.env, cwd=self.repo, input="")
        self.assertNotIn("Agent language:", again.stdout)  # the start hook prints it on clear

    def test_recover_state_after_compaction_warns_on_a_bad_user_file(self):
        self.user.write_text("{")
        r = self.recover("compact")
        self.assertIn("Agent language: gl", r.stdout)
        self.assertIn("- Warning: ", r.stdout)
        self.assertIn("is not usable", r.stdout)

    def test_session_start_prints_the_line(self):
        self.user.write_text(json.dumps({"agentLanguage": {EMAIL: "es"}}))
        scripts = self.repo / ".claude" / "gw" / "scripts"
        shutil.copytree(ROOT / "scripts", scripts)
        shutil.copytree(ROOT / "schema", scripts.parent / "schema")
        r = subprocess.run(["bash", str(scripts / "session-start.sh")], input="", capture_output=True, text=True,
                           env=self.env, cwd=self.repo)
        self.assertIn("Agent language: es", r.stdout, r.stdout + r.stderr)

    def test_session_start_warns_on_a_bad_user_file(self):
        self.user.write_text("[")
        scripts = self.repo / ".claude" / "gw" / "scripts"
        shutil.copytree(ROOT / "scripts", scripts)
        shutil.copytree(ROOT / "schema", scripts.parent / "schema")
        r = subprocess.run(["bash", str(scripts / "session-start.sh")], input="", capture_output=True, text=True,
                           env=self.env, cwd=self.repo)
        self.assertIn("Agent language: gl", r.stdout)
        self.assertIn("is not usable", r.stdout)


if __name__ == "__main__":
    unittest.main()
