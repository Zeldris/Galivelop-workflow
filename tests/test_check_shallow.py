"""B59: tests/check.sh stops at its start, in seconds, in a shallow clone, naming `git fetch --unshallow`."""
import shutil
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
            try:
                p = subprocess.run(["bash", str(clone / "tests" / "check.sh")], capture_output=True, text=True,
                                   timeout=waits.timeout(60))
            except subprocess.TimeoutExpired:
                self.fail("check.sh did not stop early in a shallow clone")
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertIn("is a shallow clone", p.stderr)
            self.assertIn("git fetch --unshallow", p.stderr)
            self.assertNotIn("== ", p.stdout)


if __name__ == "__main__":
    unittest.main()
