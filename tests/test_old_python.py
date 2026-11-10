"""tests/old-python.sh (E22): the oldest Python older than `python3` compiles the sources and runs the tests of the
change. The interpreters are stubs named in GW_OLD_PYTHONS; every failing case checks the message, not only the exit
code."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tests" / "old-python.sh"
# The minor of `python3`, which the script compares with: not sys.version_info, as check.sh also runs these tests on
# the older Python.
CURRENT = int(subprocess.run(["python3", "-c", "import sys; print(sys.version_info[1])"],
                             capture_output=True, text=True, check=True).stdout)

STUB = """#!/usr/bin/env bash
for a in "$@"; do
  case "$a" in *version_info*) echo "3 {minor}"; exit 0 ;; esac
done
kind=unittest
for a in "$@"; do case "$a" in *"compile("*) kind=compile ;; esac; done
if [ "$kind" = unittest ]; then echo "unittest $*" >> "{log}"; else echo compile >> "{log}"; fi
[ "${{STUB_FAIL:-}}" = "$kind" ] && exit 1
exit 0
"""


@unittest.skipIf(CURRENT <= 9, "needs a python3 newer than the stubs (3.7 and 3.9)")
class OldPython(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-old-python-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.log = self.tmp / "calls.log"

    def stub(self, name, minor):
        path = self.tmp / name
        path.write_text(STUB.format(minor=minor, log=self.log))
        path.chmod(0o755)
        return str(path)

    def run_sh(self, candidates, *files, fail=""):
        env = dict(os.environ, GW_OLD_PYTHONS=candidates, STUB_FAIL=fail)
        r = subprocess.run(["bash", str(SCRIPT), *files], capture_output=True, text=True, env=env, cwd=str(self.tmp))
        calls = self.log.read_text().splitlines() if self.log.exists() else []
        return r.returncode, r.stdout + r.stderr, calls

    def test_oldest_supported_runs_the_tests_of_the_change(self):
        cands = " ".join([self.stub("py37", 7), self.stub("py310", 10), self.stub("py39", 9), "no-such-python"])
        code, out, calls = self.run_sh(cands, "scripts/tests-for.py")
        self.assertEqual(code, 0, out)
        self.assertIn("py39 (3.9)", out)  # 3.7 is under the floor; 3.9 is older than 3.10
        self.assertEqual(calls[0], "compile")
        self.assertEqual(len(calls), 2, calls)
        self.assertIn("tests/test_tests_for.py", calls[1])
        # testMap also asks for the hook suites on any script; on the older Python they run only when they changed.
        self.assertNotIn("test_hooks.py", calls[1])

    def test_a_changed_hook_suite_runs(self):
        code, out, calls = self.run_sh(self.stub("py39", 9), "tests/test_hooks.py")
        self.assertEqual(code, 0, out)
        self.assertIn("tests/test_hooks.py", calls[-1])

    def test_failures_fail(self):
        py = self.stub("py39", 9)
        code, out, calls = self.run_sh(py, "scripts/tests-for.py", fail="unittest")
        self.assertEqual(code, 1, out)
        self.assertTrue(calls[-1].startswith("unittest"), calls)
        code, out, calls = self.run_sh(py, "README.md", fail="compile")
        self.assertEqual(code, 1, out)
        self.assertIn("the change calls for no tests", out)

    def test_no_older_python_only_warns(self):
        cands = " ".join([self.stub("py37", 7), self.stub("same", CURRENT)])
        code, out, calls = self.run_sh(cands, "scripts/tests-for.py")
        self.assertEqual(code, 0, out)
        self.assertIn("warning: no Python older than 3.%d" % CURRENT, out)
        self.assertEqual(calls, [])

    def test_off_skips(self):
        code, out, calls = self.run_sh("off", "scripts/tests-for.py")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped (GW_OLD_PYTHONS=off)", out)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
