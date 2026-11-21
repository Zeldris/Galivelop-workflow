"""scripts/front.py (E5, trozo 1): `check` validates a DTCG-subset tokens JSON and `generate` writes tokens.css,
_tokens.scss, stylelint.tokens.json and playwright.projects.json. Every failing case checks the reason in the message,
not only the exit code."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

SCRIPT = ROOT / "scripts" / "front.py"

SAMPLE = {
    "color": {
        "$type": "color",
        "brand": {"$value": "#0044cc"},
        "link": {"$value": "{color.brand}"},
        "Ñandú verde": {"$value": "#00aa44"},
    },
    "space": {"$type": "dimension", "sm": {"$value": "8px"}, "md": {"$value": "16px"}},
    "font": {
        "family": {"base": {"$type": "fontFamily", "$value": ["Inter", "Open Sans", "sans-serif"]}},
        "weight": {"bold": {"$type": "fontWeight", "$value": 700}},
    },
    "motion": {"fast": {"$type": "duration", "$value": "150ms"}},
    "ratio": {"golden": {"$type": "number", "$value": 1.618}},
    "breakpoint": {
        "$type": "dimension",
        "mobile": {"$value": "375px", "$extensions": {"gw": {"height": 667}}},
        "tablet": {"$value": "768px"},
        "desktop": {"$value": "1280px"},
    },
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-front-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()
        self.front = {"tokens": "design/tokens.json"}
        (self.tmp / "design").mkdir()

    def write_config(self, front="default"):
        cfg = dict(BASE_CONFIG)
        block = self.front if front == "default" else front
        if block is not None:
            cfg["front"] = block
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(cfg, indent=2) + "\n")

    def tokens(self, data):
        text = data if isinstance(data, str) else json.dumps(data)
        (self.tmp / "design" / "tokens.json").write_text(text, encoding="utf-8")

    def run_cli(self, *args, cwd=None):
        self.write_config()
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        return subprocess.run(["python3", "-B", str(SCRIPT), "--root", str(self.tmp), *args], cwd=cwd or str(self.tmp),
                              capture_output=True, text=True, env=env)

    def out(self, name):
        return (self.tmp / "front" / "generated" / name).read_text(encoding="utf-8")

    def generate(self, data=None):
        self.tokens(SAMPLE if data is None else data)
        r = self.run_cli("generate")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def fails(self, data, reason, command="check", code=1):
        self.tokens(data)
        r = self.run_cli(command)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        self.assertIn(reason, r.stderr)
        self.assertIn("front.py", r.stderr)  # the message names the command that fixes it
        return r


class Check(Base):
    def test_valid_sample_passes(self):
        self.tokens(SAMPLE)
        r = self.run_cli("check")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_broken_alias_fails_with_the_alias(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["link"]["$value"] = "{color.nope}"
        self.fails(bad, "alias {color.nope} does not resolve")

    def test_alias_to_a_group_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["link"]["$value"] = "{space}"
        self.fails(bad, "alias {space} points to a group")

    def test_cycle_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["a"] = {"$value": "{color.b}"}
        bad["color"]["b"] = {"$value": "{color.a}"}
        self.fails(bad, "alias cycle")

    def test_self_alias_is_a_cycle(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["a"] = {"$value": "{color.a}"}
        self.fails(bad, "alias cycle")

    def test_type_not_allowed_fails_with_the_type(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["shadow"] = {"$type": "shadow", "$value": "0 0 1px #000"}
        self.fails(bad, "$type 'shadow' is not allowed")

    def test_missing_type_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["misc"] = {"x": {"$value": "1px"}}
        self.fails(bad, "misc.x has no $type")

    def test_type_is_inherited_from_a_group(self):
        # color.brand has no own $type: the group's one applies (and the sample passes)
        self.tokens(SAMPLE)
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_inherited_type_is_validated_too(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["space"]["bad"] = {"$value": "lots"}
        self.fails(bad, "space.bad: dimension value 'lots'")

    def test_leaf_without_value_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["x"] = {"$type": "color", "$description": "no value"}
        self.fails(bad, "color.x: a token needs $value")

    def test_breakpoint_without_px_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["breakpoint"]["tablet"]["$value"] = "48rem"
        self.fails(bad, "breakpoint.tablet must be a px dimension")

    def test_breakpoint_alias_to_px_is_resolved(self):
        data = json.loads(json.dumps(SAMPLE))
        data["size"] = {"wide": {"$type": "dimension", "$value": "1440px"}}
        data["breakpoint"]["wide"] = {"$value": "{size.wide}"}
        self.generate(data)
        projects = json.loads(self.out("playwright.projects.json"))
        self.assertIn({"name": "chromium-wide", "browser": "chromium", "viewport": {"width": 1440, "height": 800}},
                      projects)

    def test_bad_breakpoint_height_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["breakpoint"]["mobile"]["$extensions"]["gw"]["height"] = "tall"
        self.fails(bad, "$extensions.gw.height must be a positive integer")

    def test_missing_breakpoint_group_fails(self):
        bad = {k: v for k, v in SAMPLE.items() if k != "breakpoint"}
        self.fails(bad, "breakpoint group 'breakpoint' not found")

    def test_empty_breakpoint_group_fails(self):
        bad = dict(SAMPLE, breakpoint={"$type": "dimension"})
        self.fails(bad, "breakpoint group 'breakpoint' has no breakpoints")

    def test_custom_breakpoint_group(self):
        self.front = {"tokens": "design/tokens.json", "breakpointGroup": "bp"}
        data = dict(SAMPLE)
        data["bp"] = data.pop("breakpoint")
        self.tokens(data)
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_unknown_main_breakpoint_fails(self):
        self.front = {"tokens": "design/tokens.json", "mainBreakpoints": ["huge"]}
        self.fails(SAMPLE, "mainBreakpoints names 'huge', which is not a breakpoint")

    def test_empty_file_fails(self):
        self.fails("", "is empty")

    def test_invalid_json_fails_with_the_line(self):
        self.fails('{\n "a": ,\n}', "invalid JSON at line 2")

    def test_duplicate_key_fails(self):
        self.fails('{"a": {"$value": "1px", "$type": "dimension"}, "a": {}}', "duplicate key 'a'")

    def test_root_must_be_an_object(self):
        self.fails("[1]", "must be a JSON object")

    def test_tokens_file_missing_fails(self):
        self.write_config()
        r = self.run_cli("check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("design/tokens.json not found", r.stderr)
        self.assertIn("front.tokens", r.stderr)

    def test_tokens_path_outside_the_repo_fails(self):
        (self.tmp.parent / "outside-tokens.json").write_text("{}")
        self.addCleanup(lambda: (self.tmp.parent / "outside-tokens.json").unlink())
        self.front = {"tokens": "x/../../outside-tokens.json"}
        r = self.run_cli("check")
        self.assertEqual(r.returncode, 2)
        self.assertIn("front.tokens", r.stderr)

    def test_tokens_symlink_outside_the_repo_fails(self):
        target = self.tmp.parent / "outside-link-target.json"
        target.write_text(json.dumps(SAMPLE))
        self.addCleanup(target.unlink)
        os.symlink(str(target), str(self.tmp / "design" / "tokens.json"))
        r = self.run_cli("check")
        self.assertEqual(r.returncode, 2)
        self.assertIn("outside the repository", r.stderr)

    def test_out_path_outside_the_repo_fails(self):
        self.front = {"tokens": "design/tokens.json", "out": "../elsewhere"}
        self.tokens(SAMPLE)
        r = self.run_cli("generate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("front.out", r.stderr)
        self.assertFalse((self.tmp.parent / "elsewhere").exists())

    def test_names_that_collide_after_css_sanitizing_fail(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["Brand Alt"] = {"$value": "#111111"}
        bad["color"]["brand-alt"] = {"$value": "#222222"}
        self.fails(bad, "both become --color-brand-alt")

    def test_name_without_letters_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["日本"] = {"$value": "#111111"}
        self.fails(bad, "has no CSS-safe name")

    def test_name_with_a_dot_or_brace_fails(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["a.b"] = {"$value": "#111111"}
        self.fails(bad, "must not contain '.', '{' or '}'")

    def test_check_does_not_write(self):
        self.tokens(SAMPLE)
        self.assertEqual(self.run_cli("check").returncode, 0)
        self.assertFalse((self.tmp / "front").exists())

    def test_runs_from_another_cwd(self):
        self.tokens(SAMPLE)
        other = Path(tempfile.mkdtemp(prefix="gw-front-cwd-"))
        self.addCleanup(shutil.rmtree, other, True)
        r = self.run_cli("check", cwd=str(other))
        self.assertEqual(r.returncode, 0, r.stderr)


class NoFront(Base):
    def test_without_tokens_every_subcommand_does_nothing(self):
        for front in (None, {"tokens": None}):
            self.front = front
            for sub in ("check", "generate"):
                r = self.run_cli(sub)
                self.assertEqual(r.returncode, 0, (front, sub, r.stderr))
                self.assertNotIn("Traceback", r.stderr)
                self.assertFalse((self.tmp / "front").exists())

    def test_unknown_subcommand_is_a_usage_error(self):
        r = self.run_cli("run")
        self.assertEqual(r.returncode, 2)


class Generate(Base):
    def test_four_files_are_written(self):
        r = self.generate()
        names = sorted(p.name for p in (self.tmp / "front" / "generated").iterdir())
        self.assertEqual(names, ["_tokens.scss", "playwright.projects.json", "stylelint.tokens.json", "tokens.css"])
        for name in names:
            self.assertIn(name, r.stdout)

    def test_two_runs_give_the_same_bytes(self):
        self.generate()
        first = {p.name: p.read_bytes() for p in (self.tmp / "front" / "generated").iterdir()}
        self.generate()
        second = {p.name: p.read_bytes() for p in (self.tmp / "front" / "generated").iterdir()}
        self.assertEqual(first, second)
        for name, data in first.items():
            self.assertTrue(data.endswith(b"\n") and not data.endswith(b"\n\n"), name)
            self.assertNotIn(b"\r", data, name)

    def test_key_order_in_the_source_does_not_change_the_output(self):
        self.generate()
        first = self.out("tokens.css"), self.out("playwright.projects.json")
        reordered = {k: SAMPLE[k] for k in reversed(list(SAMPLE))}
        self.generate(reordered)
        self.assertEqual(first, (self.out("tokens.css"), self.out("playwright.projects.json")))

    def test_css_has_custom_properties_and_alias_as_var(self):
        self.generate()
        css = self.out("tokens.css")
        self.assertIn("\n:root {\n", css)
        self.assertIn("  --color-brand: #0044cc;\n", css)
        self.assertIn("  --color-link: var(--color-brand);\n", css)
        self.assertIn("  --space-sm: 8px;\n", css)
        self.assertIn('  --font-family-base: Inter, "Open Sans", sans-serif;\n', css)
        self.assertIn("  --font-weight-bold: 700;\n", css)
        self.assertIn("  --ratio-golden: 1.618;\n", css)
        self.assertIn("  --motion-fast: 150ms;\n", css)
        self.assertTrue(css.rstrip("\n").endswith("}"))

    def test_scss_has_variables_and_alias_as_variable(self):
        self.generate()
        scss = self.out("_tokens.scss")
        self.assertIn("$color-brand: #0044cc;\n", scss)
        self.assertIn("$color-link: $color-brand;\n", scss)
        self.assertIn('$font-family-base: Inter, "Open Sans", sans-serif;\n', scss)

    def test_unicode_names_become_css_safe(self):
        self.generate()
        self.assertIn("  --color-nandu-verde: #00aa44;\n", self.out("tokens.css"))
        self.assertIn("$color-nandu-verde: #00aa44;\n", self.out("_tokens.scss"))

    def test_sorted_properties(self):
        self.generate()
        names = [line.split(":")[0].strip() for line in self.out("tokens.css").splitlines() if line.startswith("  --")]
        self.assertEqual(names, sorted(names))

    def test_stylelint_fragment(self):
        self.generate()
        cfg = json.loads(self.out("stylelint.tokens.json"))
        self.assertEqual(cfg["plugins"], ["stylelint-declaration-strict-value"])
        props, opts = cfg["rules"]["scale-unlimited/declaration-strict-value"]
        for prop in ("color", "background-color", "border-color", "font-size", "/^margin/", "/^padding/", "/^gap/"):
            self.assertIn(prop, props)
        for keyword in ("inherit", "transparent", "currentColor", "0", "auto"):
            self.assertIn(keyword, opts["ignoreValues"])

    def test_matrix_follows_e16(self):
        # E-16: every breakpoint in Chromium; the main ones (smallest and largest) also in WebKit and Firefox
        self.generate()
        projects = json.loads(self.out("playwright.projects.json"))
        got = sorted((p["name"], p["browser"], p["viewport"]["width"], p["viewport"]["height"]) for p in projects)
        self.assertEqual(got, sorted([
            ("chromium-mobile", "chromium", 375, 667),
            ("chromium-tablet", "chromium", 768, 800),
            ("chromium-desktop", "chromium", 1280, 800),
            ("webkit-mobile", "webkit", 375, 667),
            ("firefox-mobile", "firefox", 375, 667),
            ("webkit-desktop", "webkit", 1280, 800),
            ("firefox-desktop", "firefox", 1280, 800),
        ]))

    def test_matrix_with_configured_main_breakpoints_and_browsers(self):
        self.front = {"tokens": "design/tokens.json", "mainBreakpoints": ["tablet"],
                      "browsers": {"all": ["chromium", "firefox"], "main": ["webkit"]}}
        self.generate()
        names = sorted(p["name"] for p in json.loads(self.out("playwright.projects.json")))
        self.assertEqual(names, sorted(["chromium-mobile", "chromium-tablet", "chromium-desktop", "firefox-mobile",
                                        "firefox-tablet", "firefox-desktop", "webkit-tablet"]))

    def test_browser_in_both_lists_is_not_duplicated(self):
        self.front = {"tokens": "design/tokens.json", "browsers": {"all": ["chromium"], "main": ["chromium"]}}
        self.generate()
        names = [p["name"] for p in json.loads(self.out("playwright.projects.json"))]
        self.assertEqual(len(names), len(set(names)))

    def test_single_breakpoint_is_both_smallest_and_largest(self):
        data = dict(SAMPLE, breakpoint={"$type": "dimension", "only": {"$value": "1024px"}})
        self.generate(data)
        names = sorted(p["name"] for p in json.loads(self.out("playwright.projects.json")))
        self.assertEqual(names, ["chromium-only", "firefox-only", "webkit-only"])

    def test_generate_fails_closed_on_invalid_tokens_and_writes_nothing(self):
        bad = json.loads(json.dumps(SAMPLE))
        bad["color"]["link"]["$value"] = "{color.nope}"
        self.fails(bad, "alias {color.nope} does not resolve", command="generate")
        self.assertFalse((self.tmp / "front").exists())

    def test_custom_out_folder(self):
        self.front = {"tokens": "design/tokens.json", "out": "web/gen"}
        self.generate()
        self.assertTrue((self.tmp / "web" / "gen" / "tokens.css").is_file())


class Config(unittest.TestCase):
    def test_schema_defaults_and_template_agree(self):
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]["front"]
        template = json.loads((ROOT / "templates" / "gw.json").read_text())
        self.assertEqual(template["front"], schema["default"])
        self.assertIsNone(schema["default"]["tokens"])
        self.assertEqual(schema["default"]["browsers"], {"all": ["chromium"], "main": ["webkit", "firefox"]})
        self.assertEqual(schema["default"]["breakpointGroup"], "breakpoint")
        self.assertEqual(schema["default"]["mainBreakpoints"], [])

    def test_partial_block_is_filled_from_the_schema(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import config
        got = config.front({"front": {"tokens": "t.json", "browsers": {"main": ["webkit"]}}})
        self.assertEqual(got["browsers"], {"all": ["chromium"], "main": ["webkit"]})
        self.assertEqual(got["out"], "front/generated")


if __name__ == "__main__":
    unittest.main()
