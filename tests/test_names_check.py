"""scripts/names-check.py: a Spanish name in the workflow's own files fails with its reason; English passes.
One pass case and one fail case per kind of name, in temporary folders."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("names_check", ROOT / "scripts" / "names-check.py")
names_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(names_check)


def problems(files):
    """Problems for {relative path: text} written in a temporary folder."""
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in files.items():
            path = Path(tmp) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return names_check.check_files(tmp, list(files))


class Kinds(unittest.TestCase):
    def assertFails(self, files, *fragments):
        found = problems(files)
        self.assertTrue(found, "expected a problem, got none")
        for fragment in fragments:
            self.assertTrue(any(fragment in line for line in found), f"'{fragment}' not in {found}")

    def test_path_passes(self):
        self.assertEqual(problems({"docs/es/config.md": "x"}), [])

    def test_path_fails(self):
        self.assertFails({"scripts/comprobar.py": "x = 1\n"}, "path component 'comprobar.py'", "Spanish word")

    def test_path_accent_fails(self):
        self.assertFails({"docs/configuración.md": "x"}, "accented letter")

    def test_python_function_passes(self):
        self.assertEqual(problems({"a.py": "def load_config(path):\n    return path\n"}), [])

    def test_python_function_fails(self):
        self.assertFails({"a.py": "def cargar_config():\n    pass\n"}, "function 'cargar_config'",
                         "Spanish word 'cargar'")

    def test_python_class_fails(self):
        self.assertFails({"a.py": "class Nuevo:\n    pass\n"}, "class 'Nuevo'", "Spanish word 'nuevo'")

    def test_python_argument_fails(self):
        self.assertFails({"a.py": "def f(archivo):\n    return 1\n"}, "argument 'archivo'")

    def test_python_variable_fails(self):
        self.assertFails({"a.py": "limite = 3\n"}, "variable 'limite'")

    def test_python_option_passes(self):
        text = "import argparse\np = argparse.ArgumentParser()\np.add_argument('--dry-run')\n"
        self.assertEqual(problems({"a.py": text}), [])

    def test_python_option_fails(self):
        text = "import argparse\np = argparse.ArgumentParser()\np.add_argument('--sin-notas')\n"
        self.assertFails({"a.py": text}, "command-line option 'sin-notas'")

    def test_python_subcommand_fails(self):
        text = "sub = object()\nsub.add_parser('comprobar')\n"
        self.assertFails({"a.py": text}, "subcommand 'comprobar'")

    def test_python_string_is_not_a_name(self):
        self.assertEqual(problems({"a.py": "OLD = {'comprobar.py': 'check.py'}\n"}), [])

    def test_shell_variable_passes(self):
        self.assertEqual(problems({"a.sh": "#!/usr/bin/env bash\nroot=1\nfor f in a b; do echo \"$f\"; done\n"}), [])

    def test_shell_variable_fails(self):
        self.assertFails({"a.sh": "#!/usr/bin/env bash\narchivo=1\n"}, "'archivo'")

    def test_shell_function_fails(self):
        self.assertFails({"a.sh": "#!/usr/bin/env bash\ncomprobar() {\n  :\n}\n"}, "'comprobar'")

    def test_shell_without_extension_is_read(self):
        self.assertFails({"hooks/pre-x": "#!/usr/bin/env bash\ncarpeta=1\n"}, "'carpeta'")

    def test_shell_option_label_fails(self):
        self.assertFails({"a.sh": "#!/usr/bin/env bash\ncase \"$1\" in\n  --sin-notas) :;;\nesac\n"}, "sin-notas")

    def test_js_passes(self):
        self.assertEqual(problems({"a.mjs": "const total = 1;\nfunction render(item) { return item; }\n"}), [])

    def test_js_variable_fails(self):
        self.assertFails({"a.mjs": "const archivo = 1;\n"}, "'archivo'")

    def test_js_function_fails(self):
        self.assertFails({"a.js": "function cargarTodo() {}\n"}, "'cargarTodo'", "Spanish word 'cargar'")

    def test_json_key_passes(self):
        self.assertEqual(problems({"schema/a.json": '{"protectedBranch": "main"}'}), [])

    def test_json_key_fails(self):
        self.assertFails({"schema/a.json": '{"rama": "main"}'}, "JSON key 'rama'")

    def test_json_outside_workflow_dirs_is_not_read(self):
        self.assertEqual(problems({"other/a.json": '{"rama": "main"}'}), [])

    def test_css_variable_passes(self):
        self.assertEqual(problems({"a.css": ":root { --main-color: red; }\n"}), [])

    def test_css_variable_fails(self):
        self.assertFails({"a.css": ":root { --archivo-color: red; }\n"}, "CSS variable 'archivo-color'")

    def test_accent_in_a_name_fails(self):
        self.assertFails({"a.py": "def sección():\n    pass\n"}, "accented letter")

    def test_documents_for_people_are_not_read(self):
        self.assertEqual(problems({"docs/a.md": "# Cargar el archivo\n"}), [])

    def test_installed_copy_is_skipped(self):
        self.assertEqual(problems({".claude/gw/scripts/a.py": "def cargar():\n    pass\n"}), [])

    def test_english_look_alikes_pass(self):
        text = "def final(real, base, total, error, color, plan, local):\n    return real\n"
        self.assertEqual(problems({"a.py": text}), [])


class Exceptions(unittest.TestCase):
    def test_every_exception_has_a_reason(self):
        for kind, entries in names_check.EXCEPTIONS.items():
            for name, reason in entries.items():
                self.assertTrue(reason and len(reason) > 20, f"{kind} '{name}' needs a reason")

    def test_path_exception_is_accepted(self):
        name = "docs/records/x-nuevo.md"
        with unittest.mock.patch.dict(names_check.EXCEPTIONS["path"], {name: "historic, for the test"}):
            self.assertEqual(problems({name: "x"}), [])

    def test_name_exception_is_accepted(self):
        with unittest.mock.patch.dict(names_check.EXCEPTIONS["name"], {"archivo_viejo": "legacy, for the test"}):
            self.assertEqual(problems({"a.py": "archivo_viejo = 1\n"}), [])

    def test_unused_exception_is_reported_in_the_repo(self):
        with unittest.mock.patch.dict(names_check.EXCEPTIONS["name"], {"nothing_here_ever": "stale, for the test"}):
            found = names_check.check_files(ROOT, [])
        self.assertTrue(any("'nothing_here_ever'" in line and "remove the entry" in line for line in found), found)


class Repo(unittest.TestCase):
    def test_the_repo_passes(self):
        out = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "names-check.py")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("names-check: OK", out.stdout)


if __name__ == "__main__":
    unittest.main()
