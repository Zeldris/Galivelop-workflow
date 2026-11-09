"""scripts/context_guard.py (B21): startup-context and compaction-loop guard, and its wiring in recover.py --state.

Temporary repos with a JSONL transcript written by each test; HOME points to a temp folder so no real ~/.claude
skills are counted.
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
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402
import context_guard as cg  # noqa: E402

MODEL = "claude-sonnet-5-5"
BASE_CONFIG = {"version": "0.5.1", "schemaVersion": 1, "language": "en", "log": "docs/log.md",
               "protectedBranch": "main", "pushToProtected": "direct", "check": ["true"],
               "reviewMark": "docs/reviewed.txt", "content": ["^docs/"]}


def turn(tokens, model=MODEL, **extra):
    """An assistant line whose usage sums to `tokens` (split over the three counted keys)."""
    usage = {"input_tokens": 10, "cache_creation_input_tokens": tokens - 10 - 100, "cache_read_input_tokens": 100,
             "output_tokens": 999}
    return dict({"type": "assistant", "message": {"model": model, "usage": usage}}, **extra)


BOUNDARY = {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-11-09T10:00:00Z"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-guard-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        (self.root / ".claude").mkdir(parents=True)
        (self.root / "docs").mkdir()
        self.home = self.tmp / "home"
        self.home.mkdir()
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.home)
        self.addCleanup(lambda: os.environ.__setitem__("HOME", old_home) if old_home else os.environ.pop("HOME", None))
        subprocess.run(["git", "init", "-q", str(self.root)], check=True,
                       env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull))
        self.write_config({})

    def write_config(self, extra):
        (self.root / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **extra)))

    def cfg(self):
        return config.load(self.root)

    def transcript(self, lines, name="s.jsonl"):
        path = self.tmp / name
        path.write_text("".join((l if isinstance(l, str) else json.dumps(l)) + "\n" for l in lines))
        return path


class UsageOf(Base):
    def test_sums_the_three_input_counters_and_ignores_output(self):
        self.assertEqual(cg.usage_of(turn(5000)), 5000)

    def test_missing_keys_count_as_zero(self):
        entry = {"type": "assistant", "message": {"model": MODEL, "usage": {"input_tokens": 7}}}
        self.assertEqual(cg.usage_of(entry), 7)

    def test_synthetic_model_and_sidechain_and_other_types_are_skipped(self):
        self.assertIsNone(cg.usage_of(turn(5000, model="<synthetic>")))
        self.assertIsNone(cg.usage_of(turn(5000, isSidechain=True)))
        self.assertIsNone(cg.usage_of({"type": "user", "message": {"usage": {"input_tokens": 1}}}))
        self.assertIsNone(cg.usage_of({"type": "assistant", "message": {"model": MODEL}}))


class Startups(Base):
    def test_no_boundary_is_one_segment(self):
        segs = cg.startups(self.transcript([{"type": "user"}, turn(1000), turn(2000)]))
        self.assertEqual(segs, [{"start": "", "first_usage": 1000, "model": MODEL}])

    def test_each_boundary_form_opens_a_segment(self):
        lines = [turn(1000), BOUNDARY, {"type": "compact_boundary", "timestamp": "t2"}, turn(3000),
                 {"type": "user", "isCompactSummary": True, "timestamp": "t3"}, "not json", turn(4000)]
        segs = cg.startups(self.transcript(lines))
        self.assertEqual([s["first_usage"] for s in segs], [1000, None, 3000, 4000])
        self.assertEqual(segs[1]["start"], "2026-11-09T10:00:00Z")

    def test_a_segment_without_a_measured_turn_has_none(self):
        segs = cg.startups(self.transcript([turn(1000), BOUNDARY, turn(900, isSidechain=True)]))
        self.assertIsNone(segs[1]["first_usage"])


class Cutoff(Base):
    def test_explicit_cutoff_wins(self):
        self.assertEqual(cg.cutoff_for(MODEL, {"contextGuard": {"cutoff": 140000}}), 140000)

    def test_default_is_window_times_share(self):
        self.assertEqual(cg.cutoff_for(MODEL, {}), 160000)
        self.assertEqual(cg.cutoff_for(MODEL, {"contextGuard": {"window": 100000, "autocompactShare": 0.5}}), 50000)

    def test_one_million_model(self):
        self.assertEqual(cg.cutoff_for("claude-opus-4-7[1m]", {}), 800000)

    def test_estimate_uses_3_5_characters_per_token(self):
        self.assertEqual(cg.estimate_tokens("x" * 350), 100)


class Breakdown(Base):
    def test_labels_order_and_sources(self):
        (self.root / "docs" / "log.md").write_text("l" * 3500)
        (self.root / "AGENTS.md").write_text("a" * 700 + "\n" + "@extra.md\n")
        (self.root / "CLAUDE.md").write_text("c" * 350)
        (self.root / "extra.md").write_text("e" * 350)
        skill = self.root / ".claude" / "skills" / "s1"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: s1\ndescription: " + "d" * 70 + "\n---\n" + "body" * 5000)
        parts = cg.breakdown(self.root, self.cfg(), hook_chars=350)
        self.assertEqual([p[0] for p in parts], ["log", "AGENTS.md/CLAUDE.md", "hook output", "skills"])
        by = {p[0]: p for p in parts}
        self.assertEqual(by["log"][1], 1000)
        self.assertGreaterEqual(by["AGENTS.md/CLAUDE.md"][1], 400)  # includes extra.md
        self.assertEqual(by["hook output"][1], 100)
        self.assertLess(by["skills"][1], 60)  # frontmatter only, not the body
        self.assertIn("handoff.py archive", by["log"][2])
        self.assertIn("doctor.py", by["AGENTS.md/CLAUDE.md"][2])

    def test_missing_files_estimate_zero(self):
        parts = cg.breakdown(self.root, self.cfg())
        self.assertEqual([p[1] for p in parts], [0, 0, 0, 0])


class Report(Base):
    def report(self, lines, source="clear", **kw):
        return cg.report(self.root, self.cfg(), self.transcript(lines), source, **kw)

    def test_no_measured_turn(self):
        out = self.report([{"type": "user"}])
        self.assertEqual(len(out), 1)
        self.assertIn("unknown (no measured turn yet", out[0])

    def test_below_warn_is_one_line(self):
        out = self.report([turn(16000)])
        self.assertEqual(len(out), 1)
        self.assertIn("16,000 tokens = 10 % of the compaction cutoff 160,000 (model claude-sonnet-5-5)", out[0])

    def test_between_warn_and_alarm_names_the_culprit(self):
        (self.root / "docs" / "log.md").write_text("l" * 70000)  # 20,000 tokens
        out = self.report([turn(60000)], hook_chars=3500)
        self.assertIn("= 38 % of", out[0])
        self.assertTrue(any(l.startswith("- Warning: startup context above 25 %") for l in out), out)
        self.assertFalse(any("ALARM" in l for l in out), out)
        rows = [l for l in out if l.startswith("  ")]
        self.assertTrue(rows[0].startswith("  rest of the system"), rows)  # 60,000 - 21,000 is the largest
        self.assertTrue(any(l.startswith("  log: ~20,000 tokens (33 %) — fix: shorten it") for l in rows), rows)
        sizes = [int(l.split("~")[1].split(" ")[0].replace(",", "")) for l in rows]
        self.assertEqual(sizes, sorted(sizes, reverse=True))

    def test_above_alarm(self):
        out = self.report([turn(100000)])
        self.assertTrue(any(l.startswith("- ALARM: startup context above 50 %") for l in out), out)
        self.assertFalse(any("compaction loop" in l for l in out), out)

    def test_loop_on_compact_source(self):
        out = self.report([turn(100000), BOUNDARY], source="compact")
        loop = [l for l in out if "compaction loop" in l]
        self.assertEqual(len(loop), 1, out)
        self.assertIn("ask the user for /clear", loop[0])

    def test_no_loop_on_compact_when_the_startup_was_small(self):
        out = self.report([turn(20000), BOUNDARY], source="compact")
        self.assertFalse(any("ALARM" in l for l in out), out)

    def test_loop_on_two_consecutive_segments_whatever_the_source(self):
        out = self.report([turn(100000), BOUNDARY, turn(110000)], source="startup")
        self.assertTrue(any("compaction loop" in l for l in out), out)
        out = self.report([turn(100000), BOUNDARY, turn(20000)], source="startup")
        self.assertFalse(any("compaction loop" in l for l in out), out)

    def test_own_thresholds_and_cutoff(self):
        self.write_config({"contextGuard": {"cutoff": 140000, "warn": 10, "alarm": 20}})
        out = self.report([turn(30000)])
        self.assertIn("= 21 % of the compaction cutoff 140,000", out[0])
        self.assertTrue(any("above 20 %" in l for l in out), out)

    def test_missing_transcript_fails_open(self):
        out = cg.report(self.root, self.cfg(), str(self.tmp / "nope.jsonl"), "compact")
        self.assertEqual(len(out), 1)
        self.assertIn("Startup context: unknown", out[0])
        self.assertIn("unknown", cg.report(self.root, self.cfg(), None, "clear")[0])


class Cli(Base):
    def run_cli(self, script, *args):
        env = dict(os.environ, HOME=str(self.home))
        env.pop("CLAUDE_PROJECT_DIR", None)
        return subprocess.run(["python3", "-B", str(ROOT / "scripts" / script), *args], capture_output=True,
                              text=True, env=env, stdin=subprocess.DEVNULL)

    def test_cli_prints_the_report(self):
        path = self.transcript([turn(100000), BOUNDARY])
        r = self.run_cli("context_guard.py", "--root", str(self.root), "--session", str(path), "--source", "compact")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ALARM: compaction loop", r.stdout)

    def test_cli_without_transcript_says_unknown_and_exits_0(self):
        r = self.run_cli("context_guard.py", "--root", str(self.root), "--session", str(self.tmp / "nope.jsonl"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Startup context: unknown", r.stdout)

    def test_cli_config_error_exits_2_with_the_message(self):
        (self.root / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, contextGuard={"warn": 0})))
        r = self.run_cli("context_guard.py", "--root", str(self.root))
        self.assertEqual(r.returncode, 2)
        self.assertIn("$.contextGuard.warn: must be at least 1", r.stderr)

    def test_recover_state_smoke(self):
        path = self.transcript([turn(100000), BOUNDARY])
        r = self.run_cli("recover.py", "--state", "--session", str(path), "--source", "compact", "--root", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("- Startup context of the last stretch: 100,000 tokens = 62 %", r.stdout)
        self.assertIn("- Warning: startup context above 25 %", r.stdout)
        self.assertIn("- ALARM: compaction loop", r.stdout)


if __name__ == "__main__":
    unittest.main()
