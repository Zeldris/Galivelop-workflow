"""scripts/version.py: markers in sync with plugin.json, and a bump that moves them all."""
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def run(root, *args):
    return subprocess.run(["python3", str(root / "scripts" / "version.py"), *args], capture_output=True, text=True)


class Version(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for rel in ("scripts", "skills", "templates", "schema", ".claude-plugin"):
            shutil.copytree(ROOT / rel, self.tmp / rel, ignore=shutil.ignore_patterns("__pycache__"))
        (self.tmp / ".claude").mkdir()
        shutil.copy(ROOT / ".claude" / "gw.json", self.tmp / ".claude" / "gw.json")
        shutil.copy(ROOT / "CHANGELOG.md", self.tmp / "CHANGELOG.md")

    def test_this_repo_markers_match_plugin_json(self):
        r = run(ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args], check=True, capture_output=True)

    def commit_all(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def test_release_needs_a_new_version_when_copyable_files_changed_since_the_tag(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        (tmp / "README.md").write_text("not copyable\n"); self.commit_all("docs only")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        script = tmp / "scripts" / "doctor.py"
        script.write_text(script.read_text() + "# changed\n"); self.commit_all("copyable change")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"changed since v{VERSION} (scripts/doctor.py)", r.stdout)
        self.assertIn("python3 scripts/version.py X.Y.Z", r.stdout)
        self.assertEqual(run(tmp).returncode, 0, "without --release only the markers are checked")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.commit_all("bump")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_release_on_the_tagged_commit_itself_passes(self):
        self.git("init", "-q")
        self.commit_all("first release")
        self.git("tag", f"v{VERSION}")  # the only tag, on HEAD: nothing changed since it
        r = run(self.tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_release_without_an_earlier_tag_fails_closed(self):
        self.git("init", "-q")
        self.commit_all("one")
        (self.tmp / "README.md").write_text("x\n"); self.commit_all("two")
        r = run(self.tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("git fetch --tags origin", r.stdout)

    def test_bump_moves_every_marker_and_adds_a_changelog_entry(self):
        tmp = self.tmp
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(run(tmp).returncode, 0, run(tmp).stdout)
        self.assertIn('"version": "9.8.7"', (tmp / ".claude-plugin" / "plugin.json").read_text())
        self.assertIn('"version": "9.8.7"', (tmp / "templates" / "gw.json").read_text())
        self.assertIn("## [9.8.7] - Unreleased", (tmp / "CHANGELOG.md").read_text())
        self.assertIn('version: "9.8.7"', (tmp / "skills" / "selector" / "SKILL.md").read_text())
        self.assertIn("galivelop-workflow v9.8.7", (tmp / "scripts" / "config.py").read_text())

    def test_bump_leaves_the_installed_config_alone(self):
        installed = (self.tmp / ".claude" / "gw.json").read_bytes()
        self.assertEqual(run(self.tmp, "9.8.7").returncode, 0)
        self.assertEqual((self.tmp / ".claude" / "gw.json").read_bytes(), installed)

    def test_resync_fixes_every_stale_marker_and_templates_gw_json_in_one_go(self):
        tmp = self.tmp
        gw = tmp / "templates" / "gw.json"
        gw.write_text(gw.read_text().replace(f'"version": "{VERSION}"', '"version": "0.0.9"', 1))
        for rel, old in (("scripts/config.py", "0.0.1"), ("scripts/doctor.py", "0.0.2"), ("schema/gw.schema.json", "0.0.3")):
            path = tmp / rel
            path.write_text(path.read_text().replace(f"galivelop-workflow v{VERSION}", f"galivelop-workflow v{old}", 1))
        skill = tmp / "skills" / "selector" / "SKILL.md"
        skill.write_text(skill.read_text().replace(f'version: "{VERSION}"', 'version: "0.0.4"', 1))
        r = run(tmp)
        self.assertEqual(r.returncode, 1)
        for name in ("templates/gw.json", "config.py", "doctor.py", "gw.schema.json", "SKILL.md"):
            self.assertIn(name, r.stdout)
        r = run(tmp, VERSION)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(tmp)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_only_real_markers_count_and_bytes_are_kept(self):
        tmp = self.tmp
        prose = tmp / "scripts" / "prose.py"
        prose.write_bytes(f"# galivelop-workflow v{VERSION}\r\n\r\n\r\n\r\n\r\n"
                          "# an example: galivelop-workflow v0.0.1\r\n".encode())
        body = tmp / "skills" / "extra" / "SKILL.md"
        body.parent.mkdir()
        body.write_text(f'---\nname: extra\nmetadata:\n  version: "{VERSION}"\n---\n\nExample:\n\n'
                        'metadata:\n  version: "0.0.2"\n')
        latin = tmp / "templates" / "latin.txt"
        latin.write_bytes(b"# galivelop-workflow v0.0.3\n# caf\xe9\n")
        latin_bytes = latin.read_bytes()
        r = run(tmp)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("prose.py", r.stdout)
        self.assertNotIn("extra", r.stdout)
        self.assertIn("latin.txt: not UTF-8", r.stdout)
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("skipped templates/latin.txt", r.stderr)
        self.assertEqual(latin.read_bytes(), latin_bytes)
        self.assertEqual(prose.read_bytes(), b"# galivelop-workflow v9.8.7\r\n\r\n\r\n\r\n\r\n"
                                             b"# an example: galivelop-workflow v0.0.1\r\n")
        text = body.read_text()
        self.assertIn('metadata:\n  version: "9.8.7"\n---', text)
        self.assertTrue(text.endswith('version: "0.0.2"\n'))

    def test_skill_version_is_read_the_same_by_aplicar_and_version_py(self):
        tmp = self.tmp
        crlf = tmp / "skills" / "crlf" / "SKILL.md"
        crlf.parent.mkdir()
        crlf.write_bytes(f"---\r\nname: crlf\r\nmetadata:\r\n  version: \"{VERSION}\"\r\n---\r\n\r\nBody\r\n".encode())
        note = tmp / "skills" / "note" / "SKILL.md"
        note.parent.mkdir()
        note.write_text(f"---\nname: note\nmetadata:\n  version: {VERSION}  # note\n---\n\nBody\n")
        spec = importlib.util.spec_from_file_location("aplicar_under_test", ROOT / "scripts" / "aplicar.py")
        aplicar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(aplicar)
        self.assertEqual(aplicar.skill_version(crlf), VERSION)
        self.assertEqual(aplicar.skill_version(note), VERSION)
        r = run(tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.assertIn(b'  version: "9.8.7"\r\n---\r\n', crlf.read_bytes())
        self.assertIn("  version: 9.8.7  # note\n", note.read_text())

    def test_a_workflow_file_without_a_marker_is_flagged(self):
        tmp = self.tmp
        (tmp / "scripts" / "nuevo.sh").write_text("#!/usr/bin/env bash\necho hi\n")
        (tmp / "templates" / "es" / "NUEVO.md").write_text("# Nuevo\n")
        skill = tmp / "skills" / "bare" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text("---\nname: bare\n---\n\nBody\n")
        (tmp / "skills" / "bare" / "notes.md").write_text("owned through its SKILL.md: no header needed\n")
        r = run(tmp)
        self.assertEqual(r.returncode, 1, r.stdout)
        for rel in ("scripts/nuevo.sh", "templates/es/NUEVO.md", "skills/bare/SKILL.md"):
            self.assertIn(f"missing marker: {rel}", r.stdout)
        self.assertNotIn("notes.md", r.stdout)
        self.assertNotIn("templates/claude/settings.json", r.stdout)

    def test_bump_touches_only_the_top_level_json_version(self):
        tmp = self.tmp
        for rel in ("templates/gw.json", ".claude-plugin/plugin.json"):
            path = tmp / rel
            data = json.loads(path.read_text())
            data = dict({"$schema": "x", "nested": {"version": "keep-me"}}, **data)
            path.write_text(json.dumps(data, indent=2) + "\n")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        for rel in ("templates/gw.json", ".claude-plugin/plugin.json"):
            data = json.loads((tmp / rel).read_text())
            self.assertEqual(data["version"], "9.8.7", rel)
            self.assertEqual(data["nested"], {"version": "keep-me"}, rel)

    def test_bump_fails_loudly_without_a_top_level_version_or_a_changelog_heading(self):
        tmp = self.tmp
        gw = tmp / "templates" / "gw.json"
        original = gw.read_text()
        data = json.loads(original)
        del data["version"]
        gw.write_text(json.dumps(data, indent=2) + "\n")
        plugin_before = (tmp / ".claude-plugin" / "plugin.json").read_bytes()
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('templates/gw.json has no top-level "version"', r.stderr)
        self.assertIn("python3 scripts/version.py 9.8.7", r.stderr)
        self.assertEqual((tmp / ".claude-plugin" / "plugin.json").read_bytes(), plugin_before, "nothing written")
        gw.write_text(original)
        (tmp / "CHANGELOG.md").write_text("# Changelog\n\nNo entries yet.\n")
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("CHANGELOG.md has no `## [x.y.z]` heading", r.stderr)
        self.assertEqual((tmp / ".claude-plugin" / "plugin.json").read_bytes(), plugin_before, "nothing written")

    def test_not_semver_is_refused(self):
        self.assertEqual(run(ROOT, "1.2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
