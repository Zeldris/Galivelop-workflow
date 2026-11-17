"""The task record (C11): taskRecord in config.py, scripts/task.py (new, log, resolve), the templates, and the
commit-msg check of commit-message.py (a contract touched and a new decision log entry in a feat/fix/hotfix commit
that changes code), end to end through `git commit` in a temporary project."""
import json
import re
import shutil
import subprocess
import sys
import unittest

from test_hooks import Base, ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402
import task  # noqa: E402

ROADMAP = "# Roadmap\n\n| id | task |\n|---|---|\n| C11 | record |\n| C12 | other |\n"
TASK = ROOT / "scripts" / "task.py"
DOTS = " · "


def contract(extra=""):
    return ("# C11 · record\n\n## Goal\n\nx\n\n## Scope\n\n—\n\n## Acceptance\n\n- [ ] —\n\n## Files\n\n—\n\n"
            "## Change log\n\n—\n\n## Verification\n\n—\n" + extra)


def entry(task_id="C11", head=None, drop=None, empty=None):
    parts = [head or f"# 2026-11-17{DOTS}session{DOTS}pending{DOTS}{task_id}"]
    for name in ("Why", "Alternatives", "Changed because"):
        if name != drop:
            parts.append(f"## {name}\n\n" + ("" if name == empty else "reason"))
    return "\n\n".join(parts) + "\n"


class Record(Base):
    hooks = ("pre-push", "pre-commit", "commit-msg")
    config = {}

    def build(self):
        super().build()
        shutil.copy2(TASK, self.p.work / ".claude" / "gw" / "scripts" / "task.py")
        self.p.write("docs/roadmap.md", ROADMAP)
        self.p.git("add", "-A")
        self.p.git("commit", "-q", "--no-verify", "-m", "roadmap")

    def enable(self, **keys):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg.update(commitFormat="conventional", commitRefs=True, taskId="[A-Z]\\d+", refsSources=["docs/roadmap.md"])
        cfg["taskRecord"] = dict({"enabled": True}, **keys)
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.git("add", "-A")
        self.p.git("commit", "-q", "--no-verify", "-m", "config")

    def attempt(self, message, files, n=[0]):
        n[0] += 1
        self.p.write("src/code.py", f"x = {n[0]}\n")
        for rel, text in files.items():
            self.p.write(rel, text)
        return self.p.commit(message, ok=False)

    def good(self, message, files):
        r = self.attempt(message, files)
        self.assertEqual(r.returncode, 0, r.stderr)

    def refused(self, message, files, *reasons):
        before = self.p.sha()
        r = self.attempt(message, files)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertEqual(self.p.sha(), before)
        self.assertIn("commit-msg:", r.stderr)
        for reason in reasons:
            self.assertIn(reason, r.stderr)
        self.p.git("reset", "-q", "--hard", "HEAD")
        self.p.git("clean", "-qfd")

    FULL = {"docs/tasks/C11.md": contract(), "docs/tasks/C11/2026-11-17-session-abc1234.md": entry()}


class Config(unittest.TestCase):
    def test_defaults_are_off_and_match_the_design(self):
        tr = config.task_record({})
        self.assertFalse(tr["enabled"])
        self.assertEqual(tr["path"], "docs/tasks")
        self.assertEqual(tr["requiredFor"], ["feat", "fix", "hotfix"])
        self.assertEqual(tr["sections"], ["Goal", "Scope", "Acceptance", "Files", "Change log", "Verification"])
        self.assertEqual(tr["logSections"], ["Why", "Alternatives", "Changed because"])  # A8: names in English
        template = json.loads((ROOT / "templates" / "gw.json").read_text())
        self.assertEqual(template["taskRecord"], tr)
        self.assertIn("taskRecord", template["fullCheckSkipKeys"])

    def test_a_bad_value_is_refused_by_the_schema(self):
        out = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "config.py"), "validate"], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)


class Hook(Record):
    def test_disabled_by_default_changes_nothing(self):
        self.good("feat(C11): code only\n\nRefs: C11", {})

    def test_complete_record_passes(self):
        self.enable()
        self.good("feat(C11): code\n\nRefs: C11", self.FULL)

    def test_fix_and_hotfix_are_required_too(self):
        self.enable()
        for t in ("fix", "hotfix"):
            with self.subTest(t=t):
                self.refused(f"{t}(C11): code\n\nRefs: C11", {}, "does not touch its task record docs/tasks/C11.md")

    def test_missing_contract(self):
        self.enable()
        self.refused("feat(C11): code\n\nRefs: C11", {"docs/tasks/C11/2026-11-17-session-abc1234.md": entry()},
                     "does not touch its task record docs/tasks/C11.md", "task.py new C11")

    def test_missing_entry(self):
        self.enable()
        self.refused("feat(C11): code\n\nRefs: C11", {"docs/tasks/C11.md": contract()},
                     "adds no decision log entry in docs/tasks/C11/", "task.py log C11 --agent")

    def test_an_edited_entry_is_not_a_new_one(self):
        self.enable()
        self.good("feat(C11): code\n\nRefs: C11", self.FULL)
        self.refused("fix(C11): more\n\nRefs: C11", {"docs/tasks/C11.md": contract("more\n"),
                                                     "docs/tasks/C11/2026-11-17-session-abc1234.md": entry() + "edit\n"},
                     "adds no decision log entry")

    def test_entry_form(self):
        self.enable()
        bad = {
            "no header": (entry(head="# a title"), "the first line is not"),
            "bad date": (entry(head=f"# 17/11/2026{DOTS}session{DOTS}pending{DOTS}C11"), "the first line is not"),
            "wrong id": (entry(task_id="C12"), "names the id 'C12', not 'C11'"),
            "bad commit": (entry(head=f"# 2026-11-17{DOTS}session{DOTS}soon{DOTS}C11"), "not `pending` or a sha"),
            "no section": (entry(drop="Alternatives"), "no non-empty `## Alternatives`"),
            "empty section": (entry(empty="Why"), "no non-empty `## Why`"),
            "no id": (entry(head=f"# 2026-11-17{DOTS}session{DOTS}pending"), "the first line is not"),
        }
        for name, (text, why) in bad.items():
            with self.subTest(name=name):
                self.refused("feat(C11): code\n\nRefs: C11", {"docs/tasks/C11.md": contract(),
                                                             "docs/tasks/C11/2026-11-17-session-abc1234.md": text}, why)

    def test_a_resolved_sha_in_the_header_is_accepted(self):
        self.enable()
        text = entry(head=f"# 2026-11-17{DOTS}gw-orchestrate-dealer{DOTS}0a1b2c3{DOTS}C11")
        self.good("feat(C11): code\n\nRefs: C11", {"docs/tasks/C11.md": contract(), "docs/tasks/C11/x.md": text})

    def test_contract_form(self):
        self.enable()
        self.refused("feat(C11): code\n\nRefs: C11", {"docs/tasks/C11.md": "# C11\n\n## Goal\n\nx\n",
                                                     "docs/tasks/C11/a.md": entry()}, "no `## Scope` section")
        swapped = contract().replace("## Scope", "## Tmp").replace("## Goal", "## Scope").replace("## Tmp", "## Goal")
        self.refused("feat(C11): code\n\nRefs: C11", {"docs/tasks/C11.md": swapped, "docs/tasks/C11/a.md": entry()},
                     "not in the order")

    def test_every_ref_needs_its_record(self):
        self.enable()
        self.refused("feat(C11): code\n\nRefs: C11, C12", self.FULL, "docs/tasks/C12.md")
        both = dict(self.FULL, **{"docs/tasks/C12.md": contract().replace("C11", "C12"),
                                  "docs/tasks/C12/a.md": entry("C12")})
        self.good("feat(C11): code\n\nRefs: C11, C12", both)

    def test_no_refs_is_refused_with_the_reason(self):
        self.enable(), self.configure_refs_off()
        self.refused("feat: code", self.FULL, "has no Refs trailer")

    def configure_refs_off(self):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["commitRefs"] = False
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.git("add", "-A")
        self.p.git("commit", "-q", "--no-verify", "-m", "refs off")

    def test_exemptions(self):
        self.enable()
        self.good("docs(C11): words\n\nRefs: C11", {})  # a type outside requiredFor
        self.good("refactor(C11): shape\n\nRefs: C11", {})
        self.good("WIP: feat(C11): half\n\nRefs: C11", {})
        self.p.git("rm", "-q", "--cached", "-r", "src")  # nothing staged but content below
        n = self.p.sha()
        self.p.write("docs/notes.md", "only content\n")
        self.p.git("add", "-A")
        r = self.p.git("commit", "-q", "-m", "feat(C11): only content\n\nRefs: C11", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)  # content is not code
        self.assertNotEqual(self.p.sha(), n)

    def test_the_review_mark_commit_is_exempt(self):
        self.enable()
        sha = "0123456789abcdef0123456789abcdef01234567"
        r = self.attempt(f"Reviewed: {sha}\n\nRefs: C11", {})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_merge_is_exempt(self):
        self.enable()
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("src/side.py", "s\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "side")
        p.git("checkout", "-q", "main")
        p.write("src/main.py", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "main")
        r = p.git("merge", "--no-ff", "-m", "Merge side", "side", ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_files_under_the_record_path_alone_are_not_code(self):
        self.enable(path="notes/tasks")  # outside `content`, so only the exclusion keeps them from counting
        self.p.write("notes/tasks/C11.md", contract())
        self.p.git("add", "-A")
        r = self.p.git("commit", "-q", "-m", "feat(C11): record only\n\nRefs: C11", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)


class Script(Record):
    def task(self, *args, ok=True):
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "task.py"), *args)
        if ok:
            self.assertEqual(code, 0, out)
        return code, out

    def test_new_log_resolve_make_a_record_the_hook_accepts(self):
        self.enable()
        self.task("new", "C11", "--title", "record")
        code, out = self.task("log", "C11", "--agent", "gw-orchestrate-dealer", "--date", "2026-11-17")
        rel = out.strip()
        self.assertRegex(rel, r"^docs/tasks/C11/2026-11-17-gw-orchestrate-dealer-[0-9a-f]{7}\.md$")
        text = (self.p.work / rel).read_text(encoding="utf-8")
        for name in ("Why", "Alternatives", "Changed because"):  # the template holds — in each: filled in below
            text = text.replace(f"## {name}\n\n—", f"## {name}\n\nbecause")
        (self.p.work / rel).write_text(text, encoding="utf-8")
        self.good("feat(C11): code\n\nRefs: C11", {})
        code, out = self.task("resolve", "C11")
        self.assertEqual(out.split()[0], self.p.sha()[:len(out.split()[0])])  # the commit that added it, not "pending"
        self.assertIn(rel, out)

    def test_resolve_before_the_commit_says_pending(self):
        self.enable()
        self.task("log", "C11", "--agent", "session")
        self.assertTrue(self.task("resolve", "C11")[1].startswith("pending  docs/tasks/C11/"))

    def test_refusals_say_why(self):
        self.enable()
        self.task("new", "C11")
        code, out = self.task("new", "C11", ok=False)
        self.assertEqual(code, 1)
        self.assertIn("docs/tasks/C11.md exists already", out)
        code, out = self.task("log", "C11", "--agent", "claude-opus", ok=False)
        self.assertIn("never a model", out)
        code, out = self.task("log", "C11", "--agent", "Bad Agent!", ok=False)
        self.assertIn("never a model", out)
        code, out = self.task("log", "C11", "--agent", "session", "--date", "17-11", ok=False)
        self.assertIn("is not YYYY-MM-DD", out)
        code, out = self.task("new", "nope", ok=False)
        self.assertIn("does not have the shape of taskId", out)

    def test_two_entries_of_one_day_do_not_collide(self):
        self.enable()
        a = self.task("log", "C11", "--agent", "session", "--date", "2026-11-17")[1]
        b = self.task("log", "C11", "--agent", "session", "--date", "2026-11-17")[1]
        self.assertNotEqual(a, b)


class Templates(unittest.TestCase):
    def test_the_templates_are_what_task_py_writes(self):
        for lang in ("es", "en"):
            cfg = {"language": lang}
            tmpl = (ROOT / "templates" / lang / "task.md").read_text(encoding="utf-8").split("\n", 1)[1]  # no marker line
            title = "<título>" if lang == "es" else "<title>"
            self.assertEqual(task.contract_text(cfg, "<id>"), tmpl.replace("<id> · " + title, "<id> · " + title))
            entry_tmpl = (ROOT / "templates" / lang / "task-entry.md").read_text(encoding="utf-8").split("\n", 1)[1]
            marker = "<skill o session>" if lang == "es" else "<skill or session>"
            self.assertEqual(task.entry_text(cfg, "<id>", marker, "<date>").replace("pending", "<pending>"), entry_tmpl)

    def test_a_generated_contract_and_entry_pass_their_own_form_check(self):
        cfg = {"language": "en"}
        self.assertEqual(task.contract_errors(task.contract_text(cfg, "C11"), cfg), [])
        text = task.entry_text(cfg, "C11", "session", "2026-11-17").replace("—", "x")
        self.assertEqual(task.entry_errors(text, "C11", cfg), [])


if __name__ == "__main__":
    unittest.main()
