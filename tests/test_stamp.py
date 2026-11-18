"""stamp.py (B44, B45): what a version stamp changes in a diff, and nothing else."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply  # noqa: E402
import stamp  # noqa: E402


def diff(*lines):
    return "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n" + "\n".join(lines) + "\n"


class Stamp(unittest.TestCase):
    def test_header_pattern_agrees_with_apply(self):
        self.assertEqual(stamp.HEADER.pattern, apply.HEADER.pattern)

    def test_header_and_version_keys_are_stamp_lines(self):
        self.assertEqual(stamp.normal("# galivelop-workflow v0.8.0"), "# galivelop-workflow vX")
        self.assertEqual(stamp.normal('  "version": "0.8.0",'), '  "version": "X",')
        self.assertEqual(stamp.normal("  version: 0.8.0"), "  version: X")
        self.assertIsNone(stamp.normal("version = compute()"))
        self.assertIsNone(stamp.normal("x = 1"))

    def test_only_stamp_pairs(self):
        self.assertTrue(stamp.only_stamp(["# galivelop-workflow v0.8.0"], ["# galivelop-workflow v0.8.1"]))
        self.assertFalse(stamp.only_stamp(["# galivelop-workflow v0.8.0"], ["# other v0.8.1"]))
        self.assertFalse(stamp.only_stamp([], ["# galivelop-workflow v0.8.1"]))

    def test_stamp_diff_counts(self):
        head = ("-# galivelop-workflow v0.8.0", "+# galivelop-workflow v0.8.1")
        self.assertEqual(stamp.stamp_diff(diff(*head)), (2, 0))
        self.assertEqual(stamp.stamp_diff(diff(*head, "-x = 1", "+x = 2", "+y = 3")), (2, 3))
        self.assertEqual(stamp.stamp_diff(diff("-a", "+b")), (0, 2))


if __name__ == "__main__":
    unittest.main()
