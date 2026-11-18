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
        self.assertEqual(stamp.normal('  "version": "0.8.0",', "templates/gw.json"), '  "version": "X",')
        self.assertEqual(stamp.normal('  "version": "0.8.0"', ".claude-plugin/plugin.json"), '  "version": "X"')
        self.assertEqual(stamp.normal("  version: 0.8.0", "skills/x/SKILL.md"), "  version: X")
        self.assertEqual(stamp.normal("<!-- galivelop-workflow v0.8.0 -->"), "<!-- galivelop-workflow vX -->")
        self.assertEqual(stamp.normal("// galivelop-workflow v0.8.0"), "// galivelop-workflow vX")
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

    def test_diff_lines_that_look_like_file_headers_inside_a_hunk_are_changes(self):
        text = diff("-# galivelop-workflow v0.8.0", "--- drop table users", "+# galivelop-workflow v0.8.1")
        self.assertEqual(stamp.stamp_diff(text), (2, 1))  # `-- drop table users` (shown `--- …`) is a deleted line
        self.assertFalse(stamp.only_stamp(["# galivelop-workflow v0.8.0", "-- drop table users"], ["# galivelop-workflow v0.8.1"]))
        self.assertEqual(stamp.stamp_diff(diff("-a", "+++ b")), (0, 2))

    def test_version_keys_count_only_in_the_files_version_py_stamps(self):
        line = '  "version": "4.17.20",'
        self.assertIsNone(stamp.normal(line))
        self.assertIsNone(stamp.normal(line, "package.json"))
        self.assertIsNone(stamp.normal("  version: 1.2.3", "docs/notes.md"))
        self.assertFalse(stamp.only_stamp(['  "version": "4.17.20",'], ['  "version": "4.17.21",'], "package.json"))
        self.assertTrue(stamp.only_stamp(['  "version": "4.17.20",'], ['  "version": "4.17.21",'], "templates/gw.json"))
        self.assertEqual(stamp.stamp_diff(diff('-  "version": "1.0.0",', '+  "version": "1.0.1",'), "package.json"), (0, 2))
        self.assertEqual(stamp.stamp_diff(diff('-  "version": "1.0.0",', '+  "version": "1.0.1",'), "gw.json"), (2, 0))

    def test_the_header_must_be_a_comment(self):
        self.assertIsNone(stamp.normal('MIN = "galivelop-workflow v0.8.0"'))
        self.assertFalse(stamp.only_stamp(['MIN = "galivelop-workflow v0.8.0"'], ['MIN = "galivelop-workflow v0.8.1"']))


if __name__ == "__main__":
    unittest.main()
