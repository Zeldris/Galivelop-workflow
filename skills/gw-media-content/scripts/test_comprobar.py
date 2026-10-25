"""Tests of comprobar.py: every case builds its own piece folder in a tempdir (a valid one) and breaks one thing;
each asserts the message, not only the result. Run: python3 -m unittest discover -s skills/gw-media-content/scripts"""
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comprobar  # noqa: E402

FICHA = """# Ficha: lanzamiento

Idiomas: es, en

## Canales

- x
- reddit
- linkedin
- discord

## Hechos

| Dato | Fuente |
|---|---|
| Sale la 1.0 | CHANGELOG.md |

## Reddit

- **Subreddit:** r/gamedev
- **Normas leídas:** 2026-10-25
- **Autopromoción:** solo los sábados

## Imágenes

| Imagen | Texto alternativo | Canales |
|---|---|---|
| `medios/tarjeta.webp` | es: Tarjeta de la versión / en: Release card | x, linkedin |

## Uso interno

Tarea QA-12 en la rama claude/algo.

## Publicado

| Canal | Idioma | Fecha | Enlace |
|---|---|---|---|
"""
CANALES = {
    "x": "## es\n\n**1/** Sale la versión.\nImagen: medios/tarjeta.webp\n\n**2/** Detalles.\n\n## en\n\n**1/** Release out.\n\n**2/** Details.\n",
    "reddit": "## es\n\n**Título:** Sale la versión\n\nTexto.\n\n## en\n\n**Title:** Release out\n\nText.\n",
    "linkedin": "## es\n\nTexto largo.\nImagen: medios/tarjeta.webp\n\n## en\n\nLong text.\n",
    "discord": "## es\n\n## Novedades\n\n## en\n\n## News\n",
}


def webp(ancho=100, alto=50, extra=0):
    cuerpo = b"WEBPVP8X" + struct.pack("<I", 10) + bytes(4) + (ancho - 1).to_bytes(3, "little") + (alto - 1).to_bytes(3, "little")
    return b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo + bytes(extra)


def png(ancho, alto):
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", ancho, alto) + b"\x08\x06\x00\x00\x00"


def pdf(paginas):
    return b"%PDF-1.4\n" + b"".join(b"%d 0 obj\n<< /Type /Page >>\nendobj\n" % i for i in range(paginas)) + b"%%EOF\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.carpeta = self.tmp / "2026-10-25" / "01-lanzamiento"
        (self.carpeta / "medios" / "fuente").mkdir(parents=True)
        self.escribir("ficha.md", FICHA)
        for c, t in CANALES.items():
            self.escribir(f"{c}.md", t)
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(webp())
        (self.carpeta / "medios" / "tarjeta-mini.webp").write_bytes(webp(10, 5))
        (self.carpeta / "medios" / "fuente" / "tarjeta.html").write_text("<p>ok</p>")
        self.reglas = comprobar.cargar_reglas()

    def escribir(self, nombre, texto):
        (self.carpeta / nombre).write_text(texto, encoding="utf-8")

    def cambiar(self, nombre, viejo, nuevo):
        t = (self.carpeta / nombre).read_text(encoding="utf-8")
        self.assertIn(viejo, t)
        self.escribir(nombre, t.replace(viejo, nuevo, 1))

    def fallos(self, reglas=None):
        return "\n".join(comprobar.comprobar(self.carpeta, reglas or self.reglas))

    def assertFallo(self, trozo, **kw):
        self.assertIn(trozo, self.fallos(**kw))


class Estructura(Base):
    def test_la_pieza_valida_pasa(self):
        self.assertEqual(self.fallos(), "")

    def test_cli_imprime_ok_y_sale_con_cero(self):
        r = subprocess.run([sys.executable, str(AQUI / "comprobar.py"), str(self.carpeta)], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "OK"))

    def test_cli_falla_con_una_linea_por_problema(self):
        self.cambiar("x.md", "**2/** Detalles.", "**2/** QA-12 {{hueco}}")
        r = subprocess.run([sys.executable, str(AQUI / "comprobar.py"), str(self.carpeta)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("internal jargon «QA-12»", r.stdout)
        self.assertIn("template gap «{{hueco}}»", r.stdout)

    def test_sin_argumentos_es_un_error_de_uso(self):
        r = subprocess.run([sys.executable, str(AQUI / "comprobar.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage:", r.stdout)

    def test_la_carpeta_de_fecha_expande_a_sus_piezas(self):
        self.assertEqual([p.name for p in comprobar.piezas(self.carpeta.parent)], ["01-lanzamiento"])

    def test_carpeta_vacia(self):
        vacia = self.tmp / "2026-10-26" / "02-vacia"
        vacia.mkdir(parents=True)
        out = "\n".join(comprobar.comprobar(vacia, self.reglas))
        self.assertIn("no ficha.md", out)
        self.assertIn("no channel file", out)

    def test_carpeta_que_no_existe(self):
        self.assertIn("does not exist", "\n".join(comprobar.comprobar(self.tmp / "nada", self.reglas)))

    def test_falta_la_ficha(self):
        (self.carpeta / "ficha.md").unlink()
        self.assertFallo("no ficha.md")

    def test_nombre_de_carpeta_incorrecto(self):
        malo = self.tmp / "ayer" / "tema"
        shutil.copytree(self.carpeta, malo)
        self.assertIn("folder name: expected <dir>/AAAA-MM-DD/NN-<tema>", "\n".join(comprobar.comprobar(malo, self.reglas)))

    def test_ficha_sin_publicado(self):
        self.cambiar("ficha.md", "## Publicado", "## Otro")
        self.assertFallo("no «## Publicado» section")

    def test_ficha_sin_canales(self):
        self.cambiar("ficha.md", "## Canales", "## Otros")
        self.assertFallo("no channels under «## Canales»")

    def test_canal_pedido_sin_archivo(self):
        (self.carpeta / "discord.md").unlink()
        self.assertFallo("discord.md: listed under «## Canales» but missing")

    def test_canal_conocido_no_pedido(self):
        self.cambiar("ficha.md", "- discord\n", "")
        self.assertFallo("discord.md: channel not requested; delete the file")

    def test_canal_extra_listado_solo_pasa_las_comprobaciones_genericas(self):
        self.cambiar("ficha.md", "- discord\n", "- discord\n- portal\n")
        self.escribir("portal.md", "## es\n\n" + "a" * 5000 + "\n\n## en\n\nb\nImagen: medios/tarjeta.webp\n")
        self.assertEqual(self.fallos(), "")

    def test_canal_extra_listado_comprueba_idiomas_jerga_huecos_e_imagen(self):
        self.cambiar("ficha.md", "- discord\n", "- discord\n- portal\n")
        self.escribir("portal.md", "## es\n\nWIP: {{x}}\nImagen: medios/no.webp\n")
        out = self.fallos()
        self.assertIn("portal.md: no «## en» section", out)
        self.assertIn("portal.md: internal jargon «WIP:»", out)
        self.assertIn("portal.md: template gap «{{x}}»", out)
        self.assertIn("portal.md: «Imagen: medios/no.webp» does not exist", out)

    def test_canal_desconocido_sin_listar_es_error(self):
        self.escribir("portal.md", "## es\n\na\n\n## en\n\nb\n")
        self.assertFallo("portal.md: unknown channel file; list it under «## Canales» in ficha.md")

    def test_falta_un_idioma_en_un_canal(self):
        self.escribir("linkedin.md", "## es\n\nSolo español.\n")
        self.assertFallo("linkedin.md: no «## en» section")

    def test_idioma_que_no_esta_en_la_pieza(self):
        self.escribir("linkedin.md", CANALES["linkedin"] + "\n## gl\n\nGalego.\n")
        self.assertFallo("linkedin.md: language «gl» is not in the piece")

    def test_idiomas_se_deducen_si_la_ficha_no_los_declara(self):
        self.cambiar("ficha.md", "Idiomas: es, en\n", "")
        self.escribir("linkedin.md", "## es\n\nSolo español.\n")
        self.assertFallo("linkedin.md: no «## en» section")


class Texto(Base):
    def test_hueco_de_plantilla_en_la_ficha(self):
        self.cambiar("ficha.md", "Sale la 1.0", "{{dato}}")
        self.assertFallo("ficha.md: template gap «{{dato}}»")

    def test_hueco_de_plantilla_en_un_canal(self):
        self.cambiar("reddit.md", "Texto.", "{{texto}}")
        self.assertFallo("reddit.md: template gap «{{texto}}»")

    def test_hueco_de_plantilla_en_una_fuente(self):
        (self.carpeta / "medios" / "fuente" / "tarjeta.html").write_text("<p>{{titulo}}</p>")
        self.assertFallo("medios/fuente/tarjeta.html: template gaps")

    def test_jerga_interna_en_un_canal(self):
        for jerga in ("P3", "F12", "QA-215", "claude/rama-x", "WIP:"):
            with self.subTest(jerga=jerga):
                self.cambiar("linkedin.md", "Long text.", f"Long text {jerga}.")
                self.assertFallo(f"linkedin.md: internal jargon «{jerga}»")
                self.cambiar("linkedin.md", f"Long text {jerga}.", "Long text.")

    def test_la_jerga_permitida_no_salta(self):
        self.cambiar("linkedin.md", "Long text.", "Long text con GPT-4, UTF-8 y P2P.")
        self.assertEqual(self.fallos(), "")

    def test_la_jerga_de_la_ficha_se_permite_en_uso_interno(self):
        self.assertNotIn("QA-12", self.fallos())

    def test_x_cuenta_el_emoji_como_2(self):
        self.cambiar("x.md", "**1/** Sale la versión.", "**1/** " + "🙂" * 140)
        self.assertEqual(self.fallos(), "")
        self.cambiar("x.md", "🙂" * 140, "🙂" * 141)
        self.assertFallo("x.md (es) post 1: 282 weighted characters (max 280")

    def test_x_cuenta_la_url_como_23(self):
        url = "https://ejemplo.org/" + "a" * 100
        self.cambiar("x.md", "**1/** Sale la versión.", f"**1/** {url} " + "a" * 256)
        self.assertEqual(self.fallos(), "")
        self.cambiar("x.md", "a" * 256, "a" * 257)
        self.assertFallo("x.md (es) post 1: 281 weighted characters")

    def test_x_acentos_y_comillas_cuentan_1(self):
        self.assertEqual(comprobar.longitud_x("áéíóú“”—"), 8)
        self.assertEqual(comprobar.longitud_x("日本"), 4)
        self.assertEqual(comprobar.longitud_x("❤️"), 2)
        self.assertEqual(comprobar.longitud_x("http://a.b/" + "c" * 80), 23)

    def test_x_numero_de_posts_del_hilo(self):
        self.escribir("x.md", "## es\n\n" + "".join(f"**{i}/** Uno.\n\n" for i in range(1, 6)) + "## en\n\n**1/** One.\n")
        self.assertFallo("x.md (es): 5 posts; a thread has 1 to 4")

    def test_x_sin_marcadores_es_un_post(self):
        self.escribir("x.md", "## es\n\nUn post suelto.\n\n## en\n\nOne post.\n")
        self.assertEqual(self.fallos(), "")

    def test_discord_limite_por_bloque(self):
        self.escribir("discord.md", "## es\n\n" + "a" * 1999 + "\n---\n" + "b" * 2001 + "\n\n## en\n\nok\n")
        out = self.fallos()
        self.assertIn("discord.md (es) message 2: 2001 characters (max 2000)", out)
        self.assertNotIn("message 1", out)

    def test_linkedin_limite(self):
        self.escribir("linkedin.md", "## es\n\n" + "a" * 3001 + "\n\n## en\n\nok\n")
        self.assertFallo("linkedin.md (es): 3001 characters (max 3000)")

    def test_linkedin_en_3000_pasa_y_la_linea_imagen_no_cuenta(self):
        self.escribir("linkedin.md", "## es\n\n" + "a" * 3000 + "\nImagen: medios/tarjeta.webp\n\n## en\n\nok\n")
        self.assertEqual(self.fallos(), "")

    def test_reddit_titulo_demasiado_largo(self):
        self.cambiar("reddit.md", "Sale la versión", "a" * 301)
        self.assertFallo("reddit.md (es): title of 301 characters (max 300)")

    def test_reddit_sin_titulo(self):
        self.cambiar("reddit.md", "**Title:** Release out", "Release out")
        self.assertFallo("reddit.md (en): no title")


class Reddit(Base):
    def test_falta_el_subreddit(self):
        self.cambiar("ficha.md", "- **Subreddit:** r/gamedev\n", "")
        self.assertFallo("reddit.md needs «Subreddit:» in ficha.md")

    def test_falta_la_autopromocion(self):
        self.cambiar("ficha.md", "- **Autopromoción:** solo los sábados\n", "")
        self.assertFallo("«Autopromoción:» line")

    def test_fecha_de_normas_no_valida(self):
        self.cambiar("ficha.md", "2026-10-25\n- **Auto", "ayer\n- **Auto")
        self.assertFallo("«Normas leídas:» «ayer» has no valid AAAA-MM-DD date")

    def test_sin_reddit_no_se_piden_sus_datos(self):
        self.cambiar("ficha.md", "- reddit\n", "")
        (self.carpeta / "reddit.md").unlink()
        self.assertEqual(self.fallos(), "")


class Imagenes(Base):
    def test_imagen_que_no_existe(self):
        self.cambiar("x.md", "medios/tarjeta.webp", "medios/otra.webp")
        self.assertFallo("x.md: «Imagen: medios/otra.webp» does not exist")

    def test_imagen_que_no_es_un_render(self):
        self.cambiar("x.md", "medios/tarjeta.webp", "https://x.org/a.png")
        self.assertFallo("is not a render; point to medios/<name>.webp")

    def test_imagen_fuera_de_la_tabla(self):
        (self.carpeta / "medios" / "otra.webp").write_bytes(webp())
        (self.carpeta / "medios" / "otra-mini.webp").write_bytes(webp())
        self.cambiar("x.md", "medios/tarjeta.webp", "medios/otra.webp")
        self.assertFallo("x.md: «medios/otra.webp» is not in «## Imágenes» of ficha.md")

    def test_alt_que_falta_en_un_idioma(self):
        self.cambiar("ficha.md", " / en: Release card", "")
        self.assertFallo("«medios/tarjeta.webp» has no alt text in «en»")

    def test_ficha_sin_tabla_de_imagenes(self):
        self.cambiar("ficha.md", "## Imágenes", "## Otras")
        self.assertFallo("no «## Imágenes» section")

    def test_render_sin_mini(self):
        (self.carpeta / "medios" / "tarjeta-mini.webp").unlink()
        self.assertFallo("«medios/tarjeta.webp» has no -mini.webp")

    def test_render_no_listado_en_la_ficha(self):
        (self.carpeta / "medios" / "suelta.webp").write_bytes(webp())
        self.assertFallo("medios/suelta.webp: not in «## Imágenes»")

    def test_fuente_sin_renderizar(self):
        for nombre in ("grafico.html", "foto.jpg", "dibujo.svg", "captura.png"):
            (self.carpeta / "medios" / "fuente" / nombre).write_bytes(b"x")
            self.assertFallo(f"medios/fuente/{nombre}: not rendered")

    def test_fuente_renderizada_a_pdf_pasa(self):
        (self.carpeta / "medios" / "fuente" / "carrusel.html").write_text("<p>ok</p>")
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(pdf(3))
        self.cambiar("ficha.md", "| x, linkedin |", "| x, linkedin |\n| `medios/carrusel.pdf` | es: Carrusel / en: Carousel | linkedin |")
        self.cambiar("linkedin.md", "Imagen: medios/tarjeta.webp", "Imagen: medios/carrusel.pdf")
        self.assertEqual(self.fallos(), "")

    def test_peso_de_la_imagen(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["x"]["imagen_bytes"]["valor"] = 100
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(webp(extra=500))
        self.assertFallo("medios/tarjeta.webp: 530 bytes (max 100 for x)", reglas=reglas)

    def test_pixeles_de_la_imagen(self):
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(webp(7000, 6000))
        self.assertFallo("7000x6000 = 42000000 pixels (must be under 36152320 for linkedin)")

    def test_alt_demasiado_largo(self):
        self.cambiar("ficha.md", "Tarjeta de la versión", "a" * 1001)
        self.assertFallo("alt text «es» of «medios/tarjeta.webp» has 1001 characters (max 1000 for x)")

    def test_pdf_solo_en_linkedin(self):
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(pdf(2))
        self.cambiar("ficha.md", "| x, linkedin |", "| x, linkedin |\n| `medios/carrusel.pdf` | es: C / en: C | x |")
        self.cambiar("x.md", "medios/tarjeta.webp", "medios/carrusel.pdf")
        self.assertFallo("x.md: «medios/carrusel.pdf» is a PDF and only LinkedIn takes a document")

    def test_paginas_del_pdf(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["linkedin"]["documento_paginas"]["valor"] = 3
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(pdf(4))
        self.cambiar("ficha.md", "| x, linkedin |", "| x, linkedin |\n| `medios/carrusel.pdf` | es: C / en: C | linkedin |")
        self.cambiar("linkedin.md", "medios/tarjeta.webp", "medios/carrusel.pdf")
        self.assertFallo("medios/carrusel.pdf: 4 pages (LinkedIn max 3)", reglas=reglas)

    def test_peso_del_pdf(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["linkedin"]["documento_bytes"]["valor"] = 50
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(pdf(2))
        self.cambiar("ficha.md", "| x, linkedin |", "| x, linkedin |\n| `medios/carrusel.pdf` | es: C / en: C | linkedin |")
        self.cambiar("linkedin.md", "medios/tarjeta.webp", "medios/carrusel.pdf")
        self.assertFallo("medios/carrusel.pdf:", reglas=reglas)
        self.assertFallo("(LinkedIn max 50)", reglas=reglas)


class Cabeceras(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def dim(self, nombre, datos):
        p = self.tmp / nombre
        p.write_bytes(datos)
        return comprobar.dimensiones(p)

    def test_webp_vp8x_vp8l_y_vp8(self):
        self.assertEqual(self.dim("a.webp", webp(640, 480)), (640, 480))
        bits = (320 - 1) | ((200 - 1) << 14)
        vp8l = b"VP8L" + struct.pack("<I", 5) + b"\x2f" + struct.pack("<I", bits)
        self.assertEqual(self.dim("b.webp", b"RIFF" + struct.pack("<I", 20) + b"WEBP" + vp8l), (320, 200))
        vp8 = b"VP8 " + struct.pack("<I", 10) + b"\x00\x00\x00\x9d\x01\x2a" + struct.pack("<HH", 800, 600)
        self.assertEqual(self.dim("c.webp", b"RIFF" + struct.pack("<I", 26) + b"WEBP" + vp8), (800, 600))

    def test_png(self):
        self.assertEqual(self.dim("a.png", png(1200, 630)), (1200, 630))

    def test_jpeg(self):
        sof = b"\xff\xc0" + struct.pack(">HBHH", 11, 8, 480, 640) + b"\x03\x01\x11\x00"
        app = b"\xff\xe0" + struct.pack(">H", 6) + b"JFIF"
        self.assertEqual(self.dim("a.jpg", b"\xff\xd8" + app + sof), (640, 480))

    def test_formato_desconocido(self):
        self.assertIsNone(self.dim("a.webp", b"no es una imagen"))
        self.assertIsNone(self.dim("b.png", b"\x89PNG"))


class Reglas(unittest.TestCase):
    def test_cada_regla_lleva_valor_marca_fuente_y_fecha(self):
        reglas = comprobar.cargar_reglas()
        self.assertIn("Single place", reglas["_doc"])
        for canal, cuerpo in reglas.items():
            if canal.startswith("_"):
                continue
            for clave, r in cuerpo.items():
                with self.subTest(regla=f"{canal}.{clave}"):
                    self.assertEqual({"valor", "marca", "fuente", "comprobado"} - set(r), set())
                    self.assertIn(r["marca"], ("P", "S", "NV", "C"))
                    self.assertRegex(r["comprobado"], r"^\d{4}-\d{2}-\d{2}$")

    def test_las_claves_que_lee_el_script_existen(self):
        reglas = comprobar.cargar_reglas()
        for clave in ("x.longitud", "x.url_peso", "x.hilo_posts", "linkedin.longitud", "discord.mensaje", "reddit.titulo"):
            canal, k = clave.split(".")
            with self.subTest(clave=clave):
                self.assertIsNotNone(comprobar.regla(reglas, canal, k))

    def test_reddit_no_tiene_datos_verificados(self):
        reglas = comprobar.cargar_reglas()
        self.assertEqual({r["marca"] for r in reglas["reddit"].values()}, {"NV"})


if __name__ == "__main__":
    unittest.main()
