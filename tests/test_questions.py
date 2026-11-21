"""scripts/questions.py (C1-C3, C10): the questions file, its commands and the exported readers."""
import datetime
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import questions  # noqa: E402

SCRIPT = ROOT / "scripts" / "questions.py"
TODAY = datetime.date.today().isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, env=env)
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "gw.json").write_text((ROOT / "templates" / "gw.json").read_text())
        self.file = self.root / "docs" / "questions.md"

    def q(self, *args):
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args], capture_output=True,
                           text=True)
        return r.returncode, r.stdout, r.stderr

    def ok(self, *args):
        code, out, err = self.q(*args)
        self.assertEqual(code, 0, err)
        return out

    def fails(self, reason, *args):
        before = self.file.read_bytes() if self.file.exists() else None
        code, out, err = self.q(*args)
        self.assertEqual(code, 1, out)
        self.assertIn(reason, err)
        self.assertEqual(self.file.read_bytes() if self.file.exists() else None, before, "nothing is written")


class Add(Base):
    def test_assigns_consecutive_ids_and_creates_the_file(self):
        out = self.ok("add", "--refs", "C1", "--rec", "a", "--rec", "b", "One?", "Two?")
        self.assertEqual(out.split(), ["Q-1", "Q-2"])
        self.assertEqual(self.ok("add", "Three?").split(), ["Q-3"])
        text = self.file.read_text()
        self.assertTrue(text.startswith("# Questions"))
        self.assertIn(f"## Q-1\n- Refs: C1\n- Status: open\n- Asked: {TODAY}\n- Question: One?\n- Recommendation: a\n",
                      text)

    def test_multiline_question_is_one_line(self):
        self.ok("add", "a\nb   c")
        self.assertIn("- Question: a b c\n", self.file.read_text())

    def test_rec_next_to_each_question(self):
        self.assertEqual(self.ok("add", "--refs", "C1", "--rec", "a", "One?", "--rec", "b", "Two?", "--rec", "c",
                                 "Three?").split(), ["Q-1", "Q-2", "Q-3"])
        text = self.file.read_text()
        self.assertIn("- Question: Two?\n- Recommendation: b\n", text)
        self.assertIn("- Question: Three?\n- Recommendation: c\n", text)

    def test_unknown_option_still_fails(self):
        code, _, err = self.q("add", "--rec", "a", "One?", "--bogus", "x")
        self.assertEqual(code, 2)
        self.assertIn("unrecognized arguments: --bogus x", err)
        self.assertFalse(self.file.exists(), "nothing is written")

    def test_rec_count_must_match(self):
        self.fails("2 --rec for 1 questions", "add", "--rec", "a", "--rec", "b", "One?")

    def test_empty_question_fails(self):
        self.fails("no question text", "add", "  ")

    def test_ids_continue_after_answered_ones(self):
        self.ok("add", "One?")
        self.ok("answer", "1. yes")
        self.assertEqual(self.ok("add", "Two?").split(), ["Q-2"])

    def test_config_path_is_honoured(self):
        cfg = self.root / ".claude" / "gw.json"
        cfg.write_text(cfg.read_text().rstrip().rstrip("}").rstrip() + ',\n  "questions": {"path": "notes/q.md"}\n}\n')
        self.ok("add", "One?")
        self.assertTrue((self.root / "notes" / "q.md").is_file())
        self.assertFalse(self.file.exists())


class ListAndCount(Base):
    def test_open_only_then_all_and_refs(self):
        self.ok("add", "--refs", "A1", "--rec", "r", "One?")
        self.ok("add", "--refs", "B2", "Two?")
        self.ok("answer", "1. yes")
        out = self.ok("list")
        self.assertIn("Two?", out)
        self.assertNotIn("One?", out)
        self.assertIn("One?", self.ok("list", "--all"))
        self.assertIn("Answer (%s): yes" % TODAY, self.ok("list", "--all"))
        self.assertEqual(self.ok("list", "--refs", "A1").strip(), "no open questions")

    def test_count(self):
        self.assertEqual(self.ok("count").strip(), "0")
        self.ok("add", "--refs", "A1", "One?", "Two?")
        self.ok("add", "--refs", "B2", "Three?")
        self.assertEqual(self.ok("count").strip(), "3")
        self.assertEqual(self.ok("count", "--refs", "A1").strip(), "2")
        self.assertEqual(self.ok("count", "--refs", "A").strip(), "0")

    def test_missing_file_is_empty(self):
        self.assertEqual(self.ok("list").strip(), "no open questions")
        self.assertEqual(self.ok("list", "--all").strip(), "no questions")


class Answer(Base):
    def setUp(self):
        super().setUp()
        self.ok("add", "One?", "Two?", "Three?")

    def test_answers_by_number_with_date(self):
        self.ok("answer", "1. a, 3. ok")
        text = self.file.read_text()
        self.assertIn(f"- Status: answered\n- Asked: {TODAY}\n- Question: One?\n- Answer: a\n- Answered: {TODAY}", text)
        self.assertEqual(self.ok("count").strip(), "1")

    def test_commas_inside_an_answer_and_q_prefix(self):
        self.ok("answer", "Q-1: yes, but later; 2) fine;\n3. x")
        text = self.file.read_text()
        self.assertIn("- Answer: yes, but later\n", text)
        self.assertIn("- Answer: fine\n", text)

    def test_unknown_number_writes_nothing(self):
        self.fails("Q-9 does not exist", "answer", "1. a; 9. b")

    def test_already_answered_fails(self):
        self.ok("answer", "1. a")
        self.fails("Q-1 is already answered", "answer", "1. b")

    def test_unreadable_answers_and_empty_answer(self):
        self.fails("cannot read the answers", "answer", "yes")
        self.fails("is empty", "answer", "1. , 2. b")

    def test_marker_inside_an_answer_does_not_answer_another_question(self):
        self.ok("answer", "1. pick 1, 2) or 3")
        text = self.file.read_text()
        self.assertIn("- Answer: pick 1, 2) or 3\n", text)
        self.assertEqual(self.ok("count").strip(), "2")

    def test_comma_marker_only_for_an_open_question(self):
        self.ok("answer", "1. version 7. ok, 3. fine")
        text = self.file.read_text()
        self.assertIn("- Answer: version 7. ok\n", text)
        self.assertIn("- Answer: fine\n", text)

    def test_semicolon_always_separates(self):
        self.ok("answer", "1. a; 2) b")
        self.assertEqual(self.ok("count").strip(), "1")

    def test_same_number_twice_fails(self):
        self.fails("answered twice", "answer", "1. a, 1. b")


class AcceptRisk(Base):
    def setUp(self):
        super().setUp()
        self.ok("add", "--refs", "A1", "One?", "Two?")
        self.ok("add", "--refs", "B2", "Three?")

    def test_one_question(self):
        self.ok("accept-risk", "Q-2")
        text = self.file.read_text()
        self.assertIn(f"- Status: accepted-risk\n- Asked: {TODAY}\n- Question: Two?\n- Accepted: {TODAY}", text)
        self.assertEqual(self.ok("count").strip(), "2")

    def test_all_of_a_task(self):
        self.ok("accept-risk", "--refs", "A1")
        self.assertEqual(self.ok("count").strip(), "1")

    def test_failures(self):
        self.fails("does not exist", "accept-risk", "Q-7")
        self.fails("has no open questions", "accept-risk", "--refs", "Z9")
        self.fails("name one question or one task", "accept-risk")
        self.fails("is not a question id", "accept-risk", "abc")
        self.ok("accept-risk", "Q-1")
        self.fails("already accepted-risk", "accept-risk", "Q-1")


class Hardening(Base):
    def test_refs_cannot_inject_lines(self):
        self.fails("is not a list of task ids", "add", "--refs", "B4\n- Status: answered", "One?")
        self.fails("is not a list of task ids", "add", "--refs", "B4 B5", "One?")

    def test_refs_are_normalised(self):
        self.ok("add", "--refs", "B4 ,B5", "One?")
        self.assertIn("- Refs: B4, B5\n", self.file.read_text())

    def test_failed_write_leaves_no_tmp(self):
        self.ok("add", "One?")
        orig = os.replace
        os.replace = lambda *a: (_ for _ in ()).throw(OSError("boom"))
        try:
            with self.assertRaises(questions.QuestionsError):
                questions.write(self.file, "", [])
        finally:
            os.replace = orig
        self.assertFalse(self.file.with_name("questions.md.tmp").exists())

    def test_invalid_utf8_is_a_questions_error(self):
        self.file.parent.mkdir()
        self.file.write_bytes(b"## Q-1\n- Status: open\n- Question: \xff\n")
        for fn in (questions.read_entries, questions.open_entries):
            with self.assertRaises(questions.QuestionsError):
                fn(self.file)
        with self.assertRaises(questions.QuestionsError):
            questions.open_for_task(self.file, "A1")
        self.fails("cannot read", "count")

    def test_question_without_refs_blocks_no_task(self):
        self.ok("add", "No task?")
        self.assertEqual(questions.open_for_task(self.file, "A1"), [])
        self.assertEqual(questions.open_for_task(self.file, ""), [])

    def test_questions_file_returns_path_and_root(self):
        path, root = questions.questions_file(self.root)
        # Resolved on both sides: on macOS the temp dir is /var/..., which git reports as /private/var/...
        want = self.root.resolve()
        self.assertEqual((path.resolve(), root.resolve()), (want / "docs" / "questions.md", want))

    def test_concurrent_adds_get_different_ids(self):
        procs = [subprocess.Popen([sys.executable, str(SCRIPT), "--root", str(self.root), "add", f"Q{i}?"],
                                  stdout=subprocess.PIPE, text=True) for i in range(5)]
        ids = sorted(p.communicate()[0].strip() for p in procs)
        self.assertEqual(ids, ["Q-1", "Q-2", "Q-3", "Q-4", "Q-5"])


class Reading(Base):
    def test_open_for_task_and_unknown_lines_survive(self):
        self.ok("add", "--refs", "A1, B2", "One?")
        self.ok("add", "--refs", "C3", "Two?")
        text = self.file.read_text().replace("- Question: One?\n", "- Question: One?\n- Note: keep me\n")
        self.file.write_text(text)
        self.ok("answer", "2. x")
        self.assertIn("- Note: keep me\n", self.file.read_text())
        self.assertEqual([e.id for e in questions.open_for_task(self.file, "B2")], ["Q-1"])
        self.assertEqual(questions.open_for_task(self.file, "C3"), [])
        self.assertEqual(questions.open_for_task(self.root / "none.md", "A1"), [])

    def test_bad_status_and_repeated_id_fail_closed(self):
        self.file.parent.mkdir()
        self.file.write_text("## Q-1\n- Status: bogus\n")
        self.fails("Status 'bogus'", "count")
        self.file.write_text("## Q-1\n- Status: open\n## Q-1\n- Status: open\n")
        self.fails("appears twice", "list")

    def test_header_is_kept(self):
        self.file.parent.mkdir()
        self.file.write_text("# My own title\n\nnotes\n")
        self.ok("add", "One?")
        self.assertTrue(self.file.read_text().startswith("# My own title\n\nnotes\n\n## Q-1\n"))


class Notice(Base):
    def test_full_list_once_then_count(self):
        self.ok("add", "One?")
        first = self.ok("notice")
        self.assertIn("1 open questions (docs/questions.md)", first)
        self.assertIn("One?", first)
        again = self.ok("notice")
        self.assertEqual(again.strip(), "1 open questions (docs/questions.md)")
        self.ok("add", "Two?")
        self.assertIn("One?", self.ok("notice"))

    def test_silent_without_open_questions(self):
        self.assertEqual(self.ok("notice"), "")
        self.ok("add", "One?")
        self.ok("answer", "1. a")
        self.assertEqual(self.ok("notice"), "")

    def test_mark_lives_in_the_git_dir(self):
        self.ok("add", "One?")
        self.ok("notice")
        self.assertEqual((self.root / ".git" / "gw" / "questions-shown").read_text().strip(), "1")


if __name__ == "__main__":
    unittest.main()
