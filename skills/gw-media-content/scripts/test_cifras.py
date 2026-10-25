"""Tests of cifras.py: each case builds a git repo in a tempdir; every failure case asserts its message.
Run: python3 -m unittest discover -s skills/gw-media-content/scripts"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CIFRAS = AQUI / "cifras.py"
ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
CONFIG = {"version": "0.4.0", "language": "es", "log": "docs/traspaso.md", "check": ["true"], "protectedBranch": "main",
          "pushToProtected": "direct", "reviewMark": "docs/registros/revisado.txt", "content": ["^docs/"]}
CHANGELOG = "# Changelog\n\n## [1.1.0] - 2026-10-02\n\n### Added\n\n- a\n\n### Fixed\n\n- b\n\n## [1.0.0]\n\n### Old\n"


def git(cwd, *args, date=None):
    import os
    env = dict(os.environ, **ENV)
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env=env)


def run(cwd, *args):
    proc = subprocess.run([sys.executable, str(CIFRAS), *args], cwd=str(cwd), capture_output=True, text=True)
    return proc


class Cifras(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "proyecto"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        self.commit("a.txt", "uno\n", "primero", "2026-09-01T10:00:00")

    def commit(self, rel, text, msg, date="2026-10-01T10:00:00"):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", msg, date=date)

    def cifras(self, *args):
        proc = run(self.repo, *args)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_outside_a_repo_fails_closed_with_the_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(tmp)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not inside a git repository", proc.stderr)
        self.assertIn("cd <project>", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_repo_without_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q")
            proc = run(tmp)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("has no commits yet", proc.stderr)

    def test_unknown_ref(self):
        proc = run(self.repo, "--desde", "no-existe")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--desde no-existe: git does not know that ref", proc.stderr)
        self.assertIn("git tag --list", proc.stderr)

    def test_unknown_version_file(self):
        proc = run(self.repo, "--version-file", "nada.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--version-file nada.json: no such file", proc.stderr)

    def test_version_file_without_a_version(self):
        self.commit("pkg.json", '{"name": "x"}', "pkg")
        proc = run(self.repo, "--version-file", "pkg.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no version found in it", proc.stderr)

    def test_bad_option_exits_2(self):
        self.assertEqual(run(self.repo, "--nada").returncode, 2)

    def test_without_tags_counts_the_whole_history(self):
        self.commit("b.txt", "dos\n", "segundo", "2026-10-03T10:00:00")
        out = self.cifras()
        self.assertIn("first commit", out["desde"])
        c = out["cifras"]
        self.assertEqual(c["commits_desde"]["valor"], 2)
        self.assertEqual(c["commits_desde"]["fuente"], "git rev-list --count HEAD")
        self.assertIsNone(c["ultima_etiqueta"]["valor"])
        self.assertIn("no tags", c["ultima_etiqueta"]["nota"])
        self.assertEqual(c["rango_fechas"]["valor"], {"primero": "2026-09-01", "ultimo": "2026-10-03"})
        self.assertEqual(c["archivos_cambiados"]["valor"], {"archivos": 2})
        self.assertEqual([s.split(" ", 1)[1] for s in c["commits_asuntos"]["valor"]], ["segundo", "primero"])

    def test_from_the_last_tag(self):
        git(self.repo, "tag", "v1.0.0")
        self.commit("b.txt", "dos\n", "segundo", "2026-10-03T10:00:00")
        self.commit("b.txt", "dos\ntres\n", "cambia b", "2026-10-05T10:00:00")  # same file again: still 1 file
        self.commit("c.txt", "x\n", "tercero", "2026-10-06T10:00:00")
        out = self.cifras()
        self.assertEqual(out["desde"], "last tag v1.0.0")
        c = out["cifras"]
        self.assertEqual(c["ultima_etiqueta"]["valor"], "v1.0.0")
        self.assertEqual(c["commits_desde"]["valor"], 3)
        self.assertEqual(c["commits_sin_merges"]["valor"], 3)
        self.assertEqual(c["commits_desde"]["fuente"], "git rev-list --count v1.0.0..HEAD")
        self.assertEqual(c["archivos_cambiados"]["valor"], {"archivos": 2, "lineas_anadidas": 3, "lineas_borradas": 0})
        self.assertEqual(c["archivos_cambiados"]["fuente"], "git diff --numstat v1.0.0 HEAD")
        self.assertEqual(c["rango_fechas"]["valor"], {"primero": "2026-10-03", "ultimo": "2026-10-06"})

    def test_merge_commits_are_counted_apart_and_not_listed(self):
        git(self.repo, "tag", "v1.0.0")
        git(self.repo, "checkout", "-q", "-b", "rama")
        self.commit("r.txt", "r\n", "en la rama", "2026-10-02T10:00:00")
        git(self.repo, "checkout", "-q", "-")
        self.commit("m.txt", "m\n", "en la principal", "2026-10-03T10:00:00")
        git(self.repo, "merge", "-q", "--no-ff", "-m", "Merge rama", "rama", date="2026-10-04T10:00:00")
        c = self.cifras()["cifras"]
        self.assertEqual((c["commits_desde"]["valor"], c["commits_sin_merges"]["valor"]), (3, 2))
        self.assertEqual(sorted(s.split(" ", 1)[1] for s in c["commits_asuntos"]["valor"]),
                         ["en la principal", "en la rama"])

    def test_desde_overrides_the_tag(self):
        git(self.repo, "tag", "v1.0.0")
        self.commit("b.txt", "dos\n", "segundo", "2026-10-03T10:00:00")
        git(self.repo, "tag", "v1.1.0")
        self.commit("c.txt", "x\n", "tercero", "2026-10-06T10:00:00")
        out = self.cifras("--desde", "v1.0.0")
        self.assertEqual(out["desde"], "--desde v1.0.0")
        self.assertEqual(out["cifras"]["commits_desde"]["valor"], 2)
        self.assertEqual(out["cifras"]["ultima_etiqueta"]["valor"], "v1.1.0")

    def test_zero_commits_since_the_tag(self):
        git(self.repo, "tag", "v1.0.0")
        c = self.cifras()["cifras"]
        self.assertEqual(c["commits_desde"]["valor"], 0)
        self.assertIsNone(c["rango_fechas"]["valor"])
        self.assertIn("no commits in the range", c["rango_fechas"]["nota"])
        self.assertEqual(c["archivos_cambiados"]["valor"]["archivos"], 0)

    def test_version_from_known_files_and_the_option(self):
        self.assertIsNone(self.cifras()["cifras"]["version_proyecto"]["valor"])
        self.assertIn("--version-file", self.cifras()["cifras"]["version_proyecto"]["nota"])
        self.commit("pyproject.toml", '[project]\nname = "x"\nversion = "2.3.4"\n', "py")
        v = self.cifras()["cifras"]["version_proyecto"]
        self.assertEqual((v["valor"], v["fuente"]), ("2.3.4", "read pyproject.toml"))
        self.commit(".claude-plugin/plugin.json", '{"version": "0.9.1"}', "plugin")
        self.assertEqual(self.cifras()["cifras"]["version_proyecto"]["valor"], "0.9.1")  # first in the list wins
        self.commit("VERSION", "7.0.0\n", "ver")
        self.assertEqual(self.cifras("--version-file", "VERSION")["cifras"]["version_proyecto"]["valor"], "7.0.0")

    def test_changelog_latest_section(self):
        self.assertIsNone(self.cifras()["cifras"]["changelog_ultima_seccion"]["valor"])
        self.assertIn("no CHANGELOG.md", self.cifras()["cifras"]["changelog_ultima_seccion"]["nota"])
        self.commit("CHANGELOG.md", CHANGELOG, "cl")
        v = self.cifras()["cifras"]["changelog_ultima_seccion"]["valor"]
        self.assertEqual(v, {"seccion": "[1.1.0] - 2026-10-02", "encabezados": ["Added", "Fixed"]})
        self.commit("CHANGELOG.md", "# Changelog\n\ntexto\n", "cl2")
        self.assertIn("no '## ' section", self.cifras()["cifras"]["changelog_ultima_seccion"]["nota"])

    def test_counts_test_files(self):
        self.commit("tests/test_a.py", "", "t1")
        self.commit("src/b_test.go", "", "t2")
        self.commit("web/c.spec.ts", "", "t3")
        self.commit("src/contest.py", "", "no es un test")
        self.assertEqual(self.cifras()["cifras"]["archivos_de_test"]["valor"], 3)

    def test_log_path_through_the_config_reader_when_the_project_has_one(self):
        self.assertNotIn("bitacora", self.cifras()["cifras"])
        flujo = AQUI.parent.parent.parent  # this repo; the project gets the installed layout of aplicar.py
        (self.repo / ".claude/gw/scripts").mkdir(parents=True)
        (self.repo / ".claude/gw/schema").mkdir()
        (self.repo / ".claude/gw/scripts/config.py").write_text((flujo / "scripts/config.py").read_text(encoding="utf-8"))
        (self.repo / ".claude/gw/schema/gw.schema.json").write_text(
            (flujo / "schema/gw.schema.json").read_text(encoding="utf-8"))
        self.commit(".claude/gw.json", json.dumps(CONFIG), "cfg")
        b = self.cifras()["cifras"]["bitacora"]
        self.assertEqual(b["valor"], "docs/traspaso.md")
        self.assertEqual(b["fuente"], "python3 .claude/gw/scripts/config.py get log")

    def test_invalid_config_is_reported_not_hidden(self):
        self.test_log_path_through_the_config_reader_when_the_project_has_one()
        self.commit(".claude/gw.json", '{"version": "0.4.0"}', "cfg roto")
        b = self.cifras()["cifras"]["bitacora"]
        self.assertIsNone(b["valor"])
        self.assertIn("invalid", b["nota"])

    def test_output_is_json_with_root_and_today(self):
        out = self.cifras()
        self.assertEqual(Path(out["raiz"]).resolve(), self.repo.resolve())
        self.assertRegex(out["hoy"], r"^\d{4}-\d{2}-\d{2}$")
        for name, fig in out["cifras"].items():
            self.assertIn("fuente", fig, name)
            self.assertIn("valor", fig, name)


if __name__ == "__main__":
    unittest.main()
