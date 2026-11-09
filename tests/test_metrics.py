"""scripts/metrics.py (B1/B2): the Stop hook that appends the token usage of the session transcripts to a ledger.

Synthetic transcripts in temporary repos; every case runs the script the way the hook does (JSON on stdin).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "metrics.py"
MODEL = "claude-sonnet-5-5"
BASE_CONFIG = {"version": "0.5.1", "schemaVersion": 1, "language": "en", "log": "docs/log.md",
               "protectedBranch": "main", "pushToProtected": "direct", "check": ["true"],
               "reviewMark": "docs/reviewed.txt", "content": ["^docs/"]}
LEDGER = "docs/metrics/ledger.jsonl"
SESSION = "abcdef12-0000-4000-8000-000000000000"


def line(msg_id, stamp, out=10, inp=1, cw=2, cr=3, model=MODEL, **extra):
    usage = {"input_tokens": inp, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr, "output_tokens": out}
    return dict({"type": "assistant", "timestamp": stamp, "uuid": f"u-{msg_id}-{out}",
                 "message": {"id": msg_id, "model": model, "usage": usage}}, **extra)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-metrics-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        (self.root / ".claude").mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.tmp / "home"), GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        self.env.pop("CLAUDE_PROJECT_DIR", None)
        self.git("init", "-q", "-b", "work")
        self.write_config({})
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "feat(B1): base\n\nRefs: B1, B2\nSiguiente: x")
        self.transcript = self.tmp / "proj" / f"{SESSION}.jsonl"
        self.transcript.parent.mkdir()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], env=self.env, check=True, capture_output=True,
                              text=True).stdout

    def write_config(self, extra):
        (self.root / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **extra)))

    def write_log(self, lines, path=None):
        path = path or self.transcript
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(x) + "\n" for x in lines))

    def subagent(self, name, lines, meta):
        d = self.transcript.parent / SESSION / "subagents"
        self.write_log(lines, d / f"agent-{name}.jsonl")
        if meta is not None:
            (d / f"agent-{name}.meta.json").write_text(json.dumps(meta))

    def record(self, payload=None, args=(), transcript=True):
        event = dict({"session_id": SESSION, "stop_hook_active": False}, **(payload or {}))
        if transcript:
            event.setdefault("transcript_path", str(self.transcript))
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "record", "--root", str(self.root), *args],
                           input=json.dumps(event), capture_output=True, text=True, env=self.env)
        return r

    def rows(self):
        path = self.root / LEDGER
        if not path.is_file():
            return []
        return [json.loads(x) for x in path.read_text().splitlines()]


class Record(Base):
    def test_split_response_counts_once_with_max_output(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=5), line("m1", "2026-11-09T10:00:01Z", out=40),
                        line("m1", "2026-11-09T10:00:02Z", out=25)])
        r = self.record()
        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        rows = self.rows()
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual({k: rows[0][k] for k in ("input", "cacheWrite", "cacheRead", "output")},
                         {"input": 1, "cacheWrite": 2, "cacheRead": 3, "output": 40})
        self.assertEqual((rows[0]["session"], rows[0]["agent"], rows[0]["model"], rows[0]["date"]),
                         ("abcdef12", "main", MODEL, "2026-11-09"))

    def test_line_format_is_sorted_compact_json(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        self.record()
        text = (self.root / LEDGER).read_text()
        self.assertEqual(sorted(json.loads(text)), ["agent", "branch", "cacheRead", "cacheWrite", "date", "input",
                                                    "model", "output", "recorded", "refs", "session"])
        self.assertNotIn(", ", text)
        self.assertTrue(text.endswith("}\n"))

    def test_subagent_with_meta_and_without(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        self.subagent("a1", [line("s1", "2026-11-09T10:01:00Z", out=7)], {"agentType": "Explore",
                                                                         "description": "private text here"})
        self.subagent("a2", [line("s2", "2026-11-09T10:02:00Z", out=9)], None)
        self.record()
        agents = {r["agent"]: r["output"] for r in self.rows()}
        self.assertEqual(agents, {"main": 10, "Explore": 7, "?": 9})
        self.assertNotIn("private text", (self.root / LEDGER).read_text())

    def test_split_by_utc_date(self):
        self.write_log([line("m1", "2026-11-09T23:59:00Z"), line("m2", "2026-11-10T00:01:00Z"),
                        line("m3", "2026-11-10T01:30:00+02:00")])  # 2026-11-09T23:30Z
        self.record()
        days = {r["date"]: r["input"] for r in self.rows()}
        self.assertEqual(days, {"2026-11-09": 2, "2026-11-10": 1})

    def test_rerun_writes_nothing_and_new_usage_appends_the_delta(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=10)])
        self.record()
        before = (self.root / LEDGER).read_text()
        r = self.record()
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertEqual((self.root / LEDGER).read_text(), before)
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=10), line("m2", "2026-11-09T11:00:00Z", out=30, inp=4)])
        self.record()
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[1]["input"], rows[1]["output"], rows[1]["cacheWrite"]), (4, 30, 2))
        self.record()
        self.assertEqual(len(self.rows()), 2)

    def test_growing_output_of_a_recorded_response_adds_only_the_difference(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=10)])
        self.record()
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=10), line("m1", "2026-11-09T10:00:01Z", out=25)])
        self.record()
        rows = self.rows()
        self.assertEqual([(r["input"], r["output"]) for r in rows], [(1, 10), (0, 15)])

    def test_rotated_transcript_writes_nothing(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=100)])
        self.record()
        self.write_log([line("m1", "2026-11-09T10:00:00Z", out=3)])
        self.record()
        self.assertEqual(len(self.rows()), 1)

    def test_synthetic_model_is_skipped(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z", model="<synthetic>"), {"type": "user", "message": {}}])
        r = self.record()
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertEqual(self.rows(), [])

    def test_record_false_writes_nothing(self):
        self.write_config({"metrics": {"record": False}})
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        r = self.record()
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertFalse((self.root / "docs" / "metrics").exists())

    def test_configured_ledger_path(self):
        self.write_config({"metrics": {"ledger": "data/t/tokens.jsonl"}})
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        self.record()
        self.assertTrue((self.root / "data" / "t" / "tokens.jsonl").is_file())
        self.assertEqual(self.rows(), [])

    def test_refs_and_branch_come_from_head(self):
        self.git("checkout", "-q", "-b", "claude/trabajo")
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        self.record()
        row = self.rows()[0]
        self.assertEqual((row["branch"], row["refs"]), ("claude/trabajo", ["B1", "B2"]))

    def test_head_without_refs_gives_an_empty_list(self):
        self.git("commit", "-q", "--allow-empty", "-m", "plain message")
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        self.record()
        self.assertEqual(self.rows()[0]["refs"], [])

    def test_missing_transcript_warns_and_exits_zero(self):
        r = self.record(payload={"transcript_path": str(self.tmp / "nope.jsonl")}, transcript=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        msg = json.loads(r.stdout)["systemMessage"]
        self.assertIn("metrics:", msg)
        self.assertIn("doctor.py", msg)
        self.assertEqual(self.rows(), [])

    def test_missing_config_warns_and_exits_zero(self):
        (self.root / ".claude" / "gw.json").unlink()
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        r = self.record()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("metrics:", json.loads(r.stdout)["systemMessage"])

    def test_stop_hook_active_records_but_prints_nothing(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        r = self.record(payload={"stop_hook_active": True})
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertEqual(len(self.rows()), 1)
        r = self.record(payload={"stop_hook_active": True, "transcript_path": str(self.tmp / "nope.jsonl")},
                        transcript=False)
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_transcript_option(self):
        self.write_log([line("m1", "2026-11-09T10:00:00Z")])
        r = self.record(payload={"transcript_path": ""}, args=("--transcript", str(self.transcript)), transcript=False)
        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        self.assertEqual(len(self.rows()), 1)


if __name__ == "__main__":
    unittest.main()
