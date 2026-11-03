"""scripts/reviewed.sh warning about code changed since the previous review mark (D24, private-project-1 P6).

Reuses the temporary-repo helpers of test_hooks.py (imported, not modified). The warning never blocks the mark.
"""
import unittest

from test_hooks import Base


class UnreviewedWarning(Base):
    def setUp(self):
        super().setUp()
        p = self.p
        p.git("checkout", "-q", "-b", "feature")
        self.script = str(p.work / ".claude" / "gw" / "scripts" / "reviewed.sh")

    def commit_push(self, rel, text):
        self.p.write(rel, text); self.p.commit("change " + rel)
        self.assertEqual(self.p.push("-u", "origin", "feature")[0], 0)

    def mark(self):
        code, out = self.p.run("bash", self.script)
        self.assertEqual(code, 0, out)  # a warning never blocks
        self.assertIn("Reviewed: ", self.p.git("log", "-1", "--format=%s").stdout)
        return out

    def test_first_mark_lists_code_since_the_fork(self):
        self.commit_push("src/a.py", "a = 1\n")
        self.commit_push("docs/notes.md", "changed\n")
        out = self.mark()
        self.assertIn("warning: code changed since the fork from origin/main", out)
        self.assertIn("  src/a.py", out)
        self.assertNotIn("docs/notes.md", out)  # content, not code

    def test_second_mark_lists_only_code_after_the_previous_mark(self):
        self.commit_push("src/a.py", "a = 1\n")
        self.mark()
        self.assertEqual(self.p.push("origin", "feature")[0], 0)
        prev = self.p.sha("HEAD~1")
        self.commit_push("src/b.py", "b = 1\n")
        out = self.mark()
        self.assertIn("code changed since the previous review mark " + prev, out)
        self.assertIn("  src/b.py", out)
        self.assertNotIn("src/a.py", out)

    def test_no_warning_when_only_content_changed(self):
        self.commit_push("docs/notes.md", "changed\n")
        out = self.mark()
        self.assertNotIn("warning", out)

    def test_no_warning_after_a_mark_with_nothing_new(self):
        self.commit_push("src/a.py", "a = 1\n")
        self.mark()
        self.assertEqual(self.p.push("origin", "feature")[0], 0)
        out = self.mark()
        self.assertNotIn("warning", out)

    def test_path_with_spaces_listed_whole(self):
        self.commit_push("src/my file.py", "a = 1\n")
        self.assertIn("  src/my file.py\n", self.mark())

    def test_unusable_previous_mark_falls_back_to_the_fork(self):
        self.commit_push("docs/revisado.txt", "0" * 40 + "\n")  # a sha that is no commit
        self.commit_push("src/a.py", "a = 1\n")
        out = self.mark()
        self.assertIn("no usable previous mark", out)
        self.assertIn("  src/a.py", out)


if __name__ == "__main__":
    unittest.main()
