"""PreToolUse hook: scripts/whole-read.py (B26, E58), in a temporary project laid out like one that applied the workflow,
run the way Claude Code runs a hook: the event JSON on stdin, the answer on stdout with exit 0. A warning is
`additionalContext`; "no opinion" is no output at all. Every warning case checks the text, not only the exit code.
"""
import json
import os
import shutil
import time
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT, Project

SCRIPT = "whole-read.py"
LIMIT = 1000


class Base(unittest.TestCase):
    cfg = {"wholeReadWarnBytes": LIMIT, "wholeReadRepeatOnly": False}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-whole-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Project(self.tmp, config=self.cfg, hooks=())
        self.scripts = self.p.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        (self.p.work / "docs" / "records").mkdir(parents=True, exist_ok=True)
        self.state = self.tmp / "state"  # TMPDIR of the hook: where it keeps the session's reads
        self.state.mkdir()

    def write_config(self, extra):
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **extra)))

    def put(self, rel, size):
        path = self.p.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x" * size)
        return path

    def read(self, path, session=None, **tool_input):
        event = {"hook_event_name": "PreToolUse", "cwd": str(self.p.work), "tool_name": "Read",
                 "tool_input": dict({"file_path": str(path)}, **tool_input)}
        if session:
            event["session_id"] = session
        return self.raw(json.dumps(event))

    def bash(self, command, session=None, cwd=None):
        event = {"hook_event_name": "PreToolUse", "cwd": str(cwd or self.p.work), "tool_name": "Bash",
                 "tool_input": {"command": command}}
        if session:
            event["session_id"] = session
        return self.raw(json.dumps(event))

    def raw(self, text):
        code, out = self.p.run("python3", str(self.scripts / SCRIPT), stdin=text, env={"TMPDIR": str(self.state)})
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
        # an invalid config gives every default, the list and wholeReadRepeatOnly (true) included: read twice
        for _ in range(2):
            self.assertEqual(self.read(self.put("docs/records/a.png", 30000), session="s1"), "")
            self.assertEqual(self.read(self.put("docs/notes/a.md", 30000), session="s1"), "")  # nothing extra
        path = self.put("docs/records/b.md", 30000)
        self.assertEqual(self.read(path, session="s1"), "")
        self.assertIn("30000 bytes", self.warning(self.read(path, session="s1")))

    def test_missing_key_uses_the_default_20000(self):
        self.write_config({"wholeReadRepeatOnly": False})
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
        for _ in range(2):
            self.assertEqual(self.read(self.put("docs/handoff.md", 5000), session="s1"), "")
        path = self.put("docs/handoff.md", 30000)
        self.assertEqual(self.read(path, session="s1"), "")  # the default warns only on a repeat
        self.assertIn("30000 bytes", self.warning(self.read(path, session="s1")))


class Bash(Base):
    def test_cat_of_the_log_warns_and_names_the_program(self):
        self.put("docs/log.md", LIMIT + 1)
        text = self.warning(self.bash("cat docs/log.md"))
        for part in ("docs/log.md is 1001 bytes", "this `cat` takes it whole", "recover.py --state"):
            self.assertIn(part, text)

    def test_whole_readers_and_redirection(self):
        self.put("docs/records/r.md", LIMIT + 1)
        for command in ("cat -n docs/records/r.md", "nl docs/records/r.md | less", "less docs/records/r.md",
                        "sed 's/a/b/' docs/records/r.md", "sed -e 's/a/b/' docs/records/r.md", "cat < docs/records/r.md",
                        "git status && cat docs/records/r.md; echo done", "echo $(cat docs/records/r.md)",
                        "FOO=1 cat docs/records/r.md 2>&1", "cat docs/records/*.md", "/bin/cat docs/records/r.md"):
            self.assertIn("docs/records/r.md is 1001 bytes", self.warning(self.bash(command)), command)

    def test_partial_readers_say_nothing(self):
        self.put("docs/records/r.md", LIMIT * 5)
        for command in ("grep -n x docs/records/r.md", "head -50 docs/records/r.md", "tail docs/records/r.md",
                        "sed -n '1,40p' docs/records/r.md", "sed -ne '/x/p' docs/records/r.md", "sed 10q docs/records/r.md",
                        "sed -i 's/a/b/' docs/records/r.md", "sed --quiet p docs/records/r.md", "wc -l docs/records/r.md",
                        "bat -r 1:10 docs/records/r.md", "cat > docs/records/r.md", "echo docs/records/r.md",
                        "cat 'docs/records/r.md"):  # an open quote: the command cannot be split
            self.assertEqual(self.bash(command), "", command)

    def test_output_to_a_filter_or_a_file_is_no_whole_read(self):
        self.put("docs/records/r.md", LIMIT * 5)
        for command in ("cat docs/records/r.md | head -5", "cat docs/records/r.md | grep x", "cat docs/records/r.md > o",
                        "sed 's/a/b/' docs/records/r.md > out", "cat docs/records/r.md >/dev/null",
                        "cat docs/records/r.md &> o", "cat docs/records/r.md | cat -n | head", "nl -b a docs/records/r.md >o"):
            self.assertEqual(self.bash(command), "", command)
        for command in ("cat docs/records/r.md | cat -n", "cat docs/records/r.md 2>/dev/null",
                        "cat docs/records/r.md >&2", "cat docs/records/r.md || true", "nl -b a docs/records/r.md",
                        "sed -l 80 's/a/b/' docs/records/r.md"):
            self.assertIn("5000 bytes", self.warning(self.bash(command)), command)

    def test_a_cd_inside_a_subshell_ends_with_it(self):
        self.put("docs/records/log.md", LIMIT + 1)
        self.put("docs/log.md", LIMIT + 2)
        text = self.warning(self.bash("(cd records && ls); cat log.md", cwd=self.p.work / "docs"))
        self.assertIn("log.md is 1002 bytes", text)
        self.assertNotIn("records/log.md", text)

    def test_heredoc_bodies_are_not_commands(self):
        self.put("docs/log.md", LIMIT * 5)
        self.assertEqual(self.bash("cat > notes.txt <<'EOF'\ncat docs/log.md\nEOF\necho ok"), "")
        self.assertEqual(self.bash("python3 - <<EOF\nprint(open('docs/log.md').read())\ncat docs/log.md\nEOF"), "")
        self.assertIn("5000 bytes", self.warning(self.bash("cat > n.txt <<-EOF\n\tx\n\tEOF\ncat docs/log.md")))
        self.assertIn("5000 bytes", self.warning(self.bash("tr a b <<< x; cat docs/log.md")))  # a here-string ends nothing
        self.assertEqual(self.bash("cat > n.txt <<\\EOF\ncat docs/log.md\nEOF\necho ok"), "")

    def test_cd_moves_the_folder_paths_resolve_against(self):
        self.put("docs/log.md", LIMIT + 1)
        self.assertIn("docs/log.md", self.warning(self.bash("cd docs && cat log.md")))
        self.assertIn("docs/log.md", self.warning(self.bash("cat docs/log.md", cwd=self.p.work)))
        self.assertEqual(self.bash("cat log.md"), "")  # no such file at the root

    def test_unwatched_or_small_files_say_nothing(self):
        self.put("docs/notes.md", LIMIT * 5)
        self.put("docs/log.md", LIMIT)
        self.assertEqual(self.bash("cat docs/notes.md docs/log.md"), "")

    def test_two_watched_files_give_two_notes(self):
        self.put("docs/log.md", LIMIT + 1)
        self.put("docs/records/r.md", LIMIT + 2)
        text = self.warning(self.bash("cat docs/log.md docs/records/r.md"))
        self.assertIn("docs/log.md is 1001 bytes", text)
        self.assertIn("docs/records/r.md is 1002 bytes", text)


class Ranges(Base):  # E85: a long range of the log or a roadmap file read by Bash warns like a whole read
    ROADMAPS = [{"path": "docs/roadmap.md", "done": "hecho", "open": ["pendiente"]},
                {"path": "docs/roadmap.en.md", "done": "done", "open": ["pending"]}]
    cfg = {"wholeReadWarnBytes": LIMIT, "wholeReadRepeatOnly": False, "roadmapFiles": ROADMAPS}

    def setUp(self):
        super().setUp()
        self.write_config(self.cfg)
        self.log = self.put("docs/log.md", LIMIT + 1)
        self.road = self.put("docs/roadmap.md", LIMIT + 2)

    def test_a_long_range_of_the_log_names_the_state_command(self):
        for command in ("sed -n 1,80p docs/log.md", "sed -n '1,80p' docs/log.md", "head -n 80 docs/log.md",
                        "head -80 docs/log.md", "head -n80 docs/log.md", "sed -ne 1,80p docs/log.md", "sed -n -e1,80p docs/log.md", "sed -ne1,80p docs/log.md", "head --lines=80 docs/log.md",
                        "head --lines 80 docs/log.md", "sed -n -e 1,80p docs/log.md", "sed --quiet 1,80p docs/log.md",
                        "sed -n 1,\\$p docs/log.md", "sed -n p docs/log.md", "sed -n 1,41p docs/log.md"):
            text = self.warning(self.bash(command))
            for part in ("docs/log.md is 1001 bytes", "wholeReadShortLines 40", "recover.py --state"):
                self.assertIn(part, text, command)
            self.assertNotIn("takes it whole", text, command)
        self.assertIn("reads 80 lines of it", self.warning(self.bash("sed -n 1,80p docs/log.md")))
        self.assertIn("to the end", self.warning(self.bash("sed -n p docs/log.md")))

    def test_a_long_range_of_a_roadmap_file_names_roadmap_show(self):
        self.put("docs/roadmap.en.md", LIMIT + 3)
        for command in ("sed -n 1,80p docs/roadmap.md", "head -n 80 docs/roadmap.md", "head -100 docs/roadmap.md",
                        "cat docs/roadmap.md", "sed 's/a/b/' docs/roadmap.md"):
            text = self.warning(self.bash(command))
            self.assertIn("docs/roadmap.md is 1002 bytes", text, command)
            self.assertIn("roadmap.py show <id>", text, command)
            self.assertNotIn("recover.py", text, command)
        self.assertIn("docs/roadmap.en.md is 1003 bytes", self.warning(self.bash("sed -n 1,80p docs/roadmap.en.md")))
        self.assertIn("roadmap.py show", self.warning(self.read(self.road)))  # a whole Read too

    def test_short_ranges_and_other_readers_are_silent(self):
        self.assertIn("1001 bytes", self.warning(self.bash("sed -n 1,41p docs/log.md")))  # the same file, a longer range
        for command in ("sed -n 1,20p docs/log.md", "head -n 20 docs/log.md", "head -20 docs/log.md",
                        "head docs/log.md", "sed -n 1,40p docs/roadmap.md", "sed -n 5p docs/roadmap.md",
                        "sed -n 80,60p docs/roadmap.md", "tail -n 80 docs/log.md", "head -c 5000 docs/log.md",
                        "sed -n '/a/,/b/p' docs/log.md", "sed -n '1,80p;90q' docs/log.md", "sed -i 1,80p docs/log.md", "sed -nie 1,80p docs/log.md", "sed -ne 1,80p -e 90p docs/log.md", "sed -ne",
                        "head -n 1k docs/log.md", "head -n -5 docs/log.md", "head -n", "sed -n", "sed -n 1,80p",
                        "grep -n x docs/log.md", "ls docs", "echo sed -n 1,80p docs/log.md", "sed -n 1,80p docs/nope.md"):
            self.assertEqual(self.bash(command), "", command)

    def test_a_file_piped_into_a_range_command_warns_with_that_commands_lines(self):  # E85
        for command in ("cat docs/log.md | head -n 200", "cat docs/log.md | sed -n 1,200p", "cat docs/log.md | head -200",
                        "cat < docs/log.md | head -n 200", "cat docs/log.md | head --lines=200"):
            text = self.warning(self.bash(command))
            for part in ("docs/log.md is 1001 bytes", "reads 200 lines of it", "recover.py --state"):
                self.assertIn(part, text, command)
        self.assertIn("to the end", self.warning(self.bash("cat docs/log.md | sed -n p")))
        self.assertIn("docs/roadmap.md", self.warning(self.bash("cat docs/roadmap.md | head -n 200")))

    def test_piped_range_forms_of_the_e85_review_warn_with_a_clean_label(self):  # D173
        for command in ("cat docs/log.md | head -n +200", "cat docs/log.md | head -n200 -", "cat docs/log.md | head -n 200 | cat -n",
                        "cat docs/log.md | sed -n 1,500p | less", "sed -n 1,5000p docs/log.md | head -n 200",
                        "cat docs/log.md | cat | head -n 200", "cat < docs/log.md | head -n 200"):
            text = self.warning(self.bash(command))
            for part in ("docs/log.md is 1001 bytes", "reads 200 lines of it") if "500p" not in command else ("docs/log.md is 1001 bytes", "reads 500 lines of it"):
                self.assertIn(part, text, command)
        text = self.warning(self.bash("cat < docs/log.md | head -n 200"))
        self.assertIn("this `cat < docs/log.md | head -n 200`", text)
        self.assertNotIn("  ", text.split("this `", 1)[1].split("`", 1)[0])

    def test_a_piped_range_is_not_applied_to_several_files_or_to_a_sink_after_it(self):  # D173
        for command in ("cat docs/log.md docs/roadmap.md | head -n 200", "cat docs/log.md | head -n 200 | tee out.txt",
                        "cat docs/log.md | head -n 200 | wc -l", "cat docs/log.md | head -n 200 other.txt"):
            self.assertEqual(self.bash(command), "", command)

    def test_a_piped_range_that_is_short_or_not_the_files_own_stays_silent(self):  # E85
        for command in ("cat docs/log.md | head -n 20", "cat docs/log.md | head", "cat docs/log.md | head -n 200 other.txt",
                        "cat docs/log.md | head -n 200 > out.txt", "cat docs/log.md | head -n 200 | wc -l",
                        "cat docs/log.md | head -c 500", "cat docs/log.md | head -n -5", "cat docs/log.md | grep x",
                        "cat docs/log.md | head -n 200 < other.txt", "cat docs/log.md > out.txt | head -n 200"):
            self.assertEqual(self.bash(command), "", command)

    def test_the_threshold_is_the_key_and_zero_warns_every_range(self):
        self.write_config(dict(self.cfg, wholeReadShortLines=100))
        self.assertEqual(self.bash("sed -n 1,80p docs/log.md"), "")
        self.assertIn("reads 101 lines", self.warning(self.bash("head -n 101 docs/log.md")))
        self.write_config(dict(self.cfg, wholeReadShortLines=0))
        self.assertIn("wholeReadShortLines 0", self.warning(self.bash("head -n 1 docs/log.md")))
        self.put("docs/handoff.md", 30000)  # an invalid config gives every default: 20000 bytes, the log docs/handoff.md
        for bad in ("x", -1, True, 2.5):
            self.write_config(dict(self.cfg, wholeReadShortLines=bad))
            self.assertEqual(self.bash("sed -n 1,40p docs/handoff.md"), "", bad)
            self.assertIn("wholeReadShortLines 40", self.warning(self.bash("sed -n 1,41p docs/handoff.md")), bad)

    def test_small_files_and_the_warning_off_are_silent(self):
        self.assertIn("1002 bytes", self.warning(self.bash("head -n 80 docs/roadmap.md")))  # big enough: it warns
        self.put("docs/log.md", LIMIT)
        self.put("docs/roadmap.md", 10)
        self.assertEqual(self.bash("sed -n 1,80p docs/log.md; head -n 80 docs/roadmap.md"), "")
        self.write_config(dict(self.cfg, wholeReadWarnBytes=0))
        self.put("docs/roadmap.md", LIMIT * 5)
        self.assertEqual(self.bash("sed -n 1,80p docs/roadmap.md"), "")

    def test_only_the_log_and_roadmap_files_count_for_a_range(self):
        self.assertIn("1001 bytes", self.warning(self.bash("sed -n 1,80p docs/log.md")))
        for rel in ("docs/records/r.md", "docs/notes.md", "docs/roadmap.md.bak"):
            self.put(rel, LIMIT * 5)
            self.assertEqual(self.bash(f"sed -n 1,80p {rel}; head -n 80 {rel}"), "", rel)
        self.assertIn("5000 bytes", self.warning(self.bash("cat docs/records/r.md")))  # a whole read still does

    def test_path_forms(self):
        for command in ("sed -n 1,80p ./docs/roadmap.md", f"sed -n 1,80p {self.road}", "sed -n 1,80p 'docs/roadmap.md'",
                        'head -n 80 "docs/roadmap.md"', "sed -n 1,80p docs/../docs/roadmap.md",
                        "cd docs && sed -n 1,80p roadmap.md", "sed -n 1,80p docs/roadm*.md"):
            self.assertIn("docs/roadmap.md is 1002 bytes", self.warning(self.bash(command)), command)
        self.assertIn("docs/roadmap.md", self.warning(self.bash("head -n 80 roadmap.md", cwd=self.p.work / "docs")))
        self.assertEqual(self.bash("head -n 80 roadmap.md"), "")  # no such file at the root

    def test_chains_pipes_and_redirections(self):
        for command in ("git status && sed -n 1,80p docs/log.md; echo done", "true || head -n 80 docs/log.md",
                        "echo $(sed -n 1,80p docs/log.md)", "FOO=1 head -n 80 docs/log.md", "sed -n 1,80p docs/log.md | cat -n",
                        "sed -n 1,80p < docs/log.md", "head -n 80 < docs/log.md", "head -n 80 docs/log.md 2>/dev/null",
                        "sed -n 1,80p docs/log.md\nhead -n 80 docs/log.md"):
            self.assertIn("1001 bytes", self.warning(self.bash(command)), command)
        for command in ("sed -n 1,80p docs/log.md | head -5", "head -n 80 docs/log.md | grep x",
                        "head -n 80 docs/log.md > out", "sed -n 1,80p docs/log.md >/dev/null",
                        "cat > n.txt <<EOF\nhead -n 80 docs/log.md\nEOF"):
            self.assertEqual(self.bash(command), "", command)

    def test_two_files_in_one_command_give_two_notes(self):
        text = self.warning(self.bash("head -n 80 docs/log.md docs/roadmap.md"))
        self.assertIn("docs/log.md is 1001 bytes", text)
        self.assertIn("docs/roadmap.md is 1002 bytes", text)

    def test_a_range_warns_every_time_and_is_not_a_repeat(self):
        self.write_config(dict(self.cfg, wholeReadRepeatOnly=True))
        for _ in range(2):
            self.assertIn("1001 bytes", self.warning(self.bash("sed -n 1,80p docs/log.md", session="s1")))
        self.assertEqual([f.name for f in self.state.iterdir() if f.suffix == ".json"], [])  # nothing remembered
        self.assertEqual(self.read(self.log, session="s1"), "", "the first whole Read is still free")

    def test_a_range_short_of_the_end_is_not_denied(self):  # D180: one that reaches the end is (Deny)
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/log.md": "tool"}))
        self.log.write_text(("x" * 10 + "\n") * 200)  # over LIMIT bytes and over 80 lines
        text = self.warning(self.bash("head -n 80 docs/log.md"))
        self.assertIn("recover.py --state", text)
        self.assertIn("deny", json.dumps(json.loads(self.bash("cat docs/log.md"))))  # a whole read still is

    def test_bad_roadmap_files_and_malformed_input_fail_open(self):
        self.assertIn("1002 bytes", self.warning(self.bash("sed -n 1,80p docs/roadmap.md")))  # a good key warns
        for bad in ("x", [3], [{"path": 3}], [{"path": ""}], {"path": "docs/roadmap.md"}):
            self.write_config(dict(self.cfg, roadmapFiles=bad))
            self.assertEqual(self.bash("sed -n 1,80p docs/roadmap.md"), "", bad)
        for command in ("head -n 80 'docs/log.md", "sed -n 1,80p \"docs/log.md", "", "   ", "|", "head -n 80 |"):
            self.assertEqual(self.bash(command), "", command)
        for bad in (json.dumps({"tool_name": "Bash", "tool_input": {"command": 3}}),
                    json.dumps({"tool_name": "Bash", "tool_input": {}}),
                    json.dumps({"tool_name": "Bash", "tool_input": "head"}), "not json"):
            self.assertEqual(self.raw(bad), "", bad)


class Pointers(Base):
    def test_a_pointer_file_is_watched_and_its_command_given(self):
        self.write_config(dict(self.cfg, readPointers={"docs/plan.md": "python3 tools/plan.py --section"}))
        text = self.warning(self.read(self.put("docs/plan.md", LIMIT + 1)))
        self.assertIn("docs/plan.md is 1001 bytes", text)
        self.assertIn("Instead: `python3 tools/plan.py --section` (readPointers", text)
        self.assertIn("python3 tools/plan.py", self.warning(self.bash("cat docs/plan.md")))

    def test_a_pointer_wins_over_the_log_note_and_folders_end_in_slash(self):
        self.write_config(dict(self.cfg, readPointers={"docs/log.md": "tool state", "docs/big/": "tool big"}))
        text = self.warning(self.read(self.put("docs/log.md", LIMIT + 1)))
        self.assertIn("`tool state`", text)
        self.assertNotIn("recover.py", text)
        self.assertIn("`tool big`", self.warning(self.read(self.put("docs/big/a.md", LIMIT + 1))))
        self.assertEqual(self.read(self.put("docs/big-old/a.md", LIMIT + 1)), "")

    def test_a_bad_value_gives_the_default(self):
        self.write_config(dict(self.cfg, readPointers={"docs/plan.md": 3}))
        self.assertEqual(self.read(self.put("docs/plan.md", LIMIT + 1)), "")


class RepeatOnly(Base):
    cfg = {"wholeReadWarnBytes": LIMIT, "wholeReadRepeatOnly": True}

    def test_only_an_unchanged_second_whole_read_warns(self):
        path = self.put("docs/log.md", LIMIT + 1)
        self.assertEqual(self.read(path, session="s1"), "")
        text = self.warning(self.read(path, session="s1"))
        self.assertIn("already read it whole and it has not changed", text)
        self.assertIn("docs/log.md is 1001 bytes", text)
        self.assertEqual(self.read(path, session="s2"), "")  # another session: its first read

    def test_a_change_resets_it(self):
        path = self.put("docs/log.md", LIMIT + 1)
        self.read(path, session="s1")
        path.write_text("y" * (LIMIT + 1))
        stamp = time.time() + 5  # not a wait
        os.utime(path, (stamp, stamp))
        self.assertEqual(self.read(path, session="s1"), "")
        self.assertIn("1001 bytes", self.warning(self.read(path, session="s1")))

    def test_bash_and_read_count_as_the_same_read(self):
        path = self.put("docs/records/r.md", LIMIT + 1)
        self.assertEqual(self.bash("cat docs/records/r.md", session="s1"), "")
        self.assertIn("already read it whole", self.warning(self.read(path, session="s1")))

    def test_a_partial_read_is_not_remembered(self):
        path = self.put("docs/log.md", LIMIT + 1)
        self.assertEqual(self.read(path, session="s1", limit=20), "")
        self.assertEqual(self.bash("grep -n x docs/log.md", session="s1"), "")
        self.assertEqual(self.read(path, session="s1"), "")

    def test_without_a_session_id_nothing_is_warned_or_kept(self):
        path = self.put("docs/log.md", LIMIT + 1)
        for session in (None, None, "../evil", "../evil"):
            self.assertEqual(self.read(path, session=session), "")
        self.assertEqual(list(self.state.iterdir()), [])

    def test_other_sessions_stale_files_are_cleaned(self):
        old = self.state / "gw-reads-old.json"
        old.write_text("{}")
        fresh = self.state / "gw-reads-fresh.json"
        fresh.write_text("{}")
        past = time.time() - 8 * 86400
        os.utime(old, (past, past))
        self.read(self.put("docs/log.md", LIMIT + 1), session="s1")
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists())
        self.assertTrue((self.state / "gw-reads-s1.json").is_file())

    def test_two_parallel_reads_are_both_kept(self):  # the lock: the last os.replace must not drop the other read
        a, b = self.put("docs/log.md", LIMIT + 1), self.put("docs/records/r.md", LIMIT + 1)
        import fcntl
        import subprocess
        with open(self.state / "gw-reads-s1.lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            runs = []
            for path in (a, b):
                event = {"hook_event_name": "PreToolUse", "cwd": str(self.p.work), "tool_name": "Read",
                         "tool_input": {"file_path": str(path)}, "session_id": "s1"}
                runs.append(subprocess.Popen(["python3", str(self.scripts / SCRIPT)], stdin=subprocess.PIPE,
                                             cwd=self.p.work, env=dict(self.p.env, TMPDIR=str(self.state)),
                                             stdout=subprocess.DEVNULL))
                runs[-1].stdin.write(json.dumps(event).encode())
                runs[-1].stdin.close()
            time.sleep(0.5)
            self.assertEqual([r.poll() for r in runs], [None, None], "both wait for the lock")
        self.assertEqual([r.wait(30) for r in runs], [0, 0])
        self.assertIn("already read it whole", self.warning(self.read(a, session="s1")))
        self.assertIn("already read it whole", self.warning(self.read(b, session="s1")))

    def test_forget_drops_the_session_reads(self):
        path = self.put("docs/log.md", LIMIT + 1)
        self.read(path, session="s1")
        code, out = self.p.run("python3", "-c", "import importlib.util as u, sys; s = u.spec_from_file_location('w', "
                               "sys.argv[1]); m = u.module_from_spec(s); s.loader.exec_module(m); m.forget('s1')",
                               str(self.scripts / SCRIPT), env={"TMPDIR": str(self.state)})
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(path, session="s1"), "", "after a compaction the first read is a first read again")

    def test_a_state_that_is_a_link_is_not_followed(self):
        target = self.tmp / "elsewhere.json"
        target.write_text("{}")
        (self.state / "gw-reads-s1.json").symlink_to(target)
        path = self.put("docs/log.md", LIMIT + 1)
        for _ in range(2):
            self.assertEqual(self.read(path, session="s1"), "")
        self.assertEqual(target.read_text(), "{}")

    def test_a_lock_that_is_a_link_is_not_followed(self):  # B4 (E28): a planted link never creates its target
        target = self.tmp / "elsewhere.lock"
        (self.state / "gw-reads-s1.lock").symlink_to(target)
        path = self.put("docs/log.md", LIMIT + 1)
        self.read(path, session="s1")
        self.assertIn("already read it whole", self.warning(self.read(path, session="s1")), "still fails open")
        self.assertFalse(os.path.lexists(target), "the link's target was created")
        self.assertTrue((self.state / "gw-reads-s1.lock").is_symlink())

    def test_a_lock_that_is_a_fifo_or_a_folder_is_skipped(self):  # B4 (E28): no lock, no hang, the advice still
        import subprocess
        path = self.put("docs/log.md", LIMIT + 1)
        lock = self.state / "gw-reads-s1.lock"
        for make in (os.mkfifo, os.mkdir):
            make(str(lock))
            event = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(self.p.work), "tool_name": "Read",
                                "tool_input": {"file_path": str(path)}, "session_id": "s1"})
            outs = []
            for _ in range(2):
                try:
                    r = subprocess.run(["python3", str(self.scripts / SCRIPT)], input=event, capture_output=True,
                                       text=True, cwd=self.p.work, env=dict(self.p.env, TMPDIR=str(self.state)),
                                       timeout=20)
                except subprocess.TimeoutExpired:
                    self.fail(f"the hook hung on a {make.__name__} lock")
                self.assertEqual(r.returncode, 0, r.stderr)
                outs.append(r.stdout)
            self.assertIn("already read it whole", self.warning(outs[1]), make.__name__)
            (os.rmdir if make is os.mkdir else os.unlink)(str(lock))
            (self.state / "gw-reads-s1.json").unlink()


class Deny(Base):  # E70: wholeReadDenyPaths rejects the whole read instead of warning
    def denial(self, out):
        data = json.loads(out)
        spec = data["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertEqual(spec["permissionDecision"], "deny", out)
        self.assertNotIn("additionalContext", spec)
        return spec["permissionDecisionReason"]

    def test_a_whole_read_of_a_denied_file_is_rejected_with_its_command(self):
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "python3 tools/plan.py --section"}))
        path = self.put("docs/plan.md", 10)  # whatever its size
        text = self.denial(self.read(path))
        self.assertIn("docs/plan.md", text)
        self.assertIn("`python3 tools/plan.py --section`", text)
        self.assertIn("wholeReadDenyPaths", text)
        self.assertIn("python3 tools/plan.py", self.denial(self.bash("cat docs/plan.md")))

    def test_a_partial_read_or_a_filter_passes(self):
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        path = self.put_lines("docs/plan.md", 40)
        self.assertEqual(self.read(path, offset=1, limit=10), "")
        self.assertEqual(self.bash("grep -n x docs/plan.md; cat docs/plan.md | head"), "")

    def put_lines(self, rel, count, end="\n"):
        path = self.p.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("line\n" * (count - 1) + "line" + end)
        return path

    def test_a_limit_that_reaches_the_end_is_a_whole_read(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        path = self.put_lines("docs/plan.md", 40, end="")  # a last line without a newline counts
        for given in ({"limit": 5000}, {"limit": 40}, {"offset": 1, "limit": 40}, {"offset": 0, "limit": 99},
                      {"limit": "5000"}):
            text = self.denial(self.read(path, **given))
            self.assertIn("docs/plan.md may not be read whole", text, given)
            self.assertIn("`tool`", text, given)
        self.assertIn("limit 5000; the file has 40 lines", self.denial(self.read(path, limit=5000)))

    def test_offset_one_without_a_limit_is_a_whole_read(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        path = self.put_lines("docs/plan.md", 40)
        text = self.denial(self.read(path, offset=1))
        self.assertIn("docs/plan.md may not be read whole", text)
        self.assertIn("offset 1 and no limit", text)
        self.assertEqual(self.read(path, offset=2), "", "a later offset is a partial read")

    def test_a_bash_range_that_reaches_the_end_is_a_whole_read(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        self.put_lines("docs/plan.md", 40)
        for command in ("sed -n p docs/plan.md", "sed -n '1,$p' docs/plan.md", "head -n 100000 docs/plan.md",
                        "head -n 40 docs/plan.md", "cat docs/plan.md | head -n 100000"):
            text = self.denial(self.bash(command))
            self.assertIn("docs/plan.md may not be read whole", text, command)
            self.assertIn("`tool`", text, command)
        self.assertIn("it runs to the end", self.denial(self.bash("sed -n p docs/plan.md")))
        self.assertIn("the file has 40 lines", self.denial(self.bash("head -n 100000 docs/plan.md")))
        for command in ("head -n 39 docs/plan.md", "sed -n 2,40p docs/plan.md", "cat docs/plan.md | head"):
            self.assertEqual(self.bash(command), "", command)

    def test_an_offset_that_is_not_an_integer_is_the_start(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        path = self.put_lines("docs/plan.md", 40)
        for given in ({"offset": "1"}, {"offset": 1.0}, {"offset": "1", "limit": 5000}, {"offset": 1.0, "limit": 40}):
            self.assertIn("docs/plan.md may not be read whole", self.denial(self.read(path, **given)), given)
        self.assertEqual(self.read(path, offset=2, limit=5000), "")

    def test_pages_only_excuses_a_pdf(self):  # D180: Read ignores pages on any other file
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool", "docs/plan.PDF": "tool"}))
        path = self.put_lines("docs/plan.md", 40)
        for given in ({"pages": "1"}, {"pages": "1-3", "limit": 5000}):
            self.assertIn("docs/plan.md may not be read whole", self.denial(self.read(path, **given)), given)
        self.assertEqual(self.read(self.put_lines("docs/plan.PDF", 40), pages="1-3", limit=5000), "")

    def test_a_partial_limit_or_a_later_offset_passes(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        path = self.put_lines("docs/plan.md", 40)
        for given in ({"limit": 39}, {"offset": 2, "limit": 5000}, {"offset": 30}):
            self.assertEqual(self.read(path, **given), "", given)
        self.denial(self.read(path, limit=40))  # the contrast: the limit that reaches the end is denied
        other = self.put_lines("docs/other.md", 40)
        self.assertEqual(self.read(other, limit=5000), "", "only the denied paths fail closed")

    def test_an_unsplittable_command_that_names_a_denied_path_is_denied(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool", "docs/big/": "tool big"}))
        self.put("docs/plan.md", 10)
        self.put("docs/big/a.md", 10)
        for command in ("cat docs/plan.md 'oops", "grep -n x \"docs/plan.md", "cat ./docs/../docs/plan.md 'x",
                        "sed --file=docs/plan.md 'x"):
            text = self.denial(self.bash(command))
            self.assertIn("docs/plan.md may not be read whole", text, command)
            self.assertIn("cannot be split", text, command)
            self.assertIn("`tool`", text, command)
        self.assertIn("`tool big`", self.denial(self.bash("cat docs/big/a.md 'x")))

    def test_an_unsplittable_command_with_a_glob_of_a_denied_path_is_denied(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        self.put("docs/plan.md", 10)
        self.put("docs/other.md", 10)
        for command in ("cat docs/pla*.md 'x", "cat docs/pl?n.md 'x", "cat d*/plan.[m]d 'x"):
            self.assertIn("docs/plan.md may not be read whole", self.denial(self.bash(command)), command)
        self.assertEqual(self.bash("cat docs/oth*.md 'x"), "")

    def test_an_unsplittable_command_that_names_no_denied_path_passes(self):  # D180
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        self.put("docs/plan.md", 10)
        self.put("docs/handoff.md", LIMIT + 1)
        for command in ("cat docs/handoff.md 'oops", "echo 'plan", "cat docs/plan.mdx 'x"):
            self.assertEqual(self.bash(command), "", command)
        self.denial(self.bash("cat docs/plan.md 'oops"))  # the contrast: naming the denied path is denied
        self.write_config(self.cfg)  # without wholeReadDenyPaths nothing changes
        self.assertEqual(self.bash("cat docs/plan.md 'oops"), "")

    def test_folders_end_in_slash_and_other_paths_pass(self):
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/big/": "tool big"}))
        self.assertIn("`tool big`", self.denial(self.read(self.put("docs/big/a.png", 10))))
        self.assertEqual(self.read(self.put("docs/big-old/a.md", 10)), "")

    def test_it_denies_even_with_the_warning_off_and_repeat_only(self):
        self.write_config({"wholeReadWarnBytes": 0, "wholeReadRepeatOnly": True,
                           "wholeReadDenyPaths": {"docs/plan.md": "tool"}})
        self.denial(self.read(self.put("docs/plan.md", 10), session="s1"))

    def test_a_denial_wins_over_a_warning_in_the_same_command(self):
        self.write_config(dict(self.cfg, wholeReadDenyPaths={"docs/plan.md": "tool"}))
        self.put("docs/plan.md", 10)
        self.put("docs/handoff.md", LIMIT + 1)
        text = self.denial(self.bash("cat docs/handoff.md docs/plan.md"))
        self.assertIn("docs/plan.md", text)
        self.assertNotIn("recover.py", text)

    def test_a_bad_value_denies_nothing(self):
        for bad in ({"docs/plan.md": 3}, ["docs/plan.md"], {"": "tool"}):
            self.write_config(dict(self.cfg, wholeReadDenyPaths=bad))
            self.assertEqual(self.read(self.put("docs/plan.md", 10)), "", bad)


class Screenshots(Base):  # E50: loose screenshots read one by one get the advice to mount them in one sheet
    cfg = {"wholeReadWarnBytes": LIMIT, "wholeReadRepeatOnly": False,
           "screenshotSheet": {"command": "npm run sheet -- <images>"}}

    def shot(self, rel):
        return self.put(rel, 10)

    def test_the_third_distinct_image_warns_with_the_project_command(self):
        self.assertEqual(self.read(self.shot("shots/a.png"), session="s1"), "")
        self.assertEqual(self.read(self.shot("shots/a.png"), session="s1"), "", "a reread does not count")
        self.assertEqual(self.read(self.shot("shots/b.jpg"), session="s1"), "")
        text = self.warning(self.read(self.shot("shots/c.PNG"), session="s1"))
        for part in ("3 images one by one", "`npm run sheet -- <images>`", "screenshotSheet.command",
                     "shots/c.PNG"):
            self.assertIn(part, text)
        self.assertEqual(self.read(self.shot("shots/d.png"), session="s1"), "", "not on every image after it")
        self.assertEqual(self.read(self.shot("shots/e.png"), session="s1"), "")
        self.assertIn("6 images one by one", self.warning(self.read(self.shot("shots/f.png"), session="s1")))

    def test_without_a_command_it_gives_an_example_and_the_key(self):
        self.write_config({"screenshotSheet": {"after": 1}})
        text = self.warning(self.read(self.shot("a.webp"), session="s1"))
        self.assertIn("montage", text)
        self.assertIn("set screenshotSheet.command", text)

    def test_silent_cases(self):
        self.write_config({"screenshotSheet": {"after": 0}})
        self.assertEqual(self.read(self.shot("a.png"), session="s1"), "", "after 0 turns it off")
        self.write_config({"screenshotSheet": {"after": 1, "ignorePaths": ["sheets/", "one.png"],
                                               "extensions": [".png"]}})
        for rel in ("sheets/all.png", "one.png", "x.jpg"):
            self.assertEqual(self.read(self.shot(rel), session="s1"), "", rel)
        self.assertEqual(self.read(self.shot("two.png")), "", "no session, no count")
        self.assertEqual(self.read(self.shot("missing.png").with_name("gone.png"), session="s1"), "", "no file")

    def test_bad_values_fall_back_to_the_defaults(self):
        self.write_config({"screenshotSheet": {"after": "x", "extensions": 3, "command": 4, "ignorePaths": "y"}})
        for name in ("a", "b"):
            self.assertEqual(self.read(self.shot(f"{name}.png"), session="s1"), "")
        self.assertIn("montage", self.warning(self.read(self.shot("c.png"), session="s1")))

    def test_it_works_with_the_size_warning_off_and_beside_it(self):
        self.write_config({"wholeReadWarnBytes": 0, "screenshotSheet": {"after": 1}})
        self.assertIn("1 images one by one", self.warning(self.read(self.shot("a.png"), session="s1")))
        self.write_config({"wholeReadWarnBytes": LIMIT, "wholeReadRepeatOnly": False, "screenshotSheet": {"after": 2}})
        self.assertIn("docs/log.md is", self.warning(self.read(self.put("docs/log.md", LIMIT + 1), session="s2")))
        self.read(self.shot("b.png"), session="s2")
        self.assertIn("2 images one by one", self.warning(self.read(self.shot("c.png"), session="s2")))

    def test_forget_restarts_the_count(self):
        self.write_config({"screenshotSheet": {"after": 2}})
        self.read(self.shot("a.png"), session="s1")
        code, out = self.p.run("python3", "-c", "import importlib.util as u, sys; s = u.spec_from_file_location('w', "
                               "sys.argv[1]); m = u.module_from_spec(s); s.loader.exec_module(m); m.forget('s1')",
                               str(self.scripts / SCRIPT), env={"TMPDIR": str(self.state)})
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(self.shot("b.png"), session="s1"), "", "after /clear the images left the context")


if __name__ == "__main__":
    unittest.main()
