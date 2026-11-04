"""scripts/reviewed.sh warning about code changed since the previous review mark (D24, private-project-1 P6).

Reuses the temporary-repo helpers of test_hooks.py (imported, not modified). The warning never blocks the mark.
"""
import json
import unittest
from pathlib import Path

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

    def test_code_merged_from_main_is_not_listed(self):
        self.commit_push("src/a.py", "a = 1\n")
        self.mark()
        self.assertEqual(self.p.push("origin", "feature")[0], 0)
        # main advances with code of its own, the branch brings it in by merge and changes one more file
        self.p.git("checkout", "-q", "main")
        self.p.write("src/from_main.py", "m = 1\n"); self.p.commit("code on main")
        self.assertEqual(self.p.push("--no-verify", "origin", "main")[0], 0)
        self.p.git("checkout", "-q", "feature")
        self.p.git("merge", "-q", "--no-edit", "origin/main")
        self.commit_push("src/mine.py", "b = 1\n")
        out = self.mark()
        self.assertIn("  src/mine.py", out)
        self.assertNotIn("from_main.py", out)

    def test_only_merged_code_gives_no_warning(self):
        self.commit_push("docs/notes.md", "changed\n")
        self.p.git("checkout", "-q", "main")
        self.p.write("src/from_main.py", "m = 1\n"); self.p.commit("code on main")
        self.assertEqual(self.p.push("--no-verify", "origin", "main")[0], 0)
        self.p.git("checkout", "-q", "feature")
        self.p.git("merge", "-q", "--no-edit", "origin/main")
        self.assertEqual(self.p.push("origin", "feature")[0], 0)
        self.assertNotIn("warning", self.mark())

    def test_mark_inherited_from_main_is_named_as_such(self):
        self.p.git("checkout", "-q", "main")
        self.p.write("src/released.py", "r = 1\n"); self.p.commit("released code")
        self.p.write("docs/revisado.txt", self.p.sha() + "\n"); self.p.commit("release mark")
        released = self.p.sha("HEAD~1")
        self.assertEqual(self.p.push("--no-verify", "origin", "main")[0], 0)
        self.p.git("checkout", "-q", "feature")
        self.p.git("merge", "-q", "--no-edit", "origin/main")
        self.commit_push("src/a.py", "a = 1\n")
        out = self.mark()
        self.assertIn("inherited from origin/main (this branch has no mark of its own)", out)
        self.assertNotIn("previous review mark", out)
        self.assertIn("  src/a.py", out)
        self.assertNotIn("released.py", out)


class MarkFooter(Base):
    """commitNext default footer, explicit --footer, hint on commit-msg failure, unreadable config (D36, WMF P2)."""

    def setUp(self):
        super().setUp()
        self.p.git("checkout", "-q", "-b", "feature")
        self.script = str(self.p.work / ".claude" / "gw" / "scripts" / "reviewed.sh")
        self.p.write("docs/a.md", "a\n"); self.p.commit("change")
        self.assertEqual(self.p.push("-u", "origin", "feature")[0], 0)

    def configure(self, **keys):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg.update(keys)
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.commit("config")
        self.assertEqual(self.p.push("origin", "feature")[0], 0)

    def body(self, *args):
        code, out = self.p.run("bash", self.script, *args)
        self.assertEqual(code, 0, out)
        return self.p.git("log", "-1", "--format=%B").stdout.strip()

    def test_commit_next_default_footer_english(self):
        self.configure(commitNext=True)
        msg = self.body()
        self.assertTrue(msg.startswith("Reviewed: "), msg)
        self.assertTrue(msg.endswith("\n\nNext: open the PR"), msg)

    def test_commit_next_default_footer_spanish(self):
        self.configure(commitNext=True, language="es")
        msg = self.body()
        self.assertTrue(msg.startswith("Revisado: "), msg)
        self.assertTrue(msg.endswith("\n\nSiguiente: crear el PR"), msg)

    def test_no_footer_without_commit_next(self):
        self.configure(commitNext=False)
        msg = self.body()
        self.assertNotIn("\n", msg)

    def test_explicit_footer_wins_over_the_default(self):
        self.configure(commitNext=True)
        msg = self.body("--footer", "Siguiente: pasar a main")
        self.assertTrue(msg.endswith("\n\nSiguiente: pasar a main"), msg)
        self.assertNotIn("open the PR", msg)

    def test_commit_msg_failure_suggests_footer(self):
        hook = self.p.work / ".githooks" / "commit-msg"
        hook.write_text("#!/bin/sh\necho 'stub: missing next step' >&2\nexit 1\n")
        hook.chmod(0o755)
        code, out = self.p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)
        self.assertIn("stub: missing next step", out)
        self.assertIn("could not commit", out)
        self.assertIn('--footer "Siguiente: <next step>"', out)

    def test_unreadable_config_fails_closed_with_its_reason(self):
        self.p.write(".claude/gw.json", "{not json")
        code, out = self.p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)
        self.assertIn("cannot read", out)
        self.assertIn("config.py", out)
        self.assertIn("validate", out)
        self.assertNotIn("Reviewed:", self.p.git("log", "-1", "--format=%s").stdout)


class InstalledCopies(unittest.TestCase):
    def test_installed_scripts_match_their_source(self):
        root = Path(__file__).resolve().parent.parent
        drift = [f.name for f in sorted((root / "scripts").iterdir())
                 if (root / ".claude" / "gw" / "scripts" / f.name).is_file()
                 and (root / ".claude" / "gw" / "scripts" / f.name).read_bytes() != f.read_bytes()]
        self.assertEqual(drift, [], "installed copy differs from scripts/; refresh it: cp scripts/<name> .claude/gw/scripts/<name>")



class MarkUnderStrictCommitMsg(Base):
    """The mark commit passes a commit-msg with conventional format, Refs and next step on (code review of 0.5.0)."""
    hooks = ("pre-push", "pre-commit", "commit-msg")

    def test_the_mark_commit_is_accepted_in_both_languages(self):
        p = self.p
        p.git("checkout", "-q", "-b", "feature")
        script = str(p.work / ".claude" / "gw" / "scripts" / "reviewed.sh")
        for language, subject in (("en", "Reviewed: "), ("es", "Revisado: ")):
            with self.subTest(language=language):
                cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
                cfg.update(commitFormat="conventional", commitRefs=True, commitNext=True, language=language)
                p.write(".claude/gw.json", json.dumps(cfg))
                p.git("add", ".claude/gw.json")
                p.git("commit", "-q", "--no-verify", "-m", "config " + language)
                self.assertEqual(p.push("--no-verify", "-u", "origin", "feature")[0], 0)
                code, out = p.run("bash", script)
                self.assertEqual(code, 0, out)
                msg = p.git("log", "-1", "--format=%B").stdout.strip()
                self.assertTrue(msg.startswith(subject + p.sha("HEAD~1")), msg)
                self.assertEqual(p.push("--no-verify", "origin", "feature")[0], 0)


if __name__ == "__main__":
    unittest.main()
