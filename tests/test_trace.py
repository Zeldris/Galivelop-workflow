"""scripts/trace.py (D14): everything about a task id, gathered on the spot. Edge cases covered: id in every source,
whole-word matching (D1 vs D14 and D14a), Refs lists and scopes, WIP, merge commits, unknown id, malformed ids, --json,
--limit, a missing roadmap file, no roadmapFiles, not a repo. Failing cases check the message, not only the code."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

sys.dont_write_bytecode = True
SCRIPT = ROOT / "scripts" / "trace.py"
FILES = [
    {"path": "docs/roadmap.md", "done": "hecho", "open": ["pendiente"]},
    {"path": "docs/roadmap.en.md", "done": "done", "open": ["pending"]},
]
ES = "# Roadmap\n\n## `0.7` «Trazar»\n\n| Id | Tarea | Estado |\n|---|---|---|\n| D14 | `trace.py` | pendiente |\n| D1 | Otra | pendiente |\n| E9-E16 | Rango | pendiente |\n| D61, D62 | Lista | pendiente |\n"
EN = "# Roadmap\n\n## `0.7` «Trace»\n\n| Id | Task | Status |\n|---|---|---|\n| D14 | `trace.py` | pending |\n"


class Repo:
    def __init__(self, tmp, roadmap_files=True):
        self.root = Path(tmp)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_CONFIG_GLOBAL=str(self.root / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        (self.root / "gitconfig").write_text("[user]\n\tname = T\n\temail = t@example.com\n[commit]\n\tgpgsign = false\n"
                                             "[init]\n\tdefaultBranch = main\n")
        self.work = self.root / "work"
        self.work.mkdir()
        self.git("init", "-q")
        cfg = dict(BASE_CONFIG, log="docs/log.md", pendingFile="docs/pending.md", taskId="[A-H]\\d+[a-z]?")
        if roadmap_files:
            cfg["roadmapFiles"] = FILES
        self.write(".claude/gw.json", json.dumps(cfg))
        self.write("docs/roadmap.md", ES)
        self.write("docs/roadmap.en.md", EN)
        self.write("docs/log.md", "# Log\n\nNow: D14 in progress; D1 done; D14a later\n")
        self.write("docs/pending.md", "# Pending\n\n- Pending: D14 follow-up\n")
        self.write("docs/design.md", "Design of D14 here.\nNothing about D1.\n")
        self.write(".claude/skills/x.md", "copy that names D14\n")
        self.commit("chore: base")

    def git(self, *args):
        r = subprocess.run(["git", *args], cwd=self.work, env=self.env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)

    def trace(self, *args, root=True):
        cmd = [sys.executable, "-B", str(SCRIPT)] + list(args) + (["--root", str(self.work)] if root else [])
        return subprocess.run(cmd, env=self.env, capture_output=True, text=True, cwd=self.root)


class Trace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Repo(self._tmp.name)

    def test_id_in_every_source(self):
        r = self.repo
        r.commit("feat(D14): the script\n\nbody\n\nRefs: D14\nSiguiente: x")
        r.git("checkout", "-q", "-b", "agent/D14-x")
        r.commit("chore: no id here")
        r.git("checkout", "-q", "main")
        r.git("merge", "--no-ff", "-q", "-m", "Merge branch 'agent/D14-x'", "agent/D14-x")
        out = r.trace("D14")
        self.assertEqual(out.returncode, 0, out.stderr)
        for expected in ("== roadmap (1)", "docs/roadmap.md:7", "(also docs/roadmap.en.md:7)", "#### declared",
                         "#### deduced", "`0.7` «Trazar»", "== log (1)",
                         "== pending (1)", "[refs] feat(D14): the script", "[merge] Merge branch 'agent/D14-x'",
                         "== docs (1)", "docs/design.md:1"):
            self.assertIn(expected, out.stdout)
        self.assertNotIn("chore: no id here", out.stdout)  # a commit of the merged branch with no id is not declared
        self.assertNotIn(".claude/skills", out.stdout)  # generated copies are skipped

    def test_whole_word_match(self):
        out = self.repo.trace("D1", "--json")
        data = json.loads(out.stdout)
        self.assertEqual([x["line"] for x in data["declared"]["roadmap"]], [8])  # not the D14 rows
        self.assertEqual(len(data["deduced"]["log"]), 1)  # "D1 done" matches; the D14 and D14a words alone would not
        self.assertEqual(data["deduced"]["docs"][0]["line"], 2)  # not "Design of D14"
        self.assertEqual(data["deduced"]["pending"], [])

    def test_prefix_id_does_not_match_suffix_id(self):
        out = self.repo.trace("D14a", "--json")
        data = json.loads(out.stdout)
        self.assertEqual(data["declared"]["roadmap"], [])
        self.assertEqual(len(data["deduced"]["log"]), 1)

    def test_refs_list_scope_and_wip(self):
        r = self.repo
        r.commit("feat(D3, D14): scoped\n\nRefs: D3")
        r.commit("WIP: fix(D14): half\n\nRefs: D4, D14\nSiguiente: z")
        r.commit("fix(D140): other\n\nRefs: D140")
        data = json.loads(r.trace("D14", "--json").stdout)
        self.assertEqual([(c["how"], c["subject"]) for c in data["declared"]["commits"]],
                         [("refs", "WIP: fix(D14): half"), ("scope", "feat(D3, D14): scoped")])

    def test_mention_in_body_is_not_declared(self):
        self.repo.commit("chore: tidy\n\nThis relates to D14 loosely.")
        data = json.loads(self.repo.trace("D14", "--json").stdout)
        self.assertEqual(data["declared"]["commits"], [])

    def test_ranges_and_lists(self):
        r = self.repo
        r.commit("feat(E9-E16): range scope\n\nRefs: E9-E16")
        r.commit("fix(D61, D62): list scope")
        for task, rows in (("E12", 1), ("E16", 1), ("E9", 1), ("E17", 0), ("E8", 0), ("D62", 1), ("D63", 0)):
            data = json.loads(r.trace(task, "--json").stdout)
            self.assertEqual(len(data["declared"]["roadmap"]), rows, task)
            self.assertEqual(len(data["declared"]["commits"]), 1 if task in ("E12", "E16", "E9", "D62") else 0, task)
        out = r.trace("E17")
        self.assertEqual(out.returncode, 1)

    def test_merge_body_does_not_count(self):
        r = self.repo
        r.git("checkout", "-q", "-b", "agent/D63-x")
        r.commit("chore: x")
        r.git("checkout", "-q", "main")
        r.git("merge", "--no-ff", "-q", "-m", "Merge D63\n\nRefs: D63\nSiguiente: fusionar D14", "agent/D63-x")
        self.assertEqual(json.loads(r.trace("D14", "--json").stdout)["declared"]["commits"], [])
        self.assertEqual(len(json.loads(r.trace("D63", "--json").stdout)["declared"]["commits"]), 1)

    def test_unreadable_doc_is_a_note(self):
        (self.repo.work / "docs" / "bad.md").write_bytes(b"\xff\xfe D14\n")
        self.repo.commit("chore: bad doc")
        out = self.repo.trace("D14")
        self.assertIn("note: cannot read docs/bad.md", out.stdout)

    def test_unknown_id(self):
        out = self.repo.trace("D99")
        self.assertEqual(out.returncode, 1)
        self.assertIn("nothing names it", out.stderr)
        self.assertEqual(out.stdout, "")
        data = json.loads(self.repo.trace("D99", "--json").stdout)
        self.assertFalse(data["found"])

    def test_malformed_ids(self):
        for bad in ("d14", "14", "D", "D14 ", "D14;x", "../D14", "D14|D1"):
            out = self.repo.trace(bad)
            self.assertEqual(out.returncode, 2, bad)
            self.assertIn("is not a task id", out.stderr, bad)
            self.assertIn("taskId", out.stderr)

    def test_json(self):
        self.repo.commit("feat(D14): j\n\nRefs: D14")
        out = self.repo.trace("D14", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        data = json.loads(out.stdout)
        self.assertEqual(sorted(data), ["declared", "deduced", "found", "id", "notes"])
        self.assertEqual(sorted(data["declared"]), ["commits", "roadmap", "task"])
        self.assertEqual(sorted(data["deduced"]), ["docs", "log", "pending"])
        self.assertTrue(data["found"])
        self.assertEqual(data["id"], "D14")
        self.assertEqual(data["declared"]["commits"][0]["how"], "refs")
        self.assertEqual(len(data["declared"]["commits"][0]["sha"]), 40)
        row, = data["declared"]["roadmap"]  # the translation is folded into the first row, not listed twice
        self.assertEqual(row["file"], "docs/roadmap.md")
        self.assertEqual(row["also"], [{"file": "docs/roadmap.en.md", "line": 7}])

    def test_no_docs_skips_the_markdown_search(self):
        out = self.repo.trace("D14", "--no-docs", "--json")
        data = json.loads(out.stdout)
        self.assertEqual(data["deduced"]["docs"], [])
        self.assertEqual(len(data["declared"]["roadmap"]), 1)
        self.assertEqual(len(data["deduced"]["log"]), 1)
        self.assertNotIn("== docs", self.repo.trace("D14", "--no-docs").stdout)
        # nothing reads the .md files: an unreadable one raises no note (it does without the flag)
        (self.repo.work / "docs" / "bad.md").write_bytes(b"\xff\xfe D14\n")
        self.repo.commit("chore: bad doc")
        self.assertEqual(json.loads(self.repo.trace("D14", "--no-docs", "--json").stdout)["notes"], [])
        self.assertTrue(json.loads(self.repo.trace("D14", "--json").stdout)["notes"])

    def test_unknown_id_with_no_docs_says_docs_were_skipped(self):
        self.repo.write("docs/only.md", "D77 only here\n")
        self.repo.commit("docs: only")
        out = self.repo.trace("D77", "--no-docs")
        self.assertEqual(out.returncode, 1)
        self.assertIn("tracked .md files were skipped (--no-docs)", out.stderr)
        self.assertNotIn("and tracked .md files)", out.stderr)
        self.assertIn("and tracked .md files)", self.repo.trace("D78").stderr)

    def test_declared_and_deduced_are_separate(self):
        self.repo.commit("feat(D14): d\n\nRefs: D14")
        out = self.repo.trace("D14").stdout
        self.assertLess(out.index("#### declared"), out.index("== roadmap"))
        self.assertLess(out.index("== commits"), out.index("#### deduced"))
        self.assertLess(out.index("#### deduced"), out.index("== log"))
        self.assertLess(out.index("== log"), out.index("== docs"))

    def test_limit(self):
        for n in range(4):
            self.repo.commit(f"feat(D14): n{n}\n\nRefs: D14")
        out = self.repo.trace("D14", "--limit", "2")
        self.assertIn("… 2 more", out.stdout)
        self.assertEqual(len(json.loads(self.repo.trace("D14", "--json", "--limit", "2").stdout)["declared"]["commits"]), 4)
        bad = self.repo.trace("D14", "--limit", "0")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("--limit must be 1 or more", bad.stderr)

    def test_missing_roadmap_file_is_a_note(self):
        (self.repo.work / "docs" / "roadmap.en.md").unlink()
        out = self.repo.trace("D14")
        self.assertEqual(out.returncode, 0)
        self.assertIn("note: cannot read docs/roadmap.en.md", out.stdout)
        self.assertIn("docs/roadmap.md:7", out.stdout)

    def test_no_roadmap_files_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp, roadmap_files=False)
            data = json.loads(repo.trace("D14", "--json").stdout)
            self.assertEqual(data["declared"]["roadmap"], [])
            self.assertEqual(len(data["deduced"]["log"]), 1)
            # without roadmapFiles the roadmap file is just another document
            self.assertIn("docs/roadmap.md", {d["file"] for d in data["deduced"]["docs"]})

    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run([sys.executable, "-B", str(SCRIPT), "D14", "--root", tmp], capture_output=True,
                                 text=True, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        self.assertEqual(out.returncode, 2)
        self.assertIn("not inside a git repository", out.stderr)

    def test_bad_task_id_regex_in_config(self):
        cfg = json.loads((self.repo.work / ".claude" / "gw.json").read_text())
        cfg["taskId"] = "[A-H"
        self.repo.write(".claude/gw.json", json.dumps(cfg))
        out = self.repo.trace("D14")
        self.assertEqual(out.returncode, 2)
        self.assertIn("taskId", out.stderr)

    TASK_CFG = {"taskRecord": {"enabled": True}}

    def with_task(self):
        r = self.repo
        cfg = json.loads((r.work / ".claude" / "gw.json").read_text())
        cfg.update(self.TASK_CFG)
        r.write(".claude/gw.json", json.dumps(cfg))
        r.write("docs/tasks/D14.md", "# D14 · t\n\n## Goal\n\nTrace the task D14.\n\n## Acceptance\n\n- [x] a\n- [ ] b\n- [x] c\n")
        return r

    def entry(self, name, date, commit, why, task="D14", agent="session"):
        self.repo.write(f"docs/tasks/D14/{name}.md", f"# {date} · {agent} · {commit} · {task}\n\n## Why\n\n{why}\n\n"
                        "## Alternatives\n\n—\n\n## Changed because\n\n—\n")

    def test_task_record_and_log_shown_sorted_pending(self):
        r = self.with_task()
        self.entry("2026-11-18-session-bbbbbbb", "2026-11-18", "abc1234", "second")
        self.entry("2026-11-17-session-aaaaaaa", "2026-11-17", "pending", "first")
        data = json.loads(r.trace("D14", "--json").stdout)
        task = data["declared"]["task"]
        self.assertEqual([t["kind"] for t in task], ["record", "entry", "entry"])
        self.assertEqual((task[0]["done"], task[0]["total"], task[0]["goal"]), (2, 3, "Trace the task D14."))
        self.assertEqual([(t["date"], t["commit"]) for t in task[1:]], [("2026-11-17", "pending"), ("2026-11-18", "abc1234")])
        out = r.trace("D14").stdout
        self.assertIn("== task (3)", out)
        self.assertIn("Acceptance 2/3 done", out)
        self.assertIn("2026-11-17 · session · pending (docs/tasks/D14/2026-11-17-session-aaaaaaa.md): first", out)
        self.assertLess(out.index("first"), out.index("second"))
        # the task's own files are not listed again among the documents
        self.assertNotIn("docs/tasks/", "".join(d["file"] for d in data["deduced"]["docs"]))
        self.assertNotIn("docs/tasks/", out.split("== docs")[-1])

    def test_no_docs_still_shows_task(self):
        r = self.with_task()
        out = r.trace("D14", "--no-docs")
        self.assertIn("== task (1)", out.stdout)
        self.assertNotIn("== docs", out.stdout)

    def test_missing_and_empty_task_folder(self):
        r = self.with_task()
        (r.work / "docs/tasks/D14").mkdir()
        data = json.loads(r.trace("D14", "--json").stdout)
        self.assertEqual([t["kind"] for t in data["declared"]["task"]], ["record"])
        data = json.loads(r.trace("D1", "--json").stdout)  # no record, no folder
        self.assertEqual(data["declared"]["task"], [])
        self.assertNotIn("== task", r.trace("D1").stdout)

    def test_only_entries_without_record(self):
        r = self.repo
        self.entry("2026-11-17-session-aaaaaaa", "2026-11-17", "pending", "only")
        out = r.trace("D14")
        self.assertIn("== task (1)", out.stdout)

    def test_malformed_entry_warns(self):
        r = self.with_task()
        r.write("docs/tasks/D14/2026-11-16-session-ccccccc.md", "not a header\n\n## Why\n\nx\n")
        out = r.trace("D14")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("WARNING: the first line is not", out.stdout)
        self.assertIn("note: docs/tasks/D14/2026-11-16-session-ccccccc.md is not a valid decision log entry", out.stdout)
        self.assertNotIn("Traceback", out.stderr)

    def test_limit_applies_to_task(self):
        r = self.with_task()
        for i in range(3):
            self.entry(f"2026-11-1{i}-session-aaaaaa{i}", f"2026-11-1{i}", "pending", f"w{i}")
        out = r.trace("D14", "--limit", "2").stdout
        self.assertIn("== task (4)", out)
        self.assertIn("… 2 more", out)

    def test_task_in_id_range_row(self):
        r = self.repo
        r.write("docs/tasks/E12.md", "# E12\n\n## Goal\n\ng\n\n## Acceptance\n\n- [ ] x\n")
        data = json.loads(r.trace("E12", "--json").stdout)
        self.assertEqual(len(data["declared"]["roadmap"]), 1)  # the E9-E16 row
        self.assertEqual(data["declared"]["task"][0]["file"], "docs/tasks/E12.md")  # default path docs/tasks
        self.assertEqual(data["deduced"]["docs"], [])


if __name__ == "__main__":
    unittest.main()
