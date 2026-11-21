"""E5 (trozo 2, Q-32): the sample project in tests/fixtures/front-sample runs the templates in templates/front with
node and Playwright, on Linux only. The npm packages are installed OUTSIDE the tree (`<git dir>/gw/front-node/`, never
a node_modules inside the repository) and linked into a temporary copy of the templates and the sample that the specs
run from. A green case per helper passes; a red case per helper fails for its reason (the
specs assert the message); Stylelint rejects a literal color. The packages are the ones `front.py install` leaves
in its cache (the one the CI fills), and a smoke test runs the real `front.py run fast` on a repo made of the sample
(finding 8 of the chunk 3 review: front.py's own run is otherwise only tested with fakes). Without node, npm, a
Chromium or on macOS the class is skipped with the reason. Slow (npm ci, a browser): the cases share one setUpClass."""
import importlib.util
import json
import os
import signal
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import waits
from test_hooks import BASE_CONFIG, ROOT

TEMPLATE = ROOT / "templates" / "front"
SAMPLE = ROOT / "tests" / "fixtures" / "front-sample"
GENERATED = ("_tokens.scss", "playwright.projects.json", "stylelint.tokens.json", "tokens.css")


FRONT_PY = ROOT / "scripts" / "front.py"
_spec = importlib.util.spec_from_file_location("gw_front_for_sample", str(FRONT_PY))
front = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(front)


def missing_browser(modules):
    """The reason the Chromium that the pinned Playwright asks for is not installed (front.py's own reading), else None."""
    missing = front.missing_browsers(modules, ["chromium"])
    if missing:
        return (f"no Chromium build for the Playwright pinned in templates/front in {front.browsers_path(modules)} "
                f"(run: python3 {FRONT_PY} install --package-dir templates/front --browsers chromium)")
    return None


def free_port():
    with socket.socket() as sock:  # a free port, so two runs in parallel do not clash
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def skip_reason():
    if platform.system() != "Linux":
        return "the front sample runs only on Linux (E-9: render and browsers differ elsewhere)"
    if not (shutil.which("node") and shutil.which("npm")):
        return "node and npm are not installed (install node 22+ to run the front sample)"
    return None


def run(cmd, cwd, limit=900, env=None):
    """Run in its own session so that, when the time is up, the whole group dies (Playwright starts a web server)."""
    env = {**{k: v for k, v in os.environ.items() if k != "CI"}, **(env or {})}
    proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
                            start_new_session=True)
    try:
        out, err = proc.communicate(timeout=waits.timeout(limit))
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


class FrontSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reason = skip_reason()
        if reason:
            raise unittest.SkipTest(reason)
        # front.py's install: its cache (<git common dir>/gw/front-node/<lock hash>/), its lock and its stamp
        done = run([sys.executable, "-B", str(FRONT_PY), "--root", str(ROOT), "install", "--package-dir",
                    "templates/front"], ROOT)
        if done.returncode != 0:
            raise RuntimeError(f"front.py install failed:\n{done.stdout}\n{done.stderr}")
        cls.cache = front.node_cache(ROOT, TEMPLATE)
        cls.modules = cls.cache / "node_modules"
        cls.bin = cls.modules / ".bin"

    def setUp(self):
        """A temporary copy of the tree the specs import from (tests/fixtures/front-sample -> ../../../templates/front),
        with `node_modules` linked to the installed packages in the copies only."""
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-front-sample-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.template = self.tmp / "templates" / "front"
        self.sample = self.tmp / "tests" / "fixtures" / "front-sample"
        for src, dest in ((TEMPLATE, self.template), (SAMPLE, self.sample)):
            shutil.copytree(str(src), str(dest), ignore=shutil.ignore_patterns("node_modules", "test-results"))
            os.symlink(str(self.modules), str(dest / "node_modules"))

    def test_generated_files_are_up_to_date(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-front-gen-")).resolve()
        self.addCleanup(shutil.rmtree, str(tmp), True)
        subprocess.run(["git", "init", "-q", str(tmp)], check=True)
        (tmp / ".claude").mkdir()
        (tmp / "front").mkdir()
        cfg = dict(BASE_CONFIG)
        cfg["front"] = {"tokens": "front/tokens.json", "out": "front/generated", "mainBreakpoints": ["mobile", "desktop"]}
        (tmp / ".claude" / "gw.json").write_text(json.dumps(cfg, indent=2) + "\n")
        shutil.copy(str(SAMPLE / "front" / "tokens.json"), str(tmp / "front" / "tokens.json"))
        done = run([sys.executable, "-B", str(ROOT / "scripts" / "front.py"), "--root", str(tmp), "generate"], tmp)
        self.assertEqual(done.returncode, 0, done.stderr)
        for name in GENERATED:
            self.assertEqual((tmp / "front" / "generated" / name).read_bytes(),
                             (SAMPLE / "front" / "generated" / name).read_bytes(),
                             f"{name} is stale: regenerate the sample (front.py generate on a copy with the "
                             "config of this test) and commit it")

    def test_playwright_specs_pass_in_chromium(self):
        reason = missing_browser(self.modules)
        if reason:
            self.skipTest(reason)
        port = free_port()
        done = run([str(self.bin / "playwright"), "test", "--trace", "off", "--forbid-only", "--project", "chromium-*",
                    "--reporter", "line"], self.sample, env={"GW_SAMPLE_PORT": str(port)})
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertRegex(done.stdout, r"\d+ passed")
        self.assertNotRegex(done.stdout, r"\d+ (skipped|failed|flaky)")

    def test_stylelint_accepts_tokens_and_ignores_what_is_generated(self):
        done = run([str(self.bin / "stylelint"), "site/**/*.{css,scss}", "front/**/*.css"], self.sample)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_the_generated_css_passes_stylelint_on_its_own(self):
        """The generated files are written to pass the standard config (short hex), ignored or not."""
        (self.sample / ".stylelintrc.json").write_text(json.dumps(
            {"extends": ["stylelint-config-standard-scss"]}))
        done = run([str(self.bin / "stylelint"), "front/generated/*.{css,scss}"], self.sample)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_stylelint_rejects_a_literal_color(self):
        done = run([str(self.bin / "stylelint"), "stylelint-red/*.scss"], self.sample)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn('Expected variable or keyword for "#fff" of "color"', done.stdout + done.stderr)

    def test_typescript_of_the_template_compiles(self):
        done = run([str(self.bin / "tsc"), "--noEmit"], self.template)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


    # -- finding 8: the real `front.py run fast` ----------------------------------------------------------------------
    def smoke_repo(self):
        """A git repo with front.dir = the sample and the template copied inside it, as a project does (front.py links
        node_modules into front.dir only, so the imports of the template must resolve from there), the template's
        package files (the same lock hash: its cache is linked to the one setUpClass filled) and front.tokens set."""
        repo = Path(tempfile.mkdtemp(prefix="gw-front-smoke-")).resolve()
        self.addCleanup(shutil.rmtree, str(repo), True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        sample = repo / "tests" / "fixtures" / "front-sample"
        shutil.copytree(str(SAMPLE), str(sample), ignore=shutil.ignore_patterns("node_modules", "test-results"))
        shutil.copytree(str(TEMPLATE), str(sample / "gw-template"),
                        ignore=shutil.ignore_patterns("node_modules", "test-results"))
        for ts in sample.rglob("*.ts"):
            if "gw-template" in ts.parts:
                continue
            to = os.path.relpath(str(sample / "gw-template"), str(ts.parent))
            to = to if to.startswith(".") else "./" + to
            ts.write_text(re.sub(r"(\.\./)+templates/front", to, ts.read_text(encoding="utf-8")), encoding="utf-8")
        for name in ("package.json", "package-lock.json"):
            shutil.copy(str(TEMPLATE / name), str(sample / name))
        rel = "tests/fixtures/front-sample"
        cfg = dict(BASE_CONFIG)
        cfg["front"] = {"tokens": f"{rel}/front/tokens.json", "out": f"{rel}/front/generated", "dir": rel,
                        "mainBreakpoints": ["mobile", "desktop"], "stylelintFiles": [f"{rel}/site/**/*.{{css,scss}}"]}
        (repo / ".claude").mkdir()
        (repo / ".claude" / "gw.json").write_text(json.dumps(cfg, indent=2) + "\n")
        cache = front.node_cache(repo, sample)
        self.assertEqual(cache.name, self.cache.name)
        cache.parent.mkdir(parents=True)
        os.symlink(str(self.cache), str(cache))
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        return repo, sample

    def run_fast(self, repo):
        return run([sys.executable, "-B", str(FRONT_PY), "--root", str(repo), "run", "fast"], repo,
                   env={"GW_SAMPLE_PORT": str(free_port())})

    def test_front_py_run_fast_is_green_on_the_sample(self):
        reason = missing_browser(self.modules)
        if reason:
            self.skipTest(reason)
        repo, _ = self.smoke_repo()
        done = self.run_fast(repo)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertRegex(done.stdout, r"\d+ passed")

    def test_front_py_run_fast_rejects_a_literal_color_in_the_app_css(self):
        repo, sample = self.smoke_repo()
        (sample / "site" / "broken.css").write_text("a {\n  color: #f00;\n}\n")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        done = self.run_fast(repo)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn('Expected variable or keyword for "#f00" of "color"', done.stdout + done.stderr)

if __name__ == "__main__":
    unittest.main()
