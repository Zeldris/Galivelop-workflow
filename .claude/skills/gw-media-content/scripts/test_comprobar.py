"""Tests of comprobar.py: every case builds its own piece folder in a tempdir (a valid one) and breaks one thing;
each asserts the message, not only the result. Run: python3 -m unittest discover -s skills/gw-media-content/scripts"""
import json
import re
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
| `medios/tarjeta.webp` | es: Tarjeta de la versión / en: Release card | x |
| `medios/tarjeta.png` | es: Tarjeta de la versión / en: Release card | linkedin |

## Uso interno

Tarea QA-12 en la rama claude/algo.

## Publicado

| Canal | Idioma | Fecha | Enlace |
|---|---|---|---|
"""
CANALES = {
    "x": "## es\n\n**1/** Sale la versión.\nImagen: medios/tarjeta.webp\n\n**2/** Detalles.\n\n## en\n\n**1/** Release out.\n\n**2/** Details.\n",
    "reddit": "## es\n\n**Título:** Sale la versión\n\nTexto.\n\n## en\n\n**Title:** Release out\n\nText.\n",
    "linkedin": "## es\n\nTexto largo.\nImagen: medios/tarjeta.png\n\n## en\n\nLong text.\nImagen: medios/tarjeta.png\n",
    "discord": "## es\n\n### Novedades\n\n## en\n\n### News\n",
}


RENDER = "node .claude/skills/gw-media-content/scripts/render.mjs"


def webp(ancho=100, alto=50, extra=0):
    cuerpo = b"WEBPVP8X" + struct.pack("<I", 10) + bytes(4) + (ancho - 1).to_bytes(3, "little") + (alto - 1).to_bytes(3, "little")
    return b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo + bytes(extra)


def png(ancho, alto):
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", ancho, alto) + b"\x08\x06\x00\x00\x00"


def jpeg(ancho, alto):
    sof = b"\xff\xc0" + struct.pack(">HBHH", 11, 8, alto, ancho) + b"\x03\x01\x11\x00"
    return b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 6) + b"JFIF" + sof + bytes(10)


def gif(ancho, alto):
    return b"GIF89a" + struct.pack("<HH", ancho, alto) + b"\x00\x00\x00;"


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
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(png(100, 50))
        (self.carpeta / "medios" / "fuente" / "tarjeta.html").write_text("<p>ok</p>")
        self.reglas = comprobar.cargar_reglas()

    def escribir(self, nombre, texto):
        (self.carpeta / nombre).write_text(texto, encoding="utf-8")

    def cambiar(self, nombre, viejo, nuevo):
        t = (self.carpeta / nombre).read_text(encoding="utf-8")
        self.assertIn(viejo, t)
        self.escribir(nombre, t.replace(viejo, nuevo, 1))

    def pdf_en_linkedin(self, paginas):
        """LinkedIn posts a carousel PDF instead of the .png."""
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(pdf(paginas))
        (self.carpeta / "medios" / "tarjeta.png").unlink()
        self.cambiar("ficha.md", "`medios/tarjeta.png` | es: Tarjeta de la versión / en: Release card",
                     "`medios/carrusel.pdf` | es: Carrusel / en: Carousel")
        self.escribir("linkedin.md", CANALES["linkedin"].replace("tarjeta.png", "carrusel.pdf"))

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
        self.assertIn("usage: comprobar.py [--prefijos-tarea A,B,...]", r.stdout)

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
        self.cambiar("ficha.md", "Release card | x |", "Release card | x, portal |")
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

    def test_idiomas_es_obligatorio_en_la_ficha(self):
        self.cambiar("ficha.md", "Idiomas: es, en\n", "")
        self.assertFallo('no languages: add "Idiomas: es, en" to ficha.md')

    def test_sin_idiomas_se_siguen_deduciendo_para_el_resto(self):
        self.cambiar("ficha.md", "Idiomas: es, en\n", "")
        self.escribir("linkedin.md", "## es\n\nSolo español.\n")
        self.assertFallo("linkedin.md: no «## en» section")

    def test_seccion_de_idioma_repetida(self):
        self.escribir("linkedin.md", CANALES["linkedin"] + "\n## es\n\nOtra vez.\n")
        self.assertFallo("linkedin.md: «## es» appears more than once; merge the sections into one")

    def test_un_encabezado_que_no_es_idioma_cierra_la_seccion(self):
        # the 3001 characters under «## Notas» are not part of «## es»: no length error
        self.escribir("linkedin.md", "## es\n\nCorto.\nImagen: medios/tarjeta.png\n\n## Notas\n\n" + "a" * 3001 + "\n\n## en\n\nok\n")
        self.assertEqual(self.fallos(), "")

    def test_una_seccion_cortada_por_un_encabezado_queda_vacia(self):
        self.escribir("linkedin.md", "## es\n## Notas\nTexto largo.\n\n## en\n\nok\n")
        self.assertFallo("linkedin.md: no «## es» section")


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
        for jerga, texto in (("P3", "hallazgo P3"), ("F12", "finding F12"), ("P1", "ver (P1)"), ("QA-215", "QA-215"),
                             ("EPIC-3", "EPIC-3"), ("claude/rama-x", "claude/rama-x"), ("WIP:", "WIP:")):
            with self.subTest(jerga=jerga):
                self.cambiar("linkedin.md", "Long text.", f"Long text {texto}.")
                self.assertFallo(f"linkedin.md: internal jargon «{jerga}»")
                self.cambiar("linkedin.md", f"Long text {texto}.", "Long text.")

    def test_los_prefijos_de_un_proyecto_no_son_jerga_por_defecto(self):
        for texto in ("INS-3", "FLU-12", "WMF-7"):
            with self.subTest(texto=texto):
                self.cambiar("linkedin.md", "Long text.", f"Long text {texto}.")
                self.assertEqual(self.fallos(), "")
                self.cambiar("linkedin.md", f"Long text {texto}.", "Long text.")

    def test_los_prefijos_se_añaden_con_el_argumento(self):
        self.cambiar("linkedin.md", "Long text.", "Long text INS-3 y FLU-12.")
        problemas = "\n".join(comprobar.comprobar(self.carpeta, self.reglas, ("INS", "FLU")))
        self.assertIn("linkedin.md: internal jargon «INS-3»", problemas)
        self.assertIn("linkedin.md: internal jargon «FLU-12»", problemas)
        self.assertEqual(comprobar.jerga("QA-1 y INS-3", ("INS",)), ["INS-3", "QA-1"])  # the generic ones stay

    def test_cli_prefijos_tarea(self):
        self.cambiar("linkedin.md", "Long text.", "Long text INS-3.")
        for args in (["--prefijos-tarea", "INS,FLU"], ["--prefijos-tarea=ins, flu"]):
            r = subprocess.run([sys.executable, str(AQUI / "comprobar.py"), *args, str(self.carpeta)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, args)
            self.assertIn("internal jargon «INS-3»", r.stdout)
        sin = subprocess.run([sys.executable, str(AQUI / "comprobar.py"), str(self.carpeta)], capture_output=True, text=True)
        self.assertEqual((sin.returncode, sin.stdout.strip()), (0, "OK"))

    def test_cli_prefijos_tarea_mal_escrito(self):
        for args, motivo in ((["--prefijos-tarea"], "--prefijos-tarea needs prefixes"),
                             (["--prefijos-tarea", "IN S-1"], "--prefijos-tarea needs prefixes"),
                             (["--rapido"], "unknown option --rapido")):
            r = subprocess.run([sys.executable, str(AQUI / "comprobar.py"), *args, str(self.carpeta)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn(motivo, r.stdout)
            self.assertIn("usage: comprobar.py [--prefijos-tarea A,B,...]", r.stdout)

    def test_la_jerga_permitida_no_salta(self):
        self.cambiar("linkedin.md", "Long text.", "Long text con GPT-4, UTF-8 y P2P.")
        self.assertEqual(self.fallos(), "")

    def test_cifrados_y_prioridades_no_son_jerga(self):
        for texto in ("AES-256", "WPA-3", "AK-47", "bugs P1/P2", "pulsa F5", "SHA-256 e ISO-8601", "El P1 y el P2"):
            with self.subTest(texto=texto):
                self.cambiar("linkedin.md", "Long text.", f"Long text {texto}.")
                self.assertEqual(self.fallos(), "")
                self.cambiar("linkedin.md", f"Long text {texto}.", "Long text.")

    def test_una_rama_dentro_de_un_enlace_no_es_jerga(self):
        self.cambiar("linkedin.md", "Long text.", "Long text https://github.com/o/r/tree/claude/mi-rama-x y https://x.org/QA-12 fin.")
        self.assertEqual(self.fallos(), "")
        self.cambiar("linkedin.md", "claude/mi-rama-x y", "claude/mi-rama-x y claude/otra")
        self.assertFallo("linkedin.md: internal jargon «claude/otra»")

    def test_la_jerga_de_la_ficha_se_permite_en_uso_interno_pero_no_en_el_alt(self):
        # QA-12 is in «## Uso interno» of the fixture: allowed there, an error in an alt text
        self.assertIn("QA-12", (self.carpeta / "ficha.md").read_text(encoding="utf-8"))
        self.assertEqual(self.fallos(), "")
        self.cambiar("ficha.md", "Release card | x |", "Release card QA-12 | x |")
        self.assertFallo("ficha.md: alt text of «medios/tarjeta.webp» has internal jargon «QA-12»")

    def test_un_puntos_suspensivos_suelto_en_prosa_no_es_hueco(self):
        self.cambiar("linkedin.md", "Long text.", "Long text … y más… o … así.")
        self.assertEqual(self.fallos(), "")

    def test_un_puntos_suspensivos_que_es_toda_la_linea_o_el_valor_si_es_hueco(self):
        self.cambiar("linkedin.md", "Long text.", "Long text.\n\n…\n")
        self.assertFallo("linkedin.md: template gap «…» left")
        self.cambiar("linkedin.md", "\n\n…\n", "")
        self.cambiar("ficha.md", "## Reddit", "- **Estado:** …\n\n## Reddit")
        self.assertFallo("ficha.md: template gap «…» left")

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

    def lx(self, texto):
        return comprobar.longitud_x(texto, comprobar.regla(self.reglas, "x", "url_peso"),
                                    comprobar.regla(self.reglas, "x", "simbolo_ancho_peso"))

    def test_x_acentos_y_comillas_cuentan_1(self):
        self.assertEqual(self.lx("áéíóú“”—"), 8)
        self.assertEqual(self.lx("日本"), 4)
        self.assertEqual(self.lx("❤️"), 2)
        self.assertEqual(self.lx("http://a.b/" + "c" * 80), 23)
        self.assertEqual(self.lx("©"), 1)

    def test_x_una_secuencia_de_emoji_es_un_bloque_de_2(self):
        for nombre, texto in (("familia", "👨‍👩‍👧‍👦"), ("bandera", "🇪🇸"), ("tono de piel", "👍🏽"), ("profesión", "👩🏽‍💻"),
                              ("tecla", "1️⃣"), ("corazón", "❤️")):
            with self.subTest(nombre):
                self.assertEqual(self.lx(texto), 2)
                self.assertEqual(self.lx("a" + texto + "b"), 4)
        self.assertEqual(self.lx("🇪🇸🇫🇷"), 4)
        self.assertEqual(self.lx("👍👍"), 4)

    def test_x_la_puntuacion_final_no_es_parte_del_enlace(self):
        self.assertEqual(self.lx("(https://a.b/c)."), 1 + 23 + 2)
        self.assertEqual(self.lx("¿https://a.b/c?"), 1 + 23 + 1)
        self.assertEqual(self.lx("«https://a.b/c», https://d.e/f;"), 1 + 23 + 2 + 1 + 23 + 1)
        self.assertEqual(self.lx("https://a.b/c?q=1&r=2"), 23)

    def test_x_un_hilo_con_emoji_de_familia_en_el_limite(self):
        familia = "👨‍👩‍👧‍👦"
        self.cambiar("x.md", "**1/** Sale la versión.", "**1/** " + familia * 140)
        self.assertEqual(self.fallos(), "")
        self.cambiar("x.md", familia * 140, familia * 141)
        self.assertFallo("x.md (es) post 1: 282 weighted characters (max 280")

    def test_x_texto_antes_del_primer_marcador(self):
        self.cambiar("x.md", "## es\n\n**1/**", "## es\n\nIntro suelta.\n\n**1/**")
        self.assertFallo("x.md (es): text before «**1/**»")

    def test_x_el_marcador_n_de_m_vale(self):
        self.escribir("x.md", "## es\n\n**1/2** Uno.\nImagen: medios/tarjeta.webp\n\n**2/2** Dos.\n\n## en\n\n**1/2** One.\n\n**2/2** Two.\n")
        self.assertEqual(self.fallos(), "")
        self.assertEqual(comprobar.posts_x("**1/2** Uno.\n\n**2/2** Dos."), ("", ["Uno.", "Dos."]))

    def test_x_numero_de_posts_del_hilo(self):
        self.escribir("x.md", "## es\n\n" + "".join(f"**{i}/** Uno.\n\n" for i in range(1, 6)) + "## en\n\n**1/** One.\n")
        self.assertFallo("x.md (es): 5 posts; a thread has 1 to 4")

    def test_x_sin_marcadores_es_un_post(self):
        self.escribir("x.md", "## es\n\nUn post suelto.\nImagen: medios/tarjeta.webp\n\n## en\n\nOne post.\n")
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
        self.escribir("linkedin.md", "## es\n\n" + "a" * 3000 + "\nImagen: medios/tarjeta.png\n\n## en\n\nok\nImagen: medios/tarjeta.png\n")
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
        self.assertFallo("x.md: «Imagen: medios/otra.webp» does not exist; render it (" + RENDER + " ")

    def test_imagen_que_no_es_un_render(self):
        self.cambiar("x.md", "medios/tarjeta.webp", "https://x.org/a.png")
        self.assertFallo("x.md: «Imagen: https://x.org/a.png» is not a render; point to medios/<name>.webp")
        self.cambiar("linkedin.md", "medios/tarjeta.png", "https://x.org/a.png")
        self.assertFallo("linkedin.md: «Imagen: https://x.org/a.png» is not a render; point to medios/<name>.png")

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
        self.assertFallo("«medios/tarjeta.webp» has no -mini.webp; render it again (" + RENDER + " ")

    def test_render_no_listado_en_la_ficha(self):
        (self.carpeta / "medios" / "suelta.webp").write_bytes(webp())
        self.assertFallo("medios/suelta.webp: not in «## Imágenes»")

    def test_fuente_sin_renderizar(self):
        for nombre in ("grafico.html", "foto.jpg", "dibujo.svg", "captura.png"):
            (self.carpeta / "medios" / "fuente" / nombre).write_bytes(b"x")
            self.assertFallo(f"medios/fuente/{nombre}: not rendered; run {RENDER} ")

    def test_fuente_renderizada_a_pdf_pasa(self):
        (self.carpeta / "medios" / "fuente" / "carrusel.html").write_text("<p>ok</p>")
        self.pdf_en_linkedin(3)
        self.assertEqual(self.fallos(), "")

    def test_peso_de_la_imagen(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["x"]["imagen_bytes"]["valor"] = 100
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(webp(extra=500))
        self.assertFallo("medios/tarjeta.webp: 530 bytes (max 100 for x)", reglas=reglas)

    def test_pixeles_de_la_imagen(self):
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(png(7000, 6000))
        self.assertFallo("medios/tarjeta.png: 7000x6000 = 42000000 pixels (must be under 36152320 for linkedin)")
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(jpeg(7000, 6000))
        self.assertFallo("medios/tarjeta.png: 7000x6000 = 42000000 pixels (must be under 36152320 for linkedin)")

    def test_alt_demasiado_largo(self):
        self.cambiar("ficha.md", "Tarjeta de la versión", "a" * 1001)
        self.assertFallo("alt text «es» of «medios/tarjeta.webp» has 1001 characters (max 1000 for x)")

    def test_pdf_solo_en_linkedin(self):
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(pdf(2))
        self.cambiar("ficha.md", "| linkedin |", "| linkedin |\n| `medios/carrusel.pdf` | es: C / en: C | x |")
        self.cambiar("x.md", "medios/tarjeta.webp", "medios/carrusel.pdf")
        self.assertFallo("x.md: «medios/carrusel.pdf» is a PDF and only LinkedIn takes a document")

    def test_paginas_del_pdf(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["linkedin"]["documento_paginas"]["valor"] = 3
        self.pdf_en_linkedin(4)
        self.assertFallo("medios/carrusel.pdf: 4 pages (LinkedIn max 3)", reglas=reglas)

    def test_peso_del_pdf(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["linkedin"]["documento_bytes"]["valor"] = 50
        self.pdf_en_linkedin(2)
        self.assertFallo("medios/carrusel.pdf:", reglas=reglas)
        self.assertFallo("(LinkedIn max 50)", reglas=reglas)


class Formatos(Base):
    def test_linkedin_acepta_png_jpg_y_gif_y_x_solo_webp(self):
        for ext, datos in ((".png", png(100, 50)), (".jpg", jpeg(100, 50)), (".gif", gif(100, 50))):
            with self.subTest(ext):
                (self.carpeta / "medios" / "tarjeta.png").unlink(missing_ok=True)
                (self.carpeta / "medios" / f"tarjeta{ext}").write_bytes(datos)
                t = (self.carpeta / "linkedin.md").read_text(encoding="utf-8")
                self.escribir("linkedin.md", t.replace("tarjeta.png", f"tarjeta{ext}"))
                f = (self.carpeta / "ficha.md").read_text(encoding="utf-8")
                self.escribir("ficha.md", f.replace("tarjeta.png", f"tarjeta{ext}"))
                self.assertEqual(self.fallos(), "")
                (self.carpeta / "medios" / f"tarjeta{ext}").unlink()
                self.escribir("linkedin.md", t)
                self.escribir("ficha.md", f)

    def test_x_con_png_es_un_error(self):
        self.cambiar("x.md", "medios/tarjeta.webp", "medios/tarjeta.png")
        self.cambiar("ficha.md", "| x |", "| x, linkedin |")
        self.assertFallo("x.md: «medios/tarjeta.png» is a .png and x takes .webp; point to medios/<name>.webp")

    def test_linkedin_con_webp_es_un_error(self):
        self.cambiar("linkedin.md", "medios/tarjeta.png", "medios/tarjeta.webp")
        self.assertFallo("linkedin.md: «medios/tarjeta.webp» is a .webp and linkedin takes .png, .jpg, .gif; "
                         "point to medios/<name>.png")

    def test_un_png_suelto_en_medios_sin_fila_es_un_error(self):
        (self.carpeta / "medios" / "suelta.png").write_bytes(png(10, 10))
        self.assertFallo("medios/suelta.png: not in «## Imágenes»")

    def test_el_peso_de_un_png_se_comprueba(self):
        reglas = json.loads(json.dumps(self.reglas))
        reglas["x"]["imagen_bytes"]["valor"] = 20
        self.cambiar("x.md", "medios/tarjeta.webp", "medios/tarjeta.png")
        self.cambiar("ficha.md", "| x |", "| x, linkedin |")
        self.assertFallo("medios/tarjeta.png: 29 bytes (max 20 for x)", reglas=reglas)

    def test_linkedin_formatos_estan_en_reglas_con_fuente_primaria(self):
        r = self.reglas["linkedin"]["imagen_formatos"]
        self.assertEqual((r["valor"], r["marca"]), ([".png", ".jpg", ".gif"], "P"))
        self.assertIn("images-api", r["fuente"])


class FilasDeImagenes(Base):
    def test_un_canal_de_la_fila_sin_linea_imagen(self):
        self.cambiar("ficha.md", "Release card | x |", "Release card | x, discord |")
        self.assertFallo("ficha.md: «medios/tarjeta.webp» lists channel «discord» but discord.md has no "
                         "«Imagen: medios/tarjeta.webp» line")

    def test_linea_imagen_de_un_canal_que_la_fila_no_lista(self):
        self.cambiar("discord.md", "## es\n", "## es\nImagen: medios/tarjeta.webp\n")
        self.assertFallo("discord.md: «medios/tarjeta.webp» is not listed for «discord» in «## Imágenes» of ficha.md")

    def test_la_fila_se_valida_contra_cada_canal_de_su_celda(self):
        # discord.md has no `Imagen:` line (an error of its own), but the row says discord: weight and alt are checked
        reglas = json.loads(json.dumps(self.reglas))
        reglas["discord"]["imagen_bytes"]["valor"] = 100
        self.cambiar("ficha.md", "Release card | x |", "Release card | x, discord |")
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(webp(extra=500))
        self.assertFallo("medios/tarjeta.webp: 530 bytes (max 100 for discord)", reglas=reglas)
        self.cambiar("ficha.md", "Tarjeta de la versión", "a" * 1025)
        self.assertFallo("alt text «es» of «medios/tarjeta.webp» has 1025 characters (max 1024 for discord)")

    def test_la_fila_de_linkedin_comprueba_los_pixeles_aunque_el_canal_no_apunte(self):
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(png(7000, 6000))
        self.escribir("linkedin.md", "## es\n\nTexto largo.\n\n## en\n\nLong text.\n")
        out = self.fallos()
        self.assertIn("lists channel «linkedin» but linkedin.md has no «Imagen: medios/tarjeta.png» line", out)
        self.assertIn("7000x6000 = 42000000 pixels", out)


class ImagenesTruncadas(Base):
    MSG = "not a valid image; render it again (" + RENDER + " "

    def test_una_imagen_que_no_es_imagen_en_x(self):
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(b"basura")
        self.assertFallo("medios/tarjeta.webp: " + self.MSG)

    def test_png_truncado_con_la_firma_completa(self):
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(png(100, 50)[:20])
        self.assertFallo("medios/tarjeta.png: " + self.MSG)

    def test_png_sin_ihdr(self):
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(30))
        self.assertFallo("medios/tarjeta.png: " + self.MSG)

    def test_jpeg_truncado_con_la_firma_completa(self):
        (self.carpeta / "medios" / "tarjeta.png").write_bytes(jpeg(100, 50)[:18])
        self.assertFallo("medios/tarjeta.png: " + self.MSG)

    def test_webp_vp8x_truncado(self):
        (self.carpeta / "medios" / "tarjeta.webp").write_bytes(webp()[:29])
        self.assertFallo("medios/tarjeta.webp: " + self.MSG)

    def test_el_mini_tambien_tiene_que_ser_valido(self):
        (self.carpeta / "medios" / "tarjeta-mini.webp").write_bytes(webp(10, 5)[:25])
        self.assertFallo("medios/tarjeta-mini.webp: " + self.MSG)

    def test_el_pdf_ilegible_da_la_orden_completa(self):
        self.pdf_en_linkedin(1)
        (self.carpeta / "medios" / "carrusel.pdf").write_bytes(b"%PDF-1.4\n")
        self.assertFallo("medios/carrusel.pdf: the page count cannot be read; render the PDF again (" + RENDER + " ")


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
        self.assertEqual(self.dim("b.webp", b"RIFF" + struct.pack("<I", 4 + len(vp8l)) + b"WEBP" + vp8l), (320, 200))
        vp8 = b"VP8 " + struct.pack("<I", 10) + b"\x00\x00\x00\x9d\x01\x2a" + struct.pack("<HH", 800, 600)
        self.assertEqual(self.dim("c.webp", b"RIFF" + struct.pack("<I", 4 + len(vp8)) + b"WEBP" + vp8), (800, 600))

    def test_webp_truncado(self):
        # VP8X needs 30 bytes, VP8L 25; the RIFF size is consistent here, so only the minimum length can catch it
        vp8x = b"WEBPVP8X" + struct.pack("<I", 10) + bytes(4) + b"\x63\x00"
        self.assertIsNone(self.dim("a.webp", b"RIFF" + struct.pack("<I", len(vp8x)) + vp8x))
        vp8l = b"WEBPVP8L" + struct.pack("<I", 5) + b"\x2f" + b"\x01\x02"
        self.assertIsNone(self.dim("b.webp", b"RIFF" + struct.pack("<I", len(vp8l)) + vp8l))

    def test_webp_con_el_tamano_riff_mayor_que_el_archivo(self):
        self.assertIsNone(self.dim("a.webp", webp()[:28] + b"\x00\x00"[:0]))
        entero = webp(extra=100)
        self.assertEqual(self.dim("b.webp", entero), (100, 50))
        self.assertIsNone(self.dim("c.webp", entero[:-101]))

    def test_gif(self):
        self.assertEqual(self.dim("a.gif", gif(300, 200)), (300, 200))
        self.assertIsNone(self.dim("b.gif", gif(300, 200)[:8]))

    def test_dimensiones_a_cero_no_son_validas(self):
        self.assertIsNone(self.dim("a.png", png(0, 10)))

    def test_png(self):
        self.assertEqual(self.dim("a.png", png(1200, 630)), (1200, 630))

    def test_jpeg(self):
        sof = b"\xff\xc0" + struct.pack(">HBHH", 11, 8, 480, 640) + b"\x03\x01\x11\x00"
        app = b"\xff\xe0" + struct.pack(">H", 6) + b"JFIF"
        self.assertEqual(self.dim("a.jpg", b"\xff\xd8" + app + sof), (640, 480))

    def test_formato_desconocido(self):
        self.assertIsNone(self.dim("a.webp", b"no es una imagen"))
        self.assertIsNone(self.dim("b.png", b"\x89PNG"))

    def test_png_y_jpeg_truncados_con_la_firma_completa(self):
        self.assertIsNone(self.dim("a.png", png(10, 10)[:20]))
        self.assertIsNone(self.dim("b.png", b"\x89PNG\r\n\x1a\n" + bytes(30)))
        self.assertIsNone(self.dim("a.jpg", jpeg(10, 10)[:16]))
        self.assertIsNone(self.dim("b.jpg", b"\xff\xd8\xff\xe0"))


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
        for clave in comprobar.CLAVES:
            canal, k = clave.split(".")
            with self.subTest(clave=clave):
                self.assertIsNotNone(comprobar.regla(reglas, canal, k))
                self.assertIn(clave, reglas["_doc"])

    def test_el_script_no_lee_ninguna_clave_fuera_de_claves(self):
        fuente = (AQUI / "comprobar.py").read_text(encoding="utf-8")
        leidas = set(re.findall(r"regla\(reglas, [\"'](\w+)[\"'], [\"'](\w+)[\"']\)", fuente))
        self.assertTrue(leidas)
        for canal, k in leidas:
            self.assertIn(f"{canal}.{k}", comprobar.CLAVES)

    def test_sin_una_clave_falla_cerrado_y_nombra_cual(self):
        reglas = comprobar.cargar_reglas()
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        for clave in comprobar.CLAVES:
            canal, k = clave.split(".")
            with self.subTest(clave=clave):
                rota = json.loads(json.dumps(reglas))
                del rota[canal][k]
                esperado = f"reglas.json lacks {clave}; restore it"
                with self.assertRaises(comprobar.ReglasIncompletas) as e:
                    comprobar.validar_reglas(rota)
                self.assertEqual(str(e.exception), esperado)
                ruta = tmp / "reglas.json"
                ruta.write_text(json.dumps(rota), encoding="utf-8")
                with self.assertRaises(comprobar.ReglasIncompletas) as e:
                    comprobar.cargar_reglas(ruta)
                self.assertEqual(str(e.exception), esperado)
                self.assertEqual(comprobar.comprobar(tmp, rota), [esperado])

    def test_sin_url_peso_no_se_usa_un_23_escondido(self):
        rota = json.loads(json.dumps(comprobar.cargar_reglas()))
        rota["x"]["simbolo_ancho_peso"]["valor"] = None
        self.assertEqual(comprobar.comprobar(Path("."), rota), ["reglas.json lacks x.simbolo_ancho_peso; restore it"])

    def test_la_cli_con_reglas_rotas_sale_con_uno_y_dice_que_falta(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        shutil.copytree(AQUI.parent, tmp / "skill", ignore=shutil.ignore_patterns("__pycache__", "plantilla"))
        reglas = json.loads((tmp / "skill" / "reglas.json").read_text(encoding="utf-8"))
        del reglas["discord"]["mensaje"]
        (tmp / "skill" / "reglas.json").write_text(json.dumps(reglas), encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp / "skill" / "scripts" / "comprobar.py"), str(tmp)], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (1, "reglas.json lacks discord.mensaje; restore it"))

    def test_reddit_no_tiene_datos_verificados(self):
        reglas = comprobar.cargar_reglas()
        self.assertEqual({r["marca"] for r in reglas["reddit"].values()}, {"NV"})


if __name__ == "__main__":
    unittest.main()
