"""scripts/config.py: validation, defaults, CLI and failing closed."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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

    def test_related_tests_entries_are_strings_or_objects(self):
        ok = {"fast": ["npx vitest", {"command": "npm test {files}", "paths": "^app/", "cwd": "app"}], "slow": []}
        self.write(dict(VALID, relatedTests=ok))
        self.assertEqual(cli(self.tmp, "validate").returncode, 0)
        self.write(dict(VALID, relatedTests={"fast": [5]}))
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("relatedTests.fast[0]: matches none of the allowed forms", r.stderr)

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
        del bad["log"]
        self.write(bad)
        r = cli(self.tmp, "validate")
        self.assertEqual(r.returncode, 2)
        for fragment in ("pushToProtected", "unknown key 'chek'", "missing required key 'log'", "at least 1"):
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
        for name in ("config.py", "rojo-sin-arreglo.sh"):
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
        names = ("es-codigo.sh", "fusionar.sh", "prepush-ramas.sh", "revisado.sh", "tests-relacionados.sh",
                 "rojo-sin-arreglo.sh", "check-verde.sh", "check.sh")
        for name in names:
            with self.subTest(script=name):
                lines = [ln for ln in (ROOT / "scripts" / name).read_text().splitlines() if ln.startswith('root="$(')]
                self.assertEqual(len(lines), 1, lines)
                line = lines[0].split(" || ")[0]
                r = self.run_in_wt("bash", "-c", f'here="{here}"; {line} && printf "%s" "$root"')
                self.assertEqual((r.returncode, r.stdout), (0, str(self.wt)), r.stderr)

    def test_shell_script_finds_the_worktree_root_with_git_dir_exported(self):
        # rojo-sin-arreglo.sh stashes the fix file at the root it found: a wrong root says "no uncommitted changes".
        (self.wt / "fix.txt").write_text("good\n")
        script = str(self.wt / ".claude" / "gw" / "scripts" / "rojo-sin-arreglo.sh")
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
