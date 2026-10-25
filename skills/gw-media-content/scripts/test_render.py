"""Tests of render.mjs and of the piece template (plantilla/). render.mjs is run with node as a child process: its
arguments and sizes through `--plan` (no Playwright, no ImageMagick), its fail-closed messages with a folder where
Playwright or ImageMagick are missing, its output names with a stub Playwright and a stub `magick`, and, when
Playwright, Chromium and ImageMagick are installed, with the real ones. The template is checked against
comprobar.py. Run: python3 -m unittest discover -s skills/gw-media-content/scripts"""
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comprobar  # noqa: E402

RENDER = AQUI / "render.mjs"
PLANTILLA = AQUI.parent / "plantilla"
NODE = shutil.which("node")
SIN_NODE = "node is not installed; render.mjs is run with node (install it from nodejs.org)"


def webp(ancho=100, alto=50):
    """The same minimal WebP header that test_comprobar.py builds: enough for the size check."""
    cuerpo = b"WEBPVP8X" + (10).to_bytes(4, "little") + bytes(4) + (ancho - 1).to_bytes(3, "little") + (alto - 1).to_bytes(3, "little")
    return b"RIFF" + len(cuerpo).to_bytes(4, "little") + cuerpo


def png_valido(ancho=8, alto=8):
    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))
    filas = b"".join(b"\x00" + b"\x40\x80\xc0" * ancho for _ in range(alto))
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(filas)) + trozo(b"IEND", b""))


def ejecutable(ruta: Path, texto: str):
    ruta.write_text(texto, encoding="utf-8")
    ruta.chmod(ruta.stat().st_mode | stat.S_IXUSR)


# A `magick` that says it knows WebP and creates its last argument (the output), logging its arguments.
MAGICK = """#!/bin/sh
if [ "$1" = "-list" ]; then echo "WEBP  rw"; exit 0; fi
echo "$@" >> "$MAGICK_LOG"
for last; do :; done
# the stub only creates the output (the tests run with an empty PATH, so no cp or cat)
: > "$last"
"""
# A Playwright with just what render.mjs calls. GW_STUB_BROKEN lists broken images, GW_STUB_OVERFLOW overflows.
PLAYWRIGHT = """
const fs = require('fs');
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
exports.chromium = { launch: async () => {
  if (process.env.GW_STUB_NO_CHROMIUM) throw new Error('Executable does not exist at /nowhere\\nsecond line');
  return { close: async () => {}, newPage: async (opciones) => {
    let llamadas = 0;
    return {
      goto: async () => {},
      evaluate: async () => (++llamadas === 1 ? (process.env.GW_STUB_BROKEN ? ['rota.png'] : []) : !!process.env.GW_STUB_OVERFLOW),
      screenshot: async ({ path, clip }) => {
        fs.writeFileSync(path, png);
        fs.appendFileSync(process.env.GW_STUB_LOG, JSON.stringify({ clip, viewport: opciones.viewport, scale: opciones.deviceScaleFactor }) + '\\n');
      },
      pdf: async ({ path, width, height }) => fs.writeFileSync(path, '%PDF-1.4 ' + width + 'x' + height),
      locator: () => ({ count: async () => Number(process.env.GW_STUB_SLIDES ?? 3) }),
      close: async () => {},
    };
  } };
} };
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.fecha = self.tmp / "2026-10-25"
        self.pieza = self.fecha / "01-prueba"
        (self.pieza / "medios" / "fuente").mkdir(parents=True)
        self.vacio = self.tmp / "vacio"
        self.vacio.mkdir()

    def fuente(self, nombre, texto="<p>ok</p>", pieza=None):
        ruta = (pieza or self.pieza) / "medios" / "fuente" / nombre
        ruta.write_text(texto, encoding="utf-8") if isinstance(texto, str) else ruta.write_bytes(texto)

    def render(self, *args, cwd=None, env=None, path=None):
        """Runs render.mjs; PATH holds only `path` (an empty folder by default) and HOME is the tempdir, so what the
        run finds is what the test put there."""
        e = {"PATH": str(path or self.vacio), "HOME": str(self.tmp), "MAGICK_LOG": str(self.tmp / "magick.log"),
             "GW_STUB_LOG": str(self.tmp / "stub.log")}
        e.update(env or {})
        return subprocess.run([NODE, str(RENDER), *map(str, args)], capture_output=True, text=True, cwd=cwd or self.tmp, env=e)

    def plan(self, *args):
        r = self.render("--plan", *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def falso_playwright(self):
        carpeta = self.tmp / "node_modules" / "playwright"
        carpeta.mkdir(parents=True)
        (carpeta / "package.json").write_text('{"name": "playwright", "main": "index.js"}')
        (carpeta / "index.js").write_text(PLAYWRIGHT)

    def falso_magick(self):
        bin_ = self.tmp / "bin"
        bin_.mkdir()
        ejecutable(bin_ / "magick", MAGICK)
        return bin_


@unittest.skipUnless(NODE, SIN_NODE)
class Argumentos(Base):
    def test_sin_argumentos_es_un_error_de_uso(self):
        r = self.render()
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage: node render.mjs", r.stderr)

    def test_ayuda(self):
        r = self.render("--help")
        self.assertEqual((r.returncode, "usage: node render.mjs" in r.stdout), (0, True))

    def test_opcion_desconocida(self):
        r = self.render("--rapido", self.pieza)
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown option --rapido", r.stderr)

    def test_carpeta_que_no_existe(self):
        r = self.render("--plan", self.tmp / "nada")
        self.assertEqual(r.returncode, 1)
        self.assertIn("is not a folder", r.stderr)

    def test_carpeta_sin_fuentes(self):
        r = self.render("--plan", self.vacio)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no medios/fuente/", r.stderr)

    def test_fuente_vacia(self):
        r = self.render("--plan", self.pieza)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no source (.html, .svg, .png or .jpg)", r.stderr)

    def test_tamano_por_defecto_y_salidas(self):
        self.fuente("tarjeta.html")
        (f,) = self.plan(self.pieza)[0]["fuentes"]
        self.assertEqual((f["fuente"], f["tipo"], f["tamano"]), ("tarjeta.html", "pagina", {"width": 1200, "height": 675}))
        self.assertEqual([Path(s).name for s in f["salidas"]], ["tarjeta.webp", "tarjeta-mini.webp", "tarjeta.png"])

    def test_tamano_de_la_etiqueta_gw_size(self):
        self.fuente("a.html", '<meta charset="utf-8">\n<meta name="gw-size" content="1080x1350">')
        self.assertEqual(self.plan(self.pieza)[0]["fuentes"][0]["tamano"], {"width": 1080, "height": 1350})

    def test_tamano_de_un_svg_en_un_comentario(self):
        self.fuente("logo.svg", "<!-- gw-size: 800x400 --><svg xmlns='http://www.w3.org/2000/svg'/>")
        self.assertEqual(self.plan(self.pieza)[0]["fuentes"][0]["tamano"], {"width": 800, "height": 400})

    def test_tamano_fuera_de_rango(self):
        self.fuente("a.html", '<meta name="gw-size" content="50x50">')
        r = self.render("--plan", self.pieza)
        self.assertEqual(r.returncode, 1)
        self.assertIn("gw-size 50x50 is out of range", r.stderr)

    def test_el_carrusel_sale_en_pdf(self):
        self.fuente("carrusel-version.html", '<meta name="gw-size" content="1080x1350">')
        (f,) = self.plan(self.pieza)[0]["fuentes"]
        self.assertEqual((f["tipo"], [Path(s).name for s in f["salidas"]]), ("pdf", ["carrusel-version.pdf"]))

    def test_una_captura_sale_en_webp_y_png(self):
        self.fuente("pantalla.jpg", b"\xff\xd8\xff")
        (f,) = self.plan(self.pieza)[0]["fuentes"]
        self.assertEqual((f["tipo"], f["tamano"], len(f["salidas"])), ("captura", None, 3))

    def test_otros_archivos_no_son_fuentes(self):
        self.fuente("tarjeta.html")
        self.fuente("notas.txt", "x")
        self.assertEqual([f["fuente"] for f in self.plan(self.pieza)[0]["fuentes"]], ["tarjeta.html"])

    def test_dos_fuentes_con_el_mismo_nombre(self):
        self.fuente("a.html")
        self.fuente("a.png", b"x")
        r = self.render("--plan", self.pieza)
        self.assertEqual(r.returncode, 1)
        self.assertIn("would both give medios/a.*", r.stderr)

    def test_pedir_una_fuente(self):
        self.fuente("a.html")
        self.fuente("b.html")
        self.assertEqual([f["fuente"] for f in self.plan(self.pieza, "medios/fuente/b.html")[0]["fuentes"]], ["b.html"])

    def test_pedir_una_fuente_que_no_existe(self):
        self.fuente("a.html")
        r = self.render("--plan", self.pieza, "z.html")
        self.assertEqual(r.returncode, 1)
        self.assertIn("z.html is not a source", r.stderr)

    def test_la_carpeta_de_fecha_expande_a_sus_piezas(self):
        otra = self.fecha / "02-otra"
        (otra / "medios" / "fuente").mkdir(parents=True)
        self.fuente("a.html")
        self.fuente("b.html", pieza=otra)
        (self.fecha / "03-sin-medios").mkdir()
        self.assertEqual([Path(p["pieza"]).name for p in self.plan(self.fecha)], ["01-prueba", "02-otra"])


@unittest.skipUnless(NODE, SIN_NODE)
class FallaCerrado(Base):
    def test_sin_playwright(self):
        self.fuente("tarjeta.html")
        r = self.render(self.pieza, path=self.falso_magick())
        self.assertEqual(r.returncode, 1)
        self.assertIn("Playwright not found", r.stderr)
        self.assertIn("npm i -D playwright && npx playwright install chromium", r.stderr)
        self.assertFalse((self.pieza / "medios" / "tarjeta.webp").exists())

    def test_playwright_se_busca_tambien_en_gw_playwright_dir(self):
        self.fuente("tarjeta.html")
        otro = self.tmp / "otro"
        (otro / "node_modules" / "playwright").mkdir(parents=True)
        (otro / "node_modules" / "playwright" / "package.json").write_text('{"name": "playwright", "main": "index.js"}')
        (otro / "node_modules" / "playwright" / "index.js").write_text(PLAYWRIGHT)
        r = self.render(self.pieza, path=self.falso_magick(), env={"GW_PLAYWRIGHT_DIR": str(otro)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.pieza / "medios" / "tarjeta.webp").is_file())

    def test_sin_imagemagick(self):
        self.fuente("tarjeta.html")
        self.falso_playwright()
        r = self.render(self.pieza)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ImageMagick with WebP support not found", r.stderr)
        self.assertIn("apt install imagemagick webp", r.stderr)
        self.assertIn("brew install imagemagick webp", r.stderr)

    def test_imagemagick_sin_webp(self):
        self.fuente("tarjeta.html")
        self.falso_playwright()
        bin_ = self.tmp / "bin"
        bin_.mkdir()
        ejecutable(bin_ / "magick", '#!/bin/sh\necho "PNG  rw"\n')
        r = self.render(self.pieza, path=bin_)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ImageMagick with WebP support not found", r.stderr)

    def test_un_carrusel_solo_necesita_playwright(self):
        self.fuente("carrusel.html")
        self.falso_playwright()
        r = self.render(self.pieza)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.pieza / "medios" / "carrusel.pdf").is_file())

    def test_una_captura_solo_necesita_imagemagick(self):
        self.fuente("pantalla.png", b"png")
        r = self.render(self.pieza, path=self.falso_magick())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(p.name for p in (self.pieza / "medios").glob("*.*")), ["pantalla-mini.webp", "pantalla.png", "pantalla.webp"])

    def test_chromium_sin_instalar(self):
        self.fuente("tarjeta.html")
        self.falso_playwright()
        r = self.render(self.pieza, path=self.falso_magick(), env={"GW_STUB_NO_CHROMIUM": "1"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot start Chromium (Executable does not exist at /nowhere)", r.stderr)
        self.assertIn("npx playwright install chromium", r.stderr)


@unittest.skipUnless(NODE, SIN_NODE)
class ConPlaywrightFalso(Base):
    """Output names, sizes and error handling with a stub Playwright and a stub magick."""

    def setUp(self):
        super().setUp()
        self.falso_playwright()
        self.bin = self.falso_magick()

    def test_una_pagina_da_webp_mini_y_png(self):
        self.fuente("tarjeta.html", '<meta name="gw-size" content="1200x675">')
        r = self.render(self.pieza, path=self.bin)
        self.assertEqual(r.returncode, 0, r.stderr)
        medios = self.pieza / "medios"
        for n in ("tarjeta.webp", "tarjeta-mini.webp", "tarjeta.png"):
            self.assertTrue((medios / n).is_file(), n)
        log = (self.tmp / "magick.log").read_text().splitlines()
        self.assertEqual([("-resize 1600x>" in l, "-resize 720x>" in l, "-quality" in l) for l in log],
                         [(True, False, True), (False, True, True), (True, False, False)])

    def test_el_tamano_de_la_etiqueta_llega_a_la_captura(self):
        self.fuente("a.html", '<meta name="gw-size" content="1000x500">')
        r = self.render(self.pieza, path=self.bin)
        self.assertEqual(r.returncode, 0, r.stderr)
        visto = json.loads((self.tmp / "stub.log").read_text().splitlines()[0])
        tam = {"width": 1000, "height": 500}
        self.assertEqual((visto["viewport"], visto["clip"], visto["scale"]), (tam, {"x": 0, "y": 0, **tam}, 1))

    def test_el_carrusel_da_un_pdf_a_su_tamano(self):
        self.fuente("carrusel.html", '<meta name="gw-size" content="1080x1350">')
        r = self.render(self.pieza, path=self.bin)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.pieza / "medios" / "carrusel.pdf").read_text(), "%PDF-1.4 1080pxx1350px")
        self.assertIn("(3 pages", r.stdout)
        self.assertFalse((self.pieza / "medios" / "carrusel.webp").exists())

    def test_un_carrusel_sin_slides_falla(self):
        self.fuente("carrusel.html")
        r = self.render(self.pieza, path=self.bin, env={"GW_STUB_SLIDES": "0"})
        self.assertEqual(r.returncode, 1)
        self.assertIn('no <section class="slide">', r.stderr)

    def test_una_imagen_rota_falla_y_no_deja_salida(self):
        self.fuente("a.html")
        r = self.render(self.pieza, path=self.bin, env={"GW_STUB_BROKEN": "1"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("image(s) that do not load: rota.png", r.stderr)
        self.assertFalse((self.pieza / "medios" / "a.webp").exists())

    def test_el_contenido_que_desborda_falla(self):
        self.fuente("a.html")
        r = self.render(self.pieza, path=self.bin, env={"GW_STUB_OVERFLOW": "1"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("the content overflows 1200x675", r.stderr)

    def test_un_fallo_no_impide_renderizar_el_resto(self):
        self.fuente("a.html")
        self.fuente("pantalla.png", b"png")
        r = self.render(self.pieza, path=self.bin, env={"GW_STUB_OVERFLOW": "1"})
        self.assertEqual(r.returncode, 1)
        self.assertTrue((self.pieza / "medios" / "pantalla.webp").is_file())

    def test_la_carpeta_de_fecha_renderiza_cada_pieza(self):
        otra = self.fecha / "02-otra"
        (otra / "medios" / "fuente").mkdir(parents=True)
        self.fuente("a.html")
        self.fuente("b.html", pieza=otra)
        r = self.render(self.fecha, path=self.bin)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.pieza / "medios" / "a.webp").is_file())
        self.assertTrue((otra / "medios" / "b.webp").is_file())


def hay_render_real():
    """(True, '') when Playwright and ImageMagick with WebP are installed; otherwise (False, reason)."""
    if not NODE:
        return False, SIN_NODE
    dir_pw = os.environ.get("GW_PLAYWRIGHT_DIR")
    ok = subprocess.run([NODE, "-e", "require(require.resolve('playwright', {paths: [process.cwd(), process.env.GW_PLAYWRIGHT_DIR || '.']}))"],
                        capture_output=True, cwd=dir_pw or os.getcwd())
    if ok.returncode:
        return False, "Playwright is not installed (npm i -D playwright && npx playwright install chromium); the real render needs it"
    for orden in ("magick", "convert"):
        if shutil.which(orden):
            try:
                if "WEBP" in subprocess.run([orden, "-list", "format"], capture_output=True, text=True).stdout:
                    return True, ""
            except OSError:
                pass
    return False, "ImageMagick with WebP support is not installed; the real render needs it"


def rellenar(texto: str) -> str:
    """Fixture filler: the template's placeholders become valid text (a date for AAAA-MM-DD, a number for JSON)."""
    texto = texto.replace("AAAA-MM-DD", "2026-10-25").replace("<tema>", "prueba")
    texto = texto.replace("{{número}}", "5").replace("{{antes.png}}", "antes.png").replace("{{despues.png}}", "despues.png")
    return re.sub(r"\{\{[^}]*\}\}", "texto de prueba", texto)


class Plantilla(Base):
    def copiar(self):
        destino = self.tmp / "difusion" / "2026-10-25" / "01-prueba"
        shutil.copytree(PLANTILLA, destino)
        return destino

    def test_la_plantilla_tiene_todo(self):
        esperados = {"ficha.md", "x.md", "reddit.md", "linkedin.md", "discord.md"}
        self.assertEqual({p.name for p in PLANTILLA.glob("*.md")}, esperados)
        fuentes = {p.name for p in (PLANTILLA / "medios" / "fuente").glob("*.html")}
        self.assertEqual(fuentes, {"tarjeta.html", "diagrama.html", "metricas.html", "cita.html", "codigo.html", "antes-despues.html", "carrusel.html"})

    def test_cada_fuente_declara_su_tamano_y_es_autonoma(self):
        for f in (PLANTILLA / "medios" / "fuente").glob("*.html"):
            t = f.read_text(encoding="utf-8")
            m = re.search(r'<meta name="gw-size" content="(\d+)x(\d+)">', t)
            self.assertTrue(m, f"{f.name}: no gw-size")
            esperado = ("1080", "1350") if f.name.startswith("carrusel") else ("1200", "675")
            self.assertEqual(m.groups(), esperado, f.name)
            self.assertNotRegex(t, r"(?i)(src|href)=[\"']https?:|@import|<link\b", f"{f.name}: needs the network")
            self.assertIn("--fondo:", t, f"{f.name}: palette variables")
            self.assertNotIn("{{", t.split("</head>")[0], f"{f.name}: a gap in the head (the comments must not hold braces)")

    def test_los_huecos_de_la_plantilla_en_bruto(self):
        pieza = self.copiar()
        problemas = comprobar.comprobar(pieza)
        con_hueco = {p.split(":")[0] for p in problemas if "template gap «" in p}
        self.assertEqual(con_hueco, {"ficha.md", "x.md", "reddit.md", "linkedin.md", "discord.md"})
        huecos_html = {p.split(":")[0].split("/")[-1] for p in problemas if "template gaps {{…}} left" in p}
        self.assertEqual(len(huecos_html), 7, problemas)
        # nothing else is wrong with the raw template: the rest is the renders that do not exist yet
        otros = [p for p in problemas if "template gap" not in p and "does not exist" not in p and "not rendered" not in p]
        # the date line is the same gap seen by the Reddit check
        otros = [p for p in otros if "«Normas leídas:» «AAAA-MM-DD»" not in p]
        self.assertEqual(otros, [])

    def test_la_plantilla_rellena_pasa_comprobar(self):
        pieza = self.copiar()
        medios = pieza / "medios"
        for f in list(pieza.glob("*.md")) + list((medios / "fuente").glob("*.html")):
            f.write_text(rellenar(f.read_text(encoding="utf-8")), encoding="utf-8")
        for f in (medios / "fuente").glob("*.html"):  # a user keeps only the sources the piece uses
            if f.name != "tarjeta.html":
                f.unlink()
        (medios / "tarjeta.webp").write_bytes(webp())
        (medios / "tarjeta-mini.webp").write_bytes(webp(10, 5))
        (medios / "tarjeta.png").write_bytes(png_valido(100, 50))
        self.assertEqual(comprobar.comprobar(pieza), [])

    def test_el_alt_de_la_plantilla_pide_los_dos_idiomas(self):
        pieza = self.copiar()
        (pieza / "ficha.md").write_text(rellenar((pieza / "ficha.md").read_text(encoding="utf-8")).replace("/ en: texto de prueba", "", 1), encoding="utf-8")
        self.assertIn("has no alt text in «en»", "\n".join(comprobar.comprobar(pieza)))


@unittest.skipUnless(*hay_render_real())
class RenderReal(Base):
    def test_las_plantillas_rellenas_se_renderizan(self):
        pieza = self.tmp / "difusion" / "2026-10-25" / "01-prueba"
        shutil.copytree(PLANTILLA / "medios", pieza / "medios")
        for f in (pieza / "medios" / "fuente").glob("*.html"):
            t = rellenar(f.read_text(encoding="utf-8")).replace("texto de prueba</pre>", "const a = 1; // x</pre>")
            f.write_text(t, encoding="utf-8")
        for n in ("antes", "despues"):
            (pieza / "medios" / "fuente" / f"{n}.png").write_bytes(png_valido())
        env = dict(os.environ)
        r = subprocess.run([NODE, str(RENDER), str(pieza)], capture_output=True, text=True, env=env,
                           cwd=os.environ.get("GW_PLAYWRIGHT_DIR") or os.getcwd())
        if "cannot start Chromium" in r.stderr:
            self.skipTest("Chromium is not installed (npx playwright install chromium); the real render needs it")
        self.assertEqual(r.returncode, 0, r.stderr)
        medios = pieza / "medios"
        for n in ("tarjeta", "diagrama", "metricas", "cita", "codigo", "antes-despues"):
            for sufijo in (".webp", "-mini.webp", ".png"):
                self.assertTrue((medios / f"{n}{sufijo}").is_file(), n + sufijo)
        self.assertEqual(comprobar.dimensiones(medios / "tarjeta.webp"), (1200, 675))
        self.assertEqual(comprobar.dimensiones(medios / "tarjeta-mini.webp")[0], 720)
        self.assertEqual(comprobar.dimensiones(medios / "tarjeta.png")[0], 1200)
        self.assertEqual(comprobar.paginas_pdf(medios / "carrusel.pdf"), 4)


if __name__ == "__main__":
    unittest.main()
