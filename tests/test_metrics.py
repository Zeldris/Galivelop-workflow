"""scripts/metrics.py (B1-B6): the Stop hook that appends the token usage of the session transcripts to a ledger.

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
sys.path.insert(0, str(ROOT / "scripts"))
import metrics  # noqa: E402
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


def table(since, **models):
    return {"since": since, "models": {k.replace("_", "-"): {"input": v, "cacheWrite": v * 1.25, "cacheRead": v / 10,
                                                             "output": v * 5} for k, v in models.items()}}


class Prices(Base):
    PRICES = [table("2026-01-01", claude_x=1, claude_x_5=2), table("2026-06-01", claude_x=3)]

    def test_exact_key_then_longest_date_suffix_prefix(self):
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x-5", "2026-02-01")["key"], "claude-x-5")
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x-5-20260101", "2026-02-01")["key"], "claude-x-5")
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x-9", "2026-02-01")["key"], "claude-x")
        self.assertIsNone(metrics.price_of(self.PRICES, "claude-xy", "2026-02-01"))

    def test_newest_table_on_or_before_the_row_date(self):
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x", "2026-05-31")["input"], 1)
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x", "2026-06-01")["input"], 3)
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x", "2026-06-01")["since"], "2026-06-01")
        self.assertEqual(metrics.price_of(self.PRICES, "claude-x-5", "2026-07-01")["key"], "claude-x")  # dropped key
        self.assertIsNone(metrics.price_of(self.PRICES, "claude-x", "2025-12-31"))

    def test_cost_of_a_row(self):
        row = {"model": "claude-x", "date": "2026-02-01", "input": 1_000_000, "cacheWrite": 2_000_000,
               "cacheRead": 10_000_000, "output": 100_000}
        self.assertAlmostEqual(metrics.cost_of(row, self.PRICES), 1 + 2.5 + 1 + 0.5)
        self.assertIsNone(metrics.cost_of(dict(row, model="other"), self.PRICES))
        self.assertIsNone(metrics.cost_of(dict(row, date="2025-01-01"), self.PRICES))

    def price(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "price", *args, "--root", str(self.root)],
                              capture_output=True, text=True, env=self.env)

    def test_cli_uses_the_default_table_and_the_project_one(self):
        r = self.price("claude-opus-5-5", "--date", "2026-11-09")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {"input": 4, "cacheWrite": 5, "cacheRead": 0.2, "output": 20,
                                                "since": "2026-10-06", "key": "claude-opus-5-5"})
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.assertEqual(json.loads(self.price("claude-x", "--date", "2026-07-01").stdout)["input"], 3)
        r = self.price("claude-opus-5-5", "--date", "2026-11-09")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no price for claude-opus-5-5 on 2026-11-09", r.stderr)
        self.assertIn("metrics.prices", r.stderr)

    def test_cli_rejects_a_bad_date(self):
        r = self.price("claude-x", "--date", "2026-1-1")
        self.assertEqual(r.returncode, 2)
        self.assertIn("is not a date YYYY-MM-DD", r.stderr)


class Report(Base):
    """B4: metrics.py report --period sums the ledger rows of a period by model, agent, branch and task id."""
    PRICES = [{"since": "2026-01-01", "models": {"claude-x": {"input": 1, "cacheWrite": 2, "cacheRead": 0.5,
                                                              "output": 10}}}]

    def rows(self, *rows):
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        base = {"agent": "main", "branch": "work", "cacheRead": 0, "cacheWrite": 0, "input": 0, "output": 0,
                "model": "claude-x", "recorded": "2026-11-09T00:00:00Z", "refs": ["B4"], "session": "s1"}
        path.write_text("".join(json.dumps(dict(base, **r)) + "\n" for r in rows) + "not json\n")

    def report(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "report", *args, "--root", str(self.root)],
                              capture_output=True, text=True, env=self.env)

    def test_period_bounds(self):
        import datetime
        d = datetime.date(2026, 11, 9)  # a Monday
        self.assertEqual(metrics.period_of("day", d), ("2026-11-09", "2026-11-09", "2026-11-09"))
        self.assertEqual(metrics.period_of("week", datetime.date(2026, 11, 15)), ("2026-W46", "2026-11-09", "2026-11-15"))
        self.assertEqual(metrics.period_of("week", datetime.date(2027, 1, 1)), ("2026-W53", "2026-12-28", "2027-01-03"))
        self.assertEqual(metrics.period_of("month", datetime.date(2028, 2, 10)), ("2028-02", "2028-02-01", "2028-02-29"))
        self.assertEqual(metrics.period_of("quarter", d), ("2026-Q4", "2026-10-01", "2026-12-31"))
        self.assertEqual(metrics.period_of("quarter", datetime.date(2026, 3, 31)), ("2026-Q1", "2026-01-01", "2026-03-31"))

    def test_sums_by_dimension_with_money_and_only_the_period(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.rows({"date": "2026-11-09", "input": 1_000_000, "output": 100_000},
                  {"date": "2026-11-10", "agent": "Explore", "branch": "other", "refs": ["B4", "B5"],
                   "session": "s2", "cacheRead": 2_000_000},
                  {"date": "2026-11-10", "model": "gpt-z", "refs": [], "output": 500},
                  {"date": "2026-11-16", "input": 7})  # next week: left out
        r = self.report("--period", "week", "--date", "2026-11-11")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("# Token report: 2026-W46", out)
        self.assertIn("2026-11-09 to 2026-11-15", out)
        # totals: 2 sessions; 1M input + 2M cache read + 100,500 output; $1 + $1 + $1 priced, gpt-z unpriced
        self.assertIn("| 2 | 1,000,000 | 0 | 2,000,000 | 100,500 | 3,100,500 | $3.00 + unpriced |", out)
        self.assertIn("| `claude-x` | 1,000,000 | 0 | 2,000,000 | 100,000 | 3,100,000 | 100.0% | $3.00 |", out)
        self.assertIn("| `Explore` | 0 | 0 | 2,000,000 | 0 | 2,000,000 | 64.5% | $1.00 |", out)
        self.assertIn("| `other` |", out)
        self.assertIn("| `B5` | 0 | 0 | 2,000,000 |", out)
        self.assertIn("| `B4` | 1,000,000 | 0 | 2,000,000 | 100,000 | 3,100,000 |", out)  # both ids get the row
        self.assertIn("| `(none)` | 0 | 0 | 0 | 500 | 500 | 0.0% | $0.00 + unpriced |", out)
        self.assertIn("## Without a price", out)
        self.assertIn("- `gpt-z`: 500 tokens", out)
        self.assertNotIn("7 |", out.split("## Totals")[1].split("##")[0])
        self.assertFalse((self.root / "docs" / "metrics" / "weekly").exists())  # printed only

    def test_write_saves_the_same_text_under_the_period_folder(self):
        self.rows({"date": "2026-11-09", "model": "claude-opus-5-5", "output": 1_000_000})
        r = self.report("--period", "day", "--date", "2026-11-09", "--write")
        self.assertEqual(r.returncode, 0, r.stderr)
        path = self.root / "docs" / "metrics" / "daily" / "2026-11-09.md"
        self.assertEqual(path.read_text(), r.stdout)
        self.assertIn("$20.00", r.stdout)  # default price table: opus 5.5 output at 20 USD per million
        self.assertIn("wrote docs/metrics/daily/2026-11-09.md", r.stderr)
        self.write_config({"metrics": {"reports": "out/m"}})
        self.assertEqual(self.report("--period", "quarter", "--date", "2026-11-09", "--write").returncode, 0)
        self.assertTrue((self.root / "out" / "m" / "quarterly" / "2026-Q4.md").is_file())

    def test_a_period_without_rows_writes_nothing(self):
        self.rows({"date": "2026-11-09", "output": 5})
        r = self.report("--period", "month", "--date", "2026-10-31", "--write")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("no ledger rows in month 2026-10", r.stderr)
        self.assertFalse((self.root / "docs" / "metrics" / "monthly").exists())
        (self.root / LEDGER).unlink()
        r = self.report("--period", "day")
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to report", r.stderr)

    def test_rejects_an_unknown_period(self):
        r = self.report("--period", "year")
        self.assertEqual(r.returncode, 2)
        self.assertIn("invalid choice: 'year'", r.stderr)


class Compare(Base):
    """B5: metrics.py compare sets a period beside the one before it or beside one the user picks."""
    PRICES = Report.PRICES
    rows = Report.rows

    def compare(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "compare", *args, "--root", str(self.root)],
                              capture_output=True, text=True, env=self.env)

    def test_against_the_previous_period(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.rows({"date": "2026-11-08", "input": 1_000_000},  # W45, Sunday
                  {"date": "2026-11-09", "input": 1_500_000, "agent": "Explore"},  # W46, Monday
                  {"date": "2026-11-15", "output": 100_000, "refs": ["B5"]},
                  {"date": "2026-11-16", "input": 9})  # W47: left out
        r = self.compare("--period", "week", "--date", "2026-11-12")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("# Token comparison: 2026-W46 against 2026-W45", out)
        self.assertIn("`2026-W45` is 2026-11-02 to 2026-11-08, `2026-W46` is 2026-11-09 to 2026-11-15", out)
        self.assertIn("| Input | 1,000,000 | 1,500,000 | +500,000 (+50.0%) |", out)
        self.assertIn("| Output | 0 | 100,000 | new |", out)
        self.assertIn("| Sessions | 1 | 1 | = |", out)
        self.assertIn("| USD | $1.00 | $2.50 | +$1.50 (+150.0%) |", out)
        self.assertIn("| `main` | 1,000,000 | 100,000 | -900,000 (-90.0%) | $1.00 | $1.00 | = |", out)
        self.assertIn("| `Explore` | 0 | 1,500,000 | new | $0.00 | $1.50 | new |", out)
        self.assertIn("| `B5` | 0 | 100,000 | new |", out)
        self.assertNotIn("1,500,009", out)
        # rows ordered by the later period first
        self.assertLess(out.index("| `Explore` |"), out.index("| `main` |"))

    def test_against_a_chosen_period_with_unpriced_tokens(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.rows({"date": "2026-09-03", "input": 2_000_000},
                  {"date": "2026-11-01", "model": "gpt-z", "output": 40})
        r = self.compare("--period", "month", "--date", "2026-11-20", "--against", "2026-09-30")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("# Token comparison: 2026-11 against 2026-09", out)
        self.assertIn("| Tokens | 2,000,000 | 40 | -1,999,960 (-100.0%) |", out)
        self.assertIn("| USD | $2.00 | $0.00 + unpriced | n/a |", out)
        self.assertIn("| `claude-x` | 2,000,000 | 0 | -2,000,000 (-100.0%) | $2.00 | $0.00 | -$2.00 (-100.0%) |", out)
        self.assertIn("- `gpt-z`: 0 tokens in `2026-09`, 40 in `2026-11`", out)

    def test_previous_day_and_quarter_cross_the_year(self):
        import datetime
        self.rows({"date": "2025-12-31", "output": 3}, {"date": "2026-01-01", "output": 6})
        r = self.compare("--period", "day", "--date", "2026-01-01")
        self.assertIn("# Token comparison: 2026-01-01 against 2025-12-31", r.stdout)
        self.assertIn("| Output | 3 | 6 | +3 (+100.0%) |", r.stdout)
        r = self.compare("--period", "quarter", "--date", "2026-02-01")
        self.assertIn("# Token comparison: 2026-Q1 against 2025-Q4", r.stdout)
        self.assertIsNone(metrics.compare(self.root, {"_root": str(self.root)}, "day", datetime.date(2030, 1, 1)))

    def test_the_same_period_twice_and_empty_periods(self):
        self.rows({"date": "2026-11-09", "output": 5})
        r = self.compare("--period", "week", "--date", "2026-11-09", "--against", "2026-11-15")
        self.assertEqual(r.returncode, 2)
        self.assertIn("2026-11-09 and 2026-11-15 are in the same week (2026-W46)", r.stderr)
        self.assertEqual(r.stdout, "")
        r = self.compare("--period", "day", "--date", "2026-01-05")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("no ledger rows in either day; nothing to compare", r.stderr)
        r = self.compare("--period", "day", "--date", "2026-11-09", "--against", "26-11-09")
        self.assertEqual(r.returncode, 2)
        self.assertIn("is not a date YYYY-MM-DD", r.stderr)


class Quality(Base):
    """B8: metrics.py quality sets signals read from the commit messages beside the ledger spend per task id."""
    PRICES = [{"since": "2019-01-01", "models": Report.PRICES[0]["models"]}]

    def commit(self, subject, trailers="", date="2020-03-10T12:00:00Z", body=""):
        message = subject + "\n\n" + (body + "\n\n" if body else "") + trailers
        env = dict(self.env, GIT_COMMITTER_DATE=date, GIT_AUTHOR_DATE=date)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", message], env=env, check=True, capture_output=True, text=True)

    def ledger(self, *rows):
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        base = {"agent": "main", "branch": "work", "cacheRead": 0, "cacheWrite": 0, "input": 0, "output": 0,
                "model": "claude-x", "recorded": "2020-03-10T00:00:00Z", "refs": ["Q1"], "session": "s1"}
        path.write_text("".join(json.dumps(dict(base, **r)) + "\n" for r in rows))

    def quality(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "quality", *args, "--root", str(self.root)],
                              capture_output=True, text=True, env=self.env)

    def month(self, *extra):
        return self.quality("--period", "month", "--date", "2020-03-15", *extra)

    def cells(self, out, table_id):
        for text in out.splitlines():
            if text.startswith(f"| `{table_id}` |"):
                return [c.strip() for c in text.strip("|").split("|")]
        self.fail(f"no row for {table_id} in:\n{out}")

    def test_signals_per_id(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.ledger({"date": "2020-03-10", "input": 1_000_000, "refs": ["Q1"]})
        self.commit("fix(Q1): first commit is a fix, not rework", "Refs: Q1\nSiguiente: x")
        self.commit("WIP: feat(Q1): red", "Refs: Q1\nSiguiente: x")
        self.commit("fix(Q1): after the first", "Refs: Q1\nfindings: 2\nSiguiente: x")
        self.commit("fix!: also breaking", "Refs: Q1\nFINDINGS: 3\nRetries: 1\nSiguiente: x")
        self.commit("WIP: fix(Q1): red and rework", "Refs: Q1\nSiguiente: x")
        self.commit('Revert "feat(Q1): something"', "Refs: Q1\nSiguiente: x")
        self.commit("docs(Q1): not rework", "Refs: Q1\nSiguiente: x")
        self.commit("fix(Q2): shared fix", "Refs: Q1, Q2\nRefs: Q3\nSiguiente: x")
        self.commit("fix: no refs at all is ignored")
        r = self.month()
        self.assertEqual(r.returncode, 0, r.stderr)
        # Id, tokens, USD, commits, red, rework, findings, retries
        self.assertEqual(self.cells(r.stdout, "Q1"), ["`Q1`", "1,000,000", "$1.00", "8", "2", "5", "5", "1"])
        # Q2 and Q3: their first commit is the shared one, so it is not rework for them
        self.assertEqual(self.cells(r.stdout, "Q2"), ["`Q2`", "0", "$0.00", "1", "0", "0", "0", "0"])
        self.assertEqual(self.cells(r.stdout, "Q3")[3:], ["1", "0", "0", "0", "0"])
        self.assertNotIn("Ignored trailers", r.stdout)
        self.assertIn("# Quality report: 2020-03", r.stdout)
        self.assertIn("The deterministic model table (B8, later) waits for four weeks of ledger.", r.stdout)

    def test_period_is_the_committer_date_utc(self):
        self.commit("feat(Q1): early", "Refs: Q1\nSiguiente: x", date="2020-02-29T23:59:59Z")
        self.commit("fix(Q1): in march", "Refs: Q1\nRetries: 4\nSiguiente: x", date="2020-03-01T00:00:00Z")
        self.commit("fix(Q1): late", "Refs: Q1\nRetries: 8\nSiguiente: x", date="2020-03-31T23:59:59Z")
        self.commit("fix(Q1): april", "Refs: Q1\nRetries: 16\nSiguiente: x", date="2020-04-01T00:00:00Z")
        r = self.month()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.cells(r.stdout, "Q1")[3:], ["2", "0", "2", "0", "12"])  # first commit is in February
        day = self.quality("--period", "day", "--date", "2020-02-29")
        self.assertEqual(self.cells(day.stdout, "Q1")[3:], ["1", "0", "0", "0", "0"])

    def test_by_model_counts_an_id_for_every_model_that_spent_on_it(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.ledger({"date": "2020-03-10", "model": "claude-x", "input": 1_000_000, "refs": ["Q1", "Q2"]},
                    {"date": "2020-03-10", "model": "gpt-z", "output": 500, "refs": ["Q1"]},
                    {"date": "2020-03-10", "model": "gpt-z", "output": 7, "refs": [], "session": "s2"})
        self.commit("feat(Q1): a", "Refs: Q1\nSiguiente: x")
        self.commit("fix(Q1): b", "Refs: Q1\nFindings: 2\nSiguiente: x")
        self.commit("feat(Q2): c", "Refs: Q2\nRetries: 1\nSiguiente: x")
        r = self.month()
        self.assertEqual(r.returncode, 0, r.stderr)
        section = r.stdout.split("## By model")[1]
        self.assertIn("counts for every model that spent on it", section)
        # Model, tokens, USD, ids, commits, red, rework, findings, retries
        self.assertEqual(self.cells(section, "claude-x"), ["`claude-x`", "1,000,000", "$1.00", "2", "3", "0", "1", "2", "1"])
        self.assertEqual(self.cells(section, "gpt-z")[3:], ["1", "2", "0", "1", "2", "0"])
        self.assertIn("`gpt-z` | 507 | $0.00 + unpriced", section)
        ids = r.stdout.split("## By task id")[1].split("## By model")[0]
        self.assertLess(ids.index("`Q1`"), ids.index("`Q2`"))  # more tokens first

    def test_bad_trailer_values_are_listed_not_counted(self):
        self.commit("feat(Q1): a", "Refs: Q1\nSiguiente: x")
        self.commit("fix(Q1): b", "Refs: Q1\nFindings: -2\nRetries: three\nFindings: 1\nSiguiente: x")
        r = self.month()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.cells(r.stdout, "Q1")[3:], ["2", "0", "1", "1", "0"])
        section = r.stdout.split("## Ignored trailers")[1]
        self.assertIn("Findings: -2", section)
        self.assertIn("Retries: three", section)
        sha7 = self.git("rev-parse", "--short=7", "HEAD").strip()
        self.assertIn(f"`{sha7}`", section)

    def test_custom_quality_config(self):
        self.write_config({"metrics": {"quality": {"findingsTrailer": "Issues", "reworkTypes": ["refactor"]}}})
        self.commit("feat(Q1): a", "Refs: Q1\nSiguiente: x")
        self.commit("fix(Q1): not rework now", "Refs: Q1\nFindings: 9\nRetries: 2\nSiguiente: x")
        self.commit("refactor(Q1): rework now", "Refs: Q1\nIssues: 3\nSiguiente: x")
        r = self.month()
        self.assertEqual(r.returncode, 0, r.stderr)
        # Findings is not the findings trailer any more and Retries keeps its default name
        self.assertEqual(self.cells(r.stdout, "Q1")[3:], ["3", "0", "1", "3", "2"])

    def test_empty_period_exits_0_and_writes_nothing(self):
        self.commit("feat(Q1): elsewhere", "Refs: Q1\nSiguiente: x", date="2020-03-10T12:00:00Z")
        r = self.quality("--period", "month", "--date", "2019-01-05", "--write")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")
        self.assertIn("no commits with Refs and no ledger rows in month 2019-01", r.stderr)
        self.assertFalse((self.root / "docs" / "metrics").exists())

    def test_write_saves_under_the_period_folder(self):
        self.commit("feat(Q1): a", "Refs: Q1\nSiguiente: x")
        r = self.month("--write")
        self.assertEqual(r.returncode, 0, r.stderr)
        path = self.root / "docs" / "metrics" / "monthly" / "2020-03-quality.md"
        self.assertEqual(path.read_text(), r.stdout)
        self.assertIn("wrote docs/metrics/monthly/2020-03-quality.md", r.stderr)
        again = self.month("--write")
        self.assertEqual(path.read_text(), again.stdout)  # deterministic
        w = self.quality("--period", "week", "--date", "2020-03-10", "--write")
        self.assertTrue((self.root / "docs" / "metrics" / "weekly" / "2020-W11-quality.md").is_file(), w.stderr)

    def test_ledger_only_period_still_reports(self):
        self.ledger({"date": "2020-03-10", "output": 5, "refs": ["Z9"]})
        r = self.month()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.cells(r.stdout, "Z9")[3:], ["0", "0", "0", "0", "0"])

    def test_history_outside_a_repo_raises_with_git_message(self):
        plain = self.tmp / "plain2"
        plain.mkdir()
        old = os.environ.get("GIT_CEILING_DIRECTORIES")
        os.environ["GIT_CEILING_DIRECTORIES"] = str(self.tmp)
        self.addCleanup(lambda: os.environ.pop("GIT_CEILING_DIRECTORIES") if old is None
                        else os.environ.__setitem__("GIT_CEILING_DIRECTORIES", old))
        with self.assertRaises(metrics.MetricsError) as ctx:
            metrics.history_commits(plain)
        self.assertIn("git rev-parse --git-dir failed", str(ctx.exception))

    def test_not_a_git_repo_and_bad_config_exit_2_with_the_reason(self):
        other = self.tmp / "plain"
        (other / ".claude").mkdir(parents=True)
        (other / ".claude" / "gw.json").write_text(json.dumps(BASE_CONFIG))
        env = dict(self.env, GIT_CEILING_DIRECTORIES=str(self.tmp))
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "quality", "--period", "day", "--root", str(other)],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("is not inside a git repository", r.stderr)
        self.write_config({"metrics": {"quality": {"findingsTrailer": "bad name"}}})
        r = self.month()
        self.assertEqual(r.returncode, 2)
        self.assertIn("metrics.quality.findingsTrailer", r.stderr)


class Alert(Base):
    """B6: metrics.py alert (run by the SessionStart hook) warns when a model's daily spend passes factor x its mean."""
    PRICES = Report.PRICES
    rows = Report.rows

    def alert(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "alert", *args, "--root", str(self.root)],
                              capture_output=True, text=True, env=self.env)

    def week(self, model="claude-x", first=1, count=7, tokens=1_000_000):
        return [{"date": f"2026-11-{d:02d}", "model": model, "input": tokens} for d in range(first, first + count)]

    def test_priced_model_over_the_factor_warns_in_usd(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.rows(*self.week(), {"date": "2026-11-09", "input": 1_500_000}, {"date": "2026-11-09", "input": 500_000,
                                                                             "agent": "Explore"})
        r = self.alert("--date", "2026-11-09")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.splitlines()), 1, r.stdout)
        self.assertIn("metrics: claude-x spent $2.00 on 2026-11-09, 2.0x its daily mean of $1.00 over the 28 days "
                      "before (7 with data; alert at 1.5x", r.stdout)
        self.assertIn("report --period day --date 2026-11-09", r.stdout)

    def test_yesterday_counts_and_unpriced_models_go_in_tokens(self):
        self.rows(*self.week(model="gpt-z", tokens=100), {"date": "2026-11-08", "model": "gpt-z", "output": 400})
        r = self.alert("--date", "2026-11-09")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("gpt-z spent 400 tokens on 2026-11-08, 4.0x its daily mean of 100 tokens", r.stdout)

    def test_no_alert_at_the_factor_with_too_few_days_or_when_off(self):
        self.write_config({"metrics": {"prices": self.PRICES}})
        self.rows(*self.week(), {"date": "2026-11-09", "input": 1_500_000})
        r = self.alert("--date", "2026-11-09")
        self.assertEqual((r.returncode, r.stdout), (0, ""), "exactly 1.5x is not above it")
        self.write_config({"metrics": {"prices": self.PRICES, "alert": {"factor": 1.2}}})
        self.assertIn("1.5x its daily mean", self.alert("--date", "2026-11-09").stdout, "minDays/days keep defaults")
        self.write_config({"metrics": {"prices": self.PRICES, "alert": {"factor": 0}}})
        self.assertEqual(self.alert("--date", "2026-11-09").stdout, "")
        self.write_config({"metrics": {"prices": self.PRICES, "alert": {"factor": 1.2, "minDays": 8}}})
        self.assertEqual(self.alert("--date", "2026-11-09").stdout, "", "7 days of data, 8 asked")

    def test_days_outside_the_window_do_not_count(self):
        self.write_config({"metrics": {"prices": self.PRICES, "alert": {"days": 8}}})
        self.rows(*self.week(), {"date": "2026-11-10", "input": 3_000_000})
        self.assertEqual(self.alert("--date", "2026-11-10").stdout, "", "11-01 is 9 days before: only 6 with data")
        self.write_config({"metrics": {"prices": self.PRICES, "alert": {"days": 9}}})
        self.assertIn("3.0x", self.alert("--date", "2026-11-10").stdout)

    def test_bad_config_exits_2_and_no_ledger_says_nothing(self):
        r = self.alert("--date", "2026-11-09")
        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        self.write_config({"metrics": {"alert": {"factor": -1}}})
        r = self.alert()
        self.assertEqual(r.returncode, 2)
        self.assertIn("metrics.alert.factor", r.stderr)


if __name__ == "__main__":
    unittest.main()
