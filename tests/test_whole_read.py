"""PreToolUse hook: scripts/whole-read.py (B26), in a temporary project laid out like one that applied the workflow,
run the way Claude Code runs a hook: the event JSON on stdin, the answer on stdout with exit 0. A warning is
`additionalContext`; "no opinion" is no output at all. Every warning case checks the text, not only the exit code.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT, Project

SCRIPT = "whole-read.py"
LIMIT = 1000


class Base(unittest.TestCase):
    cfg = {"wholeReadWarnBytes": LIMIT}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-whole-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Project(self.tmp, config=self.cfg, hooks=())
        self.scripts = self.p.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        (self.p.work / "docs" / "records").mkdir(parents=True, exist_ok=True)

    def write_config(self, extra):
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **extra)))

    def put(self, rel, size):
        path = self.p.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x" * size)
        return path

    def read(self, path, **tool_input):
        event = {"hook_event_name": "PreToolUse", "cwd": str(self.p.work), "tool_name": "Read",
                 "tool_input": dict({"file_path": str(path)}, **tool_input)}
        return self.raw(json.dumps(event))

    def raw(self, text):
        code, out = self.p.run("python3", str(self.scripts / SCRIPT), stdin=text)
        self.assertEqual(code, 0, out)
        return out

    def warning(self, out):
        data = json.loads(out)
        self.assertEqual(list(data), ["hookSpecificOutput"], out)
        spec = data["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", spec, "it warns, it never decides")
        return spec["additionalContext"]


class Warns(Base):
    def test_log_over_the_threshold_names_size_and_fix(self):
        text = self.warning(self.read(self.put("docs/log.md", LIMIT + 1)))
        for part in ("docs/log.md is 1001 bytes", "wholeReadWarnBytes 1000", "recover.py --state", "offset and limit"):
            self.assertIn(part, text)

    def test_record_over_the_threshold(self):
        text = self.warning(self.read(self.put("docs/records/retro-x.md", LIMIT + 5)))
        self.assertIn("docs/records/retro-x.md is 1005 bytes", text)
        self.assertIn("grep -n", text)

    def test_relative_path_resolves_against_cwd(self):
        self.put("docs/log.md", LIMIT + 1)
        self.assertIn("1001 bytes", self.warning(self.read("docs/log.md")))

    def test_custom_log_and_records_dir(self):
        self.write_config(dict(self.cfg, log="notes/log.md", recordsDir="reports"))
        self.assertIn("notes/log.md", self.warning(self.read(self.put("notes/log.md", LIMIT + 1))))
        self.assertIn("reports/a.md", self.warning(self.read(self.put("reports/a.md", LIMIT + 1))))
        self.assertEqual(self.read(self.put("docs/log.md", LIMIT + 1)), "")  # no longer the log

    def test_whole_read_paths_add_files_and_folders_to_the_watched_ones(self):
        self.write_config(dict(self.cfg, wholeReadPaths=["docs/notes/", "docs/one.md"]))
        self.assertIn("docs/notes/a.md is 1001 bytes", self.warning(self.read(self.put("docs/notes/a.md", LIMIT + 1))))
        self.assertIn("docs/one.md is 1001 bytes", self.warning(self.read(self.put("docs/one.md", LIMIT + 1))))
        self.assertEqual(self.read(self.put("docs/notes-old/a.md", LIMIT + 1)), "")  # a folder only with its /
        self.assertEqual(self.read(self.put("docs/one.md.bak", LIMIT + 1)), "")
        self.assertIn("docs/log.md", self.warning(self.read(self.put("docs/log.md", LIMIT + 1))))  # still watched

    def test_whole_read_skip_extensions_replace_the_default_list(self):
        self.write_config(dict(self.cfg, wholeReadSkipExtensions=[".SVG", ".md"]))
        self.assertEqual(self.read(self.put("docs/records/a.svg", LIMIT * 5)), "")
        self.assertEqual(self.read(self.put("docs/records/a.MD", LIMIT * 5)), "")
        self.assertIn("a.png is 5000 bytes", self.warning(self.read(self.put("docs/records/a.png", LIMIT * 5))))

    def test_bad_new_keys_fall_back_to_the_defaults(self):
        self.write_config(dict(self.cfg, wholeReadSkipExtensions="png", wholeReadPaths=[3]))
        self.assertEqual(self.read(self.put("docs/records/a.png", 30000)), "")  # an invalid config gives every default, the list included
        self.assertEqual(self.read(self.put("docs/notes/a.md", 30000)), "")  # nothing extra is watched
        self.assertIn("30000 bytes", self.warning(self.read(self.put("docs/records/b.md", 30000))))

    def test_missing_key_uses_the_default_20000(self):
        self.write_config({})
        self.assertEqual(self.read(self.put("docs/log.md", 19999)), "")
        self.assertIn("20001 bytes", self.warning(self.read(self.put("docs/log.md", 20001))))


class Silent(Base):
    def test_at_or_under_the_threshold(self):
        self.assertEqual(self.read(self.put("docs/log.md", LIMIT)), "")
        self.assertEqual(self.read(self.put("docs/records/r.md", 10)), "")

    def test_offset_or_limit_is_a_partial_read(self):
        path = self.put("docs/log.md", LIMIT * 5)
        self.assertEqual(self.read(path, offset=10), "")
        self.assertEqual(self.read(path, limit=50), "")
        self.assertIn("5000 bytes", self.warning(self.read(path, offset=0, limit=None)))

    def test_other_paths_are_not_watched(self):
        self.assertEqual(self.read(self.put("docs/notes.md", LIMIT * 5)), "")
        self.assertEqual(self.read(self.put("docs/records-old/a.md", LIMIT * 5)), "")

    def test_pages_is_a_partial_read(self):
        self.assertEqual(self.read(self.put("docs/log.md", LIMIT * 5), pages="1-2"), "")

    def test_images_pdf_and_notebooks_are_not_watched(self):
        for name in ("a.png", "b.pdf", "c.ipynb"):
            self.assertEqual(self.read(self.put("docs/records/" + name, LIMIT * 5)), "")

    def test_log_is_counted_in_characters_like_logSize(self):
        path = self.p.work / "docs" / "log.md"
        path.write_text("\u00e1" * 600)  # 1200 bytes, 600 characters: under the limit of logSize
        self.assertEqual(self.read(path), "")
        path.write_text("\u00e1" * 1001)  # over in characters too
        self.assertIn("2002 bytes", self.warning(self.read(path)))
        rec = self.p.work / "docs" / "records" / "r.md"
        rec.write_text("\u00e1" * 600)  # records stay in bytes
        self.assertIn("1200 bytes", self.warning(self.read(rec)))

    def test_zero_turns_it_off(self):
        self.write_config({"wholeReadWarnBytes": 0})
        self.assertEqual(self.read(self.put("docs/log.md", LIMIT * 5)), "")

    def test_unreadable_or_missing_file(self):
        self.assertEqual(self.read(self.p.work / "docs" / "handoff.md"), "")  # does not exist
        self.assertEqual(self.read(self.p.work / "docs" / "records"), "")  # a folder: size is not content

    def test_other_tools_and_bad_events(self):
        path = self.put("docs/log.md", LIMIT * 5)
        event = {"cwd": str(self.p.work), "tool_name": "Grep", "tool_input": {"file_path": str(path)}}
        self.assertEqual(self.raw(json.dumps(event)), "")
        for bad in ("not json", "[]", json.dumps({"tool_name": "Read"}),
                    json.dumps({"tool_name": "Read", "tool_input": {"file_path": 3}})):
            self.assertEqual(self.raw(bad), "")

    def test_invalid_config_falls_back_to_the_default(self):
        (self.p.work / ".claude" / "gw.json").write_text("{not json")
        self.assertEqual(self.read(self.put("docs/handoff.md", 5000)), "")
        self.assertIn("30000 bytes", self.warning(self.read(self.put("docs/handoff.md", 30000))))


if __name__ == "__main__":
    unittest.main()
