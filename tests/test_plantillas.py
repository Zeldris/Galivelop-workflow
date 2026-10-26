"""The templates (templates/es, templates/en, templates/gw.json, templates/github) and how scripts/aplicar.py writes
them: `--init` on an empty repo yields a project doctor.py accepts, a second run changes nothing, an existing
AGENTS.md/CLAUDE.md is never overwritten, the files the project fills in (log, REVIEW.md, GLOSSARY.md, notes) are
never written again, and the Spanish and English templates stay paired. HOME is a temp folder and git runs isolated
as in test_ganchos.
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

from test_ganchos import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

APLICAR = ROOT / "scripts" / "aplicar.py"
TEMPLATES = ROOT / "templates"
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
MARKER = f"<!-- galivelop-workflow v{VERSION} -->"
LOGS = {"es": "docs/traspaso.md", "en": "docs/handoff.md"}
RENDERED = ("AGENTS.md", "CLAUDE.md", "REVIEW.md", "GLOSSARY.md", ".github/workflows/comprobar.yml",
            ".claude/gw/opt-tokens.md", ".claude/gw.json")


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

    def aplicar(self, *args):
        return self.run("python3", str(APLICAR), str(self.work), *args)

    def init(self, lang="en", *extra):
        return self.aplicar("--init", "--language", lang, "--check-command", "bash check.sh", *extra)

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

    def test_every_template_starts_with_the_version_marker(self):
        for lang in ("es", "en"):
            for name in lang_files(lang):
                with self.subTest(file=f"{lang}/{name}"):
                    first = (TEMPLATES / lang / name).read_text(encoding="utf-8").splitlines()[0]
                    self.assertEqual(first, MARKER)
        first = (TEMPLATES / "github" / "comprobar.yml").read_text().splitlines()[0]
        self.assertEqual(first, f"# galivelop-workflow v{VERSION}")

    def test_placeholders_are_only_config_keys_project_and_version(self):
        allowed = {"log", "protectedBranch", "check", "install", "reviewMark", "language", "version", "project"}
        for path in sorted(TEMPLATES.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".yml"):
                with self.subTest(file=str(path.relative_to(ROOT))):
                    found = set(re.findall(r"\{\{(\w+)\}\}", path.read_text(encoding="utf-8")))
                    self.assertLessEqual(found, allowed)

    def test_agents_authorises_subagents_and_size_limits(self):
        for lang in ("es", "en"):
            agents = (TEMPLATES / lang / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("orchestrate-dealer", agents)
            self.assertIn("Siguiente:" if lang == "es" else "Next:", agents)
            self.assertIn("core.hooksPath", agents)
            self.assertIn("@AGENTS.md", (TEMPLATES / lang / "CLAUDE.md").read_text(encoding="utf-8"))
            for name in ("AGENTS.md", "CLAUDE.md"):
                with self.subTest(file=f"{lang}/{name}"):
                    lines = len((TEMPLATES / lang / name).read_text(encoding="utf-8").splitlines())
                    self.assertLessEqual(lines, 200)

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
        text = (TEMPLATES / "github" / "comprobar.yml").read_text()
        install = text.index("- name: Install")
        for action, files in (("setup-node", "'package.json'"), ("setup-python", "'pyproject.toml'"),
                              ("setup-java", "'pom.xml'")):
            with self.subTest(action=action):
                at = text.index(f"actions/{action}@")
                self.assertLess(at, install, f"{action} must run before Install")
                self.assertIn(f"if: hashFiles({files}", text[at:install])

    def ci_install(self, **keys):
        """Run the CI template's Install step in a temp project whose gw.json has `keys`; return the commands run."""
        text = (TEMPLATES / "github" / "comprobar.yml").read_text()
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

    def test_ci_template_does_not_apply_check_wrapper_or_setup(self):
        text = (TEMPLATES / "github" / "comprobar.yml").read_text()
        self.assertNotIn("get checkWrapper", text)
        self.assertNotIn("get setup", text)

    def test_sample_config_is_valid(self):
        sample = json.loads((TEMPLATES / "gw.json").read_text())
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())
        self.assertEqual(config.validate(sample, schema), [])
        # ciInstall is left out on purpose: absent means "CI runs `install`", while [] would mean "CI installs nothing"
        self.assertEqual(set(sample), set(schema["properties"]) - {"ciInstall"},
                         "templates/gw.json must show every key but ciInstall")
        self.assertEqual(sample["version"], VERSION)

    def test_sample_check_runs_the_agent_map_script(self):
        sample = json.loads((TEMPLATES / "gw.json").read_text())
        self.assertIn("python3 .claude/gw/scripts/mapa-agente.py", sample["check"])

    def test_default_content_keeps_the_guard_scripts_as_code(self):
        content = json.loads((TEMPLATES / "gw.json").read_text())["content"]
        for path in (".claude/skills/retro/SKILL.md", "docs/plan.md", "README.md", "AGENTS.md",
                     "README.es.md", "CHANGELOG.md", "CREDITS.md"):
            self.assertTrue(any(re.search(p, path) for p in content), f"{path} should be content")
        for path in (".claude/gw/scripts/es-codigo.sh", ".claude/gw/scripts/config.py", ".claude/gw/schema/gw.schema.json",
                     ".claude/skills/opt-tokens/scripts/medir.py", ".claude/skills/x/agents/openai.yaml",
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
                for rel in RENDERED + (LOGS[lang],):
                    self.assertTrue((p.work / rel).is_file(), rel)
                    self.assertNotIn("{{", p.read(rel), rel)
                self.assertIn("`bash check.sh`", p.read("AGENTS.md"))
                self.assertIn("orchestrate-dealer", p.read("AGENTS.md"))
                self.assertIn("branches-ignore: [main]", p.read(".github/workflows/comprobar.yml"))
                self.assertFalse((p.work / ".claude/gw/opt-ai.md").exists())
                self.assertFalse(list(p.work.glob("**/*.gw-nuevo")))
                code, out = p.run("python3", str(p.work / ".claude/gw/scripts/doctor.py"))
                self.assertEqual(code, 0, out)
                self.assertNotIn("FAIL", out)
                code, out = p.init(lang)
                self.assertEqual(code, 0, out)
                self.assertIn("already exists", out)
                self.assertIn("nothing to do", out)
                code, out = p.aplicar("--check")
                self.assertEqual(code, 0, out)

    def test_init_needs_a_check_and_flags_need_init(self):
        p = self.project()
        code, out = p.aplicar("--init")
        self.assertEqual(code, 2, out)
        self.assertIn("--check-command", out)
        self.assertFalse((p.work / ".claude/gw.json").exists())
        code, out = p.aplicar("--language", "es")
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
        code, out = p.aplicar("--require-retro", "false")
        self.assertEqual(code, 2, out)
        self.assertIn("only go with --init", out)

    def test_init_agent_signatures_flag(self):
        p = self.project()
        code, out = p.init("en", "--agent-signatures", "false")
        self.assertEqual(code, 0, out)
        self.assertIs(json.loads(p.read(".claude/gw.json"))["agentSignatures"], False)
        code, out = p.aplicar("--agent-signatures", "true")
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
        code, out = p.init("es", "--with", "opt-ai")
        self.assertEqual(code, 0, out)
        self.assertIn("# opt-ai — notas del proyecto", p.read(".claude/gw/opt-ai.md"))
        self.assertFalse((p.work / ".claude/gw/scout-updates.md").exists())

    def test_existing_claude_md_without_marker_gets_a_proposal(self):
        p = self.project()
        mine = "# My rules\n\nBe careful.\n"
        p.write("CLAUDE.md", mine)
        code, out = p.init()
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("CLAUDE.md"), mine)
        self.assertTrue(p.read("CLAUDE.md.gw-nuevo").startswith(MARKER))
        self.assertIn("merge this block by hand or with the agent", out)
        code, out = p.aplicar("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("pending proposal CLAUDE.md.gw-nuevo", out)
        # Merged by hand, keeping the marker: the project's own edits stay and nothing is proposed again.
        p.write("CLAUDE.md", p.read("CLAUDE.md.gw-nuevo") + "\n- Be careful.\n")
        (p.work / "CLAUDE.md.gw-nuevo").unlink()
        code, out = p.aplicar("--update")
        self.assertEqual(code, 0, out)
        self.assertIn("- Be careful.", p.read("CLAUDE.md"))
        self.assertEqual(p.aplicar("--check")[0], 0)

    def test_older_agents_md_gets_a_proposal_not_an_overwrite(self):
        p = self.project()
        self.assertEqual(p.init()[0], 0)
        older = p.read("AGENTS.md").replace(MARKER, "<!-- galivelop-workflow v0.0.1 -->") + "\n- Our rule.\n"
        p.write("AGENTS.md", older)
        code, out = p.aplicar("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("AGENTS.md"), older)
        self.assertIn("propose AGENTS.md.gw-nuevo", out)

    def test_filled_in_files_are_never_overwritten(self):
        p = self.project()
        self.assertEqual(p.init("es")[0], 0)
        for rel in ("docs/traspaso.md", "REVIEW.md", "GLOSSARY.md", ".claude/gw/opt-tokens.md"):
            with self.subTest(rel=rel):
                edited = p.read(rel).replace(MARKER, "<!-- galivelop-workflow v0.0.1 -->") + "\nfilled in\n"
                p.write(rel, edited)
                code, out = p.aplicar("--update")
                self.assertEqual(code, 0, out)
                self.assertEqual(p.read(rel), edited)
                self.assertFalse((p.work / (rel + ".gw-nuevo")).exists())
                self.assertIn(f"template update: {rel}", out)
                self.assertEqual(p.aplicar("--check")[0], 0)  # a template note is not drift
        p.write("docs/traspaso.md", "# Bitácora propia\n\nSiguiente paso: seguir.\n")
        code, out = p.aplicar("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("docs/traspaso.md"), "# Bitácora propia\n\nSiguiente paso: seguir.\n")

    def test_existing_review_md_gets_the_template_diff_printed_not_written(self):
        p = self.project()
        p.write("REVIEW.md", "# Our review rules\n\n- Keep it short.\n")
        code, out = p.init("en")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("REVIEW.md"), "# Our review rules\n\n- Keep it short.\n")
        self.assertFalse((p.work / "REVIEW.md.gw-nuevo").exists())
        self.assertIn("REVIEW.md exists and is never written; what differs from the", out)
        self.assertIn("+++ REVIEW.md (template)", out)
        self.assertIn("-- Keep it short.", out)
        self.assertEqual(p.aplicar("--check")[0], 0)  # a printed diff is not drift
        p.write("REVIEW.md", MARKER + "\n# Our review rules, merged\n")  # marked at this version: settled
        code, out = p.aplicar()
        self.assertNotIn("REVIEW.md exists", out)

    def test_workflow_repo_skips_its_root_templates(self):
        r = subprocess.run(["python3", str(APLICAR), str(ROOT), "--dry-run"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name in ("AGENTS.md", "CLAUDE.md", "REVIEW.md", "GLOSSARY.md", "comprobar.yml", "docs/traspaso.md"):
            self.assertNotIn(name, r.stdout)


if __name__ == "__main__":
    unittest.main()
