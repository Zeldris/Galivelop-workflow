"""The templates (templates/es, templates/en, templates/gw.json, templates/github) and how scripts/apply.py writes
them: `--init` on an empty repo yields a project doctor.py accepts, a second run changes nothing, an existing
AGENTS.md/CLAUDE.md is never overwritten, the files the project fills in (log, REVIEW.md, GLOSSARY.md, notes) are
never written again, and the Spanish and English templates stay paired. HOME is a temp folder and git runs isolated
as in test_hooks.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

APPLY_SCRIPT = ROOT / "scripts" / "apply.py"
TEMPLATES = ROOT / "templates"
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
MARKER = f"<!-- galivelop-workflow v{VERSION} -->"
LOGS = {"es": "docs/handoff.md", "en": "docs/handoff.md"}  # A8: English paths in both
RENDERED = ("AGENTS.md", "CLAUDE.md", "REVIEW.md", "GLOSSARY.md", ".github/workflows/check.yml",
            ".claude/gw/gw-opt-tokens.md", ".claude/gw.json")


def lang_files(lang):
    return sorted(p.name for p in (TEMPLATES / lang).iterdir() if p.is_file())


def headings(path):
    """Markdown headings outside code fences."""
    count, fence = 0, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fence = not fence
        elif not fence and re.match(r"^#{1,6} ", line):
            count += 1
    return count


class Project:
    def __init__(self, tmp):
        self.work = tmp / "work"
        home = tmp / "home"
        home.mkdir()
        gitconfig = tmp / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[commit]\n\tgpgsign = false\n"
                             "[init]\n\tdefaultBranch = main\n")
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("GIT_") and k not in ("CLAUDECODE", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_REMOTE")}
        self.env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1", TMPDIR=str(tmp), HOME=str(home),
                        GW_NOTAS_PERSONALES=str(tmp / "no-personal-notes"))  # never the real notes, nor an exported one
        self.run("git", "init", "-q", str(self.work), cwd=tmp)
        self.write("check.sh", "exit 0\n")

    def run(self, *cmd, cwd=None):
        r = subprocess.run(list(cmd), cwd=str(cwd or self.work), env=self.env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout + r.stderr

    def run_apply(self, *args):
        return self.run("python3", str(APPLY_SCRIPT), str(self.work), *args)

    def init(self, lang="en", *extra):
        return self.run_apply("--init", "--language", lang, "--check-command", "bash check.sh", *extra)

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def read(self, rel):
        return (self.work / rel).read_text()


class Templates(unittest.TestCase):
    def test_es_and_en_have_the_same_files_and_headings(self):
        self.assertEqual(lang_files("es"), lang_files("en"))
        for name in lang_files("es"):
            with self.subTest(name=name):
                self.assertEqual(headings(TEMPLATES / "es" / name), headings(TEMPLATES / "en" / name),
                                 f"templates/es/{name} and templates/en/{name} must have the same headings")

    def test_review_template_asks_to_refute_and_to_end_with_a_verdict(self):
        for lang in ("es", "en"):
            text = (TEMPLATES / lang / "REVIEW.md").read_text(encoding="utf-8")
            with self.subTest(lang=lang):
                for verdict in ("`SHIP`", "`SHIP WITH FIXES`", "`DO NOT SHIP`"):
                    self.assertIn(verdict, text, f"{lang}/REVIEW.md: the three verdicts are missing")
                self.assertRegex(text, r"refut", f"{lang}/REVIEW.md: it must ask to refute each finding")

    def test_every_review_rule_names_its_check_or_says_judgement(self):
        """E6: each top-level bullet ends in `(check: …)` or in the judgement word of its language."""
        for lang, judgement in (("es", "criterio"), ("en", "judgement")):
            text = (TEMPLATES / lang / "REVIEW.md").read_text(encoding="utf-8")
            bullets, current = [], None
            for line in text.splitlines():
                if line.startswith("- "):
                    current = [line]
                    bullets.append(current)
                elif line.startswith("  ") and current is not None:
                    current.append(line)
                else:
                    current = None
            with self.subTest(lang=lang):
                self.assertGreater(len(bullets), 10, f"{lang}/REVIEW.md: the rules were not found")
                marker = re.compile(r"\((check: [^()]+|%s)\)$" % judgement)
                for bullet in bullets:
                    self.assertRegex(bullet[-1].strip(), marker,
                                     f"{lang}/REVIEW.md: this rule names no check nor says ({judgement}): {bullet[0]}")
                self.assertTrue(any("(check: " in b[-1] for b in bullets), f"{lang}/REVIEW.md: no rule names a check")

    def test_every_template_starts_with_the_version_marker(self):
        for lang in ("es", "en"):
            for name in lang_files(lang):
                with self.subTest(file=f"{lang}/{name}"):
                    first = (TEMPLATES / lang / name).read_text(encoding="utf-8").splitlines()[0]
                    self.assertEqual(first, MARKER)
        first = (TEMPLATES / "github" / "check.yml").read_text().splitlines()[0]
        self.assertEqual(first, f"# galivelop-workflow v{VERSION}")

    def test_placeholders_are_only_config_keys_project_version_and_computed(self):
        allowed = {"log", "protectedBranch", "check", "install", "reviewMark", "language", "version", "project",
                   "ciPushIgnore"}  # ciPushIgnore: computed from ciOnPush and protectedBranch (D54)
        for path in sorted(TEMPLATES.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".yml"):
                with self.subTest(file=str(path.relative_to(ROOT))):
                    found = set(re.findall(r"\{\{(\w+)\}\}", path.read_text(encoding="utf-8")))
                    self.assertLessEqual(found, allowed)

    def test_agents_authorises_subagents_and_size_limits(self):
        for lang in ("es", "en"):
            agents = (TEMPLATES / lang / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("gw-orchestrate-dealer", agents)
            self.assertIn("Siguiente:" if lang == "es" else "Next:", agents)
            self.assertIn("core.hooksPath", agents)
            self.assertIn("@AGENTS.md", (TEMPLATES / lang / "CLAUDE.md").read_text(encoding="utf-8"))
            for name in ("AGENTS.md", "CLAUDE.md"):
                with self.subTest(file=f"{lang}/{name}"):
                    lines = len((TEMPLATES / lang / name).read_text(encoding="utf-8").splitlines())
                    self.assertLessEqual(lines, 200)

    def test_agents_names_the_own_log_row_commands(self):
        for lang in ("es", "en"):
            agents = (TEMPLATES / lang / "AGENTS.md").read_text(encoding="utf-8")
            for needle in ("logRows", ".claude/gw/scripts/handoff.py set-row", ".claude/gw/scripts/handoff.py close-row"):
                with self.subTest(lang=lang, text=needle):
                    self.assertIn(needle, agents)

    def test_ci_that_does_not_start_allows_the_local_check_only_with_confirmation(self):
        texts = {"es": ("comprobado solo en local", "solo si la persona lo confirma", "nunca se sustituye"),
                 "en": ("checked only locally", "only if the person confirms it", "never replaced")}
        for lang, needles in texts.items():
            agents = (TEMPLATES / lang / "AGENTS.md").read_text(encoding="utf-8")
            for needle in needles:
                with self.subTest(lang=lang, text=needle):
                    self.assertIn(needle, agents)
        self.assertIn("comprobado solo en local", (ROOT / "AGENTS.md").read_text(encoding="utf-8"))

    def test_no_path_the_workflow_no_longer_uses(self):
        obsolete = (".claude/hooks/",)  # the workflow's scripts live in .claude/gw/scripts/
        places = [TEMPLATES, ROOT / "scripts", ROOT / "skills", ROOT / "docs" / "es", ROOT / "docs" / "en"]
        files = [f for d in places for f in d.rglob("*") if f.is_file() and "__pycache__" not in f.parts]
        files += [ROOT / "README.md", ROOT / "README.es.md"]
        found = [f"{f.relative_to(ROOT)}: {path}" for f in files for path in obsolete
                 if path in f.read_text(encoding="utf-8", errors="replace")]
        self.assertEqual(found, [], "paths the workflow no longer creates")

    def test_ci_sets_up_the_toolchain_from_the_project_files(self):
        text = (TEMPLATES / "github" / "check.yml").read_text()
        install = text.index("- name: Install")
        for action, files in (("setup-node", None), ("setup-python", "'pyproject.toml'"),
                              ("setup-java", "'pom.xml'")):
            with self.subTest(action=action):
                at = text.index(f"actions/{action}@")
                self.assertLess(at, install, f"{action} must run before Install")
                if files is None:  # D84: Node goes by the `dirs` step (ciNodeDirs)
                    self.assertIn("if: needs.versions.outputs.node == 'true'", text[at:install])
                else:
                    self.assertIn(f"if: hashFiles({files}", text[at:install])

    def ci_install(self, **keys):
        """Run the CI template's Install step in a temp project whose gw.json has `keys`; return the commands run."""
        text = (TEMPLATES / "github" / "check.yml").read_text()
        step = text.split("- name: Install\n        run: |\n", 1)[1].split("      - name:", 1)[0]
        script = "\n".join(l[10:] for l in step.splitlines())
        tmp = Path(tempfile.mkdtemp(prefix="gw-ci-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / ".claude" / "gw").mkdir(parents=True)
        shutil.copytree(ROOT / "scripts", tmp / ".claude" / "gw" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "schema", tmp / ".claude" / "gw" / "schema")
        cfg = {"version": VERSION, "language": "en", "log": "docs/log.md", "protectedBranch": "main",
               "pushToProtected": "direct", "check": ["true"], "reviewMark": "r.txt", "content": ["^docs/"]}
        raw = keys.pop("_raw", None)
        (tmp / ".claude" / "gw.json").write_text(raw if raw is not None else json.dumps(dict(cfg, **keys)))
        subprocess.run(["git", "init", "-q", str(tmp)], check=True)
        r = subprocess.run(["bash", "-e", "-c", script], cwd=tmp, capture_output=True, text=True)
        return r

    def test_ci_installs_ci_install_and_falls_back_to_install(self):
        cases = ((dict(install=["echo a"]), ["== echo a"]),
                 (dict(install=["echo a"], ciInstall=["echo b"]), ["== echo b"]),
                 (dict(install=["echo a"], ciInstall=[]), []),
                 ({}, []))
        for keys, expected in cases:
            with self.subTest(keys=keys):
                r = self.ci_install(**keys)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual([l for l in r.stdout.splitlines() if l.startswith("==")], expected)

    def test_ci_install_fails_closed_on_a_bad_config(self):
        r = self.ci_install(install="npm ci")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("$.install: expected array", r.stderr)

    def test_ci_install_fails_closed_when_python_is_missing_or_the_config_is_unreadable(self):
        r = self.ci_install(install=["echo a"], ciInstall="npm ci")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("$.ciInstall: expected array", r.stderr)
        self.assertNotIn("== ", r.stdout)
        r = self.ci_install(install=["echo a"], _raw="{not json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid JSON", r.stderr)
        self.assertNotIn("== echo a", r.stdout)

    def ci_python(self, pyfiles=("pyproject.toml",), **keys):
        """Run the CI template's `versions` step in a temp project; return (result, matrix JSON or None)."""
        text = (TEMPLATES / "github" / "check.yml").read_text()
        step = text.split("      - id: python\n        run: |\n", 1)[1].split("      - id: dirs", 1)[0]
        script = "\n".join(l[10:] for l in step.splitlines())
        tmp = Path(tempfile.mkdtemp(prefix="gw-ci-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / ".claude" / "gw").mkdir(parents=True)
        shutil.copytree(ROOT / "scripts", tmp / ".claude" / "gw" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "schema", tmp / ".claude" / "gw" / "schema")
        cfg = {"version": VERSION, "language": "en", "log": "docs/log.md", "protectedBranch": "main",
               "pushToProtected": "direct", "check": ["true"], "reviewMark": "r.txt", "content": ["^docs/"]}
        (tmp / ".claude" / "gw.json").write_text(json.dumps(dict(cfg, **keys)))
        subprocess.run(["git", "init", "-q", str(tmp)], check=True)
        for f in pyfiles:
            (tmp / f).write_text("")
        out = tmp / "out.txt"
        r = subprocess.run(["bash", "-e", "-c", script], cwd=tmp, capture_output=True, text=True,
                           env=dict(os.environ, GITHUB_OUTPUT=str(out)))
        return r, (out.read_text().strip() if out.exists() else None)

    def test_ci_python_matrix_from_the_config(self):
        cases = ((dict(), 'python=["3.x"]'),
                 (dict(ciPython=["3.13"]), 'python=["3.13"]'),
                 (dict(ciPython=["3.10", "3.13"]), 'python=["3.10", "3.13"]'))
        for keys, expected in cases:
            with self.subTest(keys=keys):
                r, out = self.ci_python(**keys)
                self.assertEqual((r.returncode, out), (0, expected), r.stderr)

    def test_ci_python_is_one_job_without_python_project_files(self):
        for pyfiles, expected in (((), 'python=["3.x"]'), (("requirements-dev.txt",), 'python=["3.10", "3.13"]'),
                                  (("package.json",), 'python=["3.x"]')):
            with self.subTest(pyfiles=pyfiles):
                r, out = self.ci_python(pyfiles=pyfiles, ciPython=["3.10", "3.13"])
                self.assertEqual((r.returncode, out), (0, expected), r.stderr)

    def test_ci_job_is_named_check_without_ciPython_and_check_version_with_it(self):
        text = (TEMPLATES / "github" / "check.yml").read_text()
        name = re.search(r"^    name: (.*)$", text.split("\n  check:\n", 1)[1], re.M).group(1)
        self.assertIn("matrix.python == '3.x' && 'check'", name)
        self.assertIn("format('check ({0})', matrix.python)", name)

    def test_ci_python_accepts_the_versions_setup_python_accepts(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]["ciPython"]
        for ok in ("3", "3.13", "3.x", "pypy3.10", "3.13-dev", "3.12.0-rc.1"):
            with self.subTest(ok=ok):
                self.assertEqual(config.validate([ok], schema, "$.ciPython"), [])
        for bad in ("", "3 .13", " 3.13"):
            with self.subTest(bad=bad):
                errors = config.validate([bad], schema, "$.ciPython")
                self.assertTrue(errors and "does not match" in errors[0], errors)

    def test_ci_python_fails_closed_on_a_bad_value(self):
        cases = ((dict(ciPython=[]), "$.ciPython: needs at least 1 item(s)"),
                 (dict(ciPython="3.13"), "$.ciPython: expected array"),
                 (dict(ciPython=[3.1]), "$.ciPython[0]: expected string"),
                 (dict(ciPython=["3.10", "3.10"]), "$.ciPython[1]: duplicate"),
                 (dict(ciPython=[""]), "$.ciPython[0]: '' does not match"),
                 (dict(ciPython=["3 .13"]), "$.ciPython[0]: '3 .13' does not match"))
        for keys, needle in cases:
            with self.subTest(keys=keys):
                r, out = self.ci_python(**keys)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(needle, r.stderr)
                self.assertIsNone(out)

    def test_ci_python_matrix_feeds_setup_python(self):
        text = (TEMPLATES / "github" / "check.yml").read_text()
        self.assertIn("fromJSON(needs.versions.outputs.python)", text)
        self.assertIn("python-version: ${{ matrix.python }}", text)

    def ci_dirs(self, files=(), **keys):
        """Run the CI template's `dirs` step in a temp project with `files` (repo-relative); return (result, outputs)."""
        text = (TEMPLATES / "github" / "check.yml").read_text()
        step = text.split("      - id: dirs\n", 1)[1].split("        run: |\n", 1)[1].split("  check:", 1)[0]
        script = "\n".join(l[10:] for l in step.splitlines())
        tmp = Path(tempfile.mkdtemp(prefix="gw-ci-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / ".claude" / "gw").mkdir(parents=True)
        shutil.copytree(ROOT / "scripts", tmp / ".claude" / "gw" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "schema", tmp / ".claude" / "gw" / "schema")
        cfg = {"version": VERSION, "language": "en", "log": "docs/log.md", "protectedBranch": "main",
               "pushToProtected": "direct", "check": ["true"], "reviewMark": "r.txt", "content": ["^docs/"]}
        (tmp / ".claude" / "gw.json").write_text(json.dumps(dict(cfg, **keys)))
        subprocess.run(["git", "init", "-q", str(tmp)], check=True)
        for f in files:
            (tmp / f).parent.mkdir(parents=True, exist_ok=True)
            (tmp / f).write_text("")
        out = tmp / "out.txt"
        r = subprocess.run(["bash", "-e", "-c", script], cwd=tmp, capture_output=True, text=True,
                           env=dict(os.environ, GITHUB_OUTPUT=str(out)))
        return r, (out.read_text() if out.exists() else None)

    def test_ci_dirs_default_keeps_the_root_node_and_no_rust(self):
        for files, node in (((), "false"), (("package.json",), "true"), (("app/package.json", "Cargo.toml"), "false")):
            with self.subTest(files=files):
                r, out = self.ci_dirs(files)
                self.assertEqual((r.returncode, out), (0, f"node={node}\nrust=false\nrust_workspaces<<GW_EOF\nGW_EOF\n"),
                                 r.stderr)

    def test_ci_node_dirs_one_or_several(self):
        r, out = self.ci_dirs(("app/package.json",), ciNodeDirs=["app"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.startswith("node=true\n"), out)
        r, out = self.ci_dirs(("web/package.json",), ciNodeDirs=["app", "web"])
        self.assertTrue(out.startswith("node=true\n"), out)
        r, out = self.ci_dirs(("package.json",), ciNodeDirs=["app", "web"])
        self.assertTrue(out.startswith("node=false\n"), out)
        r, out = self.ci_dirs(("package.json",), ciNodeDirs=[])
        self.assertTrue(out.startswith("node=false\n"), out)

    def test_ci_rust_dirs_feed_rust_cache_one_workspace_per_line(self):
        r, out = self.ci_dirs(("src-tauri/Cargo.toml", "tools/Cargo.toml", "docs/x"),
                              ciRustDirs=["src-tauri", "missing", "tools"])
        self.assertEqual((r.returncode, out),
                         (0, "node=false\nrust=true\nrust_workspaces<<GW_EOF\nsrc-tauri\ntools\nGW_EOF\n"), r.stderr)
        r, out = self.ci_dirs(("Cargo.toml",), ciRustDirs=["missing"])
        self.assertIn("rust=false\n", out)

    def test_ci_dirs_fail_closed_on_a_bad_value(self):
        cases = ((dict(ciNodeDirs="app"), "$.ciNodeDirs: expected array"),
                 (dict(ciNodeDirs=["/abs"]), "$.ciNodeDirs[0]: '/abs' does not match"),
                 (dict(ciNodeDirs=["a/../b"]), "$.ciNodeDirs[0]: 'a/../b' does not match"),
                 (dict(ciRustDirs=["a b"]), "$.ciRustDirs[0]: 'a b' does not match"),
                 (dict(ciRustDirs=["a", "a"]), "$.ciRustDirs[1]: duplicate"),
                 (dict(ciRustDirs=[1]), "$.ciRustDirs[0]: expected string"))
        for keys, needle in cases:
            with self.subTest(keys=keys):
                r, out = self.ci_dirs(**keys)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(needle, r.stderr)
                self.assertIsNone(out)

    def test_ci_template_uses_the_dirs_outputs_and_rust_cache(self):
        text = (TEMPLATES / "github" / "check.yml").read_text()
        self.assertIn("if: needs.versions.outputs.node == 'true'", text)
        self.assertIn("uses: Swatinem/rust-cache@v2", text)
        self.assertIn("workspaces: ${{ needs.versions.outputs.rust_workspaces }}", text)
        self.assertNotIn("hashFiles('package.json')", text)

    def test_ci_template_is_valid_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML is not installed")
        text = (TEMPLATES / "github" / "check.yml").read_text().replace("{{ciPushIgnore}}", "main")
        doc = yaml.safe_load(text)
        self.assertEqual(set(doc["jobs"]), {"versions", "check"})

    def test_ci_template_does_not_apply_check_wrapper_or_setup(self):
        text = (TEMPLATES / "github" / "check.yml").read_text()
        self.assertNotIn("get checkWrapper", text)
        self.assertNotIn("get setup", text)

    def test_sample_config_is_valid(self):
        sample = json.loads((TEMPLATES / "gw.json").read_text())
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())
        self.assertEqual(config.validate(sample, schema), [])
        # ciInstall is left out on purpose: absent means "CI runs `install`", while [] would mean "CI installs nothing";
        # shellcheckVersion is the workflow repo's own pin (E27): a project's CI template does not read it
        self.assertEqual(set(sample), set(schema["properties"]) - {"ciInstall", "ciPython", "shellcheckVersion"},
                         "templates/gw.json must show every key but ciInstall, ciPython and shellcheckVersion")
        self.assertEqual(sample["version"], VERSION)
        # D59: the AGENTS.md template asks for the next-step trailer, so a new project must have it enforced
        self.assertIs(sample["commitNext"], True)

    def test_sample_check_runs_the_agent_map_script(self):
        sample = json.loads((TEMPLATES / "gw.json").read_text())
        self.assertIn("python3 .claude/gw/scripts/agent-map.py", sample["check"])
        self.assertIn("python3 .claude/gw/scripts/tests-after-main.py", sample["check"])

    def test_default_content_keeps_the_guard_scripts_as_code(self):
        content = json.loads((TEMPLATES / "gw.json").read_text())["content"]
        for path in (".claude/skills/retro/SKILL.md", "docs/plan.md", "README.md", "AGENTS.md",
                     "README.es.md", "CHANGELOG.md", "CREDITS.md"):
            self.assertTrue(any(re.search(p, path) for p in content), f"{path} should be content")
        for path in (".claude/gw/scripts/is-code.sh", ".claude/gw/scripts/config.py", ".claude/gw/schema/gw.schema.json",
                     ".claude/skills/gw-opt-tokens/scripts/measure.py", ".claude/skills/x/agents/openai.yaml",
                     "src/AGENTS.md", "src/notes.md", "README.es.md.sh"):
            self.assertFalse(any(re.search(p, path) for p in content), f"{path} must stay code (reviewed)")


class Init(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-plantillas-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def project(self, name="p"):
        (self.tmp / name).mkdir()
        return Project(self.tmp / name)

    def test_init_on_an_empty_repo_es_and_en(self):
        for lang in ("es", "en"):
            with self.subTest(lang=lang):
                p = self.project(lang)
                code, out = p.init(lang)
                self.assertEqual(code, 0, out)
                cfg = json.loads(p.read(".claude/gw.json"))
                self.assertEqual((cfg["language"], cfg["log"], cfg["check"]), (lang, LOGS[lang], ["bash check.sh"]))
                self.assertEqual(cfg["schemaVersion"], 1)  # A9: a new config is written in the current format
                for rel in RENDERED + (LOGS[lang],):
                    self.assertTrue((p.work / rel).is_file(), rel)
                    self.assertIsNone(re.search(r"(?<!\$)\{\{", p.read(rel)), rel)  # `${{ }}` is GitHub's own
                self.assertIn("`bash check.sh`", p.read("AGENTS.md"))
                self.assertIn("gw-orchestrate-dealer", p.read("AGENTS.md"))
                self.assertIn("branches-ignore: [main]", p.read(".github/workflows/check.yml"))
                self.assertFalse((p.work / ".claude/gw/gw-opt-ai.md").exists())
                self.assertFalse(list(p.work.glob("**/*.gw-new")))
                code, out = p.run("python3", str(p.work / ".claude/gw/scripts/doctor.py"))
                self.assertEqual(code, 0, out)
                self.assertNotIn("FAIL", out)
                code, out = p.init(lang)
                self.assertEqual(code, 0, out)
                self.assertIn("already exists", out)
                self.assertIn("nothing to do", out)
                code, out = p.run_apply("--check")
                self.assertEqual(code, 0, out)

    def test_init_needs_a_check_and_flags_need_init(self):
        p = self.project()
        code, out = p.run_apply("--init")
        self.assertEqual(code, 2, out)
        self.assertIn("--check-command", out)
        self.assertFalse((p.work / ".claude/gw.json").exists())
        code, out = p.run_apply("--language", "es")
        self.assertEqual(code, 2, out)
        self.assertIn("only go with --init", out)

    def test_init_flags_for_the_keys_the_project_decides(self):
        p = self.project()
        code, out = p.init("en", "--require-retro", "true", "--visible-language", "es", "--visible-language", "en",
                           "--design-reference", "WCAG 2.2")
        self.assertEqual(code, 0, out)
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual((cfg["requireRetro"], cfg["visibleLanguages"], cfg["designReferences"]),
                         (True, ["es", "en"], ["WCAG 2.2"]))
        code, out = p.run_apply("--require-retro", "false")
        self.assertEqual(code, 2, out)
        self.assertIn("only go with --init", out)

    def test_init_agent_signatures_flag(self):
        p = self.project()
        code, out = p.init("en", "--agent-signatures", "false")
        self.assertEqual(code, 0, out)
        self.assertIs(json.loads(p.read(".claude/gw.json"))["agentSignatures"], False)
        code, out = p.run_apply("--agent-signatures", "true")
        self.assertEqual(code, 2, out)
        self.assertIn("only go with --init", out)
        self.assertIn("--agent-signatures", out)
        p2 = self.project("p2")
        code, out = p2.init("en")
        self.assertEqual(code, 0, out)
        self.assertIs(json.loads(p2.read(".claude/gw.json"))["agentSignatures"], True)
        code, out = self.project("p3").init("en", "--agent-signatures", "maybe")
        self.assertEqual(code, 2, out)
        self.assertIn("invalid choice", out)

    def test_agent_signatures_has_one_default(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())
        sample = json.loads((TEMPLATES / "gw.json").read_text())
        self.assertEqual(sample["agentSignatures"], schema["properties"]["agentSignatures"]["default"])

    def test_require_retro_has_one_default(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())
        sample = json.loads((TEMPLATES / "gw.json").read_text())
        self.assertEqual(sample["requireRetro"], schema["properties"]["requireRetro"]["default"])

    def test_init_dry_run_writes_nothing(self):
        p = self.project()
        code, out = p.init("en", "--dry-run", "--protected-branch", "trunk", "--push-to-protected", "pr")
        self.assertEqual(code, 0, out)
        self.assertIn('"protectedBranch": "trunk"', out)
        self.assertIn("create  AGENTS.md", out)
        self.assertFalse((p.work / ".claude").exists())
        self.assertFalse((p.work / "AGENTS.md").exists())

    def test_optional_skill_brings_its_notes(self):
        p = self.project()
        code, out = p.init("es", "--with", "gw-opt-ai")
        self.assertEqual(code, 0, out)
        self.assertIn("# gw-opt-ai — notas del proyecto", p.read(".claude/gw/gw-opt-ai.md"))
        self.assertFalse((p.work / ".claude/gw/gw-scout-updates.md").exists())

    def test_existing_claude_md_without_marker_gets_a_proposal(self):
        p = self.project()
        mine = "# My rules\n\nBe careful.\n"
        p.write("CLAUDE.md", mine)
        code, out = p.init()
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("CLAUDE.md"), mine)
        self.assertTrue(p.read("CLAUDE.md.gw-new").startswith(MARKER))
        self.assertIn("merge this block by hand or with the agent", out)
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("pending proposal CLAUDE.md.gw-new", out)
        # Merged by hand, keeping the marker: the project's own edits stay and nothing is proposed again.
        p.write("CLAUDE.md", p.read("CLAUDE.md.gw-new") + "\n- Be careful.\n")
        (p.work / "CLAUDE.md.gw-new").unlink()
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertIn("- Be careful.", p.read("CLAUDE.md"))
        self.assertEqual(p.run_apply("--check")[0], 0)

    def test_older_agents_md_gets_a_proposal_not_an_overwrite(self):
        p = self.project()
        self.assertEqual(p.init()[0], 0)
        older = p.read("AGENTS.md").replace(MARKER, "<!-- galivelop-workflow v0.0.1 -->") + "\n- Our rule.\n"
        p.write("AGENTS.md", older)
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("AGENTS.md"), older)
        self.assertIn("propose AGENTS.md.gw-new", out)

    def test_filled_in_files_are_never_overwritten(self):
        p = self.project()
        self.assertEqual(p.init("es")[0], 0)
        for rel in ("docs/handoff.md", "REVIEW.md", "GLOSSARY.md", ".claude/gw/gw-opt-tokens.md"):
            with self.subTest(rel=rel):
                edited = p.read(rel).replace(MARKER, "<!-- galivelop-workflow v0.0.1 -->") + "\nfilled in\n"
                p.write(rel, edited)
                code, out = p.run_apply("--update")
                self.assertEqual(code, 0, out)
                self.assertEqual(p.read(rel), edited)
                self.assertFalse((p.work / (rel + ".gw-new")).exists())
                self.assertIn(f"template update: {rel}", out)
                self.assertEqual(p.run_apply("--check")[0], 0)  # a template note is not drift
        p.write("docs/handoff.md", "# Bitácora propia\n\nSiguiente paso: seguir.\n")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("docs/handoff.md"), "# Bitácora propia\n\nSiguiente paso: seguir.\n")

    def test_existing_review_md_gets_the_template_diff_printed_not_written(self):
        p = self.project()
        p.write("REVIEW.md", "# Our review rules\n\n- Keep it short.\n")
        code, out = p.init("en")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("REVIEW.md"), "# Our review rules\n\n- Keep it short.\n")
        self.assertFalse((p.work / "REVIEW.md.gw-new").exists())
        self.assertIn("REVIEW.md exists and is never written; what differs from the", out)
        self.assertIn("+++ REVIEW.md (template)", out)
        self.assertIn("-- Keep it short.", out)
        self.assertEqual(p.run_apply("--check")[0], 0)  # a printed diff is not drift
        p.write("REVIEW.md", MARKER + "\n# Our review rules, merged\n")  # marked at this version: settled
        code, out = p.run_apply()
        self.assertNotIn("REVIEW.md exists", out)

    def test_workflow_repo_skips_its_root_templates(self):
        r = subprocess.run(["python3", str(APPLY_SCRIPT), str(ROOT), "--dry-run"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name in ("AGENTS.md", "CLAUDE.md", "REVIEW.md", "GLOSSARY.md", "check.yml", "docs/handoff.md"):
            self.assertNotIn(name, r.stdout)


if __name__ == "__main__":
    unittest.main()
