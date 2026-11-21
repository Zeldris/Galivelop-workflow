"""E5 (trozo 2, Q-32): the sample project in tests/fixtures/front-sample runs the templates in templates/front with
node and Playwright, on Linux only. The npm packages are installed OUTSIDE the tree (`<git dir>/gw/front-node/`, never
a node_modules inside the repository) and linked into a temporary copy of the templates and the sample that the specs
run from. A green case per helper passes; a red case per helper fails for its reason (the
specs assert the message); Stylelint rejects a literal color. Without node, npm, a Chromium or on macOS the class is
skipped with the reason. Slow (npm ci, a browser): the cases share one setUpClass."""
import fcntl
import json
import os
import signal
import platform
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


def node_cache():
    """The folder with the installed packages: inside the git directory (never in the tree), else in the temp folder."""
    done = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], capture_output=True, text=True)
    base = Path(done.stdout.strip()) / "gw" if done.returncode == 0 else Path(tempfile.gettempdir())
    return base / "front-node"


def browsers_path():
    return Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or Path.home() / ".cache" / "ms-playwright")


def missing_browser(modules):
    """The reason the Chromium that the pinned Playwright asks for is not installed, else None."""
    data = json.loads((modules / "playwright-core" / "browsers.json").read_text(encoding="utf-8"))
    path = browsers_path()
    for entry in data["browsers"]:
        if entry["name"] in ("chromium", "chromium-headless-shell"):
            folder = f"{entry['name'].replace('-', '_')}-{entry['revision']}"
            if not (path / folder).is_dir():
                return (f"no {folder} in {path}: the Playwright pinned in templates/front needs it "
                        "(run `npx playwright install chromium` there)")
    return None


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
        cache = node_cache()
        cache.mkdir(parents=True, exist_ok=True)
        with open(str(cache / ".lock"), "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)  # one npm ci at a time, and the others wait for it
            wanted = (TEMPLATE / "package-lock.json").read_bytes() + (TEMPLATE / "package.json").read_bytes()
            stamp = cache / "installed-from"
            if not (stamp.is_file() and stamp.read_bytes() == wanted and (cache / "node_modules" / ".bin").is_dir()):
                shutil.copy(str(TEMPLATE / "package.json"), str(cache / "package.json"))
                shutil.copy(str(TEMPLATE / "package-lock.json"), str(cache / "package-lock.json"))
                shutil.rmtree(str(cache / "node_modules"), True)
                done = run(["npm", "ci", "--no-audit", "--no-fund"], cache)
                if done.returncode != 0:
                    raise RuntimeError(f"npm ci failed in {cache}:\n{done.stdout}\n{done.stderr}")
                stamp.write_bytes(wanted)
        cls.modules = cache / "node_modules"
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
        with socket.socket() as sock:  # a free port, so two runs in parallel do not clash
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
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


if __name__ == "__main__":
    unittest.main()
