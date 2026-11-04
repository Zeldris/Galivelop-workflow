"""scripts/tests-after-main.py: a TestCase defined after the unittest.main() call fails with file, line and the fix."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "tests-after-main.py"

CLEAN = '''import unittest


class A(unittest.TestCase):
    def test_a(self):
        pass


if __name__ == "__main__":
    unittest.main()
'''
INSIDE_IF = '''import unittest


class A(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()

    class Late(unittest.TestCase):
        def test_late(self):
            pass
'''
OUTSIDE_IF = '''import unittest


class A(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()


class Late(unittest.TestCase):
    def test_late(self):
        pass
'''
FROM_IMPORT = '''from unittest import TestCase, main


class A(TestCase):
    pass


if __name__ == "__main__":
    main()


class Late(TestCase):
    pass
'''
INHERITED = '''import unittest as ut


class A(ut.TestCase):
    pass


ut.main(exit=False)


class Late(A):
    pass
'''
NO_MAIN = '''import unittest


class A(unittest.TestCase):
    pass


class B(unittest.TestCase):
    pass
'''
HELPER_AFTER = '''import unittest


class A(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()

class Helper:
    pass


def helper():
    pass
'''
MAIN_IN_FUNCTION = '''import unittest


def run():
    unittest.main()


class A(unittest.TestCase):
    pass
'''
SYNTAX = "import unittest\n\nclass A(unittest.TestCase:\n    pass\n"


class TestsAfterMain(unittest.TestCase):
    def run_on(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test_x.py"
            f.write_bytes(source if isinstance(source, bytes) else source.encode())
            r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(f)], capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr, f.name

    def assertFlagged(self, source, cls, line):
        code, out, name = self.run_on(source)
        self.assertEqual(code, 1, out)
        self.assertIn(f"{name}:{line}: class {cls} is defined after the unittest.main() call", out)
        self.assertIn("move it above", out)

    def test_clean_file_passes(self):
        code, out, _ = self.run_on(CLEAN)
        self.assertEqual(code, 0, out)

    def test_class_after_main_inside_the_if(self):
        self.assertFlagged(INSIDE_IF, "Late", 11)

    def test_class_after_main_outside_the_if(self):
        self.assertFlagged(OUTSIDE_IF, "Late", 12)

    def test_main_imported_from_unittest(self):
        self.assertFlagged(FROM_IMPORT, "Late", 12)

    def test_aliased_module_and_inherited_case(self):
        self.assertFlagged(INHERITED, "Late", 11)

    def test_file_without_main_passes(self):
        code, out, _ = self.run_on(NO_MAIN)
        self.assertEqual(code, 0, out)

    def test_non_test_code_after_main_passes(self):
        code, out, _ = self.run_on(HELPER_AFTER)
        self.assertEqual(code, 0, out)

    def test_main_inside_a_function_is_not_a_main_call(self):
        code, out, _ = self.run_on(MAIN_IN_FUNCTION)
        self.assertEqual(code, 0, out)

    def test_syntax_error_fails_with_reason_and_line(self):
        code, out, name = self.run_on(SYNTAX)
        self.assertEqual(code, 1, out)
        self.assertIn(f"{name}:3: cannot parse the test file", out)
        self.assertIn("fix the syntax error", out)

    def test_undecodable_file_fails_with_reason(self):
        code, out, name = self.run_on(b"\xff\xfe\x00 not python \x80\n")
        self.assertEqual(code, 1, out)
        self.assertIn(f"{name}:", out)
        self.assertIn("cannot", out)

    def test_missing_file_fails_with_reason(self):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "/nonexistent/test_y.py"], capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot read the test file", r.stderr)

    def test_discovers_tracked_test_files_and_passes_without_any(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", tmp], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            (Path(tmp) / "test_late.py").write_text(OUTSIDE_IF)
            subprocess.run(["git", "-C", tmp, "add", "test_late.py"], check=True)
            r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", tmp], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("test_late.py:12: class Late", r.stderr)

    def test_this_repo_is_clean(self):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(ROOT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
