"""scripts/roadmap.py (D55): see or mark one roadmap row in every language. Every failing case checks the message,
not only the exit code, and that nothing was written."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

sys.dont_write_bytecode = True
SCRIPT = ROOT / "scripts" / "roadmap.py"
FILES = [
    {"path": "docs/roadmap.md", "done": "hecho", "open": ["pendiente", "en curso"]},
    {"path": "docs/roadmap.en.md", "done": "done", "open": ["pending", "in progress"]},
]
ES = """# Roadmap

## `0.6` «Medir»

| Id | Tarea | Estado |
|---|---|---|
| D55 | `roadmap.py show` con `a | b` en código y \\| escapado | pendiente |
| E27 | Otra | hecha (2026-11-11) |
| D5 | Corta | en curso |
"""
EN = """# Roadmap

## `0.6` "Measure"

| Id | Task | Status |
|---|---|---|
| D55 | `roadmap.py show` with `a | b` in code and \\| escaped | pending |
| E27 | Another | done (2026-11-11) |
| D5 | Short | in progress |
"""


class Roadmap(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-roadmap-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "-C", str(self.tmp), "init", "-q"], check=True)
        self.configure(FILES)
        self.write("docs/roadmap.md", ES)
        self.write("docs/roadmap.en.md", EN)

    def write(self, rel, text):
        (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.tmp / rel).write_text(text, encoding="utf-8")

    def read(self, rel):
        return (self.tmp / rel).read_text(encoding="utf-8")

    def configure(self, files):
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, roadmapFiles=files), indent=2) + "\n")

    def run_cli(self, *args):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.tmp), *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def assertUnchanged(self):
        self.assertEqual(self.read("docs/roadmap.md"), ES)
        self.assertEqual(self.read("docs/roadmap.en.md"), EN)

    def test_show_prints_the_row_of_each_language_with_its_section(self):
        code, out, err = self.run_cli("show", "D5")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), [
            "docs/roadmap.md:9 (`0.6` «Medir»)", "| D5 | Corta | en curso |",
            'docs/roadmap.en.md:9 (`0.6` "Measure")', "| D5 | Short | in progress |"])

    def test_list_prints_id_status_and_description_of_a_version(self):
        self.write("docs/roadmap.md", ES + "\n### Extra\n\n| Id | Tarea | Estado |\n|---|---|---|\n"
                   "| Z1 | " + "x" * 100 + " | pendiente |\n\n## `0.7` «Otra»\n\n| Id | T | E |\n|---|---|---|\n"
                   "| Q1 | fuera | pendiente |\n")
        code, out, err = self.run_cli("list", "0.6")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), [
            "D55  pendiente  `roadmap.py show` con `a | b` en código y \\| escapado",
            "E27  hecha (2026-11-11)  Otra", "D5  en curso  Corta", "Z1  pendiente  " + "x" * 80])

    def test_list_status_filters_ignoring_case(self):
        code, out, err = self.run_cli("list", "0.6", "--status", "EN CURSO")
        self.assertEqual((code, out), (0, "D5  en curso  Corta\n"), err)

    def test_list_reads_only_the_first_file(self):
        code, out, _ = self.run_cli("list", "0.6", "--status", "hecha")
        self.assertEqual(out, "E27  hecha (2026-11-11)  Otra\n")

    def test_list_unknown_version_says_how_to_find_the_sections(self):
        code, out, err = self.run_cli("list", "9.9")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("no section for version '9.9' in docs/roadmap.md", err)
        self.assertIn("grep -n '^## ' docs/roadmap.md", err)

    def test_done_marks_every_language_and_keeps_pipes_inside_code(self):
        code, out, err = self.run_cli("done", "D55", "--date", "2026-11-11", "--note", "nota", "--note", "note")
        self.assertEqual(code, 0, err)
        self.assertIn("| D55 | `roadmap.py show` con `a | b` en código y \\| escapado | hecho (2026-11-11; nota) |\n",
                      self.read("docs/roadmap.md"))
        self.assertIn("| D55 | `roadmap.py show` with `a | b` in code and \\| escaped | done (2026-11-11; note) |\n",
                      self.read("docs/roadmap.en.md"))
        self.assertEqual(len(out.splitlines()), 2)
        # Nothing else moved.
        self.assertEqual(self.read("docs/roadmap.md").replace("hecho (2026-11-11; nota)", "pendiente"), ES)

    def test_done_without_notes_writes_only_the_date(self):
        code, _, err = self.run_cli("done", "D5", "--date", "2026-01-02")
        self.assertEqual(code, 0, err)
        self.assertIn("| D5 | Corta | hecho (2026-01-02) |", self.read("docs/roadmap.md"))
        self.assertIn("| D5 | Short | done (2026-01-02) |", self.read("docs/roadmap.en.md"))

    def test_a_pipe_in_a_note_is_escaped_and_the_row_stays_findable(self):
        code, _, err = self.run_cli("done", "D5", "--date", "2026-01-02", "--note", "a|b", "--note", "c|d")
        self.assertEqual(code, 0, err)
        self.assertIn("| D5 | Corta | hecho (2026-01-02; a\\|b) |\n", self.read("docs/roadmap.md"))
        code, out, err = self.run_cli("show", "D5")
        self.assertEqual(code, 0, err)
        self.assertIn("| D5 | Short | done (2026-01-02; c\\|d) |", out)
        code, _, err = self.run_cli("done", "D5", "--date", "2026-01-03", "--force")
        self.assertEqual(code, 0, err)
        self.assertIn("| D5 | Corta | hecho (2026-01-03) |\n", self.read("docs/roadmap.md"))

    def test_the_open_status_ignores_case_and_markdown_emphasis(self):
        self.write("docs/roadmap.md", ES.replace("| pendiente |", "| Pendiente |")
                   .replace("| D5 | Corta | en curso |", "| D5 | Corta | **en curso** |"))
        self.write("docs/roadmap.en.md", EN.replace("| pending |", "| _`Pending`_ |"))
        code, _, err = self.run_cli("done", "D55", "--date", "2026-01-02")
        self.assertEqual(code, 0, err)
        code, _, err = self.run_cli("done", "D5", "--date", "2026-01-02")
        self.assertEqual(code, 0, err)  # Spanish `**en curso**`, English plain `in progress`
        self.assertIn("| D5 | Corta | hecho (2026-01-02) |", self.read("docs/roadmap.md"))

    def test_a_task_that_is_not_open_is_refused_unless_forced(self):
        code, _, err = self.run_cli("done", "E27", "--date", "2026-11-12")
        self.assertEqual(code, 1)
        self.assertIn("E27 is not open", err)
        self.assertIn("--force", err)
        self.assertUnchanged()
        code, _, err = self.run_cli("done", "E27", "--date", "2026-11-12", "--force")
        self.assertEqual(code, 0, err)
        self.assertIn("| E27 | Otra | hecho (2026-11-12) |", self.read("docs/roadmap.md"))

    def test_a_row_missing_in_one_language_writes_nothing(self):
        self.write("docs/roadmap.en.md", EN.replace("| D55 |", "| D56 |"))
        code, _, err = self.run_cli("done", "D55", "--date", "2026-11-11")
        self.assertEqual(code, 1)
        self.assertIn("docs/roadmap.en.md: no row for D55", err)
        self.assertEqual(self.read("docs/roadmap.md"), ES)

    def test_a_status_that_is_not_open_in_the_second_file_writes_nothing(self):
        self.write("docs/roadmap.en.md", EN.replace("in progress |", "discarded |"))
        code, _, err = self.run_cli("done", "D5", "--date", "2026-11-11")
        self.assertEqual(code, 1)
        self.assertIn("docs/roadmap.en.md:9: D5 is not open", err)
        self.assertEqual(self.read("docs/roadmap.md"), ES)

    def test_two_rows_for_one_id_are_refused(self):
        self.write("docs/roadmap.md", ES + "| D5 | Repetida | pendiente |\n")
        code, _, err = self.run_cli("show", "D5")
        self.assertEqual(code, 1)
        self.assertIn("2 rows for D5 (lines 9, 10)", err)

    def test_the_wrong_number_of_notes_is_refused(self):
        code, _, err = self.run_cli("done", "D55", "--note", "solo una")
        self.assertEqual(code, 1)
        self.assertIn("1 --note for 2 roadmap files", err)
        self.assertUnchanged()

    def test_a_bad_date_is_refused(self):
        code, _, err = self.run_cli("done", "D55", "--date", "11/11/2026")
        self.assertEqual(code, 1)
        self.assertIn("is not YYYY-MM-DD", err)
        self.assertUnchanged()

    def test_an_id_is_a_whole_cell_not_a_prefix(self):
        code, _, err = self.run_cli("show", "D")
        self.assertEqual(code, 1)
        self.assertIn("docs/roadmap.md: no row for D", err)

    def test_no_roadmap_files_says_how_to_turn_it_on(self):
        self.configure([])
        code, _, err = self.run_cli("show", "D55")
        self.assertEqual(code, 1)
        self.assertIn("roadmapFiles is empty", err)

    def test_a_missing_file_names_the_config_key(self):
        self.configure(FILES + [{"path": "docs/roadmap.fr.md", "done": "fait", "open": ["à faire"]}])
        code, _, err = self.run_cli("done", "D55", "--date", "2026-11-11")
        self.assertEqual(code, 1)
        self.assertIn("cannot read docs/roadmap.fr.md", err)
        self.assertUnchanged()

    def test_an_invalid_config_fails_closed(self):
        self.configure([{"path": "/abs/roadmap.md", "done": "hecho", "open": ["pendiente"]}])
        code, _, err = self.run_cli("show", "D55")
        self.assertEqual(code, 2)
        self.assertIn("roadmap", err)


if __name__ == "__main__":
    unittest.main()
