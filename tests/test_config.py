"""scripts/config.py: validation, defaults, CLI and failing closed."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

SCRIPT = ROOT / "scripts" / "config.py"
VALID = {"version": "0.1.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main",
         "pushToProtected": "pr", "check": ["make check", "make lint"], "reviewMark": "docs/reviewed.txt",
         "content": ["^docs/"]}


def cli(root, *args):
    return subprocess.run(["python3", str(SCRIPT), "--root", str(root), *args], capture_output=True, text=True)


class Config(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, data):
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(data))

    def test_this_repo_config_is_valid(self):
        self.assertEqual(cli(ROOT, "validate").returncode, 0)

    def test_ci_install_is_unset_until_given_and_an_empty_list_is_a_value(self):
        self.write(VALID)
        r = cli(self.tmp, "get", "ciInstall")
        self.assertEqual(r.returncode, 2)
        self.assertIn("key 'ciInstall' is not set and has no default", r.stderr)
        self.write(dict(VALID, ciInstall=[]))
        r = cli(self.tmp, "get", "ciInstall", "--json")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "[]"))
        self.write(dict(VALID, ciInstall=["npm ci"], setup=["make build"]))
        self.assertEqual(cli(self.tmp, "get", "ciInstall").stdout.splitlines(), ["npm ci"])
        self.assertEqual(cli(self.tmp, "get", "setup").stdout.splitlines(), ["make build"])

    def test_new_keys_default_to_empty_and_reject_bad_values(self):
        self.write(VALID)
        for key in ("setup", "linkRoots", "staleRefs"):
            self.assertEqual(cli(self.tmp, "get", key, "--json").stdout.strip(), "[]", key)
        for bad, needle in ((dict(VALID, setup="make"), "$.setup: expected array"),
                            (dict(VALID, ciInstall=[""]), "$.ciInstall[0]: must not be empty"),
                            (dict(VALID, linkRoots=["../x"]), "$.linkRoots[0]"),
                            (dict(VALID, staleRefs={"skip": ["/abs"]}), "matches none of the allowed forms")):
            self.write(bad)
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(needle, r.stderr)

    def test_release_docs_defaults_to_empty_and_rejects_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "releaseDocs", "--json").stdout.strip(), "[]")
        self.write(dict(VALID, releaseDocs=["README.md", "docs/x.md"]))
        self.assertEqual(cli(self.tmp, "get", "releaseDocs").stdout.splitlines(), ["README.md", "docs/x.md"])
        for bad, needle in ((dict(VALID, releaseDocs="README.md"), "$.releaseDocs: expected array"),
                            (dict(VALID, releaseDocs=["/abs.md"]), "$.releaseDocs[0]"),
                            (dict(VALID, releaseDocs=["../x.md"]), "$.releaseDocs[0]")):
            self.write(bad)
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(needle, r.stderr)

    def test_ci_ignore_defaults_to_empty_and_rejects_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "ciIgnore", "--json").stdout.strip(), "[]")
        self.write(dict(VALID, ciIgnore=["Vercel", "deploy-*"]))
        self.assertEqual(cli(self.tmp, "get", "ciIgnore").stdout.splitlines(), ["Vercel", "deploy-*"])
        for bad, needle in ((dict(VALID, ciIgnore="Vercel"), "$.ciIgnore: expected array"),
                            (dict(VALID, ciIgnore=[""]), "$.ciIgnore[0]: must not be empty")):
            self.write(bad)
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(needle, r.stderr)

    def test_agent_map_defaults_and_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "agentMap", "--json").stdout.strip(), "{}")
        self.write(dict(VALID, agentMap={"path": "docs/m.md", "prefixes": {"b/": "backend/src/"}, "roots": ["backend"]}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        for bad, needle in ((dict(VALID, agentMap={"oops": 1}), "$.agentMap: unknown key 'oops'"),
                            (dict(VALID, agentMap={"path": "../m.md"}), "$.agentMap.path"),
                            (dict(VALID, agentMap={"prefixes": {"b/": "../x"}}), "$.agentMap.prefixes.b/"),
                            (dict(VALID, agentMap={"prefixes": {"b/": 3}}), "$.agentMap.prefixes.b/: expected string"),
                            (dict(VALID, agentMap={"prefixes": {"a/b/": "x"}}), "must be one folder-like name"),
                            (dict(VALID, agentMap={"roots": ["/abs"]}), "$.agentMap.roots[0]")):
            self.write(bad)
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(needle, r.stderr)

    def test_scout_dir_default_and_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "scoutDir").stdout.strip(), ".claude/gw/scout")
        self.write(dict(VALID, scoutDir="docs/scout"))
        self.assertEqual(cli(self.tmp, "get", "scoutDir").stdout.strip(), "docs/scout")
        for bad in ("../x", "/abs", ""):
            self.write(dict(VALID, scoutDir=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("$.scoutDir", r.stderr)

    def test_instruction_lines_default_and_own_values(self):
        self.write(VALID)
        self.assertEqual(json.loads(cli(self.tmp, "get", "instructionLines").stdout), {"warn": 150, "fail": 250})
        self.assertEqual(config.instruction_lines({}), (150, 250))
        self.write(dict(VALID, instructionLines={"warn": 100, "fail": 150}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.assertEqual(config.instruction_lines(config.load(self.tmp)), (100, 150))
        self.assertEqual(config.instruction_lines({"instructionLines": {"warn": 200}}), (200, 250))  # the rest by default
        self.write(dict(VALID, instructionLines={"warn": 250, "fail": 250}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)

    def test_review_trivial_lines_default_own_value_and_invalid(self):
        self.write(VALID)
        self.assertEqual(json.loads(cli(self.tmp, "get", "reviewTrivialLines").stdout), 30)
        self.assertEqual(config.review_trivial_lines({}), 30)
        self.assertEqual(config.review_trivial_lines({"reviewTrivialLines": 0}), 0)
        for bad in ("x", -1, True, None):  # an accessor never trusts a value: the default
            self.assertEqual(config.review_trivial_lines({"reviewTrivialLines": bad}), 30)
        self.write(dict(VALID, reviewTrivialLines=-1))
        self.assertEqual(cli(self.tmp, "validate").returncode, 2)

    def test_log_size_and_log_archive_defaults_and_own_values(self):
        self.write(VALID)
        self.assertEqual(json.loads(cli(self.tmp, "get", "logSize").stdout), 20000)
        self.assertEqual(cli(self.tmp, "get", "logArchive").stdout.strip(), "docs/records/handoff-archive.md")
        self.assertEqual((config.log_size({}), config.log_archive({})), (20000, "docs/records/handoff-archive.md"))
        self.write(dict(VALID, logSize=0, logArchive="notes/old.md"))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.assertEqual((config.log_size(config.load(self.tmp)), config.log_archive(config.load(self.tmp))), (0, "notes/old.md"))
        for bad in ({"logSize": -1}, {"logArchive": "../x.md"}, {"logArchive": "/abs.md"}):
            self.write(dict(VALID, **bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("$." + next(iter(bad)), r.stderr)

    def test_metrics_default_own_values_and_validation(self):
        self.write(VALID)
        default = config.metrics({})
        self.assertEqual(json.loads(cli(self.tmp, "get", "metrics").stdout), default)
        self.assertEqual({k: default[k] for k in ("ledger", "record", "reports")},
                         {"ledger": "docs/metrics/ledger.jsonl", "record": True, "reports": "docs/metrics"})
        self.assertEqual(default["prices"][0]["models"]["claude-opus-5-5"],
                         {"input": 4, "cacheWrite": 5, "cacheRead": 0.2, "output": 20})
        self.assertEqual(config.metrics({"metrics": {"record": False}}), dict(default, record=False))
        own = [{"since": "2027-01-01", "models": {"m": {"input": 1, "cacheWrite": 1, "cacheRead": 1, "output": 1}}}]
        self.assertEqual(config.metrics({"metrics": {"prices": own}})["prices"], own)
        self.write(dict(VALID, metrics={"prices": own}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        bad = [({"record": "yes"}, "$.metrics.record"), ({"reports": ""}, "$.metrics.reports"),
               ({"prices": [{"since": "2027-1-1", "models": {}}]}, "$.metrics.prices[0].since"),
               ({"prices": [{"since": "2027-01-01", "models": {"m": {"input": 1}}}]}, "$.metrics.prices[0].models.m"),
               ({"prices": [{"since": "2027-01-01", "models": {"m": dict(own[0]["models"]["m"], output=-1)}}]},
                "$.metrics.prices[0].models.m.output")]
        for value, where in bad:
            self.write(dict(VALID, metrics=value))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, value)
            self.assertIn(where, r.stderr)

    def test_models_agent_fields_and_check_levers(self):
        self.assertEqual(config.models({}), {"disabled": [], "agentFields": ["model", "effort"], "checkLevers": True})
        self.assertEqual(config.models({"models": {"agentFields": []}})["agentFields"], [])
        self.write(dict(VALID, models={"agentFields": ["effort"], "checkLevers": False}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        for value, where in (({"agentFields": ["speed"]}, "$.models.agentFields[0]"),
                             ({"agentFields": ["model", "model"]}, "$.models.agentFields"),
                             ({"checkLevers": "no"}, "$.models.checkLevers")):
            self.write(dict(VALID, models=value))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, value)
            self.assertIn(where, r.stderr)

    def test_selector_case_session_effort_is_validated(self):
        case = {"case": "Data migration", "skill": "none", "sessionModel": "large", "sessionEffort": "xhigh"}
        self.write(dict(VALID, selector={"cases": [case]}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.write(dict(VALID, selector={"cases": [dict(case, sessionEffort="huge")]}))
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("$.selector.cases[0].sessionEffort", r.stderr)

    def test_metrics_quality_defaults_fill_key_by_key(self):
        default = {"findingsTrailer": "Findings", "retriesTrailer": "Retries", "reworkTypes": ["fix", "revert"]}
        self.assertEqual(config.metrics({})["quality"], default)
        self.assertEqual(config.metrics({"metrics": {"quality": {"retriesTrailer": "Tries"}}})["quality"],
                         dict(default, retriesTrailer="Tries"))
        self.assertEqual(config.metrics({"metrics": {"quality": "x"}})["quality"], default)
        self.write(dict(VALID, metrics={"quality": {"reworkTypes": ["fix"]}}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        for value, where in (({"findingsTrailer": "1x"}, "$.metrics.quality.findingsTrailer"),
                             ({"retriesTrailer": "a b"}, "$.metrics.quality.retriesTrailer"),
                             ({"reworkTypes": [""]}, "$.metrics.quality.reworkTypes[0]"),
                             ({"other": 1}, "$.metrics.quality")):
            self.write(dict(VALID, metrics={"quality": value}))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, value)
            self.assertIn(where, r.stderr)

    def test_context_guard_default_and_own_values(self):
        self.write(VALID)
        default = {"cutoff": 0, "window": 200000, "autocompactShare": 0.8, "warn": 25, "alarm": 50,
                   "charsPerToken": 3.5, "bigWindow": 1000000}
        self.assertEqual(json.loads(cli(self.tmp, "get", "contextGuard").stdout), default)
        self.assertEqual(config.context_guard({}), default)
        self.assertEqual(config.context_guard({"contextGuard": {"cutoff": 140000}}), dict(default, cutoff=140000))
        self.write(dict(VALID, contextGuard={"cutoff": 140000, "autocompactShare": 1, "warn": 10}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)

    def test_context_guard_bad_values_fail_with_their_reason(self):
        cases = [({"warn": 0}, "$.contextGuard.warn: must be at least 1, got 0"),
                 ({"alarm": 101}, "$.contextGuard.alarm: must be at most 100, got 101"),
                 ({"window": 999}, "$.contextGuard.window: must be at least 1000, got 999"),
                 ({"autocompactShare": 0}, "$.contextGuard.autocompactShare: must be above 0, got 0"),
                 ({"autocompactShare": 1.5}, "$.contextGuard.autocompactShare: must be at most 1, got 1.5"),
                 ({"cutoff": -1}, "$.contextGuard.cutoff: must be at least 0, got -1"),
                 ({"charsPerToken": 0}, "$.contextGuard.charsPerToken: must be above 0, got 0"),
                 ({"charsPerToken": "3"}, "$.contextGuard.charsPerToken"),
                 ({"bigWindow": 999}, "$.contextGuard.bigWindow: must be at least 1000, got 999"),
                 ({"limit": 1}, "$.contextGuard: unknown key 'limit'")]
        for bad, message in cases:
            self.write(dict(VALID, contextGuard=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(message, r.stderr)

    def test_context_guard_new_keys_set_values(self):
        self.write(dict(VALID, contextGuard={"charsPerToken": 4, "bigWindow": 500000}))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.assertEqual(config.context_guard({"contextGuard": {"charsPerToken": 4}})["charsPerToken"], 4)
        self.assertEqual(config.context_guard({"contextGuard": {"bigWindow": 500000}})["bigWindow"], 500000)

    def test_subagent_keys_defaults_set_values_and_bad_values(self):
        default = {"subagentCap": 30, "subagentCapStep": 10, "subagentCounterStaleDays": 7,
                   "subagentTranscriptBytes": 524288, "subagentCapAction": "ask"}
        self.write(VALID)
        self.assertEqual(config.subagent_settings(self.tmp), default)
        for key, value in default.items():
            self.assertEqual(cli(self.tmp, "get", key).stdout.strip(), str(value))
        own = {"subagentCap": 5, "subagentCapStep": 2, "subagentCounterStaleDays": 1,
               "subagentTranscriptBytes": 2048, "subagentCapAction": "deny"}
        self.write(dict(VALID, **own))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.assertEqual(config.subagent_settings(self.tmp), own)
        cases = [({"subagentCapStep": 0}, "$.subagentCapStep: must be at least 1, got 0"),
                 ({"subagentCounterStaleDays": -1}, "$.subagentCounterStaleDays: must be at least 1, got -1"),
                 ({"subagentTranscriptBytes": 10}, "$.subagentTranscriptBytes: must be at least 1024, got 10"),
                 ({"subagentTranscriptBytes": 67108865}, "$.subagentTranscriptBytes: must be at most 67108864"),
                 ({"subagentCapAction": "block"}, "$.subagentCapAction: must be one of ['ask', 'warn', 'deny'], got 'block'"),
                 ({"subagentCapStep": "3"}, "$.subagentCapStep")]
        for bad, message in cases:
            self.write(dict(VALID, **bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(message, r.stderr)
            self.assertEqual(config.subagent_settings(self.tmp), default, "an invalid config gives the defaults")

    def test_script_keys_of_c4_defaults_set_values_and_bad_values(self):
        defaults = {"commandTimeout": "900", "commandKillGrace": "5", "installLocal": "false",
                    "prepushClashBranches": "10", "reviewBeforeMainListFiles": "10", "checkTailLines": "40",
                    "mergeCleanup": "true", "privateCheck.maxHits": None}
        self.write(VALID)
        for key, value in defaults.items():
            if value is not None:
                self.assertEqual(cli(self.tmp, "get", key).stdout.strip(), value, key)
        self.assertIn("package-lock.json", cli(self.tmp, "get", "installLockfiles").stdout.split("\n"))
        self.assertEqual(len(cli(self.tmp, "get", "installLockfiles").stdout.split()), 25)
        self.assertEqual(cli(self.tmp, "get", "wholeReadSkipExtensions").stdout.split(),
                         [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".pdf", ".ipynb"])
        self.assertEqual(cli(self.tmp, "get", "wholeReadPaths").stdout.strip(), "")
        self.assertEqual(cli(self.tmp, "get", "retro.decidedWords").stdout.strip().split("|")[:2],
                         ["aplicad[ao]s?", "rechazad[ao]s?"])
        self.assertEqual(cli(self.tmp, "get", "retro.filePattern").stdout.strip(), "(^|/)retro-[^/]*\\.md$")
        self.assertIn("SyntaxError", cli(self.tmp, "get", "redWithoutFix.compileRegex").stdout)
        self.assertIn("[[:space:]]", cli(self.tmp, "get", "redWithoutFix.testRegex").stdout)
        self.assertEqual(cli(self.tmp, "get", "branchPrefixes.agent").stdout.split(), ["worktree-agent-*", "agent/*"])
        self.assertEqual(cli(self.tmp, "get", "branchPrefixes.keep").stdout.split(), ["claude/*"])
        self.assertEqual(config.private_check({})["maxHits"], 10)
        self.assertEqual(config.private_check({"privateCheck": {"emails": False}})["maxHits"], 10)
        # `default KEY` needs no config at all (a script's fallback when the config cannot be read)
        (self.tmp / ".claude" / "gw.json").write_text("{not json")
        self.assertEqual(cli(self.tmp, "default", "checkLockWait").stdout.strip(), "0")
        self.assertEqual(cli(self.tmp, "default", "installLocal").stdout.strip(), "false")
        r = cli(self.tmp, "default", "noSuchKey")
        self.assertEqual(r.returncode, 2)
        self.assertIn("key 'noSuchKey' has no default in the schema", r.stderr)
        own = {"commandTimeout": 60, "commandKillGrace": 2, "installLockfiles": ["a.lock"], "installLocal": True,
               "prepushClashBranches": 3, "reviewBeforeMainListFiles": 4, "checkTailLines": 7,
               "retro": {"statusMarker": "(Decision)"}, "redWithoutFix": {"compileRegex": "boom"},
               "branchPrefixes": {"keep": ["wip/*"]}, "mergeCleanup": False, "wholeReadSkipExtensions": [".svg"],
               "wholeReadPaths": ["docs/notes/"], "privateCheck": {"maxHits": 2}}
        self.write(dict(VALID, **own))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        for key in ("commandTimeout", "commandKillGrace", "prepushClashBranches", "reviewBeforeMainListFiles",
                    "checkTailLines"):
            self.assertEqual(cli(self.tmp, "get", key).stdout.strip(), str(own[key]))
        self.assertEqual(cli(self.tmp, "get", "installLocal").stdout.strip(), "true")
        self.assertEqual(cli(self.tmp, "get", "mergeCleanup").stdout.strip(), "false")
        self.assertEqual(cli(self.tmp, "get", "retro.statusMarker").stdout.strip(), "(Decision)")
        self.assertEqual(cli(self.tmp, "get", "retro.filePattern").stdout.strip(), "(^|/)retro-[^/]*\\.md$",
                         "an inner key not given keeps its default")
        self.assertEqual(cli(self.tmp, "get", "redWithoutFix.compileRegex").stdout.strip(), "boom")
        self.assertEqual(cli(self.tmp, "get", "branchPrefixes.keep").stdout.split(), ["wip/*"])
        self.assertEqual(cli(self.tmp, "get", "branchPrefixes.agent").stdout.split(), ["worktree-agent-*", "agent/*"])
        self.assertEqual(config.private_check(config.load(self.tmp))["maxHits"], 2)
        cases = [({"commandTimeout": 0}, "$.commandTimeout: must be at least 1, got 0"),
                 ({"commandKillGrace": 0}, "$.commandKillGrace: must be at least 1, got 0"),
                 ({"prepushClashBranches": 0}, "$.prepushClashBranches: must be at least 1, got 0"),
                 ({"reviewBeforeMainListFiles": -1}, "$.reviewBeforeMainListFiles: must be at least 1, got -1"),
                 ({"checkTailLines": 0}, "$.checkTailLines: must be at least 1, got 0"),
                 ({"installLocal": "yes"}, "$.installLocal: expected boolean, got str"),
                 ({"mergeCleanup": 1}, "$.mergeCleanup: expected boolean, got int"),
                 ({"installLockfiles": [""]}, "$.installLockfiles[0]: must not be empty"),
                 ({"wholeReadSkipExtensions": ["png"]}, "$.wholeReadSkipExtensions[0]"),
                 ({"branchPrefixes": {"other": []}}, "$.branchPrefixes: unknown key 'other'"),
                 ({"redWithoutFix": {"testRegex": ""}}, "$.redWithoutFix.testRegex: must not be empty"),
                 ({"retro": {"decidedWords": "\\bdone\\b"}}, "$.retro.decidedWords: '\\\\bdone\\\\b' uses '\\\\b'"),
                 ({"retro": {"filePattern": "(unclosed"}}, "$.retro.filePattern: '(unclosed' is not a valid regex"),
                 ({"privateCheck": {"maxHits": 0}}, "maxHits: must be at least 1, got 0")]
        for bad, message in cases:
            self.write(dict(VALID, **bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(message, r.stderr)

    def test_c4_keys_are_in_the_template_and_the_skip_list(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]
        template = json.loads((ROOT / "templates" / "gw.json").read_text())
        for key in ("commandTimeout", "commandKillGrace", "installLockfiles", "installLocal", "prepushClashBranches",
                    "reviewBeforeMainListFiles", "checkTailLines", "retro", "redWithoutFix", "branchPrefixes",
                    "mergeCleanup", "wholeReadSkipExtensions", "wholeReadPaths"):
            self.assertEqual(template[key], schema[key]["default"], key)
            self.assertIn(key, schema["fullCheckSkipKeys"]["default"], key)
            self.assertIn(key, template["fullCheckSkipKeys"], key)

    def test_instruction_lines_bad_values_fail_with_their_reason(self):
        cases = [({"warn": 200, "fail": 100}, "$.instructionLines: warn (200) must not be above fail (100)"),
                 ({"warn": 300}, "warn (300) must not be above fail (250)"),
                 ({"fail": 100}, "warn (150) must not be above fail (100)"),
                 ({"warn": "x"}, "$.instructionLines.warn: expected integer, got str"),
                 ({"warn": 1.5}, "$.instructionLines.warn: expected integer, got float"),
                 ({"fail": True}, "$.instructionLines.fail: expected integer, got bool"),
                 ({"warn": -1}, "$.instructionLines.warn: must be at least 1, got -1"),
                 ({"fail": 0}, "$.instructionLines.fail: must be at least 1, got 0"),
                 ({"warning": 10}, "$.instructionLines: unknown key 'warning'"),
                 (5, "$.instructionLines: expected object, got int")]
        for bad, why in cases:
            self.write(dict(VALID, instructionLines=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(why, r.stderr)

    def test_subagent_cap_default_and_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "subagentCap").stdout.strip(), "30")
        self.write(dict(VALID, subagentCap=50))
        self.assertEqual(cli(self.tmp, "get", "subagentCap").stdout.strip(), "50")
        cases = {0: "must be at least 1, got 0", -3: "must be at least 1, got -3", "x": "expected integer, got str",
                 2.5: "expected integer, got float", True: "expected integer, got bool"}
        for bad, why in cases.items():
            self.write(dict(VALID, subagentCap=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("$.subagentCap", r.stderr)
            self.assertIn(why, r.stderr)

    def test_whole_read_warn_bytes_default_and_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "wholeReadWarnBytes").stdout.strip(), "20000")
        self.write(dict(VALID, wholeReadWarnBytes=0))
        self.assertEqual(cli(self.tmp, "get", "wholeReadWarnBytes").stdout.strip(), "0")
        for bad, why in {-1: "must be at least 0, got -1", "x": "expected integer, got str"}.items():
            self.write(dict(VALID, wholeReadWarnBytes=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("$.wholeReadWarnBytes", r.stderr)
            self.assertIn(why, r.stderr)

    def test_a13_stop_and_check_cache_keys_default_set_and_bad_values(self):
        self.write(VALID)
        defaults = {"stopPushMarkerMaxAge": "3600", "stopGitTimeout": "30", "hookStdinWait": "3",
                    "checkReuseTtl": "86400", "checkReuseKeep": "50", "stopSeverity.unpushed": "block",
                    "stopSeverity.logRequired": "block"}
        for key, value in defaults.items():
            self.assertEqual(cli(self.tmp, "get", key).stdout.strip(), value, key)
        self.write(dict(VALID, stopPushMarkerMaxAge=7200, stopGitTimeout=5, hookStdinWait=0.5, checkReuseTtl=0,
                        checkReuseKeep=7, stopSeverity={"unpushed": "warn"}))
        for key, value in {"stopPushMarkerMaxAge": "7200", "stopGitTimeout": "5", "hookStdinWait": "0.5",
                           "checkReuseTtl": "0", "checkReuseKeep": "7", "stopSeverity.unpushed": "warn",
                           "stopSeverity.logRequired": "block"}.items():
            self.assertEqual(cli(self.tmp, "get", key).stdout.strip(), value, key)
        bad = {"stopPushMarkerMaxAge": (0, "$.stopPushMarkerMaxAge: must be at least 1, got 0"),
               "stopGitTimeout": (601, "$.stopGitTimeout: must be at most 600, got 601"),
               "hookStdinWait": (0, "$.hookStdinWait: must be at least 0.1, got 0"),
               "checkReuseTtl": ("x", "$.checkReuseTtl: expected integer, got str"),
               "checkReuseKeep": (0, "$.checkReuseKeep: must be at least 1, got 0"),
               "stopSeverity": ({"unpushed": "off"}, "$.stopSeverity.unpushed: must be one of ['block', 'warn'], got 'off'")}
        for key, (value, why) in bad.items():
            self.write(dict(VALID, **{key: value}))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, key)
            self.assertIn(why, r.stderr)

    def test_a13_commit_message_keys_default_set_and_bad_values(self):
        self.write(VALID)
        types = "feat fix hotfix docs style refactor perf test build ci chore revert".split()
        self.assertEqual(cli(self.tmp, "get", "commitTypes").stdout.split(), types)
        self.assertEqual(cli(self.tmp, "get", "commitWipPrefix").stdout.rstrip("\n"), "WIP: ")
        for key in ("agentModelNames", "agentModelShapes", "agentSignaturePatterns"):
            self.assertEqual(cli(self.tmp, "get", key).stdout.strip(), "", key)
        self.assertEqual(cli(self.tmp, "get", "changeSize.severity").stdout.strip(), "warn")
        self.write(dict(VALID, commitTypes=["feat"], commitWipPrefix="RED: ", agentModelNames=["grok"],
                        agentModelShapes=["grok\\d+"], agentSignaturePatterns=["^sent from"], changeSize={"severity": "block"}))
        self.assertEqual(cli(self.tmp, "get", "commitTypes").stdout.split(), ["feat"])
        self.assertEqual(cli(self.tmp, "get", "commitWipPrefix").stdout.rstrip("\n"), "RED: ")
        self.assertEqual(cli(self.tmp, "get", "agentModelNames").stdout.split(), ["grok"])
        self.assertEqual(cli(self.tmp, "get", "changeSize.severity").stdout.strip(), "block")
        bad = {"commitTypes": ([], "$.commitTypes: needs at least 1 item"),
               "commitWipPrefix": (5, "$.commitWipPrefix: expected string, got int"),
               "agentModelNames": ([""], "$.agentModelNames[0]"),
               "agentModelShapes": (["("], "$.agentModelShapes[0]: '(' is not a valid regex"),
               "agentSignaturePatterns": (["["], "$.agentSignaturePatterns[0]: '[' is not a valid regex"),
               "changeSize": ({"severity": "off"}, "$.changeSize.severity: must be one of ['warn', 'block'], got 'off'")}
        for key, (value, why) in bad.items():
            self.write(dict(VALID, **{key: value}))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, key)
            self.assertIn(why, r.stderr)
        self.write(dict(VALID, commitTypes=["a b"]))
        self.assertIn("$.commitTypes[0]", cli(self.tmp, "validate").stderr)

    def test_hook_stdin_wait_reads_the_key_and_falls_back_to_the_default(self):
        def wait():
            r = subprocess.run(["python3", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import config; "
                                "print(config.hook_stdin_wait(sys.argv[2]))", str(SCRIPT.parent), str(self.tmp)],
                               capture_output=True, text=True)
            return r.stdout.strip()
        self.write(VALID)
        self.assertEqual(wait(), "3.0")
        self.write(dict(VALID, hookStdinWait=1.5))
        self.assertEqual(wait(), "1.5")
        self.write(dict(VALID, hookStdinWait=-1))  # invalid config: the default, not an error
        self.assertEqual(wait(), "3.0")
        self.write(dict(VALID, hookStdinWait=0))  # below 0.1: no wait at all could miss the event
        self.assertEqual(wait(), "3.0")
        (self.tmp / ".claude" / "gw.json").unlink()
        self.assertEqual(wait(), "3.0")

    def test_measure_min_calls_default_and_bad_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "measure.minCalls").stdout.strip(), "5")
        self.write(dict(VALID, measure={}))
        self.assertEqual(cli(self.tmp, "get", "measure.minCalls").stdout.strip(), "5")
        self.write(dict(VALID, measure={"minCalls": 0}))
        self.assertEqual(cli(self.tmp, "get", "measure.minCalls").stdout.strip(), "0")
        for bad, why in {-1: "must be at least 0, got -1", "x": "expected integer, got str"}.items():
            self.write(dict(VALID, measure={"minCalls": bad}))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("$.measure.minCalls", r.stderr)
            self.assertIn(why, r.stderr)

    def test_private_check_default_and_bad_values(self):
        self.write(VALID)
        r = cli(self.tmp, "get", "privateCheck")
        self.assertEqual(json.loads(r.stdout), {"emails": True, "allowEmails": [], "maxHits": 10})
        for good in (False, True, {"emails": False}, {"allowEmails": ["me@example.com"]}):
            self.write(dict(VALID, privateCheck=good))
            self.assertEqual(cli(self.tmp, "validate").returncode, 0, good)
        cases = {"x": "expected", json.dumps({"mails": True}): "mails",
                 json.dumps({"allowEmails": ["not-an-address"]}): "does not match",
                 json.dumps({"allowEmails": "me@example.com"}): "expected", json.dumps({"emails": "yes"}): "expected"}
        for bad, why in cases.items():
            value = json.loads(bad) if bad.startswith("{") else bad
            self.write(dict(VALID, privateCheck=value))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("$.privateCheck", r.stderr)
            self.assertIn(why, r.stderr)

    def test_stale_refs_forms_and_globs(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import config
        self.assertEqual(config.stale_refs({}), ([], []))
        self.assertEqual(config.stale_refs({"staleRefs": ["a"]}), (["a"], []))
        self.assertEqual(config.stale_refs({"staleRefs": {"skip": ["d/"]}}), ([], ["d/"]))
        self.assertEqual(config.stale_refs({"staleRefs": {"patterns": ["a"], "skip": ["d/"]}}), (["a"], ["d/"]))
        for glob, path, hit in (("docs/*.md", "docs/a.md", True), ("docs/*.md", "docs/x/a.md", False),
                                ("docs/**/a.md", "docs/a.md", True), ("docs/**/a.md", "docs/x/y/a.md", True),
                                ("docs/x/", "docs/x/y/a.md", True), ("docs/x/", "docs/xy/a.md", False),
                                ("./docs/a.md", "docs/a.md", True), ("a?.md", "ab.md", True), ("a.md", "axmd", False),
                                ("docs/registros", "docs/registros", True), ("docs/registros", "docs/registros/a.md", True),
                                ("docs/registros/", "docs/registros", True), ("docs/registros", "docs/registros-old/a.md", False),
                                ("/docs/registros", "docs/registros/a/b.md", True), ("docs/a.md", "docs/a.md/x", True),
                                ("docs/**", "docs", True), ("docs/**", "docs/x/y.md", True), ("docs/**", "docsx", False),
                                ("docs/x*", "docs/xy/z.md", False)):
            self.assertEqual(bool(config.glob_regex(glob).match(path)), hit, (glob, path))

    def test_get_list_scalar_bool_and_default(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "check").stdout.splitlines(), ["make check", "make lint"])
        self.assertEqual(cli(self.tmp, "get", "log").stdout.strip(), "docs/log.md")
        self.assertEqual(cli(self.tmp, "get", "requireRetro").stdout.strip(), "false")
        self.assertEqual(cli(self.tmp, "get", "install", "--json").stdout.strip(), "[]")

    def test_check_wrapper_and_worktree_links_defaults_and_values(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "checkWrapper").stdout, "\n")
        self.assertEqual(cli(self.tmp, "get", "worktreeLinks").stdout.splitlines(), ["node_modules", ".venv"])
        self.write(dict(VALID, checkWrapper="tools/qa/host.sh", worktreeLinks=["backend/node_modules", ".env"]))
        self.assertEqual(cli(self.tmp, "get", "checkWrapper").stdout.strip(), "tools/qa/host.sh")
        self.assertEqual(cli(self.tmp, "get", "worktreeLinks").stdout.splitlines(), ["backend/node_modules", ".env"])
        self.write(dict(VALID, worktreeLinks=[]))
        self.assertEqual(cli(self.tmp, "get", "worktreeLinks", "--json").stdout.strip(), "[]")

    def test_worktree_links_must_stay_inside_the_repo(self):
        for bad in ("/etc", "../x", "a/../b", "a/..", ".."):
            self.write(dict(VALID, worktreeLinks=[bad]))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("worktreeLinks[0]", r.stderr)
            self.assertIn("does not match", r.stderr)
        self.write(dict(VALID, worktreeLinks=["..hidden", "a..b/c"]))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)

    def test_check_cache_inputs_default_and_must_stay_inside_the_repo(self):
        self.write(dict(VALID))
        self.assertEqual(cli(self.tmp, "get", "checkCacheInputs").stdout.splitlines(), [".claude/gw.local.json"])
        self.write(dict(VALID, checkCacheInputs=[]))
        self.assertEqual(cli(self.tmp, "get", "checkCacheInputs", "--json").stdout.strip(), "[]")
        for bad in ("/etc", "../x", "a/../b", ".."):
            self.write(dict(VALID, checkCacheInputs=[bad]))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("checkCacheInputs[0]", r.stderr)

    def test_related_tests_entries_are_strings_or_objects(self):
        ok = {"fast": ["npx vitest", {"command": "npm test {files}", "paths": "^app/", "cwd": "app"}], "slow": []}
        self.write(dict(VALID, relatedTests=ok))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.write(dict(VALID, relatedTests={"fast": [5]}))
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("relatedTests.fast[0]: matches none of the allowed forms", r.stderr)

    def test_push_scope_is_related_unless_the_environment_changes(self):  # D49
        def scope(data, files):
            self.write(data)
            r = subprocess.run(["python3", str(SCRIPT), "--root", str(self.tmp), "push-scope"], input="\n".join(files),
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip()
        rel = dict(VALID, relatedTests={"fast": ["make test"]})
        self.assertEqual(scope(rel, ["src/a.py"]), "related")
        self.assertEqual(scope(rel, []), "related")
        self.assertEqual(scope(rel, ["src/a.py", ".claude/gw.json"]), "full environment change: .claude/gw.json")
        self.assertEqual(scope(rel, [".githooks/pre-push"]), "full environment change: .githooks/pre-push")
        self.assertEqual(scope(rel, [".claude/settings.json"]), "full environment change: .claude/settings.json")
        self.assertEqual(scope(dict(rel, fullCheckPaths=["^tools/"]), [".githooks/pre-push"]), "related")
        self.assertEqual(scope(dict(rel, fullCheckPaths=["^tools/"]), ["tools/x"]), "full environment change: tools/x")
        self.assertEqual(scope(dict(rel, fullCheckPaths=[]), [".claude/gw.json"]),
                         "full environment change: .claude/gw.json")  # the config always counts
        self.assertEqual(scope(dict(rel, branchCheck="full"), ["src/a.py"]), "full branchCheck is full")
        self.assertEqual(scope(VALID, ["src/a.py"]), "full relatedTests has no command")
        self.assertEqual(scope(dict(VALID, relatedTests={"fast": [], "slow": []}), ["src/a.py"]),
                         "full relatedTests has no command")
        for bad, needle in ((dict(rel, branchCheck="none"), "$.branchCheck"),
                            (dict(rel, fullCheckPaths=["("]), "$.fullCheckPaths[0]: '(' is not a valid regex")):
            self.write(bad)
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(needle, r.stderr)

    def test_push_scope_counts_a_config_change_by_its_keys(self):  # E47
        def git(*args):
            return subprocess.run(["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                                  capture_output=True, text=True, check=True).stdout.strip()

        def commit(data):
            self.write(data)
            git("add", "-A")
            git("commit", "-q", "-m", "c")
            return git("rev-parse", "HEAD")

        def scope(commits, files=(".claude/gw.json",)):
            listing = Path(f"{self.tmp}-commits.txt")  # outside the repo: `git add -A` must not take it
            self.addCleanup(listing.unlink, missing_ok=True)
            listing.write_text("\n".join(commits) + "\n")
            r = subprocess.run(["python3", str(SCRIPT), "--root", str(self.tmp), "--rev", commits[-1], "push-scope",
                                "--commits", str(listing)], input="\n".join(files), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip()

        rel = dict(VALID, relatedTests={"fast": ["make test"]})
        commit(rel)
        a = commit(dict(rel, reviewTrivialLines=5, wholeReadWarnBytes=1000))
        self.assertEqual(scope([a]), "related")  # both in the default fullCheckSkipKeys
        b = commit(dict(rel, reviewTrivialLines=5, wholeReadWarnBytes=1000, check=["make all"]))
        self.assertEqual(scope([a, b]), "full environment change: .claude/gw.json (check)")
        self.assertEqual(scope([a], ["src/x.py", ".githooks/pre-push"]),
                         "full environment change: .githooks/pre-push")  # fullCheckPaths still count
        c = commit(dict(rel, fullCheckSkipKeys=["check"], check=["make all"]))
        self.assertEqual(scope([c]), "full environment change: .claude/gw.json (fullCheckSkipKeys, reviewTrivialLines, wholeReadWarnBytes)")
        d = commit(dict(rel, fullCheckSkipKeys=["check"], check=["make other"]))
        self.assertEqual(scope([d]), "related")  # the project's own list replaces the default one
        # A merge is compared with each parent; a broken or missing config on either side fails closed.
        git("checkout", "-q", "-b", "side", c)
        e = commit(dict(rel, fullCheckSkipKeys=["check"], check=["make all"], testJobs=2))
        git("checkout", "-q", "-")
        git("merge", "-q", "--no-ff", "-m", "m", "side", "-X", "ours")
        m = git("rev-parse", "HEAD")
        self.assertEqual(scope([e, m]), "full environment change: .claude/gw.json (testJobs)")
        (self.tmp / ".claude" / "gw.json").write_text("{")
        git("commit", "-q", "-am", "broken")
        broken = git("rev-parse", "HEAD")
        fixed = commit(dict(rel, fullCheckSkipKeys=["check"], check=["make other"]))
        self.assertEqual(scope([fixed]),
                         "full environment change: .claude/gw.json (cannot compare it with its parent)")
        self.assertEqual(scope([broken, fixed])[:4], "full")
        # Without --commits (an older pre-push), the config counts whole, as before.
        r = subprocess.run(["python3", str(SCRIPT), "--root", str(self.tmp), "push-scope"], input=".claude/gw.json",
                           capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "full environment change: .claude/gw.json")

    def test_doctor_test_dirs_ignore_default_and_own_value(self):  # E43
        self.assertIn(".claude/worktrees", config.doctor_test_dirs_ignore({}))
        self.assertEqual(config.doctor_test_dirs_ignore({"doctorTestDirsIgnore": ["vendor"]}), ["vendor"])
        self.write(VALID)
        self.assertIn("node_modules", config.doctor_test_dirs_ignore(config.load(str(self.tmp))))
        self.write(dict(VALID, doctorTestDirsIgnore="vendor"))
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("$.doctorTestDirsIgnore: expected array, got str", r.stderr)

    def test_owned_files_validation_and_helper(self):  # D53
        self.write(dict(VALID, ownedFiles=[".githooks/commit-msg", ".claude/skills/x/*"]))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        cfg = config.load(str(self.tmp))
        self.assertTrue(config.owned(cfg, ".githooks/commit-msg"))
        self.assertTrue(config.owned(cfg, ".claude/skills/x/SKILL.md"))
        self.assertFalse(config.owned(cfg, ".githooks/pre-push"))
        self.write(VALID)
        self.assertEqual(config.load(str(self.tmp))["ownedFiles"], [])
        for bad, needle in ((["/etc/hosts"], "$.ownedFiles[0]: '/etc/hosts' is an absolute path"),
                            ([".githooks/x", "a/../b"], "$.ownedFiles[1]: 'a/../b' has a '..' component"),
                            ([""], "$.ownedFiles[0]")):
            self.write(dict(VALID, ownedFiles=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(needle, r.stderr)

    def test_related_picks_the_commands_that_apply(self):
        entries = ["echo always", {"command": "run {files}", "paths": "\\.ts$", "cwd": "app"}]
        self.write(dict(VALID, relatedTests={"fast": entries}, checkWrapper="w.sh"))
        r = subprocess.run(["python3", str(SCRIPT), "--root", str(self.tmp), "related", "--kind", "fast"],
                           input="app/a b.ts\nsrc/x.py\n", capture_output=True, text=True)
        self.assertEqual(r.stdout.split("\0")[:-1],
                         ["w.sh bash -c 'echo always'", "w.sh bash -c 'cd app && run '\"'\"'a b.ts'\"'\"''"])

    def test_missing_config_fails_closed(self):
        r = cli(self.tmp, "get", "check")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not found", r.stderr)

    def test_invalid_config_names_every_problem(self):
        bad = dict(VALID, pushToProtected="sometimes", chek=["x"], check=[])
        del bad["language"]
        self.write(bad)
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        for fragment in ("pushToProtected", "unknown key 'chek'", "missing required key 'language'", "at least 1"):
            self.assertIn(fragment, r.stderr)

    def test_broken_json_reports_the_line(self):
        (self.tmp / ".claude" / "gw.json").write_text('{\n "version": "0.1.0",\n}')
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertRegex(r.stderr, r"invalid JSON at line [23]")

    def test_unknown_key_in_get_fails(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "get", "nope").returncode, 2)

    def test_rev_reads_the_config_of_that_commit(self):
        git = ["git", "-C", str(self.tmp), "-c", "user.name=T", "-c", "user.email=t@example.com",
               "-c", "commit.gpgsign=false"]
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "no config"], check=True)
        self.write(VALID)
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-q", "-m", "config"], check=True)
        self.write(dict(VALID, protectedBranch="trunk"))  # the working tree says otherwise
        self.assertEqual(cli(self.tmp, "get", "protectedBranch").stdout.strip(), "trunk")
        r = cli(self.tmp, "--rev", "HEAD", "get", "protectedBranch")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "main"), r.stderr)
        self.assertEqual(cli(self.tmp, "--rev", "HEAD", "get", "requireRetro").stdout.strip(), "false")
        r = cli(self.tmp, "--rev", "HEAD~1", "get", "protectedBranch")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not in commit HEAD~1", r.stderr)
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        (self.tmp / ".claude" / "gw.json").write_text("{}")
        subprocess.run([*git, "commit", "-q", "-am", "broken"], check=True)
        self.assertEqual(cli(self.tmp, "--rev", "HEAD", "validate").returncode, 2)

    def test_not_a_git_repo_fails(self):
        plain = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(cli(plain, "validate").returncode, 2)
        finally:
            shutil.rmtree(plain)


def load_field(root, field, rev=None):
    """config.load(root, rev)[field] printed by a fresh python3 (the CLI hides keys that start with `_`)."""
    code = ("import sys; sys.path.insert(0, %r); import config, pathlib; "
            "print(config.load(pathlib.Path(%r), %r)[%r])" % (str(ROOT / "scripts"), str(root), rev, field))
    return subprocess.run(["python3", "-c", code], capture_output=True, text=True)


class SchemaVersion(unittest.TestCase):
    """A9: gw.json carries a schemaVersion; an older one is migrated in memory, a newer one fails closed."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()
        self.git = ["git", "-C", str(self.tmp), "-c", "user.name=T", "-c", "user.email=t@example.com",
                    "-c", "commit.gpgsign=false"]

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, data):
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(data))

    def current(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gw_config", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_absent_is_version_0_and_loads_migrated(self):
        self.write(VALID)
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        r = load_field(self.tmp, "_schemaFrom")
        self.assertEqual(r.stdout.strip(), "0", r.stderr)
        r = load_field(self.tmp, "schemaVersion")
        self.assertEqual(r.stdout.strip(), str(self.current().SCHEMA_VERSION), r.stderr)
        self.assertEqual(json.loads((self.tmp / ".claude" / "gw.json").read_text()), VALID)  # load() never writes
        r = cli(self.tmp, "get", "_schemaFrom")
        self.assertEqual(r.returncode, 2)
        self.assertIn("key '_schemaFrom' is not set", r.stderr)

    def test_current_version_loads_as_is(self):
        version = self.current().SCHEMA_VERSION
        self.write(dict(VALID, schemaVersion=version))
        self.assertEqual(load_field(self.tmp, "_schemaFrom").stdout.strip(), str(version))
        self.assertEqual(cli(self.tmp, "get", "schemaVersion").stdout.strip(), str(version))

    def test_newer_version_fails_closed_naming_both_numbers_and_the_fix(self):
        version = self.current().SCHEMA_VERSION
        self.write(dict(VALID, schemaVersion=version + 1))
        r = cli(self.tmp, "get", "check")
        self.assertEqual(r.returncode, 2)
        self.assertIn(f"schemaVersion {version + 1} is newer than this copy of the workflow knows ({version})",
                      r.stderr)
        self.assertIn("/gw-update", r.stderr)
        self.assertIn("fetch origin tag vX.Y.Z", r.stderr)
        self.assertNotIn("pull --ff-only", r.stderr)

    def test_non_integer_or_negative_fails_closed(self):
        for bad in ("1", 1.5, True, None, -1):
            self.write(dict(VALID, schemaVersion=bad))
            r = cli(self.tmp, "validate")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn(f"schemaVersion must be a non-negative integer, got {bad!r}", r.stderr)

    def test_rev_with_an_old_config_is_migrated(self):
        version = self.current().SCHEMA_VERSION
        self.write(VALID)  # as a protected branch written before 0.5 has it
        subprocess.run([*self.git, "add", "-A"], check=True)
        subprocess.run([*self.git, "commit", "-q", "-m", "old"], check=True)
        self.write(dict(VALID, schemaVersion=version, protectedBranch="trunk"))
        r = cli(self.tmp, "--rev", "HEAD", "get", "protectedBranch")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "main"), r.stderr)
        self.assertEqual(load_field(self.tmp, "_schemaFrom", "HEAD").stdout.strip(), "0")
        self.assertEqual(load_field(self.tmp, "_schemaFrom").stdout.strip(), str(version))

    def test_rev_with_a_newer_config_fails_closed(self):
        version = self.current().SCHEMA_VERSION
        self.write(dict(VALID, schemaVersion=version + 1))
        subprocess.run([*self.git, "add", "-A"], check=True)
        subprocess.run([*self.git, "commit", "-q", "-m", "newer"], check=True)
        r = cli(self.tmp, "--rev", "HEAD", "get", "protectedBranch")
        self.assertEqual(r.returncode, 2)
        self.assertIn(f"HEAD:.claude/gw.json: schemaVersion {version + 1} is newer", r.stderr)

    def test_migrate_returns_a_copy_and_the_descriptions(self):
        config = self.current()
        raw = {"$schema": "x", "version": "0.4.3", "language": "en"}
        out, done = config.migrate(raw)
        self.assertEqual(raw, {"$schema": "x", "version": "0.4.3", "language": "en"})  # untouched
        self.assertEqual(list(out), ["$schema", "version", "schemaVersion", "language"])  # right after version
        self.assertEqual(out["schemaVersion"], config.SCHEMA_VERSION)
        self.assertEqual(len(done), config.SCHEMA_VERSION)
        self.assertEqual(config.migrate(out), (out, []))
        self.assertEqual([t for t, _d, _f in config.MIGRATIONS], list(range(1, config.SCHEMA_VERSION + 1)))

    def test_the_schema_knows_the_key(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())
        self.assertEqual(schema["properties"]["schemaVersion"]["type"], "integer")
        self.assertNotIn("schemaVersion", schema["required"])  # optional during 0.x
        template = json.loads((ROOT / "templates" / "gw.json").read_text())
        self.assertEqual(template["schemaVersion"], self.current().SCHEMA_VERSION)


MIN = {"version": "0.1.0", "language": "en", "protectedBranch": "main", "pushToProtected": "pr",
       "check": ["make check"], "content": ["^docs/"]}
PATH_KEYS = {  # key: (new default, old Spanish path), A8
    "log": ("docs/handoff.md", "docs/traspaso.md"),
    "reviewMark": ("docs/records/reviewed.txt", "docs/registros/revisado.txt"),
    "ciLocalLog": ("docs/records/ci-local.md", "docs/registros/ci-local.md"),
    "recordsDir": ("docs/records", "docs/registros"),
    "proposalsDir": ("docs/proposals", "docs/propuestas"),
}


class ProjectPaths(unittest.TestCase):
    """A8: the paths the workflow creates in a project are English, configurable, with an old-name fallback."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, data):
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(data))

    def touch(self, rel):
        if rel in ("docs/records", "docs/registros", "docs/proposals", "docs/propuestas"):
            rel += "/a.md"  # a folder: put a file in it
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")

    def get(self, key, *extra):
        r = cli(self.tmp, *extra, "get", key)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def test_neither_exists_gives_the_english_default(self):
        self.write(MIN)
        for key, (new, _old) in PATH_KEYS.items():
            self.assertEqual(self.get(key), new, key)

    def test_new_default_exists_wins_even_if_the_old_one_does_too(self):
        self.write(MIN)
        for new, old in PATH_KEYS.values():
            self.touch(new)
            self.touch(old)
        for key, (new, _old) in PATH_KEYS.items():
            self.assertEqual(self.get(key), new, key)

    def test_absent_key_falls_back_to_the_old_path_only_when_it_alone_exists(self):
        self.write(MIN)
        for _new, old in PATH_KEYS.values():
            self.touch(old)
        for key, (_new, old) in PATH_KEYS.items():
            self.assertEqual(self.get(key), old, key)
        
    def test_fallback_is_per_key(self):
        self.write(MIN)
        self.touch("docs/traspaso.md")
        self.assertEqual(self.get("log"), "docs/traspaso.md")
        self.assertEqual(self.get("recordsDir"), "docs/records")
        self.assertEqual(self.get("proposalsDir"), "docs/proposals")

    def test_explicit_value_always_wins(self):
        explicit = {key: "x/" + key for key in PATH_KEYS}
        explicit["ciLocalLog"] = "x/ci.md"
        self.write(dict(MIN, **explicit))
        for _new, old in PATH_KEYS.values():
            self.touch(old)
        for key, value in explicit.items():
            self.assertEqual(self.get(key), value, key)
        # an explicit value naming the new default is kept even when only the old path exists
        self.write(dict(MIN, log="docs/handoff.md"))
        self.assertEqual(self.get("log"), "docs/handoff.md")

    def test_fallback_reads_the_commit_with_rev(self):
        self.write(MIN)
        self.touch("docs/traspaso.md")
        git = ["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "x"], check=True)
        (self.tmp / "docs" / "traspaso.md").unlink()
        self.touch("docs/handoff.md")  # the working tree has the new name, the commit the old one
        self.assertEqual(self.get("log"), "docs/handoff.md")
        self.assertEqual(self.get("log", "--rev", "HEAD"), "docs/traspaso.md")

    def test_paths_at_decides_the_fallback_while_rev_gives_the_config(self):
        # A push judged by the remote tip's config (--rev) still resolves the paths of the commit it pushes.
        self.write(MIN)
        git = ["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "tip"], check=True)  # the tip: a config, no mark file yet
        self.touch("docs/registros/revisado.txt")
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "pushed"], check=True)
        self.assertEqual(self.get("reviewMark", "--rev", "HEAD~1"), "docs/records/reviewed.txt")
        self.assertEqual(self.get("reviewMark", "--rev", "HEAD~1", "--paths-at", "HEAD"), "docs/registros/revisado.txt")
        self.assertEqual(self.get("reviewMark", "--rev", "HEAD~1", "--paths-at", "HEAD~1"), "docs/records/reviewed.txt")

    def test_paths_at_follows_the_move_of_an_old_path_the_tip_names_explicitly(self):
        # The protected tip of a 0.4 project names the old paths; the pushed commit applied the A8 move (old file gone,
        # English default present). Without paths_at, or with keepLegacyPaths, the explicit value stays.
        git = ["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t"]
        for keep in (False, True):
            explicit = {key: old for key, (_new, old) in PATH_KEYS.items()}
            self.write(dict(MIN, keepLegacyPaths=True, **explicit) if keep else dict(MIN, **explicit))
            shutil.rmtree(self.tmp / "docs", ignore_errors=True)
            for _new, old in PATH_KEYS.values():
                self.touch(old)
            subprocess.run(git + ["add", "-A"], check=True)
            subprocess.run(git + ["commit", "-qm", "tip"], check=True)
            shutil.rmtree(self.tmp / "docs")
            for new, _old in PATH_KEYS.values():
                self.touch(new)
            subprocess.run(git + ["add", "-A"], check=True)
            subprocess.run(git + ["commit", "-qm", "moved"], check=True)
            for key, (new, old) in PATH_KEYS.items():
                self.assertEqual(self.get(key, "--rev", "HEAD~1", "--paths-at", "HEAD"), old if keep else new, key)
                self.assertEqual(self.get(key, "--rev", "HEAD~1", "--paths-at", "HEAD~1"), old, key)
                self.assertEqual(self.get(key, "--rev", "HEAD~1"), old, key)

    def test_a_commit_judged_by_its_own_config_keeps_its_explicit_old_path(self):
        # --paths-at equal to --rev (is-code.sh, a remote with no config yet): the config is that commit's own, so its
        # explicit value wins even when the old file is gone and the English one exists; another spelling of the old
        # path in a protected tip is followed like the canonical one
        git = ["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t"]
        self.write(dict(MIN, reviewMark="./docs/registros/revisado.txt"))
        self.touch("docs/records/reviewed.txt")
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "own"], check=True)
        self.assertEqual(self.get("reviewMark", "--rev", "HEAD", "--paths-at", "HEAD"), "./docs/registros/revisado.txt")
        self.touch("docs/notes.md")
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "pushed"], check=True)
        self.assertEqual(self.get("reviewMark", "--rev", "HEAD~1", "--paths-at", "HEAD"), "docs/records/reviewed.txt")

    def test_paths_at_with_a_missing_commit_fails_closed(self):
        self.write(MIN)
        git = ["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "tip"], check=True)
        r = cli(self.tmp, "--rev", "HEAD", "--paths-at", "nonexistent_rev", "get", "reviewMark")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("--paths-at nonexistent_rev is not a commit", r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_an_empty_folder_does_not_count_as_existing(self):
        self.write(MIN)
        (self.tmp / "docs" / "propuestas").mkdir(parents=True)  # git would not even version it
        self.assertEqual(self.get("proposalsDir"), "docs/proposals")

    def test_legacy_marker_is_hidden_from_get_and_lists_the_fallbacks(self):
        self.write(MIN)
        self.touch("docs/propuestas")
        r = cli(self.tmp, "get", "_legacy")
        self.assertEqual(r.returncode, 2)
        self.assertIn("key '_legacy' is not set and has no default", r.stderr)
        sys_path = str(ROOT / "scripts")
        code = ("import sys; sys.path.insert(0, %r); import config, pathlib; "
                "print(config.load(pathlib.Path(%r))['_legacy'])" % (sys_path, str(self.tmp)))
        out = subprocess.run(["python3", "-c", code], capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "{'proposalsDir': 'docs/propuestas'}", out.stderr)

    def test_bad_values_are_rejected(self):
        for key in ("recordsDir", "proposalsDir"):
            for bad in ("/abs", "../x", "docs/x/", ""):
                self.write(dict(MIN, **{key: bad}))
                r = cli(self.tmp, "validate")
                self.assertEqual(r.returncode, 2, (key, bad))
                self.assertIn(f"$.{key}", r.stderr)


class LinkedWorktree(unittest.TestCase):
    """Inside a `git worktree add` checkout the scripts must find that worktree, not the main checkout (WMF P1).
    Git exports GIT_DIR (the worktree's git dir, no GIT_WORK_TREE) to hooks; with it set, `rev-parse --show-toplevel`
    answers the folder it is given, so the script's own repo looked like it had no .claude/gw.json."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.main = self.tmp / "main"
        self.wt = self.tmp / "wt"

        def git(*a, cwd=self.main):
            subprocess.run(["git", *a], cwd=str(cwd), check=True, capture_output=True)

        self.main.mkdir()
        git("init", "-q", "-b", "main")
        git("config", "user.email", "t@t")
        git("config", "user.name", "t")
        scripts = self.main / ".claude" / "gw" / "scripts"
        scripts.mkdir(parents=True)
        for name in ("config.py", "red-without-fix.sh"):
            shutil.copy(ROOT / "scripts" / name, scripts / name)
        shutil.copytree(ROOT / "schema", self.main / ".claude" / "gw" / "schema")
        (self.main / ".claude" / "gw.json").write_text(json.dumps(dict(VALID, log="main-log.md")))
        git("add", "-A")
        git("commit", "-q", "-m", "init")
        git("worktree", "add", "-q", "-b", "side", str(self.wt))
        (self.wt / ".claude" / "gw.json").write_text(json.dumps(dict(VALID, log="wt-log.md")))
        (self.wt / "fix.txt").write_text("bad\n")
        git("add", "-A", cwd=self.wt)
        git("commit", "-q", "-m", "side config", cwd=self.wt)
        self.gitdir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=str(self.wt), check=True,
                                     capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_in_wt(self, *cmd, env=None):
        full = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        full.update({"CLAUDE_PROJECT_DIR": str(self.main), "GIT_DIR": self.gitdir})
        full.update(env or {})
        return subprocess.run(cmd, cwd=str(self.wt), capture_output=True, text=True, env=full)

    def test_config_py_resolves_the_worktree_with_git_dir_exported_by_a_hook(self):
        script = str(self.wt / ".claude" / "gw" / "scripts" / "config.py")
        r = self.run_in_wt("python3", script, "root")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, str(self.wt)), r.stderr)
        r = self.run_in_wt("python3", script, "get", "log")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "wt-log.md"), r.stderr)

    def plugin_config(self):
        """A copy like the plugin's scripts/ (no .claude/gw.json beside it): its root comes from the cwd and
        $CLAUDE_PROJECT_DIR, not from its own folder."""
        plugin = self.tmp / "plugin" / "scripts"
        plugin.mkdir(parents=True)
        shutil.copy(SCRIPT, plugin / "config.py")
        shutil.copytree(ROOT / "schema", plugin.parent / "schema")
        return str(plugin / "config.py")

    def run_at(self, cwd, *cmd, project=None):
        full = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "CLAUDE_PROJECT_DIR"}
        full["GIT_CEILING_DIRECTORIES"] = str(self.tmp)
        if project:
            full["CLAUDE_PROJECT_DIR"] = str(project)
        return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=full)

    def test_plugin_config_in_a_linked_worktree_prefers_it_over_claude_project_dir(self):
        # $CLAUDE_PROJECT_DIR names the main checkout (where Claude Code was opened); the worktree is the same repo.
        r = self.run_in_wt("python3", self.plugin_config(), "root")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, str(self.wt)), r.stderr)

    def test_plugin_config_from_a_sibling_repo_keeps_claude_project_dir(self):
        # A hook whose cwd is another repo (a sibling, a clone being read) must not take that repo's config.
        sibling = self.tmp / "sibling"
        sibling.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=str(sibling), check=True)
        r = self.run_at(sibling, "python3", self.plugin_config(), "root", project=self.main)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, str(self.main)), r.stderr)

    def test_plugin_config_outside_any_repo_uses_claude_project_dir_or_fails_closed(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        script = self.plugin_config()
        r = self.run_at(outside, "python3", script, "root", project=self.main)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, str(self.main)), r.stderr)
        r = self.run_at(outside, "python3", script, "root")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("not inside a git repository", r.stderr)

    def test_every_shell_script_root_line_finds_the_worktree_with_git_dir_exported(self):
        # The `root=` line of each script that finds its root from its own folder, run as is inside the worktree.
        here = self.wt / ".claude" / "gw" / "scripts"
        names = ("is-code.sh", "merge-branch.sh", "prepush-branches.sh", "reviewed.sh", "related-tests.sh",
                 "red-without-fix.sh", "check-green.sh", "check.sh")
        for name in names:
            with self.subTest(script=name):
                lines = [ln for ln in (ROOT / "scripts" / name).read_text().splitlines() if ln.startswith('root="$(')]
                self.assertEqual(len(lines), 1, lines)
                line = lines[0].split(" || ")[0]
                r = self.run_in_wt("bash", "-c", f'here="{here}"; {line} && printf "%s" "$root"')
                self.assertEqual((r.returncode, r.stdout), (0, str(self.wt)), r.stderr)

    def test_shell_script_finds_the_worktree_root_with_git_dir_exported(self):
        # red-without-fix.sh stashes the fix file at the root it found: a wrong root says "no uncommitted changes".
        (self.wt / "fix.txt").write_text("good\n")
        script = str(self.wt / ".claude" / "gw" / "scripts" / "red-without-fix.sh")
        r = self.run_in_wt("bash", script, "grep -q good fix.txt", "fix.txt")
        self.assertNotIn("has no uncommitted changes", r.stderr)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("without the fix: exit 1; with the fix: exit 0", r.stdout)


class NonCapturing(unittest.TestCase):
    def test_groups_become_non_capturing_and_the_rest_is_left_alone(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import config
        cases = {r"(INS|FLU)-\d+": r"(?:INS|FLU)-\d+", r"\(x\)(a|b)": r"\(x\)(?:a|b)", r"[(]a(b)": r"[(]a(?:b)",
                 r"(?:a)(?P<n>c)": r"(?:a)(?:c)", r"[^]()](z)": r"[^]()](?:z)", r"(?i)a(b)": r"(?i)a(?:b)",
                 r"[A-Z]{2,5}-\d+[a-z]?": r"[A-Z]{2,5}-\d+[a-z]?"}
        for src, want in cases.items():
            self.assertEqual(config.non_capturing(src), want)
        with self.assertRaises(config.ConfigError) as ctx:
            config.non_capturing(r"(a)\1")
        self.assertIn("back-reference", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
