"""scripts/mkt-sheet.py: Markdown sheets -> A4 HTML and PDF, and the check that keeps the three in step."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("mkt_sheet", ROOT / "scripts" / "mkt-sheet.py")
mkt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mkt)

GW = {"version": "0.1.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main", "pushToProtected": "pr",
      "check": ["make check"], "reviewMark": "docs/reviewed.txt", "content": ["^docs/"]}
SHEET = "# My *sheet*\n\nHello **world** & <b>.\n\n- one\n- two\n"


def run(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mkt.main(list(args), root=root)
    return code, out.getvalue(), err.getvalue()


class Convert(unittest.TestCase):
    def body(self, md):
        return mkt.convert(md)[0]

    def test_headings_and_title(self):
        body, title = mkt.convert("# Top `x`\n## Two\n### Three\n#### Four\n")
        self.assertEqual(title, "Top x")
        self.assertIn("<h1>Top <code>x</code></h1>", body)
        self.assertIn("<h2>Two</h2>", body)
        self.assertIn("<h3>Three</h3>", body)
        self.assertNotIn("<h4>", body)  # beyond ### it is plain text
        self.assertEqual(mkt.convert("no heading")[1], "")

    def test_paragraphs_join_lines(self):
        self.assertEqual(self.body("a\nb\n\nc"), "<p>a b</p>\n<p>c</p>")

    def test_inline(self):
        self.assertEqual(self.body("**b** *e* `c` [t](https://x.io/a?b=1&c=2)"),
                         '<p><strong>b</strong> <em>e</em> <code>c</code> '
                         '<a href="https://x.io/a?b=1&amp;c=2">t</a></p>')

    def test_code_is_not_formatted(self):
        self.assertEqual(self.body("`**no** <i>`"), "<p><code>**no** &lt;i&gt;</code></p>")

    def test_escaping(self):
        self.assertEqual(self.body("<script>alert(1)</script> & \"q\""),
                         "<p>&lt;script&gt;alert(1)&lt;/script&gt; &amp; \"q\"</p>")
        self.assertNotIn("<a ", self.body("[x](javascript:alert(1))"))
        self.assertNotIn("<script", self.body("# <script>"))

    def test_lists(self):
        self.assertEqual(self.body("- a\n- b *c*\n"), "<ul><li>a</li><li>b <em>c</em></li></ul>")
        self.assertEqual(self.body("1. a\n2. b\n  wrapped\n"), "<ol><li>a</li><li>b wrapped</li></ol>")
        self.assertEqual(self.body("para\n- a\n"), "<p>para</p>\n<ul><li>a</li></ul>")

    def test_rule(self):
        self.assertEqual(self.body("a\n\n---\n\nb"), "<p>a</p>\n<hr>\n<p>b</p>")

    def test_table(self):
        body = self.body("| A | B |\n|---|--:|\n| 1 | **2** |\n| x \\| y | 3 |\n\nafter")
        self.assertIn("<th>A</th><th style=\"text-align:right\">B</th>", body)
        self.assertIn("<td>1</td><td style=\"text-align:right\"><strong>2</strong></td>", body)
        self.assertIn("<td>x | y</td>", body)
        self.assertTrue(body.endswith("<p>after</p>"))

    def test_pipe_line_without_separator_is_a_paragraph(self):
        self.assertEqual(self.body("a | b"), "<p>a | b</p>")

    def test_page_is_self_contained_a4(self):
        page = mkt.render_page(SHEET.encode(), "es")
        self.assertIn('<html lang="es">', page)
        self.assertIn("<title>My sheet</title>", page)
        self.assertIn("@page { size: A4;", page)
        for external in ("http://", "https://", "<script", "<link"):
            self.assertNotIn(external, page)
        self.assertRegex(page, r"<body>\n<!-- mkt-sheet source-sha256: [0-9a-f]{64} -->\n")
        self.assertEqual(page, mkt.render_page(SHEET.encode(), "es"))  # deterministic


class Pages(unittest.TestCase):
    def test_counts_page_objects_not_pages_tree(self):
        pdf = (b"%PDF-1.4\n1 0 obj\n<</Type /Pages /Count 2 /Kids [2 0 R 3 0 R]>>\nendobj\n"
               b"2 0 obj\n<</Type /Page /Parent 1 0 R>>\nendobj\n3 0 obj\n<< /Type/Page /Parent 1 0 R >>\nendobj\n"
               b"%%EOF")
        self.assertEqual(mkt.count_pages(pdf), 2)
        self.assertEqual(mkt.count_pages(b"%PDF-1.4\n<</Type /Pages>>"), 0)


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / "docs" / "es").mkdir(parents=True)
        (self.tmp / "docs" / "es" / "a.md").write_text(SHEET, encoding="utf-8")
        self.config()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def config(self, **sheets):
        conf = dict(GW)
        conf["marketingSheets"] = dict({"sources": ["docs/es/a.md"], "outDir": "docs/mkt", "maxPages": 1}, **sheets)
        (self.tmp / ".claude").mkdir(exist_ok=True)
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(conf))

    def fake_pdf(self):
        pdf = self.tmp / "docs" / "mkt" / "es" / "a.pdf"
        pdf.write_text("%PDF-1.4\n<</Type /Page>>")
        pdf.with_suffix(".pdf.sha").write_text(mkt.sha256((self.tmp / "docs/mkt/es/a.html").read_bytes()) + "\n")


class BuildCheck(Project):
    def test_off_without_sources(self):
        self.config(sources=[])
        for cmd in ("build", "pdf", "check"):
            code, out, _ = run(self.tmp, cmd)
            self.assertEqual(code, 0)
            self.assertIn("off: marketingSheets.sources is empty", out)
        self.assertFalse((self.tmp / "docs" / "mkt").exists())

    def test_default_config_is_off(self):
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(GW))
        self.assertIn("are off", run(self.tmp, "check")[1])

    def test_build_writes_html_under_the_language_folder(self):
        code, out, _ = run(self.tmp, "build")
        self.assertEqual(code, 0)
        self.assertIn("built docs/mkt/es/a.html", out)
        page = (self.tmp / "docs" / "mkt" / "es" / "a.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="es">', page)
        self.assertIn(mkt.sha256(SHEET.encode()), page)

    def test_check_missing_html(self):
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("missing docs/mkt/es/a.html; run: python3 scripts/mkt-sheet.py build", err)

    def test_check_missing_pdf_and_sidecar(self):
        run(self.tmp, "build")
        _, _, err = run(self.tmp, "check")
        self.assertIn("missing docs/mkt/es/a.pdf; run: python3 scripts/mkt-sheet.py pdf", err)
        (self.tmp / "docs/mkt/es/a.pdf").write_text("x")
        _, _, err = run(self.tmp, "check")
        self.assertIn("missing docs/mkt/es/a.pdf.sha", err)
        self.assertIn("run: python3 scripts/mkt-sheet.py pdf", err)

    def test_check_ok(self):
        run(self.tmp, "build")
        self.fake_pdf()
        code, out, err = run(self.tmp, "check")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("presentation sheets ok (1 sheet(s))", out)

    def test_check_stale_html_after_editing_the_source(self):
        run(self.tmp, "build")
        self.fake_pdf()
        (self.tmp / "docs/es/a.md").write_text(SHEET + "\nmore\n", encoding="utf-8")
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("stale docs/mkt/es/a.html: it was not built from the current docs/es/a.md; "
                      "run: python3 scripts/mkt-sheet.py build", err)

    def test_check_stale_pdf_after_rebuilding_a_changed_html(self):
        run(self.tmp, "build")
        self.fake_pdf()
        (self.tmp / "docs/es/a.md").write_text(SHEET + "\nmore\n", encoding="utf-8")
        run(self.tmp, "build")
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("stale docs/mkt/es/a.pdf: it was not printed from the current docs/mkt/es/a.html; "
                      "run: python3 scripts/mkt-sheet.py pdf", err)

    def test_missing_source_names_it(self):
        (self.tmp / "docs/es/a.md").unlink()
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("missing source docs/es/a.md", err)
        code, _, err = run(self.tmp, "build")
        self.assertEqual(code, 1)
        self.assertIn("docs/es/a.md is listed in marketingSheets.sources but does not exist", err)

    def test_unreadable_config_fails_closed(self):
        (self.tmp / ".claude" / "gw.json").write_text("{nope")
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("cannot read the config", err)
        self.config(maxPages=0)
        self.assertIn("maxPages", run(self.tmp, "check")[2])
        self.config(sources=["/abs.md"])
        self.assertEqual(run(self.tmp, "check")[0], 1)

    def test_source_without_a_language_folder(self):
        (self.tmp / "top.md").write_text("# T\n")
        self.config(sources=["top.md"])
        code, _, err = run(self.tmp, "build")
        self.assertEqual(code, 1)
        self.assertIn("no language folder", err)

    def test_usage(self):
        self.assertEqual(run(self.tmp, "nope")[0], 2)


def playwright_resolves():
    try:
        return subprocess.run(["node", "-e", "require.resolve('playwright')"], capture_output=True,
                              cwd=str(ROOT)).returncode == 0
    except OSError:
        return False


class Pdf(Project):
    def test_playwright_not_found_message(self):
        if not shutil.which("node"):
            self.skipTest("node not installed")
        run(self.tmp, "build")
        saved = {k: os.environ.get(k) for k in ("NODE_PATH", "GW_PLAYWRIGHT_DIR")}
        os.environ["NODE_PATH"] = ""
        os.environ.pop("GW_PLAYWRIGHT_DIR", None)
        try:
            code, _, err = run(self.tmp, "pdf")
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(code, 1)
        self.assertIn("Playwright not found", err)
        self.assertIn("npm i -D playwright && npx playwright install chromium", err)
        self.assertIn("GW_PLAYWRIGHT_DIR", err)
        self.assertFalse((self.tmp / "docs/mkt/es/a.pdf").exists())

    def test_pdf_needs_a_current_html(self):
        code, _, err = run(self.tmp, "pdf")
        self.assertEqual(code, 1)
        self.assertIn("missing docs/mkt/es/a.html; run: python3 scripts/mkt-sheet.py build", err)

    @unittest.skipUnless(playwright_resolves(), "Playwright does not resolve here")
    def test_real_print_one_page_then_check_ok_then_too_long(self):
        run(self.tmp, "build")
        code, out, err = run(self.tmp, "pdf")
        self.assertEqual((code, err), (0, ""), err)
        self.assertIn("printed docs/mkt/es/a.pdf (1 page(s))", out)
        self.assertTrue((self.tmp / "docs/mkt/es/a.pdf").read_bytes().startswith(b"%PDF"))
        self.assertEqual(run(self.tmp, "check")[0], 0)
        (self.tmp / "docs/es/a.md").write_text(SHEET + "\n".join(f"Paragraph {n}.\n" for n in range(120)),
                                               encoding="utf-8")
        run(self.tmp, "build")
        (self.tmp / "docs/mkt/es/a.pdf").unlink()
        code, _, err = run(self.tmp, "pdf")
        self.assertEqual(code, 1)
        self.assertRegex(err, r"docs/mkt/es/a\.pdf would have \d+ pages, over maxPages 1")
        self.assertFalse((self.tmp / "docs/mkt/es/a.pdf").exists())


def fake_node(fake):
    """Patch the print step only: `fake(cmd, **kwargs)` answers the node call, every other command runs for real."""
    real = subprocess.run

    def dispatch(cmd, **kwargs):
        return fake(cmd, **kwargs) if cmd and cmd[0] == "node" else real(cmd, **kwargs)
    stack = contextlib.ExitStack()
    stack.enter_context(mock.patch.object(mkt.subprocess, "run", dispatch))
    stack.enter_context(mock.patch.object(mkt.shutil, "which", lambda name: "node"))
    return stack


class Review(Project):
    """Findings of the A10 review: each one with the reason it must fail."""

    def test_partial_marketing_sheets_object_takes_defaults(self):
        (self.tmp / ".claude" / "gw.json").write_text(json.dumps(dict(GW, marketingSheets={"sources": ["docs/es/a.md"]})))
        code, out, err = run(self.tmp, "build")
        self.assertEqual((code, err), (0, ""), err)
        self.assertTrue((self.tmp / "docs/mkt/es/a.html").is_file())

    def test_config_helper_fills_inner_defaults(self):
        conf = mkt.config.marketing_sheets({"marketingSheets": {"maxPages": 2}})
        self.assertEqual(conf, {"sources": [], "outDir": "docs/mkt", "maxPages": 2, "css": "", "timeout": 120})
        self.assertEqual(mkt.config.marketing_sheets({})["outDir"], "docs/mkt")

    def test_zero_counted_pages_is_an_error_not_a_pass(self):
        run(self.tmp, "build")

        def fake_run(cmd, **kwargs):
            for _html, out in json.loads(cmd[-1]):
                Path(out).write_bytes(b"%PDF-1.7\n1 0 obj\n<</Type /ObjStm>>\nendobj\n")
            return subprocess.CompletedProcess(cmd, 0, "", "")
        with fake_node(fake_run):
            code, _, err = run(self.tmp, "pdf")
        self.assertEqual(code, 1)
        self.assertIn("could not count pages in the printed docs/mkt/es/a.pdf", err)
        self.assertFalse((self.tmp / "docs/mkt/es/a.pdf").exists())

    def test_print_uses_a_file_url_and_waits_for_fonts(self):
        self.assertIn("pathToFileURL(htmlFile).href", mkt.NODE_PRINT)
        self.assertIn("document.fonts.ready", mkt.NODE_PRINT)

    @unittest.skipUnless(playwright_resolves(), "Playwright does not resolve here")
    def test_real_print_in_a_folder_with_space_and_hash(self):
        odd = self.tmp / "a b#c%d"
        odd.mkdir()
        shutil.move(str(self.tmp / "docs"), str(odd / "docs"))
        shutil.move(str(self.tmp / ".claude"), str(odd / ".claude"))
        subprocess.run(["git", "init", "-q", str(odd)], check=True)
        run(odd, "build")
        code, out, err = run(odd, "pdf")
        self.assertEqual((code, err), (0, ""), err)
        self.assertIn("(1 page(s))", out)

    def test_timeout_is_reported_with_the_key_that_raises_it(self):
        run(self.tmp, "build")
        self.config(timeout=7)

        def hang(cmd, **kwargs):
            self.assertEqual(kwargs["timeout"], 7)
            raise subprocess.TimeoutExpired(cmd, 7)
        with fake_node(hang):
            code, _, err = run(self.tmp, "pdf")
        self.assertEqual(code, 1)
        self.assertIn("printing took over 7 s", err)
        self.assertIn("marketingSheets.timeout", err)

    def test_node_that_cannot_start_is_reported(self):
        run(self.tmp, "build")

        def broken(cmd, **kwargs):
            raise PermissionError("denied")
        with fake_node(broken):
            code, _, err = run(self.tmp, "pdf")
        self.assertEqual(code, 1)
        self.assertIn("cannot run node (denied); install Node.js", err)

    def test_crlf_checkout_does_not_make_the_sheet_stale(self):
        run(self.tmp, "build")
        self.fake_pdf()
        src = self.tmp / "docs/es/a.md"
        src.write_bytes(src.read_bytes().replace(b"\n", b"\r\n"))
        html = self.tmp / "docs/mkt/es/a.html"
        html.write_bytes(html.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(mkt.sha256(b"a\r\nb"), mkt.sha256(b"a\nb"))
        code, _, err = run(self.tmp, "check")
        self.assertEqual((code, err), (0, ""), err)

    def test_repo_root_ignores_git_environment_of_a_hook(self):
        saved = {k: os.environ.get(k) for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
        os.environ["GIT_DIR"] = str(self.tmp / "nowhere")
        os.environ["GIT_WORK_TREE"] = str(self.tmp)
        try:
            root = mkt.repo_root()
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(root.resolve(), ROOT.resolve())

    def test_missing_git_is_an_error_with_a_fix(self):
        def nogit(cmd, **kwargs):
            raise FileNotFoundError("git")
        with mock.patch.object(mkt.subprocess, "run", nogit):
            with self.assertRaises(mkt.SheetError) as ctx:
                mkt.repo_root()
        self.assertIn("cannot run git to find the repo root", str(ctx.exception))
        self.assertIn("install git", str(ctx.exception))

    def test_bom_keeps_the_title_a_heading(self):
        page = mkt.render_page(b"\xef\xbb\xbf# Title\n\nText\n", "en")
        self.assertIn("<h1>Title</h1>", page)
        self.assertIn("<title>Title</title>", page)

    def test_invalid_utf8_source_names_the_file(self):
        (self.tmp / "docs/es/a.md").write_bytes(b"# T\n\n\xff\xfe bad\n")
        code, _, err = run(self.tmp, "build")
        self.assertEqual(code, 1)
        self.assertIn("docs/es/a.md is not UTF-8", err)
        self.assertNotIn("Traceback", err)

    def test_link_with_balanced_parentheses(self):
        page = mkt.render_page(b"# T\n\nSee [x](https://a.org/f_(1)) now.\n", "en")
        self.assertIn('<a href="https://a.org/f_(1)">x</a> now.', page)

    def test_link_scheme_hidden_behind_a_control_character_is_not_a_link(self):
        for target in ("\x01javascript:alert(1)", "java\tscript:alert(1)", "data:text/html,x", "vbscript:x"):
            page = mkt.render_page(f"# T\n\n[x]({target})\n".encode(), "en")
            self.assertNotIn("<a ", page, target)
            self.assertNotIn("href=", page.split("</style>")[1])
        page = mkt.render_page(b"# T\n\n[a](https://x.org) [b](mailto:a@b.c) [c](other.html) [d](#top)\n", "en")
        self.assertEqual(page.count("<a href="), 4)


class Style(Project):
    """marketingSheets.css: embedded stylesheet, rewritten url(...), and the check that notices it changed."""

    def style(self, text=None):
        (self.tmp / "docs" / "mkt" / "fonts").mkdir(parents=True, exist_ok=True)
        (self.tmp / "docs/mkt/style.css").write_text(
            text or '@font-face{font-family:X;src:url("fonts/x.woff2") format("woff2")}\nbody{color:#123456}\n'
            "i{background:url(https://a.org/i.png)}\n", encoding="utf-8")
        self.config(css="docs/mkt/style.css")

    def test_css_is_embedded_and_relative_urls_follow_the_html(self):
        self.style()
        self.config(css="docs/mkt/style.css", outDir="out")
        code, _, err = run(self.tmp, "build")
        self.assertEqual((code, err), (0, ""), err)
        page = (self.tmp / "out/es/a.html").read_text(encoding="utf-8")
        self.assertIn("color:#123456", page)
        self.assertIn('url("../../docs/mkt/fonts/x.woff2")', page)
        self.assertIn("url(https://a.org/i.png)", page)
        self.assertNotIn(mkt.CSS.strip()[:40], page)

    def test_check_detects_a_changed_stylesheet(self):
        self.style()
        run(self.tmp, "build")
        self.fake_pdf()
        self.assertEqual(run(self.tmp, "check")[0], 0)
        (self.tmp / "docs/mkt/style.css").write_text("body{color:#654321}\n", encoding="utf-8")
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("stale docs/mkt/es/a.html: the stylesheet (marketingSheets.css) or the converter changed", err)
        self.assertIn("run: python3 scripts/mkt-sheet.py build", err)

    def test_check_detects_a_changed_template(self):
        run(self.tmp, "build")
        self.fake_pdf()
        html = self.tmp / "docs/mkt/es/a.html"
        html.write_text(html.read_text(encoding="utf-8").replace("<style>", "<style>/* old template */"),
                        encoding="utf-8")
        code, _, err = run(self.tmp, "check")
        self.assertEqual(code, 1)
        self.assertIn("the stylesheet (marketingSheets.css) or the converter changed", err)

    def test_missing_stylesheet_names_the_key(self):
        run(self.tmp, "build")
        self.fake_pdf()
        self.config(css="docs/mkt/nope.css")
        for cmd in ("build", "check"):
            code, _, err = run(self.tmp, cmd)
            self.assertEqual(code, 1, cmd)
            self.assertIn("missing stylesheet: docs/mkt/nope.css (marketingSheets.css) does not exist", err)
            self.assertIn('set marketingSheets.css to ""', err)

    def test_stylesheet_that_is_not_utf8(self):
        self.style()
        (self.tmp / "docs/mkt/style.css").write_bytes(b"body{content:'\xff'}")
        code, _, err = run(self.tmp, "build")
        self.assertEqual(code, 1)
        self.assertIn("docs/mkt/style.css is not UTF-8", err)

    def test_schema_rejects_bad_css_and_timeout(self):
        schema = json.loads(mkt.config.schema_path().read_text(encoding="utf-8"))
        prop = schema["properties"]["marketingSheets"]
        for good in ({"css": ""}, {"css": "docs/mkt/style.css"}, {"timeout": 5}):
            self.assertEqual(mkt.config.validate(good, prop), [], good)
        for bad in ({"css": "../x.css"}, {"css": "/abs/x.css"}, {"css": "docs/x.txt"}, {"timeout": 0},
                    {"timeout": "9"}, {"unknown": 1}):
            self.assertNotEqual(mkt.config.validate(bad, prop), [], bad)

    def test_shipped_stylesheet_is_valid_and_its_fonts_exist(self):
        conf = json.loads((ROOT / ".claude" / "gw.json").read_text(encoding="utf-8"))["marketingSheets"]
        self.assertEqual(conf["css"], "docs/mkt/style.css")
        css = (ROOT / conf["css"]).read_text(encoding="utf-8")
        urls = mkt.CSS_URL.findall(css)
        self.assertTrue(urls)
        for _quote, url in urls:
            self.assertTrue((ROOT / "docs/mkt" / url).is_file(), url)
        self.assertNotRegex(css, r"border-radius|box-shadow|text-shadow|radial-gradient|blur\(")


if __name__ == "__main__":
    unittest.main()
