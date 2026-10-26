"""The workflow's utility scripts, end to end, in temporary projects: bitacora.py, prepush-ramas.sh, fusionar.sh,
rojo-sin-arreglo.sh, tests-relacionados.sh and enlaces-md.py.

Same conventions as test_ganchos.py (it provides the temporary project): git runs isolated from this machine's
configuration and every commit that matters has a fixed date, so the suite does not depend on today's date.
"""
import datetime
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_ganchos import BASE_CONFIG, Project, ROOT, VERSION, ZERO

sys.dont_write_bytecode = True
SCRIPTS = ("bitacora.py", "prepush-ramas.sh", "fusionar.sh", "rojo-sin-arreglo.sh", "tests-relacionados.sh",
           "enlaces-md.py")
DAY = {"GIT_AUTHOR_DATE": "2026-10-21T12:00:00+0000", "GIT_COMMITTER_DATE": "2026-10-21T12:00:00+0000"}
LOG = "docs/log.md"


def log_text(a="doing A", b="doing B", updated="2026-10-21"):
    return f"""# Log

## Current state

| Field | Value |
|---|---|
| **Updated** | {updated} |
| **Tests** | green |
| **Branches** | `feat-a`, `feat-b` |
| **Task in progress · `feat-a`** | {a} |
| **Task in progress · `feat-b`** | {b} |

## Done

1. nothing yet
"""


class Utilidades(Project):
    """The base project plus the utility scripts (committed and pushed) and a log with two branch rows."""

    def __init__(self, tmp, config=None, check="exit 0"):
        super().__init__(tmp, dict({"logRows": True}, **(config or {})), check)
        scripts = self.work / ".claude" / "gw" / "scripts"
        for name in SCRIPTS:
            shutil.copy2(ROOT / "scripts" / name, scripts / name)
        self.write(LOG, log_text())
        self.commit("scripts and log", env=DAY)
        self.git("push", "-q", "--no-verify", "origin", "main")
        self.base = self.sha()
        self.scripts = scripts

    def script(self, name, *args, **kw):
        interpreter = ["python3"] if name.endswith(".py") else ["bash"]
        return self.run(*interpreter, str(self.scripts / name), *args, **kw)

    def branch(self, name, start=None):
        self.git("checkout", "-q", "-b", name, start or self.base)


class Base(unittest.TestCase):
    config = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-utilidades-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Utilidades(self.tmp, self.config)


class BitacoraRows(Base):
    def test_check_accepts_a_well_formed_log(self):
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 0, out)

    def test_row_over_600_characters_refused(self):
        self.p.write(LOG, log_text(a="x" * 601))
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 1, out)
        self.assertIn("601 characters (limit 600)", out)
        self.p.write(LOG, log_text(a="x" * 600))
        self.assertEqual(self.p.script("bitacora.py", "check")[0], 0)

    def test_two_rows_for_one_branch_refused(self):
        self.p.write(LOG, log_text() + "\n| **Task in progress · `feat-a`** | again |\n")
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 1, out)
        self.assertIn("two rows for feat-a", out)

    def test_updated_older_than_the_commit_day_refused(self):
        self.p.write(LOG, log_text(updated="2026-10-01"))
        code, out = self.p.script("bitacora.py", "check", "--date", "2026-10-21")
        self.assertEqual(code, 1, out)
        self.assertIn("2026-10-01", out)
        self.assertEqual(self.p.script("bitacora.py", "check", "--date", "2026-10-01")[0], 0)

    def test_off_without_logrows(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        p = Utilidades(self.tmp, {"logRows": False})
        p.write(LOG, log_text(a="x" * 900))
        self.assertEqual(p.script("bitacora.py", "check")[0], 0)
        self.assertEqual(p.script("bitacora.py", "close-row", "feat-a")[0], 0)
        self.assertNotIn("Merged", (p.work / LOG).read_text())


class BitacoraSizeAndDone(Base):
    """`check` on the state-table cells and the Done section (any log, warnings unless --strict) and `done`."""
    config = {"logRows": False}  # these rules do not depend on logRows

    def log(self, text, name="x.md", newline=None):
        path = self.tmp / name
        data = text.replace("\n", newline) if newline else text
        path.write_bytes(data.encode("utf-8"))
        return path

    def check(self, text, *flags, **kw):
        return self.p.script("bitacora.py", "check", str(self.log(text, **kw)), *flags)

    @staticmethod
    def doc(cell="short", done=None):
        done = ["1. 2026-10-25 — a", "2. 2026-10-24 — b"] if done is None else done
        return ("# Log\n\n## Estado actual\n\n| Campo | Valor |\n|---|---|\n"
                f"| **Siguiente paso** | {cell} |\n| Rama | `x` |\n\n## Hecho (5 últimas)\n\n" + "\n".join(done)
                + "\n\n## Pendiente\n\n- nothing\n")

    @staticmethod
    def items(n):
        return [f"{i}. 2026-10-{30 - i} — item {i}" for i in range(1, n + 1)]

    def test_long_cell_warns_with_exit_0_and_fails_with_strict(self):
        text = self.doc(cell="x" * 801)
        code, out = self.check(text)
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: bitacora: a cell of the state table (\"Siguiente paso\") has 801 characters (limit 800)", out)
        self.assertIn("bitacora.py done", out)  # the message ends with the command that helps
        code, out = self.check(text, "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("has 801 characters (limit 800)", out)
        self.assertNotIn("WARNING", out)
        self.assertEqual(self.check(self.doc(cell="x" * 800), "--strict")[0], 0)

    def test_cell_rules_ignore_other_tables_headers_and_escaped_pipes(self):
        other = self.doc().replace("## Pendiente\n\n", "## Pendiente\n\n| a | " + "y" * 900 + " |\n\n")
        self.assertEqual(self.check(other, "--strict")[0], 0)
        escaped = self.doc(cell="a \\| " + "z" * 790)  # 795 characters: the escaped pipe does not split the cell
        self.assertEqual(self.check(escaped, "--strict")[0], 0)
        code, out = self.check(self.doc(cell="a | " + "z" * 801), "--strict")  # an unescaped pipe does: 2 cells, 1 too long
        self.assertEqual(code, 1, out)
        self.assertIn("has 801 characters", out)
        english = self.doc(cell="w" * 801).replace("## Estado actual", "## Current state")
        self.assertEqual(self.check(english, "--strict")[0], 1)

    def test_log_without_the_sections_has_nothing_to_check(self):
        for text in ("", "\n", "# Log\n\nplain text\n", "## Estado actual\n\nno table here\n",
                     "| **Rama** | " + "q" * 900 + " |\n"):
            code, out = self.check(text, "--strict")
            self.assertEqual((code, out.strip()), (0, ""), text)

    def test_table_without_value_rows_is_fine(self):
        text = "## Estado actual\n\n| Campo | Valor |\n|---|---|\n\n## Hecho (5 últimas)\n\n"
        self.assertEqual(self.check(text, "--strict")[0], 0)

    def test_six_items_warn_and_fail_with_strict(self):
        text = self.doc(done=self.items(6))
        code, out = self.check(text)
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: bitacora: the Done section has 6 items (limit 5)", out)
        code, out = self.check(text, "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("has 6 items (limit 5)", out)
        self.assertEqual(self.check(self.doc(done=self.items(5)), "--strict")[0], 0)

    def test_bad_numbering_is_reported(self):
        for done, shown in ((["1. a", "3. b"], "1, 3"), (["2. a", "3. b"], "2, 3"), (["1. a", "1. b"], "1, 1")):
            code, out = self.check(self.doc(done=done), "--strict")
            self.assertEqual(code, 1, done)
            self.assertIn(f"the Done items are numbered {shown}; number them 1..n in order", out)

    def test_glued_item_is_reported(self):
        done = ["1. 2026-10-25 — first (`abc`).2. 2026-10-24 — second glued", "3. 2026-10-23 — third"]
        code, out = self.check(self.doc(done=done), "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("an item is glued to the end of another one", out)
        self.assertIn("put each item on its own line", out)
        self.assertIn("numbered 1, 3", out)  # the glued one is not counted as an item of its own

    def test_a_version_number_before_a_date_is_not_a_glued_item(self):
        done = ["1. 2026-10-25 — released v1.2. 2026-10-24 is the date before", "2. 2026-10-24 — b"]
        self.assertEqual(self.check(self.doc(done=done), "--strict")[0], 0)
        self.assertEqual(self.check(self.doc(done=["1. 2026-10-25 — a (`x`).2. 2026-10-24 — b"]), "--strict")[0], 1)

    def test_done_messages_end_with_the_command_that_fixes_them(self):
        for done in (self.items(6), ["1. a", "3. b"], ["1. 2026-10-25 — a.2. 2026-10-24 — b"]):
            out = self.check(self.doc(done=done), "--strict")[1]
            self.assertRegex(out, r"(bitacora\.py done \"<text>\"\)|rerun: python3 \S+bitacora\.py check \S+ --strict)", done)

    def test_unreadable_log_without_logrows_warns_and_does_not_block(self):
        path = self.tmp / "latin.md"
        path.write_bytes("## Estado actual\n\n| a | caf\xe9 |\n".encode("latin-1"))
        code, out = self.p.script("bitacora.py", "check", str(path))
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: bitacora: cannot read", out)
        self.assertIn("save it as UTF-8", out)
        code, out = self.p.script("bitacora.py", "check", str(path), "--strict")
        self.assertEqual(code, 2, out)
        self.assertIn("cannot read", out)
        code, out = self.p.script("bitacora.py", "check", str(self.tmp / "missing.md"))
        self.assertEqual((code, "WARNING: bitacora: cannot read" in out), (0, True), out)

    def test_unreadable_log_with_logrows_still_fails(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"logRows": True})
        path = self.tmp / "latin.md"
        path.write_bytes("caf\xe9\n".encode("latin-1"))
        code, out = self.p.script("bitacora.py", "check", str(path))
        self.assertEqual(code, 2, out)
        self.assertIn("cannot read", out)

    def test_date_must_be_a_real_date(self):
        path = self.log(self.doc())
        for bad in ("2026-13-45", "2026-02-30", "26-10-25", "tomorrow"):
            for args in (("check", str(path), "--date", bad), ("done", "t", str(path), "--date", bad)):
                code, out = self.p.script("bitacora.py", *args)
                self.assertEqual(code, 2, (args, out))
                self.assertIn("--date must be YYYY-MM-DD and a real date", out)
        self.assertEqual(path.read_bytes().decode("utf-8"), self.doc())

    def test_continuation_lines_and_numbers_inside_text_are_not_items(self):
        done = ["1. 2026-10-25 — a long one,", "   2. indented sub point, dated 2026-10-24", "2. 2026-10-24 — b"]
        self.assertEqual(self.check(self.doc(done=done), "--strict")[0], 0)

    def test_crlf_log_is_checked(self):
        text = self.doc(cell="x" * 801, done=self.items(6))
        code, out = self.check(text, "--strict", newline="\r\n")
        self.assertEqual(code, 1, out)
        self.assertIn("has 801 characters", out)
        self.assertIn("has 6 items", out)
        self.assertEqual(self.check(self.doc(), "--strict", newline="\r\n")[0], 0)

    def test_logrows_keeps_its_rules_and_the_new_ones_stack(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"logRows": True})
        text = log_text(a="x" * 601).replace("1. nothing yet", "\n".join(self.items(6)))
        code, out = self.check(text)
        self.assertEqual(code, 1, out)  # the row rule still fails on its own
        self.assertIn("601 characters (limit 600)", out)
        self.assertIn("WARNING: bitacora: the Done section has 6 items", out)

    def test_repo_templates_follow_the_rules(self):
        for template in ("es", "en"):
            code, out = self.p.script("bitacora.py", "check", str(ROOT / "templates" / template / "log.md"), "--strict")
            self.assertEqual(code, 0, out)

    # done

    def run_done(self, text, entry="new one", **kw):
        path = self.log(text, **kw)
        code, out = self.p.script("bitacora.py", "done", entry, str(path), "--date", "2026-10-26")
        return code, out, path.read_bytes().decode("utf-8")

    def test_done_inserts_on_top_and_renumbers_leaving_the_rest_identical(self):
        text = self.doc()
        code, out, new = self.run_done(text)
        self.assertEqual(code, 0, out)
        self.assertEqual(new, text.replace("1. 2026-10-25 — a\n2. 2026-10-24 — b",
                                           "1. 2026-10-26 — new one\n2. 2026-10-25 — a\n3. 2026-10-24 — b"))
        self.assertEqual(self.check(new, "--strict")[0], 0)

    def test_done_rotates_after_five_and_keeps_multiline_items_whole(self):
        done = ["1. 2026-10-25 — a", "2. 2026-10-24 — b", "   continued b", "3. 2026-10-23 — c",
                "4. 2026-10-22 — d", "   continued d", "   and more d", "5. 2026-10-21 — e", "   continued e (dropped)"]
        code, out, new = self.run_done(self.doc(done=done), "multi   word\nentry")
        self.assertEqual(code, 0, out)
        self.assertIn("1 oldest dropped", out)
        expected = ["1. 2026-10-26 — multi word entry", "2. 2026-10-25 — a", "3. 2026-10-24 — b", "   continued b",
                    "4. 2026-10-23 — c", "5. 2026-10-22 — d", "   continued d", "   and more d"]
        self.assertEqual(new, self.doc(done=expected))
        self.assertEqual(self.check(new, "--strict")[0], 0)

    def test_done_keeps_a_free_paragraph_after_the_items_when_the_last_one_drops(self):
        done = self.items(5) + ["", "The full history is in git log.", "Second line of it."]
        code, out, new = self.run_done(self.doc(done=done))
        self.assertEqual(code, 0, out)
        self.assertIn("1 oldest dropped", out)
        self.assertEqual(new, self.doc(done=["1. 2026-10-26 — new one"] + [
            f"{i + 1}. 2026-10-{30 - i} — item {i}" for i in range(1, 5)] + done[5:]))

    def test_done_with_many_items_drops_all_the_extra_ones(self):
        code, out, new = self.run_done(self.doc(done=self.items(8)))
        self.assertEqual(code, 0, out)
        self.assertIn("4 oldest dropped", out)
        self.assertEqual(new, self.doc(done=["1. 2026-10-26 — new one"] + [
            f"{i + 1}. 2026-10-{30 - i} — item {i}" for i in range(1, 5)]))

    def test_done_fails_closed_without_the_section_and_changes_nothing(self):
        text = "# Log\n\n## Estado actual\n\ntext\n\n## Pendiente\n\n1. not a done item\n"
        code, out, new = self.run_done(text)
        self.assertEqual(code, 1, out)
        self.assertIn("has no \"## Hecho\" / \"## Done\" section", out)
        self.assertIn("rerun: python3", out)
        self.assertEqual(new, text)
        code, out, new = self.run_done("")
        self.assertEqual((code, new), (1, ""))

    def test_done_in_an_empty_section_and_at_the_end_of_the_file(self):
        code, out, new = self.run_done("## Done (last 5)\n\n## Pending\n")
        self.assertEqual((code, new), (0, "## Done (last 5)\n\n1. 2026-10-26 — new one\n\n## Pending\n"), out)
        code, out, new = self.run_done("# L\n\n## Done (last 5)\n")
        self.assertEqual((code, new), (0, "# L\n\n## Done (last 5)\n\n1. 2026-10-26 — new one\n"), out)
        code, out, new = self.run_done("# L\n\n## Done (last 5)")
        self.assertEqual((code, new), (0, "# L\n\n## Done (last 5)\n\n1. 2026-10-26 — new one\n"), out)
        code, out, new = self.run_done("# L\n\n## Done (last 5)\n\n1. 2026-10-25 — a")  # no newline after the last item
        self.assertEqual((code, new), (0, "# L\n\n## Done (last 5)\n\n1. 2026-10-26 — new one\n2. 2026-10-25 — a"), out)

    def test_done_drops_the_templates_placeholder_item(self):
        for lang, heading, example, other in (("es", "Hecho (5 últimas)", "_(fecha — qué se cerró)_", "Pendiente"),
                                              ("en", "Done (last 5)", "_(date — what was closed)_", "Pending")):
            text = f"# L\n\n## {heading}\n\n1. {example}\n   second line of the example)_\n\n## {other}\n"
            code, out, new = self.run_done(text)
            self.assertEqual((code, new), (0, f"# L\n\n## {heading}\n\n1. 2026-10-26 — new one\n\n## {other}\n"), (lang, out))
        with_real = "## Done (last 5)\n\n1. 2026-10-25 — real\n2. _(date — example)_\n\n## Pending\n"
        code, out, new = self.run_done(with_real)
        self.assertEqual(new, "## Done (last 5)\n\n1. 2026-10-26 — new one\n2. 2026-10-25 — real\n\n## Pending\n", out)
        for template in ("es", "en"):  # the real templates
            body = (ROOT / "templates" / template / "log.md").read_text(encoding="utf-8")
            code, out, new = self.run_done(body)
            self.assertEqual(code, 0, out)
            self.assertIn("1. 2026-10-26 — new one", new)
            self.assertNotIn("1. _(", new)
            self.assertNotIn("_(fecha — qué se cerró", new)
            self.assertNotIn("_(date — what was closed", new)

    def test_done_keeps_crlf_and_blank_lines_between_items(self):
        text = self.doc(done=["1. 2026-10-25 — a", "", "2. 2026-10-24 — b"])
        code, out, new = self.run_done(text, newline="\r\n")
        self.assertEqual(code, 0, out)
        want = self.doc(done=["1. 2026-10-26 — new one", "", "2. 2026-10-25 — a", "", "3. 2026-10-24 — b"])
        self.assertEqual(new, want.replace("\n", "\r\n"))

    def test_done_defaults_to_today_and_to_the_logs_file(self):
        before = (self.p.work / LOG).read_text()
        code, out = self.p.script("bitacora.py", "done", "from the default file")
        self.assertEqual(code, 0, out)
        today = datetime.date.today().isoformat()
        self.assertEqual((self.p.work / LOG).read_text(),
                         before.replace("1. nothing yet", f"1. {today} — from the default file\n2. nothing yet"))

    def test_done_bad_usage_is_exit_2(self):
        path = self.log(self.doc())
        missing = str(self.tmp / "missing.md")
        for args, message in ((("done", "text", str(path), "--date", "tomorrow"), "--date must be YYYY-MM-DD"),
                              (("done", "   ", str(path)), "TEXT is empty"),
                              (("done", "text", missing), "cannot read")):
            code, out = self.p.script("bitacora.py", *args)
            self.assertEqual(code, 2, args)
            self.assertIn(message, out)
        self.assertEqual(self.p.script("bitacora.py", "done")[0], 2)
        self.assertEqual(path.read_bytes().decode("utf-8"), self.doc())


class BitacoraOwnRow(Base):
    def commit_log(self, **kw):
        self.p.write(LOG, log_text(**kw))
        self.p.commit("edit the log", env=DAY)
        return self.p.sha()

    def test_own_row_and_free_rows_accepted(self):
        self.p.branch("feat-a")
        sha = self.commit_log(a="A moved on", updated="2026-10-22")
        self.assertEqual(self.p.script("bitacora.py", "own-row", sha, "feat-a")[0], 0)

    def test_other_branch_row_refused(self):
        self.p.branch("feat-a")
        sha = self.commit_log(b="A rewrote B")
        code, out = self.p.script("bitacora.py", "own-row", sha, "feat-a")
        self.assertEqual(code, 1, out)
        self.assertIn("Task in progress · feat-b", out)
        self.assertIn("BITACORA_COMPARTIDA=1 git push", out)

    def test_shared_row_refused_and_allowed_with_env_or_flag(self):
        self.p.branch("feat-a")
        self.p.write(LOG, log_text().replace("`feat-a`, `feat-b`", "`feat-a`, `feat-b`, `feat-c`"))
        self.p.commit("edit a shared row", env=DAY)
        sha = self.p.sha()
        code, out = self.p.script("bitacora.py", "own-row", sha, "feat-a")
        self.assertEqual(code, 1, out)
        self.assertIn("Branches", out)
        for env in ({"BITACORA_COMPARTIDA": "1"}, {"GW_SHARED_LOG": "1"}):
            self.assertEqual(self.p.script("bitacora.py", "own-row", sha, "feat-a", env=env)[0], 0, env)
        self.assertEqual(self.p.script("bitacora.py", "own-row", sha, "feat-a", "--shared")[0], 0)


class BitacoraTasks(Base):
    PLAN = "docs/plan.md"

    def plan(self, text, message="plan"):
        self.p.write(self.PLAN, text)
        self.p.commit(message, env=DAY)
        return self.p.sha()

    def test_in_progress_task_whose_entry_did_not_change_warns_but_passes(self):
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-7** 🚧 half done, missing the form\n- [ ] **INS-8** later\n")
        self.p.write("src/x.py", "x = 1\n")
        self.p.commit("Work on INS-7 and INS-8", env=DAY)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "in-progress", base, self.p.sha())
        self.assertEqual(code, 0, out)
        self.assertIn("warning", out)
        self.assertIn("INS-7", out)
        self.assertNotIn("INS-8", out)  # not marked 🚧
        self.plan("- [ ] **INS-7** 🚧 half done, the form is missing now\n- [ ] **INS-8** later\n", "update INS-7")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "in-progress", base, self.p.sha())
        self.assertEqual(code, 0, out)
        self.assertNotIn("warning", out)

    def test_closed_task_must_be_in_done(self):
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-3** the thing\n- [ ] **TASK-1** other\n")
        self.plan("- [x] **INS-3** the thing\n- [ ] **TASK-1** other\n", "close INS-3")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 1, out)
        self.assertIn("INS-3", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. ~~INS-3~~ done"))
        self.p.commit("log", env=DAY)
        self.assertEqual(self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())[0], 0)

    def test_staged_closure_must_be_in_done(self):
        self.p.branch("feat-a")
        self.plan("- [ ] **INS-3** the thing\n")
        self.p.write(self.PLAN, "- [x] **INS-3** the thing\n")
        self.p.git("add", self.PLAN)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", "--staged")
        self.assertEqual(code, 1, out)
        self.assertIn("INS-3 is closed in the plan", out)
        self.assertIn(f"git add {LOG}", out)  # the commit does not exist yet: no --amend
        self.assertNotIn("--amend", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. ~~INS-3~~ done"))
        self.p.git("add", LOG)
        self.assertEqual(self.p.script("bitacora.py", "--plan", self.PLAN, "closed", "--staged")[0], 0)

    def test_staged_reads_the_index_not_the_work_tree(self):
        self.p.branch("feat-a")
        self.plan("- [ ] **INS-3** the thing\n- [ ] **INS-4** other\n")
        self.p.write(self.PLAN, "- [x] **INS-3** the thing\n- [ ] **INS-4** other\n")
        self.p.git("add", self.PLAN)
        self.p.write(self.PLAN, "- [x] **INS-3** the thing\n- [x] **INS-4** other\n")  # not staged
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. ~~INS-3~~ done"))  # not staged either
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", "--staged")
        self.assertEqual(code, 1, out)
        self.assertIn("INS-3", out)
        self.assertNotIn("INS-4", out)

    def test_staged_takes_no_range(self):
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", "--staged", "HEAD", "HEAD")
        self.assertEqual(code, 2, out)
        self.assertIn("--staged alone", out)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", "HEAD")
        self.assertEqual(code, 2, out)
        self.assertIn("takes BASE SHA", out)

    def test_closed_on_the_configured_protected_branch_needs_no_done_entry(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"protectedBranch": "trunk"})
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-3** the thing\n")
        sha = self.plan("- [x] **INS-3** the thing\n", "close INS-3 (from trunk)")
        self.p.git("push", "-q", "--no-verify", "origin", "HEAD:trunk")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, sha)
        self.assertEqual(code, 0, out)

    def test_struck_multiline_task_and_custom_id_regex(self):
        self.p.branch("feat-a")
        base = self.plan("- TASK-1 one\n- TASK-2 two\n")
        self.plan("- ~~TASK-1 one\n  continued~~\n- TASK-2 two\n", "close TASK-1")
        args = ("--plan", self.PLAN, "--id-regex", r"TASK-\d+", "closed", base, self.p.sha())
        code, out = self.p.script("bitacora.py", *args)
        self.assertEqual(code, 1, out)
        self.assertIn("TASK-1", out)
        self.assertNotIn("TASK-2", out)

    def test_task_id_with_capturing_groups_does_not_crash_closed_and_still_checks(self):
        self.p.branch("feat-a")
        base = self.plan("- INS-1 one\n- FLU-2 two\n- INS-3 three\n- INS-1 to INS-3 range\n")
        self.plan("- ~~INS-1 to INS-3 range~~\n- INS-1 one\n- FLU-2 two\n", "close")
        args = ("--plan", self.PLAN, "--id-regex", r"(INS|FLU)-\d+", "closed", base, self.p.sha())
        code, out = self.p.script("bitacora.py", *args)
        self.assertEqual(code, 1, out)
        self.assertNotIn("Traceback", out)
        self.assertIn("INS-1 is closed in the plan", out)
        self.assertIn("INS-3 is closed in the plan", out)
        self.assertNotIn("FLU-2", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. ~~INS-1 to INS-3~~ done"))
        self.p.commit("log", env=DAY)
        args = args[:-1] + (self.p.sha(),)
        self.assertEqual(self.p.script("bitacora.py", *args)[0], 0)

    def test_task_id_from_the_config_with_groups(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"taskId": r"(INS|FLU)-\d+"})
        self.p.branch("feat-a")
        base = self.plan("- FLU-9 nine\n")
        self.plan("- ~~FLU-9 nine~~\n", "close FLU-9")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 1, out)
        self.assertIn("FLU-9 is closed in the plan", out)

    def test_backreference_in_the_id_regex_is_a_usage_error(self):
        code, out = self.p.script("bitacora.py", "--id-regex", r"(a)\1", "closed", "HEAD", "HEAD")
        self.assertEqual(code, 2, out)
        self.assertIn("back-reference", out)

    def test_only_struck_or_dated_lines_in_done_record_a_task(self):
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-3** the thing\n")
        self.plan("- [x] **INS-3** the thing\n", "close INS-3")
        for text in ("1. INS-3 done, not struck", "- [x] **INS-3** ticked", "1. mentioned later: INS-3 pending"):
            self.p.write(LOG, log_text().replace("1. nothing yet", text))
            self.p.commit("log", env=DAY)
            code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
            self.assertEqual(code, 1, f"{text}: {out}")
            self.assertIn("INS-3 is closed in the plan", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. 2026-10-21 — closed INS-3 with the fix"))
        self.p.commit("log", env=DAY)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 0, out)
        # the id on an indented continuation line of a dated entry counts; a new unstruck item after it does not
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. 2026-10-21 — the fix\n   that closes INS-3"))
        self.p.commit("log", env=DAY)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 0, out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. 2026-10-21 — the fix\n   - INS-3 pending"))
        self.p.commit("log", env=DAY)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 1, out)
        self.assertIn("INS-3 is closed in the plan", out)

    def test_check_fails_on_a_task_row_without_a_branch_even_with_good_rows(self):
        self.p.write(LOG, log_text().replace("| **Branches**", "| **Tarea en curso** | no branch here |\n| **Branches**"))
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 1, out)
        self.assertIn("task row without a branch", out)
        self.assertIn("Tarea en curso", out)
        self.p.write(LOG, log_text())
        self.assertEqual(self.p.script("bitacora.py", "check")[0], 0)


class BitacoraClash(Base):
    """WMF P2: two branches that open the same task id for different tasks."""
    PLAN = "docs/plan.md"
    START = "- [ ] **INS-1** first\n- [ ] **INS-2** second\n"

    def setUp(self):
        super().setUp()
        self.plan(self.START)
        self.p.git("push", "-q", "--no-verify", "origin", "main")
        self.base = self.p.sha()

    def plan(self, text, message="plan"):
        self.p.write(self.PLAN, text)
        self.p.commit(message, env=DAY)
        return self.p.sha()

    def clash(self, *args):
        return self.p.script("bitacora.py", "--plan", self.PLAN, "clash", *args)

    def two_branches(self, a="the form", b="the export"):
        self.p.branch("feat-b", self.base)
        b_sha = self.plan(self.START + f"- [ ] **INS-3** {b}\n", "B opens INS-3")
        self.p.branch("feat-a", self.base)
        a_sha = self.plan(self.START + f"- [ ] **INS-3** {a}\n", "A opens INS-3")
        return a_sha, b_sha

    def test_same_id_for_two_tasks_refused_with_a_free_id(self):
        a, b = self.two_branches()
        code, out = self.clash(a, b)
        self.assertEqual(code, 1, out)
        self.assertIn('INS-3 is a new task on this branch ("the form")', out)
        self.assertIn(f'on {b} ("the export")', out)
        self.assertIn("give yours a free id (INS-4)", out)
        self.assertIn("fix: renumber the task", out)

    def test_same_task_brought_over_passes_whatever_its_markup_state_or_detail(self):
        a, b = self.two_branches("The form: with a date", "~~**the form**~~ ✅ 2026-10-21 done")
        self.assertEqual(self.clash(a, b), (0, ""))

    def test_ids_the_merge_base_has_and_indented_mentions_are_not_clashes(self):
        self.p.branch("feat-b", self.base)
        b = self.plan("- [ ] **INS-1** first, renamed\n- [ ] **INS-2** second\n  - INS-3 later maybe\n")
        self.p.branch("feat-a", self.base)
        a = self.plan(self.START + "| INS-3 | a table task |\n")
        self.assertEqual(self.clash(a, b), (0, ""))

    def test_table_rows_and_struck_entries_are_entries(self):
        self.p.branch("feat-b", self.base)
        b = self.plan(self.START + "| INS-3 | the export |\n")
        self.p.branch("feat-a", self.base)
        a = self.plan(self.START + "- ~~**INS-3 · the form**~~ ✅ 2026-10-21\n")
        code, out = self.clash(a, b)
        self.assertEqual(code, 1, out)
        self.assertIn('("the form")', out)
        self.assertIn('("the export")', out)

    def test_warn_prints_and_passes_and_skips_missing_refs(self):
        a, b = self.two_branches()
        code, out = self.clash("--warn", a, "origin/gone", b)
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: bitacora: INS-3 is a new task", out)
        self.assertNotIn("fix:", out)
        code, out = self.clash(a, "origin/gone")
        self.assertEqual(code, 2, out)
        self.assertIn("origin/gone is not a commit in this clone; fetch it: git fetch origin", out)

    def test_no_common_history_fails_closed_unless_warn(self):
        a, _ = self.two_branches()
        self.p.git("checkout", "-q", "--orphan", "lonely")
        orphan = self.plan(self.START + "- [ ] **INS-3** the export\n", "orphan")
        code, out = self.clash(a, orphan)
        self.assertEqual(code, 2, out)
        self.assertIn("no common history here; fetch more of it: git fetch --deepen=200 origin", out)
        self.assertEqual(self.clash("--warn", a, orphan), (0, ""))

    def test_merge_that_kept_both_tasks_refused_until_one_is_renumbered(self):
        a, b = self.two_branches()
        self.p.git("merge", "-q", "--no-edit", "-s", "ours", b)  # keeps A's plan: one title, nothing to report
        self.assertEqual(self.clash("--merge", self.p.sha()), (0, ""))
        self.p.git("reset", "-q", "--hard", a)
        both = self.START + "- [ ] **INS-3** the form\n- [ ] **INS-3** the export\n"
        self.p.git("merge", "-q", "--no-commit", "-s", "ours", b)
        self.p.write(self.PLAN, both)
        self.p.git("add", self.PLAN)
        self.p.git("commit", "-q", "--no-verify", "--no-edit")
        merge = self.p.sha()
        code, out = self.clash("--merge", merge)
        self.assertEqual(code, 1, out)
        self.assertIn('keeps two different tasks with the id INS-3: "the form" on this branch and "the export" '
                      "on the merged one; give this branch's a free id (INS-4)", out)
        self.assertIn("in a new commit: git commit -a", out)
        fixed = self.plan(both.replace("INS-3** the form", "INS-4** the form"), "renumber")
        self.assertEqual(self.clash("--merge", merge, "--tip", fixed), (0, ""))
        self.assertEqual(self.clash("--merge", a), (0, ""))  # not a merge

    def test_merging_checks_the_index_of_a_merge_in_progress(self):
        a, b = self.two_branches()
        self.assertEqual(self.clash("--merging"), (0, ""))  # no merge in progress
        self.p.git("merge", "-q", "--no-commit", "-s", "ours", b)
        self.p.write(self.PLAN, self.START + "- [ ] **INS-3** the form\n- [ ] **INS-3** the export\n")
        self.p.write("other.md", "not staged\n")
        code, out = self.clash("--merging")
        self.assertEqual(code, 0, out)  # the work tree has both, the index does not yet
        self.p.git("add", self.PLAN)
        code, out = self.clash("--merging")
        self.assertEqual(code, 1, out)
        self.assertIn("give this branch's a free id (INS-4)", out)
        self.assertIn("then: git add -A && git commit", out)
        self.p.write(self.PLAN, self.START + "- [ ] **INS-4** the form\n- [ ] **INS-3** the export\n")
        self.p.git("add", self.PLAN)
        self.assertEqual(self.clash("--merging"), (0, ""))

    def test_bad_usage_is_exit_2(self):
        for args in ((), ("HEAD",), ("--merging", "HEAD"), ("--merge", "HEAD", "--warn"), ("--tip", "HEAD", "HEAD", "HEAD"),
                     ("--merging", "--merge", "HEAD")):
            code, out = self.clash(*args)
            self.assertEqual(code, 2, f"{args}: {out}")
            self.assertIn("clash takes REV OTHER", out)

    def test_off_without_a_plan_or_without_logrows(self):
        a, b = self.two_branches()
        code, out = self.p.script("bitacora.py", "clash", a, b)  # no plan in the config
        self.assertEqual((code, out), (0, ""))
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"logRows": False})
        self.plan(self.START)
        self.base = self.p.sha()
        a, b = self.two_branches()
        self.assertEqual(self.clash(a, b), (0, ""))


class BitacoraCloseRow(Base):
    def test_close_row_writes_merged_text_only_in_that_row(self):
        code, out = self.p.script("bitacora.py", "close-row", "feat-a")
        self.assertEqual(code, 0, out)
        text = (self.p.work / LOG).read_text()
        self.assertIn("| **Task in progress · `feat-a`** | Merged, branch finished: nothing is pending on it. |", text)
        self.assertIn("| **Task in progress · `feat-b`** | doing B |", text)
        self.assertEqual(self.p.script("bitacora.py", "check")[0], 0)

    def test_close_row_with_text_and_unknown_branch(self):
        self.assertEqual(self.p.script("bitacora.py", "close-row", "feat-b", "--text", "done, merged")[0], 0)
        self.assertIn("| **Task in progress · `feat-b`** | done, merged |", (self.p.work / LOG).read_text())
        code, out = self.p.script("bitacora.py", "close-row", "nope")
        self.assertEqual(code, 1, out)
        self.assertIn("found 0 rows for nope", out)


class PrepushRamas(Base):
    def run_hook(self, sha, remote_sha=ZERO, ref="feat-a", env=None):
        stdin = f"refs/heads/{ref} {sha} refs/heads/{ref} {remote_sha}\n"
        changed, pushed = self.tmp / "changed", self.tmp / "pushed"
        changed.write_text("")
        pushed.write_text("")
        code, out = self.p.script("prepush-ramas.sh", str(changed), str(pushed), stdin=stdin, env=env)
        return code, out, changed.read_text().split(), pushed.read_text().split()

    def edit(self, **kw):
        self.p.write(LOG, log_text(**kw))
        self.p.commit("edit the log", env=DAY)
        return self.p.sha()

    def test_own_row_passes_and_lists_files_and_commits(self):
        self.p.branch("feat-a")
        sha = self.edit(a="A moved on")
        code, out, changed, pushed = self.run_hook(sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(changed, [LOG])
        self.assertEqual(pushed, [sha])

    def test_other_row_refused_unless_shared(self):
        self.p.branch("feat-a")
        sha = self.edit(b="A rewrote B")
        code, out, _, _ = self.run_hook(sha)
        self.assertEqual(code, 1, out)
        self.assertIn("Task in progress · feat-b", out)
        for var in ("BITACORA_COMPARTIDA", "GW_SHARED_LOG"):
            self.assertEqual(self.run_hook(sha, env={var: "1"})[0], 0, var)

    def test_row_over_the_limit_refused(self):
        self.p.branch("feat-a")
        sha = self.edit(a="x" * 700)
        code, out, _, _ = self.run_hook(sha)
        self.assertEqual(code, 1, out)
        self.assertIn("700 characters", out)

    def test_commit_from_another_local_branch_may_use_its_row(self):
        self.p.branch("feat-b")
        self.edit(b="B moved on")
        self.p.branch("feat-a", "main")
        self.p.git("merge", "-q", "--ff-only", "feat-b")
        sha = self.p.sha()
        self.assertEqual(self.run_hook(sha)[0], 0)

    def test_noop_without_logrows(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"logRows": False})
        self.p.branch("feat-a")
        sha = self.edit(b="A rewrote B", a="x" * 900)
        code, out, changed, pushed = self.run_hook(sha)
        self.assertEqual((code, out, changed, pushed), (0, "", [], []))

    def test_single_branch_clone_falls_back_to_unpushed_commits(self):
        p = self.p
        p.git("push", "-q", "--no-verify", "origin", "main:other")
        p.git("update-ref", "-d", "refs/remotes/origin/main")  # a single-branch clone has no origin/main
        p.branch("feat-a")
        p.write("src/x.txt", "x\n")
        p.commit("add x", env=DAY)
        sha = p.sha()
        code, out, changed, _ = self.run_hook(sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(changed, ["src/x.txt"])
        sha = self.edit(b="A rewrote B")
        code, out, _, _ = self.run_hook(sha)
        self.assertEqual(code, 1, out)

    def test_forks_from_the_configured_protected_branch(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        p = self.p = Utilidades(self.tmp, {"protectedBranch": "trunk"})
        p.git("push", "-q", "--no-verify", "origin", "main:trunk")
        p.git("update-ref", "-d", "refs/remotes/origin/main")  # only trunk is the protected branch here
        p.branch("feat-a")
        p.write("src/x1.txt", "1\n"); p.commit("x1", env=DAY)
        p.git("push", "-q", "--no-verify", "origin", "HEAD:refs/heads/feat-a-old")  # already on a remote ref
        p.write("src/x2.txt", "2\n"); p.commit("x2", env=DAY)
        code, out, changed, _ = self.run_hook(p.sha())
        self.assertEqual(code, 0, out)
        self.assertEqual(changed, ["src/x1.txt", "src/x2.txt"])

    def test_protected_branch_row_is_never_borrowed(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"protectedBranch": "feat-b"})
        self.p.branch("feat-b")
        self.edit(b="B moved on")
        self.p.branch("feat-a", "main")
        self.p.git("merge", "-q", "--ff-only", "feat-b")
        code, out, _, _ = self.run_hook(self.p.sha())
        self.assertEqual(code, 1, out)

    def test_pre_push_calls_it(self):
        self.p.branch("feat-a")
        self.edit(b="A rewrote B")
        code, out = self.p.push("origin", "feat-a")
        self.assertNotEqual(code, 0, out)
        self.assertIn("Task in progress · feat-b", out)
        self.assertIn("prepush-ramas.sh refused the push", out)
        code, out = self.p.push("origin", "feat-a", env={"BITACORA_COMPARTIDA": "1"})
        self.assertEqual(code, 0, out)


    def test_task_id_clash_with_the_protected_branch_refused_and_with_another_branch_warned(self):
        plan, env = "docs/plan.md", {"GW_PLAN": "docs/plan.md"}
        start = "- [ ] **INS-1** first\n"
        self.p.write(plan, start); self.p.commit("plan", env=DAY)
        self.p.git("push", "-q", "--no-verify", "origin", "main")
        base = self.p.sha()
        self.p.write(plan, start + "- [ ] **INS-2** the export\n"); self.p.commit("main opens INS-2", env=DAY)
        self.p.git("push", "-q", "--no-verify", "origin", "main")
        self.p.branch("feat-b", base)
        self.p.write(plan, start + "- [ ] **INS-3** the import\n"); self.p.commit("B opens INS-3", env=DAY)
        self.p.git("push", "-q", "--no-verify", "origin", "feat-b")
        self.p.branch("feat-a", base)
        self.p.write(plan, start + "- [ ] **INS-3** the form\n"); self.p.commit("A opens INS-3", env=DAY)
        code, out, _, _ = self.run_hook(self.p.sha(), env=env)
        self.assertEqual(code, 0, out)
        self.assertIn('WARNING: bitacora: INS-3 is a new task on this branch ("the form") and on refs/remotes/origin/feat-b', out)
        self.p.write(plan, start + "- [ ] **INS-2** the form\n"); self.p.commit("A opens INS-2", env=DAY)
        code, out, _, _ = self.run_hook(self.p.sha(), env=env)
        self.assertEqual(code, 1, out)
        self.assertIn('INS-2 is a new task on this branch ("the form") and on refs/remotes/origin/main ("the export")', out)
        self.assertIn("give yours a free id (INS-3)", out)

    def test_new_merge_that_kept_two_tasks_under_one_id_refused(self):
        plan, env = "docs/plan.md", {"GW_PLAN": "docs/plan.md"}
        start = "- [ ] **INS-1** first\n"
        self.p.write(plan, start); self.p.commit("plan", env=DAY)
        self.p.git("push", "-q", "--no-verify", "origin", "main")
        base = self.p.sha()
        self.p.write(plan, start + "- [ ] **INS-2** the export\n"); self.p.commit("main opens INS-2", env=DAY)
        self.p.git("push", "-q", "--no-verify", "origin", "main")
        self.p.branch("feat-a", base)
        self.p.write(plan, start + "- [ ] **INS-2** the form\n"); self.p.commit("A opens INS-2", env=DAY)
        self.p.git("merge", "-q", "--no-commit", "-s", "ours", "origin/main")
        self.p.write(plan, start + "- [ ] **INS-2** the form\n- [ ] **INS-2** the export\n")
        self.p.git("add", plan)
        self.p.git("commit", "-q", "--no-verify", "--no-edit")
        code, out, _, _ = self.run_hook(self.p.sha(), env=env)
        self.assertEqual(code, 1, out)
        self.assertIn("the merge keeps two different tasks with the id INS-2", out)
        self.assertIn("bitacora: in merge", out)
        self.p.write(plan, start + "- [ ] **INS-3** the form\n- [ ] **INS-2** the export\n"); self.p.commit("renumber", env=DAY)
        code, out, _, _ = self.run_hook(self.p.sha(), env=env)
        self.assertEqual(code, 0, out)


class Fusionar(Base):
    def agent(self, name="worktree-agent-1", path="a.txt", text="from the agent\n"):
        """A subagent's branch with its worktree (under .claude/worktrees/) and one commit."""
        wt = self.p.work / ".claude" / "worktrees" / name
        self.p.git("worktree", "add", "-q", "-b", name, str(wt))
        (wt / path).write_text(text)
        self.p.git("add", "-A", cwd=wt)
        self.p.git("commit", "-q", "-m", "agent work", cwd=wt, env=DAY)
        return wt

    def branches(self):
        return self.p.git("branch", "--format=%(refname:short)").stdout.split()

    def test_merges_runs_check_and_removes_worktree_and_branch(self):
        self.p.write("check.sh", "echo ran >> check.log\n")
        self.p.commit("check writes a log", env=DAY)
        wt = self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1", "--reviewed")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "a.txt").is_file())
        self.assertEqual((self.p.work / "check.log").read_text(), "ran\n")
        self.assertEqual(self.p.git("log", "-1", "--format=%s").stdout.strip(), "Merge agent 1")
        self.assertEqual(len(self.p.git("log", "-1", "--format=%P").stdout.split()), 2, "merge, not rebase")
        self.assertFalse(wt.exists(), out)
        self.assertNotIn("worktree-agent-1", self.branches())
        self.assertNotIn("--reviewed", out.replace("no --reviewed", ""))

    def test_check_wrapper_prefixes_every_check(self):
        self.p.write("wrap.sh", 'echo "wrapped: $*" >> wrap.log; "$@"\n')
        self.p.write("check.sh", "echo ran >> check.log\n")
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["checkWrapper"] = "bash wrap.sh"
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.commit("wrapper", env=DAY)
        self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1", "--reviewed")
        self.assertEqual(code, 0, out)
        self.assertIn("check OK: bash wrap.sh bash -c 'bash check.sh'", out)
        self.assertEqual((self.p.work / "wrap.log").read_text(), "wrapped: bash -c bash check.sh\n")

    def test_reminds_about_review_without_the_flag(self):
        self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1")
        self.assertEqual(code, 0, out)
        self.assertIn("no --reviewed", out)

    def test_conflict_stops_and_keeps_everything(self):
        wt = self.agent(path="docs/notes.md", text="agent notes\n")
        self.p.write("docs/notes.md", "main notes\n")
        self.p.commit("main edits the same file", env=DAY)
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1")
        self.assertEqual(code, 1, out)
        self.assertIn("CONFLICT", out)
        self.assertIn("docs/notes.md", out)
        self.assertIn("git merge --abort", out)
        self.assertTrue((self.p.work / ".git" / "MERGE_HEAD").is_file())
        self.assertTrue(wt.exists())
        self.assertIn("worktree-agent-1", self.branches())

    def test_failing_check_says_how_to_undo_and_keeps_the_branch(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, check="exit 1")
        wt = self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1")
        self.assertEqual(code, 1, out)
        self.assertIn("CHECK FAILED", out)
        self.assertIn("git reset --hard HEAD^1", out)
        self.assertTrue(wt.exists())
        self.assertIn("worktree-agent-1", self.branches())

    def test_session_branches_are_merged_but_not_deleted(self):
        self.p.git("checkout", "-q", "-b", "claude/topic")
        self.p.write("t.txt", "t\n")
        self.p.commit("topic", env=DAY)
        self.p.git("checkout", "-q", "main")
        code, out = self.p.script("fusionar.sh", "claude/topic", "Merge topic")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "t.txt").is_file())
        self.assertIn("claude/topic", self.branches())

    def test_unknown_branch_and_already_merged(self):
        self.assertEqual(self.p.script("fusionar.sh", "nope", "m")[0], 2)
        code, out = self.p.script("fusionar.sh", "main", "m")
        self.assertEqual(code, 0, out)
        self.assertIn("nothing to merge", out)


class RojoSinArreglo(Base):
    def setUp(self):
        super().setUp()
        self.p.write("fix.txt", "bad\n")
        self.p.commit("the bug", env=DAY)
        self.p.write("fix.txt", "good\n")  # the fix, uncommitted

    def stashes(self):
        return self.p.git("stash", "list").stdout.strip()

    def test_test_that_fails_without_the_fix_passes_the_check_and_restores_it(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")

    def test_test_that_passes_without_the_fix_is_detected(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "test -f fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("also passes WITHOUT the fix", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")

    def test_test_that_fails_with_the_fix_too(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "grep -q never fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("does not pass with the fix", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")

    def test_fix_file_without_changes_refused(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "true", "docs/notes.md")
        self.assertEqual(code, 2, out)
        self.assertIn("no uncommitted changes", out)

    def test_untracked_new_fix_file(self):
        self.p.write("new.txt", "x\n")
        code, out = self.p.script("rojo-sin-arreglo.sh", "test -f new.txt", "new.txt")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "new.txt").is_file())
        self.assertEqual(self.stashes(), "")

    def test_fails_with_checks_the_reason(self):
        cmd = "echo boom; grep -q good fix.txt"
        self.assertEqual(self.p.script("rojo-sin-arreglo.sh", "--fails-with", "boom", cmd, "fix.txt")[0], 0)
        code, out = self.p.script("rojo-sin-arreglo.sh", "--fails-with", "other reason", cmd, "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("another reason", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")

    def test_ran_one_requires_exactly_one_matching_line(self):
        one = "echo 'ok 1 - a'; grep -q good fix.txt"
        self.assertEqual(self.p.script("rojo-sin-arreglo.sh", "--ran-one", "^ok ", one, "fix.txt")[0], 0)
        two = "echo 'ok 1 - a'; echo 'ok 2 - b'; grep -q good fix.txt"
        code, out = self.p.script("rojo-sin-arreglo.sh", "--ran-one", "^ok ", two, "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("2 lines match /^ok /", out)
        code, out = self.p.script("rojo-sin-arreglo.sh", "--ran-one", "^ok ", "grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("0 lines match /^ok /", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")

    def test_options_combine_and_need_a_value(self):
        cmd = "echo boom; echo 'ok 1'; grep -q good fix.txt"
        code, out = self.p.script("rojo-sin-arreglo.sh", "--fails-with", "boom", "--ran-one", "^ok ", cmd, "fix.txt")
        self.assertEqual(code, 0, out)
        code, out = self.p.script("rojo-sin-arreglo.sh", "--ran-one")
        self.assertEqual(code, 2, out)
        self.assertIn("--ran-one needs a regex", out)


    def test_test_in_the_same_file_as_the_fix_is_refused(self):
        """INS P2: stashing the fix would take an uncommitted test with it, and the check would lie about the cause."""
        self.p.write("m.py", "def f(x):\n    return x\n\n\ndef test_f():\n    assert f(1) == 1\n")
        self.p.commit("old test", env=DAY)
        self.p.write("m.py", "def f(x):\n    return x + 1\n\n\ndef test_f():\n    assert f(1) == 2\n")
        cmd = "python3 -c 'import m; m.test_f()'"
        code, out = self.p.script("rojo-sin-arreglo.sh", cmd, "m.py")
        self.assertEqual(code, 2, out)
        self.assertIn("m.py has uncommitted changes that touch test code", out)
        self.assertIn("def test_f", out)  # the line that gave it away
        self.assertIn("Put the test in its own file or commit it first", out)
        self.assertNotIn("also passes WITHOUT the fix", out)
        self.assertNotIn("OK, the test fails", out)
        self.assertEqual(self.stashes(), "")  # refused before stashing anything
        self.assertIn("return x + 1", (self.p.work / "m.py").read_text())

    def test_edit_deep_inside_an_indented_test_method_is_refused(self):
        """The changed line is far from `def test_`, inside a class: the hunk header names only the class."""
        body = "".join(f"        x{i} = {i}\n" for i in range(8))
        self.p.write("t.py", "from base import Base\n\n\nclass T(Base):\n    def test_f(self):\n" + body
                     + "        self.assertEqual(1, 1)\n")
        self.p.commit("old test", env=DAY)
        self.p.write("t.py", (self.p.work / "t.py").read_text().replace("assertEqual(1, 1)", "assertEqual(2, 2)"))
        code, out = self.p.script("rojo-sin-arreglo.sh", "true", "t.py")
        self.assertEqual(code, 2, out)
        self.assertIn("t.py has uncommitted changes that touch test code", out)
        self.assertEqual(self.stashes(), "")

    def test_new_fix_file_with_a_test_is_refused_too(self):
        self.p.write("added.js", "it('works', () => {})\n")
        code, out = self.p.script("rojo-sin-arreglo.sh", "true", "added.js")
        self.assertEqual(code, 2, out)
        self.assertIn("added.js has uncommitted changes that touch test code", out)
        self.assertEqual(self.stashes(), "")

    def test_test_committed_apart_from_the_fix_is_accepted(self):
        """The same file holds an old committed test, but the uncommitted change only touches the code: no refusal."""
        self.p.write("m.py", "def f(x):\n    return x\n\n\ndef test_f():\n    assert f(1) == 2\n")
        self.p.commit("test first", env=DAY)
        self.p.write("m.py", "def f(x):\n    return x + 1\n\n\ndef test_f():\n    assert f(1) == 2\n")
        code, out = self.p.script("rojo-sin-arreglo.sh", "python3 -c 'import m; m.test_f()'", "m.py")
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)
        self.assertIn("return x + 1", (self.p.work / "m.py").read_text())

    def test_an_invalid_regex_fails_closed_before_touching_the_fix(self):
        cmd = "echo 'ok 1'; grep -q good fix.txt"
        for option in ("--ran-one", "--fails-with"):
            code, out = self.p.script("rojo-sin-arreglo.sh", option, "ok[", cmd, "fix.txt")
            self.assertEqual(code, 2, out)
            self.assertIn("/ok[/ is not a valid extended regex", out)
            self.assertNotIn("OK, the test fails", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")


class TestsRelacionados(Base):
    def run_with(self, related, changed=("src/a.py",), files=(), wrapper=None):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        if related is not None:
            cfg["relatedTests"] = related
        if wrapper is not None:
            cfg["checkWrapper"] = wrapper
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(cfg))
        for f in ("src/a.py", "name with space.txt", *files):
            self.p.write(f, "x\n")
        listing = self.tmp / "changed"
        listing.write_text("".join(f + "\n" for f in changed))
        (self.p.work / "out.log").write_text("")
        self.p.git("add", "-A"); self.p.git("commit", "-q", "--no-verify", "--allow-empty", "-m", "related setup")
        code, out = self.p.script("tests-relacionados.sh", str(listing), stdin="refs/heads/x 1 refs/heads/x 2\n")
        return code, out, (self.p.work / "out.log").read_text().splitlines()

    def test_paths_limits_an_entry_to_the_files_that_match(self):
        py = {"command": "for f in {files}; do echo \"py:$f\" >> out.log; done", "paths": "\\.py$"}
        md = {"command": "echo md-ran >> out.log", "paths": "\\.md$"}
        md_files = {"command": "echo \"md:{files}\" >> out.log", "paths": "\\.md$"}
        code, out, lines = self.run_with({"fast": [py, md, md_files], "slow": [dict(py, command="echo slow-py >> out.log")]},
                                         ("src/a.py", "name with space.txt"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["py:src/a.py", "slow-py"])

    def test_cwd_runs_there_with_files_relative_to_it(self):
        entry = {"command": "for f in {files}; do echo \"$(basename \"$PWD\"):$f\" >> ../out.log; done", "cwd": "app"}
        code, out, lines = self.run_with({"fast": [entry]}, ("src/a.py", "app/src/x.ts", "app/my file.ts"),
                                         files=("app/src/x.ts", "app/my file.ts"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["app:src/x.ts", "app:my file.ts"])

    def test_cwd_skips_an_entry_with_no_file_inside_it(self):
        fast = {"command": "echo fast-ran >> ../out.log", "cwd": "app", "paths": "\\.ts$"}
        slow = {"command": "echo slow-ran >> ../out.log", "cwd": "app"}
        code, out, lines = self.run_with({"fast": [fast], "slow": [slow]}, ("src/a.py",), files=("app/x.ts",))
        self.assertEqual((code, lines), (0, []), out)
        code, out, lines = self.run_with({"fast": [fast], "slow": [slow]}, ("app/x.ts",), files=("app/x.ts",))
        self.assertEqual((code, lines), (0, ["fast-ran", "slow-ran"]), out)

    def test_cwd_alone_still_runs_a_fast_command_without_files(self):
        entry = {"command": "echo ran-in-$(basename \"$PWD\") >> ../out.log", "cwd": "app"}
        code, out, lines = self.run_with({"fast": [entry]}, (), files=("app/x.ts",))
        self.assertEqual((code, lines), (0, ["ran-in-app"]), out)

    def test_string_and_object_entries_mix(self):
        code, out, lines = self.run_with({"fast": ["echo plain >> out.log", {"command": "echo obj >> out.log"}]})
        self.assertEqual((code, lines), (0, ["plain", "obj"]), out)

    def test_wrapper_prefixes_every_command_and_runs_from_the_root_with_cwd(self):
        self.p.write("wrap.sh", 'echo "wrap:$(basename "$PWD"):$1" >> out.log; "$@"\n')
        slow = {"command": "echo \"in-$(basename \"$PWD\")\" >> ../out.log", "cwd": "app"}
        code, out, lines = self.run_with({"fast": ["echo plain >> out.log"], "slow": [slow]}, ("app/x.ts",),
                                         files=("app/x.ts",), wrapper="bash wrap.sh")
        self.assertEqual(code, 0, out)
        self.assertIn("related tests (fast): bash wrap.sh bash -c 'echo plain >> out.log'", out)
        self.assertEqual(lines, ["wrap:work:bash", "plain", "wrap:work:bash", "in-app"])

    def test_invalid_entries_fail_closed_with_the_reason(self):
        for bad, reason in (({"paths": "x"}, "missing required key 'command'"),
                            ({"command": "x", "paths": "("}, "is not a valid regex"),
                            ({"command": "x", "cwd": "../up"}, "does not match"),
                            ({"command": "x", "cwd": "/abs"}, "does not match"),
                            ({"command": "x", "other": 1}, "unknown key 'other'")):
            code, out, _ = self.run_with({"fast": [bad]})
            self.assertEqual(code, 1, out)
            self.assertIn("config is invalid", out)
            self.assertIn(reason, out)

    def test_fast_then_slow_with_quoted_existing_files(self):
        fast = "for f in {files}; do echo \"fast:$f\" >> out.log; done"
        slow = "for f in {files}; do echo \"slow:$f\" >> out.log; done"
        code, out, lines = self.run_with({"fast": [fast], "slow": [slow]},
                                         ("src/a.py", "gone.py", "name with space.txt"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["fast:src/a.py", "fast:name with space.txt", "slow:src/a.py", "slow:name with space.txt"])

    def test_no_changed_files_runs_only_fast_commands_without_files(self):
        related = {"fast": ["echo always >> out.log", "echo withfiles {files} >> out.log"],
                   "slow": ["echo slow >> out.log"]}
        code, out, lines = self.run_with(related, ())
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["always"])

    def test_failure_stops_and_names_the_command(self):
        code, out, lines = self.run_with({"fast": ["exit 3"], "slow": ["echo slow >> out.log"]})
        self.assertEqual(code, 1, out)
        self.assertIn("failed (fast): exit 3", out)
        self.assertEqual(lines, [])

    def test_slow_failure(self):
        code, out, _ = self.run_with({"slow": ["false {files}"]})
        self.assertEqual(code, 1, out)
        self.assertIn("(slow)", out)

    def test_noop_when_absent_or_empty(self):
        for related in (None, {}, {"fast": [], "slow": []}):
            code, out, lines = self.run_with(related)
            self.assertEqual((code, out, lines), (0, "", []), related)

    def test_invalid_config_fails_closed(self):
        code, out, _ = self.run_with({"fast": "not a list"})
        self.assertEqual(code, 1, out)
        self.assertIn("config is invalid", out)

    def test_pre_push_runs_it_on_the_changed_files(self):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["relatedTests"] = {"fast": ["echo {files} > related.log"]}
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.branch("feat-a")
        self.p.write("src/b.py", "b\n")
        self.p.commit("add b", env=DAY)
        code, out = self.p.push("origin", "feat-a")
        self.assertEqual(code, 0, out)
        self.assertIn("src/b.py", (self.p.work / "related.log").read_text())

    def test_pre_push_runs_them_on_the_pushed_commit(self):
        p = self.p
        out_log = self.tmp / "related.log"
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["relatedTests"] = {"fast": [f"echo {{files}} > {out_log}; cat src/b.py >> {out_log}"]}
        p.write(".claude/gw.json", json.dumps(cfg))
        p.branch("feat-a")
        p.write("src/b.py", "committed-b\n"); p.write("src/gone.py", "g\n")
        p.commit("add b", env=DAY)
        p.git("rm", "-q", "src/gone.py"); p.git("commit", "-q", "--no-verify", "-m", "drop gone")
        (p.work / "src" / "b.py").unlink()            # dirty working tree: the file is only in the commit
        p.write("src/gone.py", "untracked again\n")   # and this one only on disk
        code, out = p.push("origin", "feat-a")
        self.assertEqual(code, 0, out)
        text = out_log.read_text()
        self.assertIn("src/b.py", text)
        self.assertNotIn("src/gone.py", text)
        self.assertIn("committed-b", text)


class EnlacesMd(Base):
    config = {"staleRefs": ["fase 3\\.5", "INS-\\d{2}"]}

    def run_it(self, *args):
        self.p.git("add", "-A")
        return self.p.script("enlaces-md.py", *args)

    def test_clean_docs_pass(self):
        self.p.write("README.md", "[notes](docs/notes.md) [web](https://example.com/x) [mail](mailto:a@b.c)\n")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)

    def test_broken_link_and_anchor_listed_with_line(self):
        self.p.write("docs/a.md", "# Title\n\n[gone](missing.md)\n[ok](#title) [bad](#nope) [other](notes.md#x)\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:3: no such file missing.md", out)
        self.assertIn("docs/a.md:4: (this file) has no heading with the anchor #nope", out)
        self.assertIn("docs/a.md:4: notes.md has no heading with the anchor #x", out)
        self.assertNotIn("#title", out)
        self.assertIn("rerun: python3", out)
        code, out = self.run_it("--files-only")
        self.assertIn("no such file missing.md", out)
        self.assertNotIn("anchor", out)

    def test_links_in_code_are_ignored(self):
        self.p.write("docs/a.md", "```\n[x](nope.md)\n```\nand `[y](nope2.md)`\n")
        self.assertEqual(self.run_it()[0], 0)

    def test_stale_reference_hit_case_insensitive(self):
        self.p.write("docs/a.md", "ok\nSee FASE 3.5 and INS-12 here\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:2: stale reference /fase 3\\.5/ matches 'FASE 3.5'", out)
        self.assertIn("INS-12", out)
        self.p.write("README.es.md", "fase 3.5\n")
        self.assertIn("README.es.md:1", self.run_it()[1])

    def test_log_claude_and_other_folders_are_skipped(self):
        for rel in (LOG, ".claude/notes.md", "notes/other.md", "src/readme.txt"):
            self.p.write(rel, "fase 3.5 and INS-12\n")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)

    def test_invalid_regex_fails_closed(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"staleRefs": ["("]})
        code, out = self.run_it()
        self.assertEqual(code, 2, out)
        self.assertIn("not a valid regex", out)


class EnlacesMdSkipAndRoots(Base):
    """`staleRefs.skip` (globs the stale-reference check does not read) and `linkRoots` (folders that link from the
    repo root)."""

    def project(self, config):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, config)

    def run_it(self, *args):
        self.p.git("add", "-A")
        return self.p.script("enlaces-md.py", *args)

    def stale(self, **skip):
        return {"staleRefs": dict({"patterns": ["fase 3\\.5"]}, **skip)}

    def test_old_list_form_still_works_and_skips_nothing_extra(self):
        self.project({"staleRefs": ["fase 3\\.5"]})
        self.p.write("docs/registros/retro-1.md", "fase 3.5\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/registros/retro-1.md:1: stale reference", out)

    def test_skip_globs_hide_matching_files_only(self):
        self.project(self.stale(skip=["docs/registros/retro-*.md", "docs/historia/", "docs/**/old.md"]))
        for rel in ("docs/registros/retro-1.md", "docs/historia/a.md", "docs/historia/sub/b.md", "docs/x/y/old.md",
                    "docs/old.md"):
            self.p.write(rel, "fase 3.5\n")
        self.p.write("docs/registros/other.md", "fase 3.5\n")           # not matched by the glob
        self.p.write("docs/registros/sub/retro-2.md", "fase 3.5\n")     # `*` does not cross folders
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        hits = sorted(l.split(":")[0] for l in out.splitlines() if "stale reference" in l)
        self.assertEqual(hits, ["docs/registros/other.md", "docs/registros/sub/retro-2.md"])

    def test_empty_skip_and_a_glob_matching_nothing_hide_nothing(self):
        for skip in ([], ["nothing/here/*.md"]):
            with self.subTest(skip=skip):
                self.project(self.stale(skip=skip))
                self.p.write("docs/a.md", "fase 3.5\n")
                code, out = self.run_it()
                self.assertEqual(code, 1, out)
                self.assertIn("docs/a.md:1: stale reference", out)

    def test_missing_patterns_or_an_empty_object_check_nothing(self):
        for config in ({"staleRefs": {"skip": ["docs/"]}}, {"staleRefs": {}}):
            with self.subTest(config=config):
                self.project(config)
                self.p.write("docs/a.md", "fase 3.5\n")
                code, out = self.run_it()
                self.assertEqual(code, 0, out)

    def test_skip_does_not_hide_broken_links(self):
        self.project(self.stale(skip=["docs/"]))
        self.p.write("docs/a.md", "[x](gone.md)\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:1: no such file gone.md", out)

    def test_bad_skip_glob_fails_closed_with_the_fix(self):
        for bad in ("/abs/path", "../up", ""):
            with self.subTest(glob=bad):
                self.project(self.stale(skip=[bad]))
                code, out = self.run_it()
                self.assertEqual(code, 2, out)
                self.assertIn("staleRefs.skip[0]", out)
                self.assertIn("config.py", out)

    def test_staleRefs_object_with_an_unknown_key_fails_closed(self):
        self.project({"staleRefs": {"patterns": [], "skips": ["docs/"]}})
        code, out = self.run_it()
        self.assertEqual(code, 2, out)
        self.assertIn("matches none of the allowed forms", out)

    def test_link_roots_resolve_from_the_repo_root(self):
        self.project({"linkRoots": ["docs/prs"]})
        self.p.write("docs/notes.md", "# Notes\n")
        self.p.write("docs/prs/pr-1.md", "[ok](docs/notes.md#notes) [gone](docs/nope.md)\n")
        self.p.write("docs/prs/sub/pr-2.md", "[ok](docs/notes.md)\n")
        self.p.write("docs/other.md", "[own](notes.md) [rootish](docs/notes.md)\n")   # outside linkRoots: own folder
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/prs/pr-1.md:1: no such file docs/nope.md", out)
        self.assertNotIn("docs/prs/pr-1.md:1: no such file docs/notes.md", out)
        self.assertNotIn("anchor", out)
        self.assertIn("docs/other.md:1: no such file docs/notes.md", out)
        self.assertNotIn("docs/prs/sub/pr-2.md", out)

    def test_link_roots_slash_links_resolve_from_the_repo_root_and_never_leave_it(self):
        self.project({"linkRoots": ["docs/prs"]})
        self.p.write("docs/notes.md", "# Notes\n")
        self.p.write("docs/prs/a.md", "[ok](/docs/notes.md#notes) [gone](/docs/nope.md)\n")
        self.p.write("docs/other.md", "[abs](/docs/notes.md)\n")           # outside linkRoots: `/` is still the repo root
        self.p.write("docs/prs/out.md", "[up](../../../../../../etc/hostname) [etc](/etc/hostname) [dots](../../../x.md)\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/prs/a.md:1: no such file /docs/nope.md", out)
        self.assertNotIn("docs/prs/a.md:1: no such file /docs/notes.md", out)
        self.assertNotIn("docs/other.md", out)
        self.assertIn("docs/prs/out.md:1: link ../../../../../../etc/hostname leaves the repo; point it inside the repo", out)
        self.assertIn("docs/prs/out.md:1: no such file /etc/hostname", out)
        self.assertIn("link ../../../x.md leaves the repo", out)

    def test_without_link_roots_the_own_folder_rule_is_unchanged(self):
        for config in (None, {"linkRoots": []}):
            with self.subTest(config=config):
                self.project(config)
                self.p.write("docs/notes.md", "# Notes\n")
                self.p.write("docs/prs/pr-1.md", "[from root](docs/notes.md)\n")
                code, out = self.run_it()
                self.assertEqual(code, 1, out)
                self.assertIn("docs/prs/pr-1.md:1: no such file docs/notes.md", out)

    def test_link_roots_with_slashes_dot_and_prefix_lookalikes(self):
        self.project({"linkRoots": ["./docs/prs/"]})
        self.p.write("docs/notes.md", "x\n")
        self.p.write("docs/prs/a.md", "[ok](docs/notes.md)\n")
        self.p.write("docs/prs-old/b.md", "[ok](docs/notes.md)\n")         # `docs/prs-old` is not under docs/prs
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/prs-old/b.md:1: no such file", out)
        self.assertNotIn("docs/prs/a.md", out)
        self.project({"linkRoots": ["."]})
        self.p.write("docs/notes.md", "x\n")
        self.p.write("docs/prs/a.md", "[ok](docs/notes.md)\n")
        self.assertEqual(self.run_it()[0], 0)

    def test_link_roots_must_stay_inside_the_repo(self):
        for bad in ("/abs", "../up"):
            with self.subTest(root=bad):
                self.project({"linkRoots": [bad]})
                code, out = self.run_it()
                self.assertEqual(code, 2, out)
                self.assertIn("linkRoots[0]", out)


class RepoItself(unittest.TestCase):
    def test_scripts_are_executable_and_versioned(self):
        for name in SCRIPTS:
            path = ROOT / "scripts" / name
            with self.subTest(script=name):
                self.assertTrue(path.stat().st_mode & 0o111, f"{name} must be executable: chmod +x scripts/{name}")
                head = path.read_text(encoding="utf-8").splitlines()[:3]
                self.assertIn(f"# galivelop-workflow v{VERSION}", head)
                self.assertTrue(head[0].startswith("#!"))

    def test_python_scripts_do_not_write_bytecode(self):
        for name in (n for n in SCRIPTS if n.endswith(".py")):
            self.assertIn("sys.dont_write_bytecode = True", (ROOT / "scripts" / name).read_text(encoding="utf-8"))

    def test_gw_json_of_this_repo_is_valid(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "config.py"), "validate"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads((ROOT / ".claude" / "gw.json").read_text())["version"], VERSION)


if __name__ == "__main__":
    unittest.main()
