"""E5 (trozo 2, Q-32): the sample project in tests/fixtures/front-sample runs the templates in templates/front with
node and Playwright, on Linux only. A green case per helper passes; a red case per helper fails for its reason (the
specs assert the message); Stylelint rejects a literal color. Without node, npm, a Chromium or on macOS the class is
skipped with the reason. Slow (npm ci, a browser): the cases share one setUpClass."""
import json
import os
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
BIN = TEMPLATE / "node_modules" / ".bin"
GENERATED = ("_tokens.scss", "playwright.projects.json", "stylelint.tokens.json", "tokens.css")


def skip_reason():
    if platform.system() != "Linux":
        return "the front sample runs only on Linux (E-9: render and browsers differ elsewhere)"
    if not (shutil.which("node") and shutil.which("npm")):
        return "node and npm are not installed (install node 22+ to run the front sample)"
    browsers = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or Path.home() / ".cache" / "ms-playwright")
    if not browsers.is_dir() or not any(p.name.startswith("chromium") for p in browsers.iterdir()):
        return f"no Chromium in {browsers} (run `npx playwright install chromium` in templates/front)"
    return None


def run(cmd, cwd, limit=900, env=None):
    env = {**{k: v for k, v in os.environ.items() if k != "CI"}, **(env or {})}
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env, timeout=waits.timeout(limit))


class FrontSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reason = skip_reason()
        if reason:
            raise unittest.SkipTest(reason)
        installed = TEMPLATE / "node_modules" / ".package-lock.json"
        if installed.is_file() and installed.stat().st_mtime >= (TEMPLATE / "package-lock.json").stat().st_mtime:
            return  # already installed from this lock file (npm ci wipes node_modules and fetches it all again)
        done = run(["npm", "ci", "--no-audit", "--no-fund"], TEMPLATE)
        if done.returncode != 0:
            raise RuntimeError(f"npm ci failed in templates/front:\n{done.stdout}\n{done.stderr}")

    def test_generated_files_are_up_to_date(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-front-sample-")).resolve()
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
        with socket.socket() as sock:  # a free port, so two runs in parallel do not clash
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        done = run([str(BIN / "playwright"), "test", "--trace", "off", "--project", "chromium-*", "--reporter", "line"],
                   SAMPLE, env={"GW_SAMPLE_PORT": str(port)})
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertRegex(done.stdout, r"\d+ passed")

    def test_stylelint_accepts_tokens(self):
        done = run([str(BIN / "stylelint"), "site/**/*.{css,scss}"], SAMPLE)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_stylelint_rejects_a_literal_color(self):
        done = run([str(BIN / "stylelint"), "stylelint-red/*.scss"], SAMPLE)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn('Expected variable or keyword for "#fff" of "color"', done.stdout + done.stderr)

    def test_typescript_of_the_template_compiles(self):
        done = run([str(BIN / "tsc"), "--noEmit"], TEMPLATE)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
