"""Every skill in skills/ follows the Agent Skills specification plus the workflow's own rules.

Spec: https://github.com/agentskills/agentskills (docs/specification.mdx).
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_LINES = 200  # plan §5.1 (the spec allows 500; we keep skills shorter)


def frontmatter(text):
    """Parse the small YAML subset skills use: 'key: value' and one level of nested maps."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    data, parent = {}, None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        key, _, value = line.strip().partition(":")
        value = value.strip().strip('"').strip("'")
        if indent == 0:
            data[key] = value if value else {}
            parent = key if not value else None
        elif indent == 2 and parent is not None:
            data[parent][key] = value
    return data


class Skills(unittest.TestCase):
    def setUp(self):
        self.version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["version"]
        self.dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())

    def test_there_are_skills(self):
        self.assertTrue(self.dirs, "skills/ is empty")

    def test_each_skill(self):
        for d in self.dirs:
            with self.subTest(skill=d.name):
                path = d / "SKILL.md"
                self.assertTrue(path.is_file(), f"{d.name}: missing SKILL.md")
                text = path.read_text(encoding="utf-8")
                fm = frontmatter(text)
                self.assertIsNotNone(fm, f"{d.name}: SKILL.md must start with a '---' frontmatter block")
                self.assertEqual(fm.get("name"), d.name, f"{d.name}: 'name' must equal the folder name")
                self.assertRegex(d.name, NAME, f"{d.name}: lowercase letters, digits and single hyphens only")
                self.assertLessEqual(len(d.name), 64)
                desc = fm.get("description", "")
                self.assertTrue(desc, f"{d.name}: 'description' is required (what it does and when to use it)")
                self.assertLessEqual(len(desc), 1024, f"{d.name}: 'description' over 1024 characters")
                self.assertTrue(fm.get("license"), f"{d.name}: add 'license'")
                meta = fm.get("metadata")
                self.assertIsInstance(meta, dict, f"{d.name}: add a 'metadata' map with 'version'")
                self.assertEqual(meta.get("version"), self.version,
                                 f"{d.name}: metadata.version must be {self.version} (plugin.json)")
                lines = len(text.splitlines())
                self.assertLessEqual(lines, MAX_LINES, f"{d.name}: SKILL.md has {lines} lines (max {MAX_LINES})")

    def test_trigger_queries_are_well_formed(self):
        # skills/<name>/evals/triggers.json: queries that should and should not fire the skill (run by hand).
        for d in self.dirs:
            path = d / "evals" / "triggers.json"
            if not path.is_file():
                continue
            with self.subTest(skill=d.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(data, list, f"{d.name}: triggers.json must be a list")
                for item in data:
                    self.assertEqual(sorted(item), ["query", "should_trigger"], f"{d.name}: bad entry {item!r}")
                    self.assertTrue(item["query"].strip(), f"{d.name}: empty query")
                    self.assertIsInstance(item["should_trigger"], bool, f"{d.name}: should_trigger must be true/false")
                flags = {item["should_trigger"] for item in data}
                self.assertEqual(flags, {True, False}, f"{d.name}: needs queries that fire it and queries that do not")

    def test_matt_pocock_is_credited_in_each_of_his_skills(self):
        for d in self.dirs:
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            if "mattpocock/skills@" in text:
                with self.subTest(skill=d.name):
                    self.assertIn("Original skill by Matt Pocock", text, f"{d.name}: keep the credit line to Matt Pocock")

    def test_upstream_licence_is_bundled(self):
        uses_upstream = [d.name for d in self.dirs if "mattpocock" in (d / "SKILL.md").read_text(encoding="utf-8")]
        if uses_upstream:
            self.assertTrue((ROOT / "LICENSE-mattpocock-skills").is_file(),
                            "skills from mattpocock/skills need LICENSE-mattpocock-skills at the root")

    def test_skills_the_flow_calls_on_its_own_are_model_invoked(self):
        # AGENTS.md (phase 2), selector and revisado.sh with requireRetro have the agent run these itself.
        for name in ("retro", "opt-tokens", "selector", "orchestrate-dealer"):
            with self.subTest(skill=name):
                text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("disable-model-invocation", text.split("\n---", 1)[0],
                                 f"{name}: the agent must be able to invoke it; drop disable-model-invocation")

    def test_applying_the_workflow_points_to_a_reading_subagent(self):
        # The pilot read the workflow whole in the main session: the selector row existed and gw-init did not cite it.
        self.assertIn("| Apply or update the workflow (`gw-init`", (SKILLS / "selector" / "SKILL.md").read_text())
        self.assertIn("`orchestrate-dealer`", (SKILLS / "gw-init" / "SKILL.md").read_text())


if __name__ == "__main__":
    unittest.main()
