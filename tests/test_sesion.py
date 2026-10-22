"""Session hooks: scripts/session-start.sh (SessionStart startup|resume|clear), scripts/recuperar.py (clear|compact
and --buscar) and scripts/registro_sesion.py, in temporary projects laid out like one that applied the workflow.

HOME points to a temp folder, so nothing reads or writes the real ~/.claude; git runs isolated as in test_ganchos.
"""
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from test_ganchos import ROOT, Project

SCRIPTS = ("session-start.sh", "recuperar.py", "registro_sesion.py", "doctor.py")


def folder_of(path):
    return "".join(c if c.isalnum() else "-" for c in str(path))


class SessionProject(Project):
    """test_ganchos.Project plus the session scripts, a temp HOME and no inherited Claude Code variables."""

    def __init__(self, tmp, config=None):
        super().__init__(tmp, config)
        for name in SCRIPTS:
            shutil.copy2(ROOT / "scripts" / name, self.work / ".claude" / "gw" / "scripts" / name)
        self.home = tmp / "home"
        self.home.mkdir()
        for k in ("CLAUDE_CODE_REMOTE", "CLAUDE_ENV_FILE"):
            self.env.pop(k, None)
        self.env["HOME"] = str(self.home)
        self.scripts = self.work / ".claude" / "gw" / "scripts"
        self.commit("session scripts")

    def session_start(self, env=None, stdin=None, cwd=None):
        return self.run("bash", str(self.scripts / "session-start.sh"), env=env, stdin=stdin, cwd=cwd)

    def recuperar(self, *args, stdin=None, cwd=None):
        return self.run("python3", str(self.scripts / "recuperar.py"), *args, stdin=stdin, cwd=cwd)

    def transcript(self, folder_path, lines, name="s1.jsonl"):
        d = self.home / ".claude" / "projects" / folder_of(folder_path)
        d.mkdir(parents=True, exist_ok=True)
        path = d / name
        path.write_text("".join(json.dumps(l) + "\n" for l in lines))
        return path


class Base(unittest.TestCase):
    config = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-sesion-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = SessionProject(self.tmp, self.config)


class SessionStart(Base):
    def test_sets_hooks_path_when_unset(self):
        p = self.p
        p.git("config", "--unset", "core.hooksPath")
        code, out = p.session_start()
        self.assertEqual(code, 0, out)
        self.assertEqual(p.git("config", "--get", "core.hooksPath").stdout.strip(), ".githooks")
        self.assertNotIn("gw session-start:", out)

    def test_respects_another_hook_manager(self):
        p = self.p
        p.git("config", "core.hooksPath", ".husky")
        code, out = p.session_start()
        self.assertEqual(code, 0, out)
        self.assertEqual(p.git("config", "--get", "core.hooksPath").stdout.strip(), ".husky")
        self.assertIn("another hook manager", out)
        self.assertIn(".husky/pre-push", out)
        self.assertIn(".githooks/<hook>", out)

    def test_hooks_installed_in_git_dir_are_not_bypassed(self):
        p = self.p
        p.git("config", "--unset", "core.hooksPath")
        hook = p.work / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 0\n")
        hook.chmod(0o755)
        code, out = p.session_start()
        self.assertEqual(code, 0, out)
        self.assertEqual(p.git("config", "--get", "core.hooksPath", ok=False).stdout.strip(), "")
        self.assertIn("another hook manager", out)

    def test_install_only_when_the_lockfile_changes_in_the_cloud(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["install"] = ["echo ran >> install.log"]
        p.write(".claude/gw.json", json.dumps(cfg))
        p.write("package-lock.json", '{"v": 1}\n')
        p.write(".gitignore", "install.log\n")
        p.commit("lockfile")
        log = p.work / "install.log"
        code, out = p.session_start()                      # local session: no install
        self.assertEqual(code, 0, out)
        self.assertFalse(log.exists(), out)
        cloud = {"CLAUDE_CODE_REMOTE": "true"}
        self.assertEqual(p.session_start(env=cloud)[0], 0)
        self.assertEqual(log.read_text().count("ran"), 1)
        self.assertTrue((p.work / ".git" / "gw-install.sha").is_file())
        p.session_start(env=cloud)                         # same lockfile: skipped
        self.assertEqual(log.read_text().count("ran"), 1)
        p.write("package-lock.json", '{"v": 2}\n')         # changed lockfile: runs again
        p.session_start(env=cloud)
        self.assertEqual(log.read_text().count("ran"), 2)

    def test_failed_install_warns_exits_zero_and_retries_next_time(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["install"] = ["echo try >> tries.log; exit 3"]
        p.write(".claude/gw.json", json.dumps(cfg))
        cloud = {"CLAUDE_CODE_REMOTE": "true"}
        code, out = p.session_start(env=cloud)
        self.assertEqual(code, 0, out)
        self.assertIn("install command failed", out)
        p.session_start(env=cloud)
        self.assertEqual((p.work / "tries.log").read_text().count("try"), 2)

    def test_never_exits_non_zero(self):
        p = self.p
        (p.work / ".claude" / "gw.json").write_text("{not json")
        code, out = p.session_start(env={"CLAUDE_CODE_REMOTE": "true"})
        self.assertEqual(code, 0, out)
        self.assertIn("invalid JSON", out)
        self.assertIn("validate", out)
        (p.work / ".claude" / "gw.json").unlink()
        code, out = p.session_start()
        self.assertEqual(code, 0, out)
        self.assertIn(".claude/gw.json is missing", out)
        code, out = p.run("bash", str(p.scripts / "session-start.sh"), cwd=self.tmp,
                          env={"CLAUDE_PROJECT_DIR": str(self.tmp)})
        self.assertEqual(code, 0, out)

    def test_version_lag_warning(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["version"] = "0.0.9"
        p.write(".claude/gw.json", json.dumps(cfg))
        code, out = p.session_start()
        self.assertEqual(code, 0, out)
        self.assertIn("version 0.0.9", out)
        self.assertIn("/gw-update", out)

    def test_session_started_outside_the_repo_warns(self):
        p = self.p
        code, out = p.session_start(stdin=json.dumps({"cwd": str(self.tmp)}))
        self.assertEqual(code, 0, out)
        self.assertIn("outside the repo root", out)
        self.assertIn(f"cd {p.work} && claude", out)
        code, out = p.session_start(stdin=json.dumps({"cwd": str(p.work / "docs")}))
        self.assertNotIn("outside the repo root", out)


class Recuperar(Base):
    def test_plain_log_shows_its_first_section(self):
        p = self.p
        p.write("docs/log.md", "# Log\n\nintro\n\n## State\n\n| Field | Value |\n|---|---|\n| Next step | ship it |\n\n"
                "## Done\n\nold stuff\n")
        code, out = p.recuperar("--estado")
        self.assertEqual(code, 0, out)
        self.assertIn("## State", out)
        self.assertIn("ship it", out)
        self.assertNotIn("old stuff", out)
        self.assertIn("Last commits:", out)
        self.assertIn("base", out)
        self.assertIn("Compactions in this session: unknown", out)
        self.assertIn("--buscar", out)

    def test_pending_section_comes_back_too(self):
        self.p.write("docs/log.md", "# Log\n\n## State\n\nnow\n\n## Done\n\nold stuff\n\n## Pending\n\n- the left-over task\n")
        code, out = self.p.recuperar("--estado")
        self.assertIn("section 'Pending'", out)
        self.assertIn("the left-over task", out)
        self.assertNotIn("old stuff", out)

    def test_log_sections_from_the_config(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["logSections"] = ["Done", "Missing one"]
        p.write(".claude/gw.json", json.dumps(cfg))
        p.write("docs/log.md", "# Log\n\n## State\n\nstate-text\n\n## Done:\n\nold stuff\n### detail\nkept\n\n## Pending\n\nx\n")
        code, out = p.recuperar("--estado")
        self.assertEqual(code, 0, out)
        self.assertIn("section 'Done'", out)
        self.assertIn("old stuff", out)
        self.assertIn("kept", out)  # a subsection belongs to its section
        self.assertNotIn("state-text", out)
        self.assertIn("no section 'Missing one' (logSections in .claude/gw.json)", out)

    def test_long_first_section_is_trimmed(self):
        self.p.write("docs/log.md", "# Log\n\n## State\n" + "".join(f"line {i}\n" for i in range(60)))
        code, out = self.p.recuperar("--estado")
        self.assertIn("line 20", out)
        self.assertNotIn("line 40", out)
        self.assertIn("trimmed", out)

    def test_log_rows_show_the_current_branch_row(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["logRows"] = True
        p.write(".claude/gw.json", json.dumps(cfg))
        p.write("docs/log.md", "# Log\n\n| Field | Value |\n|---|---|\n| **Task · `main`** | other work |\n"
                "| **Task · `feature`** | INS-3 half done; next: tests |\n")
        p.git("checkout", "-q", "-b", "feature")
        code, out = p.recuperar("--estado")
        self.assertEqual(code, 0, out)
        self.assertIn("INS-3 half done", out)
        self.assertNotIn("other work", out)
        p.git("checkout", "-q", "-b", "nobody")
        code, out = p.recuperar("--estado")
        self.assertIn("no row for branch `nobody`", out)

    def test_status_is_capped(self):
        p = self.p
        for i in range(20):
            p.write(f"new{i:02d}.txt", "x\n")
        code, out = p.recuperar("--estado")
        self.assertIn("Uncommitted: 20 file(s)", out)
        self.assertIn("and 5 more", out)

    def test_counts_compactions_in_the_transcript(self):
        p = self.p
        p.transcript(p.work, [{"type": "user", "message": {"content": "hi"}},
                              {"type": "system", "subtype": "compact_boundary"},
                              {"type": "user", "isCompactSummary": True, "message": {"content": "summary"}},
                              {"type": "system", "subtype": "compact_boundary"}])
        code, out = p.recuperar("--estado")
        self.assertEqual(code, 0, out)
        self.assertIn("Compactions in this session: 2", out)
        self.assertNotIn("outside the repo", out)

    def test_hook_transcript_path_wins(self):
        p = self.p
        other = p.transcript(self.tmp / "elsewhere", [{"type": "system", "subtype": "compact_boundary"}])
        code, out = p.recuperar("--estado", stdin=json.dumps({"transcript_path": str(other)}))
        self.assertIn("Compactions in this session: 1", out)

    def test_estado_never_fails(self):
        p = self.p
        (p.work / ".claude" / "gw.json").unlink()
        code, out = p.recuperar("--estado")
        self.assertEqual(code, 0, out)
        self.assertIn("Log: unknown", out)

    def test_estado_does_not_wait_on_an_open_empty_stdin(self):
        p = self.p  # an agent's Bash tool, or `sleep 3 | recuperar.py --estado`: stdin open, nothing on it
        proc = subprocess.Popen(["python3", str(p.scripts / "recuperar.py"), "--estado"], cwd=p.work, env=p.env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        watchdog = threading.Timer(10, proc.kill)  # a hang is killed, and fails below with a negative exit code
        watchdog.start()
        try:
            out = proc.stdout.read()
        finally:
            watchdog.cancel()
            proc.stdin.close()
        self.assertEqual(proc.wait(timeout=10), 0, out)
        self.assertIn("Log:", out)

    def test_estado_into_a_closed_pipe_exits_zero_quietly(self):
        p = self.p  # `recuperar.py --estado | head -n 1`: the reader leaves before the writer is done
        proc = subprocess.Popen(["python3", str(p.scripts / "recuperar.py"), "--estado"], cwd=p.work, env=p.env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc.stdout.close()
        err = proc.stderr.read()
        self.assertEqual(proc.wait(timeout=10), 0, err)
        self.assertNotIn("BrokenPipeError", err)
        self.assertNotIn("Traceback", err)

    def test_buscar_finds_fragments_with_context(self):
        p = self.p
        p.transcript(p.work, [
            {"type": "user", "timestamp": "2026-10-21T10:00:00Z", "message": {"content": "use port 5433 for the db"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "noted"}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Bash",
                                                           "input": {"command": "python3 recuperar.py --buscar 5433"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1",
                                                      "content": "old search result 5433"}]}},
        ])
        code, out = p.recuperar("--buscar", "PORT 5433")
        self.assertEqual(code, 0, out)
        self.assertIn("user: use port 5433 for the db", out)
        self.assertNotIn("old search result", out)
        self.assertIn("1 fragment(s)", out)
        code, out = p.recuperar("--buscar", "port (")        # invalid regex: searched as plain text
        self.assertEqual(code, 0, out)
        self.assertIn("0 fragment(s)", out)

    def test_buscar_is_capped(self):
        p = self.p
        p.transcript(p.work, [{"type": "user", "message": {"content": f"needle {i}"}} for i in range(30)])
        code, out = p.recuperar("--buscar", "needle", "--max", "3")
        self.assertIn("needle 29", out)
        self.assertNotIn("needle 5 ", out)
        self.assertIn("the last 3 shown", out)

    def test_buscar_without_transcript_says_how(self):
        code, out = self.p.recuperar("--buscar", "x")
        self.assertEqual(code, 1, out)
        self.assertIn("--sesion", out)


class RegistroSesion(Base):
    def test_parent_folder_transcript_found_with_warning(self):
        p = self.p
        parent = p.transcript(self.tmp, [{"type": "user", "message": {"content": "x"}}])
        code, out = p.run("python3", str(p.scripts / "registro_sesion.py"), "--path")
        self.assertEqual(code, 0, out)
        self.assertIn(str(parent), out)
        self.assertIn("outside the repo", out)

    def test_newest_wins_and_own_folder_has_no_warning(self):
        p = self.p
        old = p.transcript(self.tmp, [{}])
        os.utime(old, (time.time() - 100, time.time() - 100))
        own = p.transcript(p.work, [{}])
        code, out = p.run("python3", str(p.scripts / "registro_sesion.py"), "--path")
        self.assertEqual(out.strip(), str(own))

    def test_sibling_repo_is_never_used(self):
        p = self.p
        p.transcript(self.tmp / "other-repo", [{}])
        code, out = p.run("python3", str(p.scripts / "registro_sesion.py"), "--path")
        self.assertEqual(code, 1, out)
        self.assertIn("cd ", out)


if __name__ == "__main__":
    unittest.main()
