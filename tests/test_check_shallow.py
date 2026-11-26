"""B59: tests/check.sh stops at its start, in seconds, in a shallow clone, naming `git fetch --unshallow`."""
import os
import shutil
import signal
import subprocess
import tempfile
import unittest

import waits
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ShallowCheckTest(unittest.TestCase):
    def test_a_shallow_clone_stops_the_check_with_the_command_that_fixes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "shallow"
            subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{ROOT}", str(clone)], check=True)
            shutil.copy(ROOT / "tests" / "check.sh", clone / "tests" / "check.sh")
            # Own process group: on a timeout the whole check (bash and the tests it started) is killed, not only bash.
            proc = subprocess.Popen(["bash", str(clone / "tests" / "check.sh")], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, start_new_session=True)
            try:
                out, err = proc.communicate(timeout=waits.timeout(60))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                self.fail("check.sh did not stop early in a shallow clone")
            p = subprocess.CompletedProcess(proc.args, proc.returncode, out, err)
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertIn("is a shallow clone", p.stderr)
            self.assertIn("git fetch --unshallow", p.stderr)
            self.assertNotIn("== ", p.stdout)
            self.assertIn("FAILED: shallow clone", p.stdout)
            self.assertIn("CHECK FAILED", p.stdout)


if __name__ == "__main__":
    unittest.main()
