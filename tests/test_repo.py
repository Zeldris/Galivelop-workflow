"""Repository-level checks: manifests, version vs CHANGELOG, ES/EN document pairs.

Run: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
PAIR_LINK = re.compile(r"\[(?:English|Español)\]\(([^)]+\.md)\)")


def tracked(pattern):
    out = subprocess.run(["git", "ls-files", pattern], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines() if line]


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


class Changelog(unittest.TestCase):
    def test_plugin_version_has_bilingual_entry(self):
        version = load(".claude-plugin/plugin.json")["version"]
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
        self.assertIsNotNone(match, f"CHANGELOG.md has no '## [{version}]' entry; add one")
        self.assertIn("### ES", match.group(1), f"entry {version} lacks '### ES'")
        self.assertIn("### EN", match.group(1), f"entry {version} lacks '### EN'")


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


if __name__ == "__main__":
    unittest.main()
