"""`handoff.py close-row <id>` closes a task (C11): the record's Acceptance and Verification are checked (every reason
listed, nothing written) and the roadmap rows go to done. A branch name still closes a branch row."""
import json
import shutil
import sys
import unittest

from test_hooks import ROOT
from test_utils import Base as UtilsBase, LOG, log_text, Utils

sys.dont_write_bytecode = True
ES = "# Roadmap\n\n| id | task | status |\n|---|---|---|\n| C11 | record | pendiente |\n| C12 | other | pendiente |\n"
EN = "# Roadmap\n\n| id | task | status |\n|---|---|---|\n| C11 | record | pending |\n| C12 | other | pending |\n"
CHECK = 'section() { echo "== $1"; }\nsection "unit tests"\nsection "shell scripts (lint)"\n'
TESTS = "import unittest\n\n\nclass Good(unittest.TestCase):\n    def test_y(self):\n        pass\n"
CONFIG = {"taskId": "[A-Z]\\d+", "check": ["bash check.sh"], "roadmapFiles": [
    {"path": "docs/roadmap.md", "done": "hecho", "open": ["pendiente"]},
    {"path": "docs/roadmap.en.md", "done": "done", "open": ["pending"]}]}


def record(acceptance="- [x] works (`tests/test_ok.py::Good::test_y`)", verification=None, nl="\n"):
    verification = "Commit {sha}, `python3 -m unittest`." if verification is None else verification
    text = (f"# C11 · record\n\n## Goal\n\nx\n\n## Scope\n\n—\n\n## Acceptance\n\n{acceptance}\n\n## Files\n\n—\n\n"
            f"## Change log\n\n—\n\n## Verification\n\n{verification}\n")
    return text.replace("\n", nl)


class CloseTask(UtilsBase):
    def build(self):
        self.p = Utils(self.tmp, CONFIG)
        for name in ("task.py", "roadmap.py"):
            shutil.copy2(ROOT / "scripts" / name, self.p.scripts / name)
        self.p.write("docs/roadmap.md", ES)
        self.p.write("docs/roadmap.en.md", EN)
        self.p.write("check.sh", CHECK)
        self.p.write("tests/test_ok.py", TESTS)
        self.p.commit("fixtures")
        self.sha = self.p.sha()[:9]

    def put(self, **kw):
        path = self.p.work / "docs/tasks/C11.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(record(**kw).replace("{sha}", self.sha).encode())  # bytes: "\r\n" stays as written

    def close(self, *args):
        return self.p.script("handoff.py", "close-row", *(args or ("C11",)))

    def refused(self, why, **kw):
        self.put(**kw)
        code, out = self.close()
        self.assertEqual(code, 1, out)
        self.assertIn(why, out)
        self.assertIn("nothing was written", out)
        self.assertIn("pendiente", (self.p.work / "docs/roadmap.md").read_text())
        return out

    def test_a_ready_record_marks_both_roadmaps_and_says_so(self):
        self.put()
        code, out = self.close()
        self.assertEqual(code, 0, out)
        self.assertRegex((self.p.work / "docs/roadmap.md").read_text(), r"\| C11 \| record \| hecho \(\d{4}-\d{2}-\d{2}\) \|")
        self.assertRegex((self.p.work / "docs/roadmap.en.md").read_text(), r"\| C11 \| record \| done \(")
        self.assertIn("| C12 | other | pendiente |", (self.p.work / "docs/roadmap.md").read_text())
        self.assertIn("docs/roadmap.md:5: hecho (", out)

    def test_a_check_section_counts_as_a_test(self):
        self.put(acceptance="- [x] lint (`== shell scripts (lint)`)\n- [x] units (`== unit tests`)")
        self.assertEqual(self.close()[0], 0)

    def test_unticked_box(self):
        out = self.refused("box not ticked", acceptance="- [x] a (`tests/test_ok.py::Good`)\n- [ ] b")
        self.assertIn("1 reasons", out)

    def test_every_reason_is_listed(self):
        out = self.refused("not ready", acceptance="- [ ] a\n- [x] no test here", verification="—")
        self.assertIn("3 reasons", out)
        self.assertIn("box not ticked", out)
        self.assertIn("ticked without a test", out)
        self.assertIn("is empty or still the template", out)

    def test_box_without_a_test(self):
        self.refused("ticked without a test", acceptance="- [x] it works, trust me")

    def test_nonexistent_test_file(self):
        self.refused("tests/test_nope.py, which does not exist", acceptance="- [x] a (`tests/test_nope.py::Good`)")

    def test_test_file_outside_the_project_or_without_the_class(self):
        self.refused("which does not exist", acceptance="- [x] a (`../test_x.py::Good`)")
        self.refused("has no class Bad", acceptance="- [x] a (`tests/test_ok.py::Bad`)")
        self.refused("has no test test_z", acceptance="- [x] a (`tests/test_ok.py::Good::test_z`)")

    def test_the_test_must_be_inside_the_named_class_and_real(self):
        self.p.write("tests/test_two.py", 'class A:\n    def test_a(self):\n        pass\n\n\nclass B:\n    def test_y(self):\n'
                     '        pass\n\n\n"""\nclass Ghost:\n    pass\n"""\n')
        self.refused("class A of tests/test_two.py has no test test_y", acceptance="- [x] a (`tests/test_two.py::A::test_y`)")
        self.refused("has no class Ghost", acceptance="- [x] a (`tests/test_two.py::Ghost`)")
        self.put(acceptance="- [x] a (`tests/test_two.py::B::test_y`)")
        self.assertEqual(self.close()[0], 0)

    def test_nonexistent_check_section(self):
        self.refused("`== nope`, which no `check` command prints", acceptance="- [x] a (`== nope`)")

    def test_empty_or_template_verification(self):
        self.refused("`## Verification` is empty or still the template", verification="—")
        self.refused("`## Verification` is empty or still the template", verification="")

    def test_a_path_or_branch_in_backticks_is_not_a_command(self):
        self.refused("names no command", verification=f"Commit {self.sha}\n\n`docs/questions.md`")
        self.refused("names no command", verification=f"Commit {self.sha} en `main`")
        self.refused("names no command", verification=f"Commit {self.sha}, `docs/roadmap.md`")
        self.put(verification=f"Commit {self.sha}, `check.sh`")  # an existing script is a command
        self.assertEqual(self.close()[0], 0)

    def test_a_section_prefix_is_not_a_section(self):
        self.refused("`== unit`, which no `check` command prints", acceptance="- [x] a (`== unit`)")
        self.refused("`== s`, which no `check` command prints", acceptance="- [x] a (`== s`)")
        self.put(acceptance="- [x] a (`== shell scripts (lint)`)")
        self.assertEqual(self.close()[0], 0)

    def test_unknown_sha(self):
        self.refused("abcdef12, which is not a commit", verification="Commit abcdef12, `python3 -m unittest`.")

    def test_verification_without_sha_or_without_command(self):
        self.refused("names no commit sha", verification="`python3 -m unittest` passes")
        self.refused("names no command", verification=f"Commit {self.sha}")

    def test_no_checkbox_and_missing_section(self):
        self.refused("has no checkbox", acceptance="free text")
        self.p.write("docs/tasks/C11.md", "# C11 · x\n\n## Goal\n\nx\n")
        code, out = self.close()
        self.assertEqual(code, 1, out)
        self.assertIn("has no `## Acceptance` section", out)
        self.assertIn("has no `## Verification` section", out)

    def test_missing_record_names_task_new(self):
        code, out = self.close("C12")
        self.assertEqual(code, 1, out)
        self.assertIn("has no task record", out)
        self.assertIn("task.py new C12", out)
        self.assertIn("pendiente", (self.p.work / "docs/roadmap.md").read_text())

    def test_row_already_done_is_refused(self):
        self.put()
        self.assertEqual(self.close()[0], 0)
        code, out = self.close()
        self.assertEqual(code, 1, out)
        self.assertIn("C11 is not open", out)
        self.assertIn("nothing was written", out)

    def test_a_task_without_a_roadmap_row_is_refused(self):
        self.p.write("docs/tasks/C13.md", record().replace("C11", "C13").replace("{sha}", self.sha))
        code, out = self.close("C13")
        self.assertEqual(code, 1, out)
        self.assertIn("no row for C13", out)

    def test_an_id_that_is_also_a_branch_name_follows_the_record(self):
        self.p.write(LOG, log_text().replace("feat-a", "C11").replace("feat-b", "C12"))
        self.put()
        self.assertEqual(self.close("C11")[0], 0)
        self.assertIn("doing A", (self.p.work / LOG).read_text())  # the branch row was not touched
        self.assertIn("hecho", (self.p.work / "docs/roadmap.md").read_text())
        code, out = self.close("C12")  # no record: the branch row closes
        self.assertEqual(code, 0, out)
        self.assertIn("Merged, branch finished", (self.p.work / LOG).read_text())
        self.put()
        self.p.write("docs/roadmap.md", ES)
        self.assertEqual(self.close("--branch", "C11")[0], 0)  # --branch is always a branch
        self.assertIn("pendiente", (self.p.work / "docs/roadmap.md").read_text())

    def test_text_is_for_branches(self):
        self.put()
        code, out = self.close("C11", "--text", "x")
        self.assertEqual(code, 2, out)
        self.assertIn("--text is for a branch row", out)

    def test_works_without_logrows(self):
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        cfg["logRows"] = False
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.put()
        self.assertEqual(self.close()[0], 0)
        code, out = self.close("C12")
        self.assertEqual(code, 1, out)
        self.assertIn("task.py new C12", out)

    def test_crlf_record(self):
        self.put(nl="\r\n")
        code, out = self.close()
        self.assertEqual(code, 0, out)

    def test_crlf_record_still_refuses(self):
        self.put(acceptance="- [ ] a", nl="\r\n")
        code, out = self.close()
        self.assertEqual(code, 1, out)
        self.assertIn("box not ticked", out)

    def test_empty_roadmap_files_is_refused(self):
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        cfg["roadmapFiles"] = []
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.put()
        code, out = self.close()
        self.assertEqual(code, 1, out)
        self.assertIn("roadmapFiles is empty", out)


if __name__ == "__main__":
    unittest.main()
