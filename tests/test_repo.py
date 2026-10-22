"""Repository-level checks: manifests, version vs CHANGELOG, ES/EN document pairs.

Run: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
PAIR_LINK = re.compile(r"\[(?:English|Español)\]\(([^)]+\.md)\)")


def tracked(pattern):
    out = subprocess.run(["git", "ls-files", pattern], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines() if line]


def run_blocks(path):
    """{step name: shell script} for the `run:` steps of a GitHub workflow (no YAML library needed)."""
    blocks, name, lines = {}, None, path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\s*- name:\s*(.+)$", line)
        if m:
            name = m.group(1).strip()
        m = re.match(r"^(\s*)run:\s*(.*)$", line)
        if not m:
            continue
        if m.group(2).strip() != "|":
            blocks[name] = m.group(2) + "\n"
            continue
        indent, body = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                break
            body.append(nxt)
        cut = min(len(b) - len(b.lstrip()) for b in body if b.strip())
        blocks[name] = "\n".join(b[cut:] for b in body) + "\n"
    return {k: re.sub(r"\$\{\{[^}]*\}\}", "x", v) for k, v in blocks.items()}


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class Manifests(unittest.TestCase):
    def test_every_tracked_json_parses(self):
        for path in tracked("*.json"):
            with self.subTest(path=str(path.relative_to(ROOT))):
                json.loads(path.read_text(encoding="utf-8"))

    def test_plugin_manifest(self):
        plugin = load(".claude-plugin/plugin.json")
        self.assertEqual(plugin["name"], "galivelop-workflow")
        self.assertRegex(plugin["version"], SEMVER)
        self.assertEqual(plugin["license"], "MIT")

    def test_marketplace_manifest(self):
        market = load(".claude-plugin/marketplace.json")
        self.assertEqual(market["name"], "galivelop-workflow")
        self.assertIn("name", market["owner"])
        entries = [p for p in market["plugins"] if p["name"] == "galivelop-workflow"]
        self.assertEqual(len(entries), 1, "marketplace.json must list the plugin once")
        self.assertEqual(entries[0]["source"], "./")
        # One fact, one place: the version lives only in plugin.json.
        self.assertNotIn("version", entries[0], "remove 'version' from marketplace.json; keep it in plugin.json")


class SchemaVersion(unittest.TestCase):
    def test_schema_carries_the_workflow_version(self):
        # aplicar.py treats the copied schema as workflow-owned through this marker (header_version).
        version = load(".claude-plugin/plugin.json")["version"]
        self.assertEqual(load("schema/gw.schema.json").get("$comment"), f"galivelop-workflow v{version}",
                         "set $comment in schema/gw.schema.json to 'galivelop-workflow v<version>'")


class Changelog(unittest.TestCase):
    def test_plugin_version_has_bilingual_entry(self):
        version = load(".claude-plugin/plugin.json")["version"]
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
        self.assertIsNotNone(match, f"CHANGELOG.md has no '## [{version}]' entry; add one")
        self.assertIn("### ES", match.group(1), f"entry {version} lacks '### ES'")
        self.assertIn("### EN", match.group(1), f"entry {version} lacks '### EN'")


class Release(unittest.TestCase):
    """.github/workflows/release.yml: its run steps pass shellcheck and refuse what must not be released."""
    WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-release-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.steps = run_blocks(self.WORKFLOW)

    def step(self, name, cwd, **env):
        script = self.tmp / "step.sh"
        script.write_text(self.steps[name])
        r = subprocess.run(["bash", "-e", str(script)], cwd=cwd, capture_output=True, text=True,
                           env=dict({k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, **env))
        return r.returncode, r.stdout + r.stderr

    def test_run_steps_pass_shellcheck(self):
        if not shutil.which("shellcheck"):
            if os.environ.get("CI") or os.environ.get("CLAUDE_CODE_REMOTE") == "true":
                self.fail("shellcheck is missing; install it (apt-get install shellcheck / pip install shellcheck-py)")
            self.skipTest("shellcheck not installed locally; CI runs it")
        for name, body in self.steps.items():
            with self.subTest(step=name):
                path = self.tmp / "block.sh"
                path.write_text("#!/usr/bin/env bash\n" + body)
                r = subprocess.run(["shellcheck", str(path)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def notes(self, changelog, tag="v1.2.3"):
        (self.tmp / "CHANGELOG.md").write_text(changelog)
        return self.step("Release notes from the CHANGELOG entry", self.tmp, GITHUB_REF_NAME=tag)

    def test_notes_take_the_entry_of_the_tag(self):
        code, out = self.notes("# Changelog\n\n## [1.2.3] - 2026-10-22\n\n- fixed\n\n## [1.2.2] - 2026-10-01\n\n- old\n")
        self.assertEqual(code, 0, out)
        notes = (self.tmp / "notes.md").read_text()
        self.assertIn("- fixed", notes)
        self.assertNotIn("- old", notes)

    def test_notes_dots_are_not_wildcards(self):
        code, out = self.notes("# Changelog\n\n## [1x2x3] - 2026-10-22\n\n- not this one\n")
        self.assertNotEqual(code, 0, out)
        self.assertIn("no entry for 1.2.3", out)

    def test_notes_only_whitespace_are_refused(self):
        code, out = self.notes("# Changelog\n\n## [1.2.3] - 2026-10-22\n\n   \n\t\n\n## [1.2.2] - 2026-10-01\n\n- old\n")
        self.assertNotEqual(code, 0, out)
        self.assertIn("or it is empty", out)

    def test_notes_unreleased_is_refused(self):
        code, out = self.notes("# Changelog\n\n## [1.2.3] - Unreleased\n\n- fixed\n")
        self.assertNotEqual(code, 0, out)
        self.assertIn("still says Unreleased", out)

    def test_notes_with_version_py_placeholders_are_refused(self):
        for placeholder in ("(por completar)", "(to be filled in)"):
            with self.subTest(placeholder=placeholder):
                code, out = self.notes(f"# Changelog\n\n## [1.2.3] - 2026-10-22\n\n### ES\n\n- {placeholder}\n")
                self.assertNotEqual(code, 0, out)
                self.assertIn("placeholders of scripts/version.py", out)

    def test_tag_off_main_is_refused(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        cfg = self.tmp / "gitconfig"
        cfg.write_text("[user]\n\tname = T\n\temail = t@example.com\n[commit]\n\tgpgsign = false\n"
                       "[init]\n\tdefaultBranch = main\n")
        env.update(GIT_CONFIG_GLOBAL=str(cfg), GIT_CONFIG_NOSYSTEM="1")

        def git(*args, cwd=self.tmp):
            return subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True,
                                  check=True).stdout.strip()
        git("init", "-q", "--bare", "origin.git")
        git("init", "-q", "work")
        work = self.tmp / "work"
        git("remote", "add", "origin", str(self.tmp / "origin.git"), cwd=work)
        git("commit", "-q", "--allow-empty", "-m", "on main", cwd=work)
        git("push", "-q", "origin", "main", cwd=work)
        on_main = git("rev-parse", "HEAD", cwd=work)
        git("commit", "-q", "--allow-empty", "-m", "not on main", cwd=work)
        off_main = git("rev-parse", "HEAD", cwd=work)
        name = "The tagged commit is on main"
        code, out = self.step(name, work, GITHUB_SHA=off_main, GITHUB_REF_NAME="v1.2.3",
                              GIT_CONFIG_GLOBAL=str(cfg), GIT_CONFIG_NOSYSTEM="1")
        self.assertNotEqual(code, 0, out)
        self.assertIn("not on main", out)
        code, out = self.step(name, work, GITHUB_SHA=on_main, GITHUB_REF_NAME="v1.2.3",
                              GIT_CONFIG_GLOBAL=str(cfg), GIT_CONFIG_NOSYSTEM="1")
        self.assertEqual(code, 0, out)


class Pairs(unittest.TestCase):
    """Every human doc in Spanish has its English pair and vice versa, linked both ways."""

    def pairs(self):
        docs = tracked("docs/es/*.md") + tracked("docs/en/*.md") + [ROOT / "README.md", ROOT / "README.es.md"]
        return docs

    def test_each_doc_links_to_an_existing_pair_that_links_back(self):
        for doc in self.pairs():
            rel = doc.relative_to(ROOT)
            with self.subTest(doc=str(rel)):
                links = PAIR_LINK.findall(doc.read_text(encoding="utf-8"))
                self.assertTrue(links, f"{rel}: add a '[English](...)' or '[Español](...)' link to its pair")
                pair = (doc.parent / links[0]).resolve()
                self.assertTrue(pair.is_file(), f"{rel}: pair {links[0]} does not exist")
                back = [(pair.parent / l).resolve() for l in PAIR_LINK.findall(pair.read_text(encoding="utf-8"))]
                self.assertIn(doc.resolve(), back, f"{pair.relative_to(ROOT)} must link back to {rel}")

    def test_folders_have_the_same_number_of_docs(self):
        es, en = tracked("docs/es/*.md"), tracked("docs/en/*.md")
        self.assertEqual(len(es), len(en), "docs/es and docs/en must have the same number of files")


class ShellcheckStep(unittest.TestCase):
    """tests/shellcheck.sh without shellcheck on PATH: a warning on a person's machine, a failure in a cloud session
    (where no CI would make up for it) and in CI."""

    def run_without_shellcheck(self, **env):
        tmp = Path(tempfile.mkdtemp(prefix="gw-shellcheck-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        for tool in ("git", "dirname", "xargs"):
            (tmp / tool).symlink_to(shutil.which(tool))
        base = {k: v for k, v in os.environ.items() if k not in ("CI", "CLAUDE_CODE_REMOTE") and not k.startswith("GIT_")}
        r = subprocess.run([shutil.which("bash"), str(ROOT / "tests" / "shellcheck.sh")], cwd=ROOT,
                           capture_output=True, text=True, env=dict(base, PATH=str(tmp), **env))
        return r.returncode, r.stdout + r.stderr

    def test_local_machine_only_warns(self):
        code, out = self.run_without_shellcheck()
        self.assertEqual(code, 0, out)
        self.assertIn("warning: shellcheck not installed locally", out)

    def test_cloud_session_fails_with_the_install_command(self):
        code, out = self.run_without_shellcheck(CLAUDE_CODE_REMOTE="true")
        self.assertEqual(code, 1, out)
        self.assertIn("missing in this cloud session", out)
        self.assertIn("pip install shellcheck-py", out)

    def test_ci_fails(self):
        code, out = self.run_without_shellcheck(CI="true")
        self.assertEqual(code, 1, out)
        self.assertIn("shellcheck is missing in CI", out)


if __name__ == "__main__":
    unittest.main()
