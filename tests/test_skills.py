"""Every skill in skills/ follows the Agent Skills specification plus the workflow's own rules.

Spec: https://github.com/agentskills/agentskills (docs/specification.mdx).
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.dont_write_bytecode = True
import doctor  # noqa: E402  (the invisible-character and size checks live there, for projects too)
SKILLS = ROOT / "skills"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility",
                "disable-model-invocation"}  # closed list (anthropics/skills quick_validate.py)
TRIGGER = re.compile(r"\bUse (when|for|at|before|after|to)\b")
MAX_LINES = 200  # plan §5.1 (the spec allows 500; we keep skills shorter)


def description_problems(fm):
    """Why a skill's frontmatter fails the closed-keys, no-angle-brackets and trigger-clause rules ([] if fine)."""
    problems = [f"unknown frontmatter key '{k}' (allowed: {', '.join(sorted(ALLOWED_KEYS))})"
                for k in fm if k not in ALLOWED_KEYS]
    desc = fm.get("description", "")
    if "<" in desc or ">" in desc:
        problems.append("the description contains '<' or '>'")
    if not TRIGGER.search(desc):
        problems.append("the description has no trigger clause ('Use when ...', 'Use for', 'Use at', 'Use before', "
                        "'Use after' or 'Use to')")
    return problems


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
        # gw-media-content only has its shared material (b1) until its SKILL.md lands (b3): remove it from here then.
        sin_skill_md = {"gw-media-content"}
        self.dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir() and p.name not in sin_skill_md)

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
                self.assertEqual(description_problems(fm), [], f"{d.name}: frontmatter rules")
                self.assertEqual(doctor.invisible_chars(text), [], f"{d.name}: invisible characters in SKILL.md")
                lines = len(text.splitlines())
                self.assertLessEqual(lines, MAX_LINES, f"{d.name}: SKILL.md has {lines} lines (max {MAX_LINES})")

    def test_frontmatter_rules_catch_their_cases(self):
        good = {"name": "x", "description": "Does a thing. Use when asked.", "license": "MIT", "metadata": {}}
        self.assertEqual(description_problems(good), [])
        self.assertEqual(description_problems(dict(good, description="Use to pick; Use for more.")), [])
        self.assertIn("unknown frontmatter key 'version'", description_problems(dict(good, version="1"))[0])
        self.assertIn("contains '<' or '>'", description_problems(dict(good, description="Use when <x>."))[0])
        self.assertIn("no trigger clause", description_problems(dict(good, description="Use only when asked."))[0])
        self.assertIn("no trigger clause", description_problems(dict(good, description="Reuse it."))[0])

    def test_instruction_files_have_no_invisible_characters_and_stay_short(self):
        files = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]
        for kind in ("AGENTS.md", "CLAUDE.md"):
            files += sorted((ROOT / "templates").glob(f"*/{kind}"))
        self.assertGreaterEqual(len(files), 6)
        for path in files:
            with self.subTest(file=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(doctor.invisible_chars(text), [], "invisible or bidi characters")
                self.assertLessEqual(len(text.splitlines()), doctor.WARN_LINES, "over doctor's warning size")

    def test_invisible_char_detection(self):
        self.assertEqual(doctor.invisible_chars("\ufeffok\nfine\n"), [])
        self.assertEqual(doctor.invisible_chars("a\u200bb\nc\u2067"), [(1, 2, "U+200B"), (2, 2, "U+2067")])
        self.assertEqual(doctor.invisible_chars("x\n\ufeffy"), [(2, 1, "U+FEFF")])
        self.assertEqual(doctor.invisible_chars("\u202a"), [(1, 1, "U+202A")])

    def test_zero_width_joiner_is_fine_only_inside_an_emoji_sequence(self):
        woman_technologist = "\U0001F469\u200d\U0001F4BB"
        self.assertEqual(doctor.invisible_chars(f"ok {woman_technologist} and \U0001F468\u200d\U0001F469\u200d\U0001F467\n"), [])
        for text, found in (("a\u200db", [(1, 2, "U+200D")]), ("\u200d" + woman_technologist, [(1, 1, "U+200D")]),
                            (woman_technologist + "\u200d", [(1, 4, "U+200D")]),
                            ("\U0001F469\u200d\u200d\U0001F4BB", [(1, 2, "U+200D"), (1, 3, "U+200D")]),
                            ("x\n\u200d\U0001F469", [(2, 1, "U+200D")]), ("\U0001F469\u200d\nx", [(1, 2, "U+200D")]),
                            ("\U0001F469\u200b\u200d\U0001F4BB", [(1, 2, "U+200B"), (1, 3, "U+200D")])):
            with self.subTest(text=text):
                self.assertEqual(doctor.invisible_chars(text), found)

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
