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
        path = self.put("docs/plan.md", LIMIT + 1)
        self.assertEqual(self.read(path, offset=1, limit=10), "")
        self.assertEqual(self.bash("grep -n x docs/plan.md; cat docs/plan.md | head"), "")

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


if __name__ == "__main__":
    unittest.main()
