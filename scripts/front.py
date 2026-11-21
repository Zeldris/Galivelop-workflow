#!/usr/bin/env python3
# galivelop-workflow v0.8.1
"""E5 (trozo 1): the design tokens of a front-end project as data, and what is generated from them.

  python3 front.py check       # validate the tokens JSON (front.tokens in .claude/gw.json)
  python3 front.py generate    # check, then write into front.out: tokens.css, _tokens.scss,
                               # stylelint.tokens.json and playwright.projects.json

The tokens file is a subset of the W3C Design Tokens format (DTCG): nested groups, leaves with `$value` and `$type`
(color, dimension, fontFamily, fontWeight, number, duration; a group's `$type` is inherited by its tokens), aliases
`{group.token}` that must resolve and must not cycle. The group `front.breakpointGroup` holds the breakpoints: each
`$value` a px dimension, the viewport height in `$extensions.gw.height` (default 800). The Playwright matrix is every
breakpoint x `front.browsers.all`, plus `front.mainBreakpoints` (default: the smallest and the largest) x
`front.browsers.main` (E-16).

Output is deterministic (sorted, LF, one trailing newline): two runs give the same bytes, so a project can declare the
files in `generated` (E72) and the check compares them. Without `front.tokens` (null, the default) every subcommand
does nothing and exits 0. Fails closed: exit 1 = the tokens are invalid, 2 = bad config, path outside the repository
or usage; each message names the command that fixes it. Root: --root, else config.find_root (this script's repo).
Python 3.8+, standard library only.
"""
import argparse
import json
import math
import os
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402  the only reader of .claude/gw.json

TYPES = ("color", "dimension", "fontFamily", "fontWeight", "number", "duration")
NUMBER = r"-?(?:\d+(?:\.\d+)?|\.\d+)"
DIMENSION = re.compile(NUMBER + r"(px|rem|em|%|vw|vh|vmin|vmax|ch|ex|pt|cm|mm|in)")
DURATION = re.compile(r"\d+(\.\d+)?(ms|s)")
PX = re.compile(r"(\d+)px")
ALIAS = re.compile(r"\{([^{}]+)\}")
# DTCG weight names as numbers: CSS font-weight only knows normal, bold, bolder, lighter and numbers
WEIGHTS = {"thin": 100, "hairline": 100, "extra-light": 200, "ultra-light": 200, "light": 300, "normal": 400,
           "regular": 400, "book": 400, "medium": 500, "semi-bold": 600, "demi-bold": 600, "bold": 700,
           "extra-bold": 800, "ultra-bold": 800, "black": 900, "heavy": 900, "extra-black": 950, "ultra-black": 950}
GENERIC_FAMILIES = ("serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-serif", "ui-sans-serif",
                    "ui-monospace", "ui-rounded", "emoji", "math", "fangsong")
STRICT_VALUE_RULE = "scale-unlimited/declaration-strict-value"
FILES = ("tokens.css", "_tokens.scss", "stylelint.tokens.json", "playwright.projects.json")


class Fail(Exception):
    """A user-facing failure: the message names the command that fixes it. `code` is the exit status."""

    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def command(root, sub="check"):
    return f"python3 {Path(__file__).resolve()} --root {root} {sub}"


def inside(root, rel):
    """The real path of repo-relative `rel` when it stays inside `root` (symlinks followed), else None."""
    if os.path.isabs(rel):
        return None
    base = os.path.realpath(str(root))
    full = os.path.realpath(os.path.join(base, rel))
    return Path(full) if full == base or full.startswith(base + os.sep) else None


def css_part(segment):
    """One name segment as CSS-safe text: accents folded to ASCII, lower case, anything else becomes '-' (also
    '_': Sass treats - and _ in a variable name as the same character)."""
    text = unicodedata.normalize("NFKD", segment)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def css_name(path):
    return "-".join(css_part(p) for p in path)


def dotted(path):
    return ".".join(path)


def non_finite(constant):
    raise ValueError(f"{constant} is not a JSON number (CSS and Sass reject it)")


def no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


class Tokens:
    """The parsed, validated tokens: `leaves` {dotted path: Leaf} in file order."""

    def __init__(self, data, group, root, front):
        self.root = root
        self.front = front
        self.leaves = {}
        self.fix = f"fix the tokens file, then check it with: {command(root)}"
        self.group = group
        self._walk(data, (), None)
        self._names()
        self._aliases()
        self._values()

    # -- structure ---------------------------------------------------------------------------------------------
    def _walk(self, node, path, inherited):
        kind = node.get("$type", inherited)
        children = [(k, v) for k, v in node.items() if not k.startswith("$")]
        if path and "$value" in node:
            if children:
                raise Fail(f"{dotted(path)}: a token with $value cannot also hold tokens ({children[0][0]}); {self.fix}")
            self.leaves[dotted(path)] = {"path": path, "value": node["$value"], "type": kind,
                                         "ext": node.get("$extensions")}
            return
        if path and not children:
            raise Fail(f"{dotted(path)}: a token needs $value (a group needs at least one token); {self.fix}")
        for key, child in children:
            if re.search(r"[.{}]", key):
                raise Fail(f"{dotted(path + (key,))}: a name must not contain '.', '{{' or '}}' "
                           f"(they are the alias syntax); {self.fix}")
            if not isinstance(child, dict):
                raise Fail(f"{dotted(path + (key,))}: expected a token or a group (an object), got "
                           f"{type(child).__name__}; {self.fix}")
            if "$type" in node and not isinstance(node["$type"], str):
                raise Fail(f"{dotted(path) or '(root)'}: $type must be a string; {self.fix}")
            self._walk(child, path + (key,), kind)

    def _names(self):
        seen = {}
        for name, leaf in self.leaves.items():
            for part in leaf["path"]:
                if not css_part(part):
                    raise Fail(f"{name} has no CSS-safe name ('{part}' has no letters or digits once folded to ASCII); "
                               f"rename it, then check: {command(self.root)}")
            css = css_name(leaf["path"])
            if not css[0].isalpha():
                raise Fail(f"{name}: the name '{css}' must start with a letter (a SCSS variable cannot start with a "
                           f"digit); rename it, then check: {command(self.root)}")
            if css in seen:
                raise Fail(f"{seen[css]} and {name} both become --{css}; rename one of them, then check: "
                           f"{command(self.root)}")
            seen[css] = name
            leaf["css"] = css

    # -- aliases -----------------------------------------------------------------------------------------------
    def alias_of(self, value):
        if isinstance(value, str) and ALIAS.fullmatch(value):
            return ALIAS.fullmatch(value).group(1)
        return None

    def _aliases(self):
        for name, leaf in self.leaves.items():
            value = leaf["value"]
            target = self.alias_of(value)
            if target is None and isinstance(value, str) and re.search(r"[{}]", value):
                raise Fail(f"{name}: '{value}' mixes an alias with other text; an alias must be the whole value "
                           f"({{group.token}}); {self.fix}")
            leaf["alias"] = target
        for name in self.leaves:
            self.resolve(name)

    def resolve(self, name):
        """The leaf an alias chain ends at (the token itself when it is not an alias); fails on a missing target, a
        group or a cycle."""
        chain = [name]
        current = self.leaves[name]
        while current["alias"] is not None:
            target = current["alias"]
            if target not in self.leaves:
                if any(k.startswith(target + ".") for k in self.leaves):
                    raise Fail(f"{chain[-1]}: alias {{{target}}} points to a group, not a token; {self.fix}")
                raise Fail(f"{chain[-1]}: alias {{{target}}} does not resolve (no such token); {self.fix}")
            if target in chain:
                raise Fail(f"alias cycle: {' -> '.join(chain + [target])}; break the loop, then check: "
                           f"{command(self.root)}")
            chain.append(target)
            current = self.leaves[target]
        return chain[-1]

    # -- values ------------------------------------------------------------------------------------------------
    def _values(self):
        for name, leaf in self.leaves.items():  # own and inherited types first: an alias takes its target's
            kind = leaf["type"]
            if kind is None and leaf["alias"] is not None:
                continue
            if kind is None:
                raise Fail(f"{name} has no $type (and no group above it sets one); add \"$type\" (one of "
                           f"{', '.join(TYPES)}); {self.fix}")
            if kind not in TYPES:
                raise Fail(f"{name}: $type '{kind}' is not allowed (allowed: {', '.join(TYPES)}); {self.fix}")
        for name, leaf in self.leaves.items():
            if leaf["alias"] is None:
                leaf["text"] = self.render(name, leaf["type"], leaf["value"])
                continue
            end_name = self.resolve(name)
            end = self.leaves[end_name]
            if leaf["type"] is None:
                leaf["type"] = end["type"]  # DTCG: an alias without a type has its target's
            elif end["type"] != leaf["type"]:
                raise Fail(f"{name}: type {leaf['type']} differs from the type of its alias target "
                           f"{{{leaf['alias']}}} ({end['type']}); {self.fix}")

    def unsafe(self, name, text):
        """Fails when `text` could break the CSS or SCSS written from it (a declaration ended early, a block or a
        comment opened, an interpolation, a line break, unbalanced parentheses)."""
        bad = next((c for c in text if c in ";{}\\" or ord(c) < 32 or ord(c) == 127), None)
        reason = None
        if bad is not None:
            reason = f"the character {bad!r} could end or open a declaration, a block or a line in the generated files"
        elif "/*" in text or "*/" in text or "//" in text:
            reason = "a comment marker (/* */ or //) could swallow what follows it in the generated files"
        elif text.count("(") != text.count(")"):
            reason = "its parentheses are not balanced"
        if reason:
            raise Fail(f"{name}: value {text!r} is not safe to write into CSS and SCSS: {reason}; {self.fix}")
        return text

    def render(self, name, kind, value):
        bad = f"; {self.fix}"
        if kind == "color":
            if not isinstance(value, str) or not value.strip():
                raise Fail(f"{name}: color value {value!r} must be a non-empty string{bad}")
            return self.unsafe(name, value.strip())
        if kind == "dimension":
            if not isinstance(value, str) or not (DIMENSION.fullmatch(value) or value in ("0", "-0")):
                raise Fail(f"{name}: dimension value {value!r} is not a number with a unit (or 0), e.g. \"16px\"{bad}")
            return value
        if kind == "duration":
            if not isinstance(value, str) or not DURATION.fullmatch(value):
                raise Fail(f"{name}: duration value {value!r} is not a number of ms or s, e.g. \"150ms\"{bad}")
            return value
        if kind == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise Fail(f"{name}: number value {value!r} must be a finite JSON number{bad}")
            return str(int(value)) if float(value).is_integer() else repr(float(value))
        if kind == "fontWeight":
            if isinstance(value, str) and value in WEIGHTS:
                return str(WEIGHTS[value])
            if (not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
                    and float(value).is_integer() and 1 <= value <= 1000):
                return str(int(value))
            raise Fail(f"{name}: fontWeight value {value!r} must be a whole number from 1 to 1000 or a name "
                       f"like \"bold\" ({', '.join(sorted(WEIGHTS))}){bad}")
        families = value if isinstance(value, list) else [value]  # fontFamily
        if not families or not all(isinstance(f, str) and f.strip() for f in families):
            raise Fail(f"{name}: fontFamily value {value!r} must be a name or a non-empty list of names{bad}")
        return ", ".join(self._family(self.unsafe(name, f.strip())) for f in families)

    @staticmethod
    def _family(text):
        if text in GENERIC_FAMILIES or re.match(r"^[A-Za-z_][A-Za-z0-9_-]*$", text):
            return text
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'

    # -- breakpoints -------------------------------------------------------------------------------------------
    def breakpoints(self):
        """[(name, width, height)] sorted by width then name; fails when a breakpoint is not a px dimension."""
        out = []
        prefix = self.group + "."
        for name, leaf in self.leaves.items():
            if not name.startswith(prefix):
                continue
            end = self.leaves[self.resolve(name)]
            match = PX.fullmatch(end["value"]) if isinstance(end["value"], str) and end["type"] == "dimension" else None
            if not match or int(match.group(1)) < 1:
                raise Fail(f"{name} must be a px dimension (a whole number of px, e.g. \"768px\"), got "
                           f"{end['value']!r}; {self.fix}")
            height = self.front["defaultHeight"]
            ext = leaf["ext"]
            gw = ext.get("gw") if isinstance(ext, dict) else None
            if isinstance(gw, dict) and "height" in gw:
                height = gw["height"]
                if isinstance(height, bool) or not isinstance(height, int) or height < 1:
                    raise Fail(f"{name}: $extensions.gw.height must be a positive integer, got {height!r}; {self.fix}")
            out.append((css_name(leaf["path"][len(self.group.split(".")):]), int(match.group(1)), height))
        return sorted(out, key=lambda b: (b[1], b[0]))


def load_tokens(root, front):
    """The validated Tokens of `front.tokens`, or None when the project has no front."""
    rel = front["tokens"]
    if rel is None:
        return None
    path = inside(root, rel)
    if path is None:
        raise Fail(f"front.tokens {rel!r} is outside the repository; set a repo-relative path in .claude/gw.json", 2)
    shown = rel
    if not path.is_file():
        raise Fail(f"{shown} not found; create it or set front.tokens in .claude/gw.json (null = no front), "
                   f"then run: {command(root)}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise Fail(f"{shown}: cannot read it as UTF-8 ({exc}); fix it, then run: {command(root)}")
    if not text.strip():
        raise Fail(f"{shown} is empty; add the tokens (a JSON object), then run: {command(root)}")
    try:
        data = json.loads(text, object_pairs_hook=no_duplicates, parse_constant=non_finite)
    except json.JSONDecodeError as exc:
        raise Fail(f"{shown}: invalid JSON at line {exc.lineno}: {exc.msg}; fix it, then run: {command(root)}")
    except ValueError as exc:
        raise Fail(f"{shown}: {exc}; fix it, then run: {command(root)}")
    if not isinstance(data, dict):
        raise Fail(f"{shown}: the root must be a JSON object (groups of tokens), got {type(data).__name__}; "
                   f"fix it, then run: {command(root)}")
    group = front["breakpointGroup"]
    node = data
    for part in group.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    fix = f"fix {shown} or front.breakpointGroup, then run: {command(root)}"
    if not isinstance(node, dict):
        raise Fail(f"breakpoint group '{group}' not found in {shown}; {fix}")
    if not _has_leaf(node):
        raise Fail(f"breakpoint group '{group}' has no breakpoints (tokens with $value); {fix}")
    tokens = Tokens(data, group, root, front)
    marks = tokens.breakpoints()
    known = {b[0] for b in marks}
    for name in front["mainBreakpoints"]:
        if css_part(name) not in known:
            raise Fail(f"front.mainBreakpoints names '{name}', which is not a breakpoint of '{group}' "
                       f"(known: {', '.join(sorted(known))}); fix .claude/gw.json, then run: {command(root)}")
    return tokens


def _has_leaf(node):
    return any(isinstance(v, dict) and ("$value" in v or _has_leaf(v)) for k, v in node.items() if not k.startswith("$"))


# -- output ----------------------------------------------------------------------------------------------------------
def depth(tokens, leaf):
    """How many aliases lead from `leaf` to a plain value (0 = a plain value)."""
    steps = 0
    while leaf["alias"] is not None:
        leaf = tokens.leaves[leaf["alias"]]
        steps += 1
    return steps


def declarations(tokens, css):
    """[(name, value)]. CSS: sorted by name (var() resolves late). SCSS: a variable must exist before another one
    uses it, so ordered by alias depth (plain values first), then by name."""
    rows = []
    for leaf in tokens.leaves.values():
        if leaf["alias"] is not None:
            target = tokens.leaves[leaf["alias"]]["css"]
            value = f"var(--{target})" if css else f"${target}"
        else:
            value = leaf["text"]
        rows.append((0 if css else depth(tokens, leaf), leaf["css"], value))
    return [(name, value) for _depth, name, value in sorted(rows)]


def render_css(tokens, source):
    lines = [f"/* Generated by scripts/front.py from {source}: do not edit. */", ":root {"]
    lines += [f"  --{name}: {value};" for name, value in declarations(tokens, True)]
    return "\n".join(lines + ["}"]) + "\n"


def render_scss(tokens, source):
    lines = [f"// Generated by scripts/front.py from {source}: do not edit."]
    lines += [f"${name}: {value};" for name, value in declarations(tokens, False)]
    return "\n".join(lines) + "\n"


def as_json(data):
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def stylelint_fragment(front):
    """Colors, spacing and sizes must be variables (var(--x), $x): functions with literals (rgb(...), calc(13px)) are
    reported too (ignoreFunctions false), and shorthands are expanded so `background: #f00` is checked."""
    rules = front["stylelint"]
    props = rules["colorProperties"] + rules["spacingProperties"] + rules["sizeProperties"]
    options = {"disableFix": True, "expandShorthand": rules["expandShorthand"], "ignoreFunctions": False,
               "ignoreValues": rules["ignoreValues"]}
    return {"plugins": ["stylelint-declaration-strict-value"], "rules": {STRICT_VALUE_RULE: [props, options]}}


def playwright_projects(tokens, front):
    marks = tokens.breakpoints()
    main = {css_part(n) for n in front["mainBreakpoints"]} or {marks[0][0], marks[-1][0]}
    out = []
    for name, width, height in marks:
        browsers = list(front["browsers"]["all"])
        if name in main:
            browsers += [b for b in front["browsers"]["main"] if b not in browsers]
        for browser in browsers:
            out.append({"name": f"{browser}-{name}", "browser": browser,
                        "viewport": {"width": width, "height": height}})
    return out


def generated_files(tokens, front):
    source = front["tokens"]
    return {"tokens.css": render_css(tokens, source), "_tokens.scss": render_scss(tokens, source),
            "stylelint.tokens.json": as_json(stylelint_fragment(front)),
            "playwright.projects.json": as_json(playwright_projects(tokens, front))}


def write_files(root, front, files):
    out = inside(root, front["out"])
    if out is None:
        raise Fail(f"front.out {front['out']!r} is outside the repository; set a repo-relative folder in "
                   f".claude/gw.json", 2)
    try:
        out.mkdir(parents=True, exist_ok=True)
        for name, text in sorted(files.items()):
            target = out / name
            data = text.encode("utf-8")
            if not target.is_file() or target.read_bytes() != data:
                tmp = out / f".{name}.tmp"
                try:
                    tmp.write_bytes(data)
                    os.replace(str(tmp), str(target))
                finally:  # a failed write or replace must not leave a stray file in a folder `generated` compares
                    if tmp.exists():
                        tmp.unlink()
    except OSError as exc:
        raise Fail(f"cannot write {front['out']}: {exc}; fix front.out in .claude/gw.json", 2)
    return [f"{front['out'].rstrip('/')}/{name}" for name in sorted(files)]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="front.py", description=__doc__.split("\n")[0])
    parser.add_argument("--root", help="project root (default: the repo of this script)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="validate the tokens JSON")
    sub.add_parser("generate", help="check, then write the generated files into front.out")
    args = parser.parse_args(argv)
    try:
        try:
            root = config.find_root(args.root)
            front = config.front(config.load(root))
        except config.ConfigError as exc:
            raise Fail(str(exc), 2)
        tokens = load_tokens(root, front)
        if tokens is None:
            return 0
        if args.cmd == "check":
            print(f"front: {front['tokens']} is valid ({len(tokens.leaves)} tokens, "
                  f"{len(tokens.breakpoints())} breakpoints)")
            return 0
        for path in write_files(root, front, generated_files(tokens, front)):
            print(f"front: wrote {path}")
        return 0
    except Fail as exc:
        print(f"front.py: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
