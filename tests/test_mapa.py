"""scripts/mapa-agente.py: every path (and `path#name`) the project's agent map cites must exist, in temporary projects
laid out like one that applied the workflow (.claude/gw/scripts, .claude/gw/schema, .claude/gw.json)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
BASE = {"version": "0.4.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main",
        "pushToProtected": "direct", "check": ["true"], "reviewMark": "docs/revisado.txt", "content": ["^docs/"]}
CODE_TS = """export function calcular(a: number) {
  return pasoUno(a);
}
class Turno {
  private async resolver(x: string): Promise<void> {
  }
}
const llamada = resolverOtro(1);
"""
CODE_PY = """def hacer(x):
    return x


class Servicio:
    pass
"""


class Mapa(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.work = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", str(self.work)], check=True)
        scripts = self.work / ".claude" / "gw" / "scripts"
        scripts.mkdir(parents=True)
        (self.work / ".claude" / "gw" / "schema").mkdir()
        self.script = scripts / "mapa-agente.py"
        shutil.copy2(ROOT / "scripts" / "config.py", scripts / "config.py")
        shutil.copy2(ROOT / "schema" / "gw.schema.json", self.work / ".claude" / "gw" / "schema" / "gw.schema.json")
        if (ROOT / "scripts" / "mapa-agente.py").is_file():
            shutil.copy2(ROOT / "scripts" / "mapa-agente.py", self.script)
        self.config()
        self.write("backend/src/a.ts", CODE_TS)
        self.write("tools/util.py", CODE_PY)
        self.write("AGENTS.md", "# Agents\n")
        self.write("docs/es/config.md", "# Config\n")

    def config(self, **extra):
        cfg = dict(BASE, **extra)
        self.write(".claude/gw.json", json.dumps(cfg))

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_map(self, mapa=None, rel="docs/mapa-agente.md"):
        if mapa is not None:
            self.write(rel, mapa)
        r = subprocess.run([sys.executable, str(self.script)], cwd=self.work, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_a_map_with_good_references_passes(self):
        code, out = self.run_map(
            "# Map\n\n- `backend/src/a.ts#calcular` calls `pasoUno`; method `backend/src/a.ts#resolver`; folder "
            "`backend/src/`.\n- `tools/util.py#hacer` and `tools/util.py#Servicio`\n")
        self.assertEqual(code, 0, out)
        self.assertIn("0 broken references out of 6", out)

    def test_a_missing_path_fails_with_the_line_and_the_fix(self):
        code, out = self.run_map("# Map\n\n- `tools/gone.py` does things\n")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/mapa-agente.md:3: path not found: tools/gone.py", out)
        self.assertIn("1 broken references out of 1", out)

    def test_a_missing_name_fails(self):
        code, out = self.run_map("- `tools/util.py#nope`\n")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/mapa-agente.md:1: tools/util.py does not define nope", out)

    def test_a_call_is_not_a_definition(self):
        code, out = self.run_map("- `backend/src/a.ts#resolverOtro`\n")
        self.assertEqual(code, 1, out)
        self.assertIn("does not define resolverOtro", out)

    def test_a_loose_name_after_a_path_name_is_looked_up_in_that_file(self):
        code, out = self.run_map("# Map\n\n- `backend/src/a.ts#calcular` and\n  then `pasoDos`\n")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/mapa-agente.md:3: backend/src/a.ts does not define pasoDos", out)
        self.assertEqual(self.run_map("- `anyThing` next to `backend/src/`\n")[0], 0)

    def test_prefixes_come_from_the_config(self):
        mapa = "- `b/a.ts#calcular` and `b/gone.ts`\n"
        code, out = self.run_map(mapa)
        self.assertEqual(code, 1, out)
        self.assertIn("path not found: b/a.ts", out)  # no prefix declared: `b/` is just a folder that is not there
        self.config(agentMap={"prefixes": {"b/": "backend/src/"}})
        code, out = self.run_map()
        self.assertEqual(code, 1, out)
        self.assertIn("path not found: backend/src/gone.ts", out)
        self.assertNotIn("a.ts", out.replace("1 broken", ""))
        self.assertIn("1 broken references out of 2", out)

    def test_a_prefix_key_without_the_slash_works_too(self):
        self.config(agentMap={"prefixes": {"b": "backend/src"}})
        self.assertEqual(self.run_map("- `b/a.ts#calcular`\n")[0], 0)

    def test_markdown_links_resolve_from_the_map_folder_and_the_root(self):
        code, out = self.run_map("| A | B |\n|---|---|\n| x | [`es/config.md`](es/config.md), [`AGENTS.md`](../AGENTS.md), "
                                 "[root](/AGENTS.md), [also](tools/util.py) |\n")
        self.assertEqual(code, 0, out)
        code, out = self.run_map("- [gone](es/gone.md)\n- [up](../../outside.md)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/mapa-agente.md:1: path not found: es/gone.md", out)
        self.assertIn("docs/mapa-agente.md:2: link leaves the repository: ../../outside.md", out)

    def test_urls_anchors_and_mail_links_are_ignored(self):
        code, out = self.run_map("- [site](https://example.com/a/b.md) [top](#section) [m](mailto:a@b.c) "
                                 "[ftp](ftp://x/y.txt) `https://example.com/x/y.md`\n")
        self.assertEqual(code, 0, out)
        self.assertIn("0 broken references out of 0", out)

    def test_a_link_fragment_does_not_count_and_a_title_is_allowed(self):
        code, out = self.run_map('- [c](es/config.md#heading "Title") [d](es/config.md?x=1)\n')
        self.assertEqual(code, 0, out)

    def test_globs_need_at_least_one_match(self):
        self.assertEqual(self.run_map("- `tools/*.py` and `backend/**/*.ts`\n")[0], 0)
        code, out = self.run_map("- `tools/*.sh`\n")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/mapa-agente.md:1: no file matches tools/*.sh", out)

    def test_a_missing_default_map_is_not_an_error(self):
        code, out = self.run_map()
        self.assertEqual(code, 0, out)
        self.assertIn("no agent map at docs/mapa-agente.md", out)

    def test_a_missing_declared_map_fails_closed(self):
        self.config(agentMap={"path": "docs/gone-map.md"})
        code, out = self.run_map()
        self.assertEqual(code, 1, out)
        self.assertIn("agentMap.path points to docs/gone-map.md, which does not exist", out)
        self.assertIn(".claude/gw.json", out)

    def test_the_map_can_live_elsewhere(self):
        self.config(agentMap={"path": "MAP.md"})
        code, out = self.run_map("- `tools/util.py#hacer` and `tools/gone.py`\n", rel="MAP.md")
        self.assertEqual(code, 1, out)
        self.assertIn("MAP.md:1: path not found: tools/gone.py", out)

    def test_table_rows_are_one_unit_each(self):
        code, out = self.run_map(
            "# Map\n\n| Contract | Defined | Implemented |\n|---|---|---|\n"
            "| Util | `tools/util.py#hacer` | [`AGENTS.md`](../AGENTS.md) |\n"
            "| Bad | `tools/gone.py` | `tools/util.py#nope` |\n")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/mapa-agente.md:6: path not found: tools/gone.py", out)
        self.assertIn("docs/mapa-agente.md:6: tools/util.py does not define nope", out)
        self.assertNotIn("docs/mapa-agente.md:5", out)
        self.assertIn("2 broken references out of 4", out)

    def test_words_placeholders_and_code_fences_are_not_paths(self):
        code, out = self.run_map(
            "- `and/or` `application/json` `skills/<name>/SKILL.md` `docs/{{x}}.md` `$HOME/x.md` `read/write`\n"
            "- `gw.json` and `Makefile` have no folder\n```\ntools/gone.py\n`tools/gone2.py`\n```\n")
        self.assertEqual(code, 0, out)
        self.assertIn("0 broken references out of 0", out)

    def test_a_reference_is_a_path_when_its_first_folder_exists_or_it_has_an_extension_or_a_final_slash(self):
        for ref in ("tools/gone", "gone/file.py", "gone/dir/"):
            with self.subTest(ref=ref):
                code, out = self.run_map(f"- `{ref}`\n")
                self.assertEqual(code, 1, out)
                self.assertIn(f"path not found: {ref}", out)
        self.assertEqual(self.run_map("- `gone/dir`\n")[0], 0)  # unknown folder, no extension, no slash: just words

    def test_roots_make_a_vanished_top_folder_count(self):
        self.assertEqual(self.run_map("- `vanished/thing`\n")[0], 0)
        self.config(agentMap={"roots": ["vanished"]})
        code, out = self.run_map()
        self.assertEqual(code, 1, out)
        self.assertIn("path not found: vanished/thing", out)

    def test_a_line_suffix_is_not_part_of_the_path(self):
        self.assertEqual(self.run_map("- `tools/util.py:12` and `tools/util.py:3-9`\n")[0], 0)

    def test_a_non_identifier_fragment_is_not_a_symbol(self):
        code, out = self.run_map("- `docs/es/config.md#some-heading` and `tools/util.py#L10`\n")
        self.assertEqual(code, 0, out)

    def test_an_invalid_config_fails_closed(self):
        self.config(agentMap={"path": "docs/m.md", "oops": 1})
        code, out = self.run_map("- `tools/util.py`\n")
        self.assertEqual(code, 2, out)
        self.assertIn("unknown key 'oops'", out)
        self.config(agentMap={"prefixes": {"b": "../escape"}})
        code, out = self.run_map()
        self.assertEqual(code, 2, out)
        self.assertIn("prefixes", out)

    def test_this_repos_own_map_is_clean(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "mapa-agente.py")], cwd=ROOT, capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 broken references", r.stdout)


if __name__ == "__main__":
    unittest.main()
