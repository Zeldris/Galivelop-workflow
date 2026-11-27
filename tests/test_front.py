"""scripts/front.py (E5, trozo 1): `check` validates a DTCG-subset tokens JSON and `generate` writes tokens.css,
_tokens.scss, stylelint.tokens.json and playwright.projects.json. Every failing case checks the reason in the message,
not only the exit code."""
import json
import os
import shutil
import subprocess
import tempfile
import time
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
        for args in (("nope",), ("run",), ("run", "slow")):
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 2, args)


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
        self.assertIn("  --color-brand: #04c;\n", css)
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
        self.assertIn("$color-brand: #04c;\n", scss)
        self.assertIn("$color-link: $color-brand;\n", scss)
        self.assertIn('$font-family-base: Inter, "Open Sans", sans-serif;\n', scss)

    def test_unicode_names_become_css_safe(self):
        self.generate()
        self.assertIn("  --color-nandu-verde: #0a4;\n", self.out("tokens.css"))
        self.assertIn("$color-nandu-verde: #0a4;\n", self.out("_tokens.scss"))

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


def tweak(**colors):
    """The sample with extra tokens under `color` (a dict name -> token)."""
    data = json.loads(json.dumps(SAMPLE))
    data["color"].update(colors)
    return data


class Review(Base):
    """E5 trozo 1, review findings: one case per cause."""

    def test_hex_colors_are_written_short_when_every_pair_repeats(self):
        """E5 trozo 2 review: Stylelint's standard config wants `#fff`, and the generated files are linted."""
        self.generate(tweak(**{"white": {"$value": "#ffffff"}, "alpha": {"$value": "#ff00ccaa"},
                               "keep": {"$value": "#0b5fff"}, "upper": {"$value": "#AABBCC"}, "named": {"$value": "red"}}))
        css = self.out("tokens.css")
        for line in ("--color-white: #fff;", "--color-alpha: #f0ca;", "--color-keep: #0b5fff;", "--color-upper: #ABC;",
                     "--color-named: red;"):
            self.assertIn(line, css)

    def test_scss_defines_a_variable_before_an_alias_uses_it(self):
        self.generate(tweak(**{"a-x": {"$value": "{color.z-y}"}, "z-y": {"$value": "#ffffff"}}))
        scss = self.out("_tokens.scss")
        self.assertLess(scss.index("$color-z-y: #fff;"), scss.index("$color-a-x: $color-z-y;"))
        chain = tweak(**{"a1": {"$value": "{color.b1}"}, "b1": {"$value": "{color.c1}"}, "c1": {"$value": "#000"}})
        self.generate(chain)
        scss = self.out("_tokens.scss")
        self.assertLess(scss.index("$color-c1:"), scss.index("$color-b1:"))
        self.assertLess(scss.index("$color-b1:"), scss.index("$color-a1:"))

    def test_underscore_and_hyphen_are_the_same_name(self):
        self.fails(tweak(**{"q_r": {"$value": "#111"}, "q-r": {"$value": "#222"}}), "both become --color-q-r")

    def test_font_weight_names_become_numbers(self):
        data = json.loads(json.dumps(SAMPLE))
        data["font"]["weight"]["semi"] = {"$type": "fontWeight", "$value": "semi-bold"}
        data["font"]["weight"]["float"] = {"$type": "fontWeight", "$value": 700.0}
        self.generate(data)
        css = self.out("tokens.css")
        self.assertIn("--font-weight-semi: 600;", css)
        self.assertIn("--font-weight-float: 700;", css)
        self.assertNotIn("semi-bold", css)

    def test_font_weight_unknown_name_fails(self):
        data = json.loads(json.dumps(SAMPLE))
        data["font"]["weight"]["x"] = {"$type": "fontWeight", "$value": "chunky"}
        self.fails(data, "fontWeight value 'chunky'")

    def test_nan_and_infinity_fail(self):
        for word in ("NaN", "Infinity", "-Infinity"):
            text = json.dumps(SAMPLE).replace("1.618", word)
            self.fails(text, f"{word} is not a JSON number")
        self.fails(json.dumps(SAMPLE).replace("1.618", "1e999"), "must be a finite JSON number")

    def test_stylelint_reports_functions_and_expands_shorthands(self):
        self.generate()
        cfg = json.loads(self.out("stylelint.tokens.json"))
        opts = cfg["rules"]["scale-unlimited/declaration-strict-value"][1]
        self.assertIs(opts["ignoreFunctions"], False)
        self.assertIs(opts["expandShorthand"], True)

    def test_dimension_needs_digits_and_a_unit(self):
        for bad in ("16.", "16", ".", "16 px", "16px\n", "px"):
            data = json.loads(json.dumps(SAMPLE))
            data["space"]["bad"] = {"$value": bad}
            self.fails(data, "dimension value")
        data = json.loads(json.dumps(SAMPLE))
        data["space"]["zero"] = {"$value": "0"}
        data["space"]["frac"] = {"$value": ".5rem"}
        self.generate(data)
        self.assertIn("--space-zero: 0;", self.out("tokens.css"))

    def test_a_failed_replace_leaves_no_temp_file(self):
        self.tokens(SAMPLE)
        blocked = self.tmp / "front" / "generated" / "tokens.css"
        blocked.mkdir(parents=True)
        r = self.run_cli("generate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("cannot write front/generated", r.stderr)
        self.assertEqual([p.name for p in blocked.parent.iterdir() if p.name.endswith(".tmp")], [])

    def test_alias_to_a_token_without_type_names_the_target(self):
        data = json.loads(json.dumps(SAMPLE))
        data["misc"] = {"plain": {"$value": "1px"}, "al": {"$type": "dimension", "$value": "{misc.plain}"}}
        self.fails(data, "misc.plain has no $type")

    def test_alias_without_type_inherits_its_targets(self):
        data = json.loads(json.dumps(SAMPLE))
        data["misc"] = {"al": {"$value": "{color.brand}"}, "bad": {"$type": "dimension", "$value": "{color.brand}"}}
        self.fails(data, "misc.bad: type dimension differs")
        del data["misc"]["bad"]
        self.generate(data)
        self.assertIn("--misc-al: var(--color-brand);", self.out("tokens.css"))

    def test_alias_chain_without_type_resolves_breakpoint(self):
        data = json.loads(json.dumps(SAMPLE))
        data["size"] = {"wide": {"$type": "dimension", "$value": "1440px"}}
        data["breakpoint"]["wide"] = {"$value": "{size.wide}"}
        self.generate(data)

    def test_values_that_could_break_the_output_fail(self):
        for bad, reason in (("red; color: blue", "could end or open"), ("red; } body {", "mixes an alias"), ("red\nblue", "could end or open"),
                            ("red /* x", "comment marker"), ("a // b", "comment marker"),
                            ("rgb(1 2 3", "parentheses are not balanced"), ("#{x}", "mixes an alias")):
            self.fails(tweak(bad={"$value": bad}), reason)
        data = json.loads(json.dumps(SAMPLE))
        data["font"]["family"]["base"]["$value"] = ["Evil; } x {"]
        self.fails(data, "could end or open")

    def test_stylelint_lists_and_default_height_are_configurable(self):
        self.front = {"tokens": "design/tokens.json", "defaultHeight": 900,
                      "stylelint": {"colorProperties": ["color"], "sizeProperties": [], "ignoreValues": ["inherit"],
                                    "expandShorthand": False}}
        self.generate()
        props, opts = json.loads(self.out("stylelint.tokens.json"))["rules"][
            "scale-unlimited/declaration-strict-value"]
        self.assertEqual(props, ["color", "/^margin/", "/^padding/", "/^gap/", "/^row-gap/", "/^column-gap/"])
        self.assertEqual(opts["ignoreValues"], ["inherit"])
        self.assertIs(opts["expandShorthand"], False)
        projects = json.loads(self.out("playwright.projects.json"))
        self.assertIn(900, [p["viewport"]["height"] for p in projects if "tablet" in p["name"]])

    def test_front_is_not_a_profile_key(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import config
        self.assertIn("front", config.PROFILE_DENIED)
        schema = json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]
        self.assertIn("front", schema["profiles"]["description"])


PACKAGE = json.dumps({"name": "x", "private": True, "devDependencies": {"@playwright/test": "1.63.0"}})
FAKE_TOOL = """#!/bin/sh
printf '%s|%s\\n' "$(basename "$0") $*" "$PWD" >> "$FAKE_LOG"
[ -e "$PWD/node_modules" ] && echo "node_modules=yes" >> "$FAKE_LOG"
[ -n "$FAKE_PROBE" ] && [ -e "$PWD/$FAKE_PROBE" ] && echo "probe=yes" >> "$FAKE_LOG"
case "$(basename "$0") $*" in *--update-snapshots*) [ -n "$FAKE_SNAP" ] && [ "${FAKE_EXIT:-0}" = 0 ] && \
  mkdir -p "$(dirname "$PWD/$FAKE_SNAP")" && printf 'new' > "$PWD/$FAKE_SNAP" ;; esac
case "$(basename "$0") $1" in "docker info") exit "${FAKE_DOCKER_INFO:-0}" ;; esac
exit "${FAKE_EXIT:-0}"
"""


class Run(Base):
    """E5 (trozo 3): `run fast|full`, in-process so the platform can be faked; node, npm, docker, Stylelint and
    Playwright are fakes that log their arguments and folder."""

    def setUp(self):
        super().setUp()
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import front
        self.mod = front
        self.tokens(SAMPLE)
        self.write_config()
        (self.tmp / "package.json").write_text(PACKAGE)
        (self.tmp / "package-lock.json").write_text("{}\n")
        (self.tmp / "site").mkdir()
        (self.tmp / "site" / "a.css").write_text("a { color: var(--color-brand); }\n")
        self.track()
        self.bin = self.tmp.parent / (self.tmp.name + "-bin")
        self.bin.mkdir()
        self.addCleanup(shutil.rmtree, self.bin, True)
        self.log = self.bin / "log"
        self.log.write_text("")
        self.browsers = self.bin / "browsers"
        (self.browsers / "chromium-1").mkdir(parents=True)
        self.env = {"PATH": str(self.bin) + os.pathsep + "/usr/bin:/bin", "FAKE_LOG": str(self.log),
                    "PLAYWRIGHT_BROWSERS_PATH": str(self.browsers), "GIT_CONFIG_GLOBAL": os.devnull}

    def fake(self, folder, *names):
        for name in names:
            path = folder / name
            path.write_text(FAKE_TOOL)
            path.chmod(0o755)

    def track(self):
        subprocess.run(["git", "-C", str(self.tmp), "add", "-A"], check=True)

    def cache_dir(self, pkg=None):
        return self.mod.node_cache(self.tmp, pkg or self.tmp)

    def cache(self, browsers=None):
        """A filled npm cache, as `npm ci` would leave it, with the stamp of this package."""
        cache = self.cache_dir()
        modules = cache / "node_modules"
        (modules / ".bin").mkdir(parents=True)
        (modules / "playwright-core").mkdir()
        (modules / "playwright-core" / "browsers.json").write_text(json.dumps({"browsers": browsers or [
            {"name": "chromium", "revision": "1"}, {"name": "webkit", "revision": "2"}]}))
        self.fake(modules / ".bin", "stylelint", "playwright")
        (cache / "installed-from").write_bytes(b"{}\n" + PACKAGE.encode())
        return modules

    def main(self, *args, system="Linux", env=None):
        import contextlib
        import io
        from unittest import mock
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.object(self.mod.platform, "system", return_value=system), \
                mock.patch.dict(os.environ, dict(self.env, **(env or {}))), \
                contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = self.mod.main(["--root", str(self.tmp), *args])
        return code, out.getvalue() + err.getvalue()

    def calls(self):
        return [line.split("|") for line in self.log.read_text().splitlines() if "|" in line]

    def test_without_tokens_run_does_nothing_and_exits_0(self):
        for front in (None, {"tokens": None}):
            self.write_config(front)
            for mode, system in (("fast", "Linux"), ("full", "Linux"), ("full", "Darwin")):
                code, out = self.main("run", mode, system=system)
                self.assertEqual(code, 0, (front, mode, out))
                self.assertEqual(out, "")
        self.assertEqual(self.calls(), [])

    def test_full_on_macos_without_docker_refuses_with_the_reason(self):
        self.cache()
        self.fake(self.bin, "node", "npm")
        from unittest import mock
        which = self.mod.shutil.which  # PATH keeps /usr/bin, where a CI runner has a real docker: hide it
        with mock.patch.object(self.mod.shutil, "which", lambda t, *a, **k: None if t == "docker" else which(t, *a, **k)):
            code, out = self.main("run", "full", system="Darwin")
        self.assertEqual(code, 3, out)
        self.assertIn("only match on Linux (E-9)", out)
        self.assertIn("Darwin without a running Docker: nothing was checked", out)
        self.assertIn("run fast", out)  # what can run here
        self.assertNotIn("passed", out)
        self.assertEqual(self.calls(), [])  # no Stylelint, no Playwright: no partial green

    def test_full_on_macos_with_docker_stopped_refuses_too(self):
        self.fake(self.bin, "docker")
        code, out = self.main("run", "full", system="Darwin", env={"FAKE_DOCKER_INFO": "1"})
        self.assertEqual(code, 3, out)
        self.assertIn("without a running Docker", out)
        self.assertEqual([c[0] for c in self.calls()], ["docker info"])

    def test_full_on_macos_with_docker_runs_the_pinned_image(self):
        self.fake(self.bin, "docker")
        code, out = self.main("run", "full", system="Darwin")
        self.assertEqual(code, 0, out)
        run = [c for c in self.calls() if c[0].startswith("docker run")]
        self.assertEqual(len(run), 1, self.calls())
        self.assertIn("mcr.microsoft.com/playwright:v1.63.0-noble", run[0][0])
        self.assertIn("npx playwright test", run[0][0])
        self.assertIn("npm ci --ignore-scripts ", run[0][0], "D3 (E28): no install script runs as root in Docker")
        self.assertNotIn("--grep-invert", run[0][0])
        code, out = self.main("run", "full", system="Darwin", env={"FAKE_EXIT": "1"})
        self.assertEqual(code, 1, out)
        self.assertIn("full checks in Docker", out)

    def test_fast_runs_stylelint_and_layout_on_the_main_breakpoints_from_a_copy(self):
        self.cache()
        self.fake(self.bin, "node", "npm")
        code, out = self.main("run", "fast")
        self.assertEqual(code, 0, out)
        calls = self.calls()
        self.assertEqual([c[0].split()[0] for c in calls], ["stylelint", "playwright"], calls)
        self.assertIn("**/*.{css,scss}", calls[0][0])
        self.assertNotIn("--allow-empty-input", calls[0][0])
        pw = calls[1][0]
        self.assertIn("--grep-invert @visual", pw)
        self.assertIn("--project chromium-mobile --project chromium-desktop", pw)
        self.assertNotIn("tablet", pw)
        for call in calls:  # a temporary copy, never the tree
            self.assertNotEqual(Path(call[1]).resolve(), self.tmp)
        self.assertIn("node_modules=yes", self.log.read_text())
        self.assertFalse((self.tmp / "node_modules").exists())
        self.assertEqual(subprocess.run(["git", "-C", str(self.tmp), "status", "--porcelain", "--ignored"],
                                        capture_output=True, text=True).stdout.count("node_modules"), 0)

    def test_full_on_linux_runs_the_whole_matrix(self):
        self.cache()
        self.fake(self.bin, "node", "npm")
        (self.browsers / "webkit-2").mkdir()
        self.write_config({"tokens": "design/tokens.json", "browsers": {"all": ["chromium"], "main": ["webkit"]}})
        code, out = self.main("run", "full")
        self.assertEqual(code, 0, out)
        pw = self.calls()[1][0]
        self.assertNotIn("--grep-invert", pw)
        self.assertNotIn("--project", pw)

    SNAP = "tests/home.spec.ts-snapshots/home-chromium-desktop-linux.png"

    def test_update_snapshots_brings_the_baselines_back_and_writes_the_stamp(self):
        """E78 (Q-36): the run is in a temporary copy, so the new or changed baselines come back to the tree and the
        pinned Playwright goes into front.snapshotStamp; nothing else of the copy comes back."""
        self.cache()
        self.fake(self.bin, "node", "npm")
        (self.browsers / "webkit-2").mkdir()
        self.write_config({"tokens": "design/tokens.json", "browsers": {"all": ["chromium"], "main": ["webkit"]}})
        old = self.tmp / "tests/a.spec.ts-snapshots/a-chromium-mobile-linux.png"
        old.parent.mkdir(parents=True)
        old.write_text("old")
        self.track()
        code, out = self.main("run", "full", "--update-snapshots", env={"FAKE_SNAP": self.SNAP})
        self.assertEqual(code, 0, out)
        self.assertIn("--update-snapshots", self.calls()[1][0])
        self.assertEqual((self.tmp / self.SNAP).read_text(), "new")
        self.assertEqual(old.read_text(), "old")
        self.assertEqual((self.tmp / "front/snapshots.version").read_text(), "1.63.0\n")
        self.assertIn(f"front: updated {self.SNAP}", out)
        self.assertIn("review them with git diff", out)
        self.assertFalse((self.tmp / "node_modules").exists())

    def test_update_snapshots_in_docker_brings_them_back_too(self):
        self.fake(self.bin, "docker")
        code, out = self.main("run", "full", "--update-snapshots", system="Darwin", env={"FAKE_SNAP": self.SNAP})
        self.assertEqual(code, 0, out)
        run = [c for c in self.calls() if c[0].startswith("docker run")]
        self.assertIn("--update-snapshots", run[0][0])
        self.assertEqual((self.tmp / self.SNAP).read_text(), "new")
        self.assertEqual((self.tmp / "front/snapshots.version").read_text(), "1.63.0\n")

    def test_update_snapshots_after_a_failure_leaves_the_tree_and_the_stamp_alone(self):
        self.fake(self.bin, "docker")
        code, out = self.main("run", "full", "--update-snapshots", system="Darwin",
                              env={"FAKE_SNAP": self.SNAP, "FAKE_EXIT": "1"})
        self.assertEqual(code, 1, out)
        self.assertFalse((self.tmp / self.SNAP).exists())
        self.assertFalse((self.tmp / "front/snapshots.version").exists())

    def test_update_snapshots_needs_full_and_an_exact_pin(self):
        code, out = self.main("run", "fast", "--update-snapshots")
        self.assertEqual(code, 2, out)
        self.assertIn("--update-snapshots only goes with `run full`", out)
        self.assertEqual(self.calls(), [])
        (self.tmp / "package.json").write_text(PACKAGE.replace('"1.63.0"', '"^1.63.0"'))
        self.track()
        code, out = self.main("run", "full", "--update-snapshots")
        self.assertEqual(code, 2, out)
        self.assertIn("no exact @playwright/test version", out)
        self.assertIn("snapshots.version", out)
        self.assertEqual(self.calls(), [])

    def test_a_missing_browser_names_the_install_command(self):
        self.cache()
        self.fake(self.bin, "node", "npm")
        code, out = self.main("run", "full")  # firefox (browsers.main) has no build in the browsers folder
        self.assertEqual(code, 3, out)
        self.assertIn("Playwright's webkit, firefox not installed", out)
        self.assertIn("install --browsers webkit firefox", out)

    def test_a_failed_check_exits_1_with_the_step(self):
        self.cache()
        self.fake(self.bin, "node", "npm")
        code, out = self.main("run", "fast", env={"FAKE_EXIT": "2"})
        self.assertEqual(code, 1, out)
        self.assertIn("stylelint failed (exit 2", out)
        self.assertIn("run fast", out)

    def test_without_node_it_says_so(self):
        code, out = self.main("run", "fast")  # no cache yet, so npm ci is needed
        self.assertEqual(code, 3, out)
        self.assertIn("node and npm not found; install node 22+", out)

    def test_without_package_json_names_front_dir(self):
        (self.tmp / "package.json").unlink()
        code, out = self.main("run", "fast")
        self.assertEqual(code, 2, out)
        self.assertIn("no package.json in '.'", out)
        self.assertIn("front.dir", out)

    def test_install_installs_into_the_git_dir_and_stamps_it(self):
        self.fake(self.bin, "node", "npm")
        code, out = self.main("install")
        self.assertEqual(code, 0, out)
        cache = self.cache_dir()
        self.assertEqual(cache.parent, self.tmp / ".git" / "gw" / "front-node")
        self.assertEqual([c[0] for c in self.calls()], ["npm ci --ignore-scripts --no-audit --no-fund"])
        self.assertEqual(Path(self.calls()[0][1]).resolve(), cache.resolve())
        self.assertEqual((cache / "installed-from").read_bytes(), b"{}\n" + PACKAGE.encode())

    def test_install_without_tokens_does_nothing_unless_given_a_package_dir(self):
        self.write_config(None)
        self.fake(self.bin, "node", "npm")
        self.assertEqual(self.main("install")[0], 0)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.main("install", "--package-dir", ".")[0], 0)
        self.assertEqual([c[0] for c in self.calls()], ["npm ci --ignore-scripts --no-audit --no-fund"])

    def test_e7_install_matrix_asks_for_each_browser_of_the_matrix_once(self):
        self.fake(self.bin, "node", "npm")
        self.write_config({"tokens": "design/tokens.json",
                           "browsers": {"all": ["chromium", "webkit"], "main": ["webkit", "firefox"]}})
        self.cache()
        code, out = self.main("install", "--matrix", "--with-deps")
        self.assertEqual(code, 0, out)
        self.assertEqual([c[0] for c in self.calls()],
                         ["playwright install --with-deps chromium webkit firefox"])

    def test_e7_install_matrix_without_tokens_does_nothing(self):
        self.write_config(None)
        self.fake(self.bin, "node", "npm")
        self.assertEqual(self.main("install", "--matrix")[0], 0)
        self.assertEqual(self.calls(), [])


    # -- review of chunk 3 -------------------------------------------------------------------------------------------
    def browsers_path(self, system, env):
        from unittest import mock
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("PLAYWRIGHT_BROWSERS_PATH", "XDG_CACHE_HOME", "LOCALAPPDATA")}
        with mock.patch.object(self.mod.platform, "system", return_value=system), \
                mock.patch.dict(os.environ, dict(clean, HOME="/h", **env), clear=True):
            return self.mod.browsers_path(Path("/nm"))

    def test_browsers_path_follows_playwright_on_each_platform(self):
        self.assertEqual(self.browsers_path("Linux", {}), Path("/h/.cache/ms-playwright"))
        self.assertEqual(self.browsers_path("Linux", {"XDG_CACHE_HOME": "/x"}), Path("/x/ms-playwright"))
        self.assertEqual(self.browsers_path("Darwin", {}), Path("/h/Library/Caches/ms-playwright"))
        self.assertEqual(self.browsers_path("Windows", {"LOCALAPPDATA": "/w"}), Path("/w/ms-playwright"))
        self.assertEqual(self.browsers_path("Darwin", {"PLAYWRIGHT_BROWSERS_PATH": "/p"}), Path("/p"))
        self.assertEqual(self.browsers_path("Linux", {"PLAYWRIGHT_BROWSERS_PATH": "0"}),
                         Path("/nm/playwright-core/.local-browsers"))

    def test_fast_on_macos_finds_the_browsers_in_library_caches(self):
        """Finding 1: on a Mac Playwright installs into ~/Library/Caches; the pre-push must not refuse every push."""
        self.cache()
        self.fake(self.bin, "node", "npm")
        home = self.bin / "home"
        (home / "Library" / "Caches" / "ms-playwright" / "chromium-1").mkdir(parents=True)
        env = {k: v for k, v in self.env.items() if k != "PLAYWRIGHT_BROWSERS_PATH"}
        from unittest import mock
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
            self.env = env
            code, out = self.main("run", "fast", system="Darwin", env={"HOME": str(home)})
        self.assertEqual(code, 0, out)

    def test_a_host_specific_build_counts_as_installed(self):
        """Finding 12: a host-specific build (revisionOverrides) is the one Playwright installs there."""
        self.cache(browsers=[{"name": "chromium", "revision": "1"},
                             {"name": "webkit", "revision": "2", "revisionOverrides": {"mac12": "7"}},
                             {"name": "firefox", "revision": "3"}])
        self.fake(self.bin, "node", "npm")
        (self.browsers / "webkit-7").mkdir()
        (self.browsers / "firefox-3").mkdir()
        code, out = self.main("run", "full")
        self.assertEqual(code, 0, out)

    def test_stylelint_runs_from_the_root_with_the_config_of_front_dir(self):
        """Finding 3: front.dir in a subfolder and the app's CSS outside it: Stylelint still checks it."""
        default_cache = self.cache()
        sub = self.tmp / "front-tests"
        sub.mkdir()
        for name in ("package.json", "package-lock.json"):
            (self.tmp / name).rename(sub / name)
        (sub / ".stylelintrc.json").write_text("{}\n")
        self.write_config({"tokens": "design/tokens.json", "dir": "front-tests", "stylelintFiles": ["site/**/*.css"]})
        self.track()
        self.assertEqual(self.mod.node_cache(self.tmp, sub), default_cache.parent)  # same files, same cache
        self.fake(self.bin, "node", "npm")
        code, out = self.main("run", "fast", env={"FAKE_PROBE": "site/a.css"})
        self.assertEqual(code, 0, out)
        calls = self.calls()
        self.assertIn("--config front-tests/.stylelintrc.json site/**/*.css", calls[0][0])
        self.assertEqual(Path(calls[1][1]).name, "front-tests")  # Playwright from the copy's front.dir
        self.assertNotEqual(Path(calls[0][1]).name, "front-tests")
        self.assertIn("probe=yes", self.log.read_text())  # the CSS outside front.dir is in the copy

    def test_globs_that_match_no_tracked_file_fail_with_the_reason(self):
        self.cache()
        self.fake(self.bin, "node", "npm")
        self.write_config({"tokens": "design/tokens.json", "stylelintFiles": ["../src/**/*.css", "nope/*.scss"]})
        code, out = self.main("run", "fast")
        self.assertEqual(code, 2, out)
        self.assertIn("matches no file git tracks", out)
        self.assertIn("front.stylelintFiles", out)
        self.assertEqual(self.calls(), [])

    def test_ignored_files_are_not_copied(self):
        """Finding 4: what git ignores (a built dist/app.css) is not part of the commit, so not of the checks."""
        self.cache()
        self.fake(self.bin, "node", "npm")
        (self.tmp / ".gitignore").write_text("dist/\n")
        (self.tmp / "dist").mkdir()
        (self.tmp / "dist" / "app.css").write_text("a { color: #f00; }\n")
        self.track()
        code, out = self.main("run", "fast", env={"FAKE_PROBE": "dist/app.css"})
        self.assertEqual(code, 0, out)
        self.assertNotIn("probe=yes", self.log.read_text())
        code, out = self.main("run", "fast", env={"FAKE_PROBE": "site/a.css"})
        self.assertIn("probe=yes", self.log.read_text())  # the probe works: tracked files are there

    def test_another_lock_gets_its_own_cache(self):
        """Finding 5: two locks never share (nor remove) one node_modules."""
        first = self.cache()
        (self.tmp / "package-lock.json").write_text('{"v": 2}\n')
        self.assertNotEqual(self.cache_dir(), first.parent)
        self.fake(self.bin, "node", "npm")
        self.assertEqual(self.main("install")[0], 0)
        self.assertTrue((first / ".bin" / "stylelint").is_file())
        self.assertTrue((self.cache_dir() / "installed-from").is_file())

    def test_old_caches_of_other_locks_are_pruned_and_busy_or_recent_ones_kept(self):
        """front.nodeCacheDays: one cache per lock would grow for ever; only old, idle ones of other locks go."""
        import fcntl
        current = self.cache().parent
        base = current.parent
        old_time = time.time() - 40 * 86400

        def other(name, age):
            folder = base / name
            (folder / "node_modules").mkdir(parents=True)
            (folder / "installed-from").write_bytes(b"x")
            os.utime(str(folder / "installed-from"), (age, age))
            return folder
        old, recent, busy, legacy = (other("a" * 16, old_time), other("b" * 16, time.time()), other("c" * 16, old_time),
                                     other("node_modules_old", old_time))
        os.utime(str(current / "installed-from"), (old_time, old_time))  # the current one, even if old, stays
        self.fake(self.bin, "node", "npm")
        with open(str(busy / ".lock"), "w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            code, out = self.main("install")
        self.assertEqual(code, 0, out)
        self.assertFalse(old.exists())
        for kept in (current, recent, busy, legacy):
            self.assertTrue(kept.is_dir(), kept)
        self.assertGreater((current / "installed-from").stat().st_mtime, old_time + 86400)  # the use is dated
        old = other("d" * 16, old_time)
        self.write_config({"tokens": "design/tokens.json", "nodeCacheDays": 0})
        self.assertEqual(self.main("install")[0], 0)
        self.assertTrue(old.is_dir())

    def test_a_failed_npm_ci_leaves_no_stamp(self):
        """Finding 6: the old stamp goes before node_modules does, and a failed npm ci writes none."""
        cache = self.cache_dir()
        (cache / "node_modules" / ".bin").mkdir(parents=True)
        (cache / "installed-from").write_bytes(b"older install")
        self.fake(self.bin, "node", "npm")
        code, out = self.main("install", env={"FAKE_EXIT": "1"})
        self.assertEqual(code, 3, out)
        self.assertIn("npm ci failed", out)
        self.assertFalse((cache / "installed-from").exists())

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
        self.assertEqual(got["lfsThresholdKb"], 200)
        self.assertEqual(got["visualTag"], "@visual")


if __name__ == "__main__":
    unittest.main()
