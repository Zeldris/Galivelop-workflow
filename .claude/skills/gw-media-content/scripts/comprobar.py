#!/usr/bin/env python3
"""gw-media-content: checks a piece folder before anything is published.

    python3 comprobar.py [--prefijos-tarea A,B,...] <dir>/AAAA-MM-DD/NN-<tema> [more folders]

A folder argument may also be a date folder or the whole <dir> (default docs/difusion): every piece below it is
checked. No config: the per-network limits are read from ../reglas.json.

Piece layout:
    ficha.md              facts with their source; sections `## Canales` (one channel per line), `## Imágenes`
                          (table: Imagen | Texto alternativo `es: ... / en: ...` | Canales: every channel listed
                          there needs an `Imagen:` line pointing to the file, and the other way round), `## Publicado`;
                          the line `Idiomas: es, en` (mandatory); for reddit.md a `## Reddit` block with the lines
                          `Subreddit:`, `Normas leídas:` (AAAA-MM-DD) and `Autopromoción:`
    <canal>.md            one per channel in `## Canales`, with one `## es` / `## en` section per language
                          (a `##` heading that is not a language ends the section: use `###` inside a post);
                          `Imagen: medios/<name>.webp` lines say which render goes with the post (.png for LinkedIn)
    medios/fuente/        sources: .html .svg .png .jpg .jpeg
    medios/               renders: <name>.webp + <name>-mini.webp (every channel but LinkedIn), <name>.png (LinkedIn
                          takes .png, .jpg and .gif), or <name>.pdf (LinkedIn document carousel)
Known channels (in reglas.json): x, reddit, linkedin, discord. Any other channel listed in `## Canales` gets only
the generic checks (template gaps, jargon, languages, `Imagen:` lines).

Prints OK, or one line per problem with the fix; exit 1 on any problem (2 on bad usage).
"""
import json
import re
import struct
import sys
import unicodedata
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REGLAS = AQUI.parent / "reglas.json"
CONOCIDOS = ("x", "reddit", "linkedin", "discord")
IDIOMAS = ("es", "en", "gl", "ca", "eu", "fr", "de", "pt", "it")
FUENTES = (".html", ".svg", ".png", ".jpg", ".jpeg")  # the same list as render.mjs
URL = re.compile(r"https?://\S+")
URL_FINAL = ".,;:!?)]}»\"'"  # punctuation that closes a sentence, not part of a link
RENDER = "node .claude/skills/gw-media-content/scripts/render.mjs"  # the installed path in a project
FORMATO_BASE = (".webp",)  # every channel without `imagen_formatos` in reglas.json
RENDERS = re.compile(r"^medios/[^/]+\.(?:webp|png|jpg|gif|pdf)$")
FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
CARPETA_PIEZA = re.compile(r"^\d{2}-[a-z0-9][a-z0-9-]*$")
# A lone … is a gap only when it is a whole line (or the whole value after a `label:`), not a word in prose.
HUECO = re.compile(r"\{\{[^}]*\}\}|(?m:^[ \t>*_-]*(?:\*{0,2}[^\n:]{1,40}:\*{0,2}[ \t]*)?…[ \t]*$)|<tema>|AAAA-MM-DD")
IMAGEN = re.compile(r"(?mi)^[ \t>*_-]*Imagen:[ \t]*(.*)$")
# Internal jargon: finding numbers (P3, F12) named as findings, task ids with a known prefix (QA-215), branch names,
# WIP: markers. A link is never read for jargon, and AES-256, WPA-3, AK-47, P1/P2 or F5 in prose pass. The prefixes
# are the generic ones; a project adds its own with --prefijos-tarea A,B,... (its INS-3 or FLU-12 ids).
PREFIJOS_TAREA = ("QA", "TASK", "TICKET", "ISSUE", "BUG", "JIRA", "GW", "EPIC", "STORY")
JERGA = (
    re.compile(r"\b(?:claude|feat|fix|chore|hotfix|release)/[\w./-]*\w|\bccr-[\w-]*\w|\bWIP:"),
    re.compile(r"(?i:\b(?:hallazgos?|findings?|propuestas?|proposals?|ítems?|items?))[ \t]+#?([PF]\d{1,3})\b"
               r"|[\[(]([PF]\d{1,3})[\])]"),
)
# Every reglas.json key the script reads ("channel.key"); cargar_reglas fails closed when one is missing.
CLAVES = (
    "x.longitud", "x.url_peso", "x.simbolo_ancho_peso", "x.hilo_posts", "x.imagen_bytes", "x.alt_max",
    "reddit.titulo",
    "linkedin.longitud", "linkedin.imagen_pixeles", "linkedin.imagen_formatos", "linkedin.alt_max",
    "linkedin.documento_bytes", "linkedin.documento_paginas",
    "discord.mensaje", "discord.imagen_bytes", "discord.alt_max",
)


class ReglasIncompletas(Exception):
    pass


def validar_reglas(reglas: dict):
    for clave in CLAVES:
        canal, k = clave.split(".")
        r = reglas.get(canal, {}).get(k)
        if not isinstance(r, dict) or r.get("valor") is None:
            raise ReglasIncompletas(f"reglas.json lacks {clave}; restore it")


def cargar_reglas(ruta=REGLAS) -> dict:
    try:
        reglas = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ReglasIncompletas(f"reglas.json cannot be read ({e}); restore it") from None
    validar_reglas(reglas)
    return reglas


def regla(reglas: dict, canal: str, clave: str):
    """Value of a rule, or None when the channel or the rule is not in reglas.json (CLAVES are always there)."""
    return reglas.get(canal, {}).get(clave, {}).get("valor")


def formatos(reglas: dict, canal: str) -> tuple:
    return tuple(regla(reglas, canal, "imagen_formatos") or FORMATO_BASE)


def patrones_jerga(prefijos=()) -> tuple:
    """The jargon patterns: the fixed ones and the task ids with the generic prefixes plus the project's own."""
    todos = dict.fromkeys(PREFIJOS_TAREA + tuple(prefijos))
    return (re.compile(r"\b(?:" + "|".join(map(re.escape, todos)) + r")-\d{1,5}\b"),) + JERGA


def jerga(texto: str, prefijos=()) -> list:
    texto = URL.sub(" ", texto)
    return sorted({next(g for g in m.groups() if g) if m.groups() else m.group(0)
                   for p in patrones_jerga(prefijos) for m in p.finditer(texto)})


def peso_x(c: str) -> int:
    """twitter-text weight: ranges 0-4351, 8192-8205, 8208-8223 and 8242-8247 weigh 1, the rest 2."""
    o = ord(c)
    if o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247:
        return 1
    return 2


def _emoji_base(c: str) -> bool:
    o = ord(c)
    return (0x1F000 <= o <= 0x1FAFF or 0x2190 <= o <= 0x21FF or 0x2300 <= o <= 0x23FF or 0x25A0 <= o <= 0x27BF
            or 0x2900 <= o <= 0x297F or 0x2B00 <= o <= 0x2BFF
            or o in (0xA9, 0xAE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299))


def _fin_emoji(texto: str, i: int) -> int:
    """Index after the emoji sequence that starts at i (i + 1 when it is a single character)."""
    n, c = len(texto), texto[i]
    if 0x1F1E6 <= ord(c) <= 0x1F1FF:  # a flag: two regional indicators
        return i + 2 if i + 1 < n and 0x1F1E6 <= ord(texto[i + 1]) <= 0x1F1FF else i + 1
    if c in "0123456789#*":  # a keycap: digit, optional FE0F, 20E3
        j = i + 2 if i + 1 < n and texto[i + 1] == "\ufe0f" else i + 1
        return j + 1 if j < n and texto[j] == "\u20e3" else i + 1
    if not _emoji_base(c):
        return i + 1
    j = i + 1
    while True:
        while j < n and (texto[j] in "\ufe0f\u20e3" or 0x1F3FB <= ord(texto[j]) <= 0x1F3FF or 0xE0020 <= ord(texto[j]) <= 0xE007F):
            j += 1  # variation selector, keycap, skin tone, tag characters
        if j + 1 < n and texto[j] == "\u200d" and _emoji_base(texto[j + 1]):  # a ZWJ chain (family, profession)
            j += 2
            continue
        return j


def longitud_x(texto: str, url_peso: int, ancho_peso: int) -> int:
    """X's weighted count: a link weighs url_peso (the punctuation that closes a sentence after it does not belong to
    it); an emoji sequence (flag, emoji with a skin tone or variation selector, ZWJ family) is one block of
    ancho_peso; any other wide character weighs ancho_peso; a variation selector on its own weighs 0."""
    def enlace(m):
        url = m.group(0)
        return "x" * url_peso + url[len(url.rstrip(URL_FINAL)):]
    texto = unicodedata.normalize("NFC", URL.sub(enlace, texto))
    total, i = 0, 0
    while i < len(texto):
        j = _fin_emoji(texto, i)
        if j > i + 1:
            total += ancho_peso
            i = j
            continue
        c, i = texto[i], i + 1
        if c != "\ufe0f":
            total += ancho_peso if peso_x(c) == 2 else 1
    return total


def secciones(texto: str) -> dict:
    """Splits a channel file by its `## es` / `## en` headings. Any other `##` heading ends the language section."""
    partes, actual = {}, None
    for linea in texto.splitlines():
        t = linea.strip()
        m = re.match(r"^##\s+(" + "|".join(IDIOMAS) + r")\s*$", t)
        if m:
            actual = m.group(1)
            partes.setdefault(actual, [])
        elif re.match(r"^##\s+\S", t):
            actual = None
        elif actual:
            partes[actual].append(linea)
    return {k: "\n".join(v) for k, v in partes.items()}


def idiomas_repetidos(texto: str) -> list:
    todos = re.findall(r"(?m)^##\s+(" + "|".join(IDIOMAS) + r")\s*$", texto)
    return sorted({i for i in todos if todos.count(i) > 1})


def apartado(texto: str, titulo: str) -> str:
    m = re.search(r"(?ms)^##\s+" + re.escape(titulo) + r"\s*$(.*?)(?=^## |\Z)", texto)
    return m.group(1) if m else ""


def campo(texto: str, *nombres) -> str:
    for n in nombres:
        m = re.search(r"(?mi)^[\s>*-]*\*{0,2}" + re.escape(n) + r"\s*:\s*\*{0,2}[ \t]*(.*)$", texto)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def canales_pedidos(ficha: str) -> list:
    out = []
    for linea in apartado(ficha, "Canales").splitlines():
        c = linea.strip().lstrip("-*").strip().strip("`").lower()
        if c:
            out.append(c)
    return out


def sin_imagenes(texto: str) -> str:
    return IMAGEN.sub("", texto).strip()


MARCA_X = re.compile(r"(?m)^\*\*\d+/(?:\d+)?\*\*\s*")  # **1/** or **1/4**


def posts_x(seccion: str):
    """(text before the first marker, posts). Each post starts with **n/** or **n/m**; without markers the whole
    section is one post."""
    trozos = MARCA_X.split(sin_imagenes(seccion))
    if len(trozos) == 1:
        return "", ([trozos[0].strip()] if trozos[0].strip() else [])
    return trozos[0].strip(), [t.strip() for t in trozos[1:] if t.strip()]


# ---- image headers (no Pillow) ----

def dimensiones(ruta: Path):
    """(width, height) of a WebP, PNG, JPEG or GIF, or None when the header is truncated or not understood."""
    d = ruta.read_bytes()
    try:
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            if len(d) < 24 or d[12:16] != b"IHDR":
                return None
            return _con_area(*struct.unpack(">II", d[16:24]))
        if d[:6] in (b"GIF87a", b"GIF89a"):
            return _con_area(*struct.unpack("<HH", d[6:10]))
        if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
            if len(d) < 20 or len(d) < struct.unpack("<I", d[4:8])[0] + 8:
                return None  # the RIFF size says more bytes than the file has: truncated
            tipo = d[12:16]
            if tipo == b"VP8X" and len(d) >= 30:
                return _con_area(1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little"))
            if tipo == b"VP8L" and len(d) >= 25 and d[20] == 0x2F:
                bits = int.from_bytes(d[21:25], "little")
                return _con_area((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
            if tipo == b"VP8 " and len(d) >= 30 and d[23:26] == b"\x9d\x01\x2a":
                return _con_area(int.from_bytes(d[26:28], "little") & 0x3FFF, int.from_bytes(d[28:30], "little") & 0x3FFF)
        if d[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(d):
                if d[i] != 0xFF:
                    i += 1
                    continue
                marca = d[i + 1]
                if marca in (0xD8, 0x01) or 0xD0 <= marca <= 0xD7 or marca == 0xFF:
                    i += 1 if marca == 0xFF else 2
                    continue
                if 0xC0 <= marca <= 0xCF and marca not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", d[i + 5:i + 9])
                    return _con_area(w, h)
                i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    except (struct.error, IndexError):
        pass
    return None


def _con_area(ancho: int, alto: int):
    return (ancho, alto) if ancho > 0 and alto > 0 else None


def paginas_pdf(ruta: Path):
    """Page count of a PDF (page objects, else the largest /Count), or None."""
    d = ruta.read_bytes()
    if not d.startswith(b"%PDF"):
        return None
    n = len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", d))
    if n:
        return n
    cuentas = [int(x) for x in re.findall(rb"/Count\s+(\d+)", d)]
    return max(cuentas) if cuentas else None


def alt_por_idioma(celda: str) -> dict:
    out = {}
    for m in re.finditer(r"(?:^|\s/\s)\s*([a-z]{2})\s*:\s*(.*?)(?=\s/\s+[a-z]{2}\s*:|$)", celda.strip()):
        out[m.group(1)] = m.group(2).strip()
    return out


def tabla_imagenes(ficha: str):
    """{path: (alt cell, channels cell)} from `## Imágenes`, or None when the section is missing."""
    if not re.search(r"(?m)^##\s+Imágenes\s*$", ficha):
        return None
    filas = {}
    for fila in apartado(ficha, "Imágenes").splitlines():
        celdas = [c.strip() for c in fila.strip().strip("|").split("|")]
        if len(celdas) < 2 or celdas[0] in ("Imagen", "") or set(celdas[0]) <= set("-: "):
            continue
        filas[celdas[0].strip("`")] = (celdas[1], celdas[2] if len(celdas) > 2 else "")
    return filas


# ---- the checks ----

def _hueco(m) -> str:
    t = m.group(0).strip()
    return "…" if t.endswith("…") and "{{" not in t else t


def comprobar_canal(canal, texto, idiomas, reglas, prefijos=()):
    f = []
    nombre = canal + ".md"
    partes = secciones(texto)
    for i in idiomas:
        if not partes.get(i, "").strip():
            f.append(f"{nombre}: no «## {i}» section; add it with the post in that language")
    for i in idiomas_repetidos(texto):
        f.append(f"{nombre}: «## {i}» appears more than once; merge the sections into one")
    for i in partes:
        if i not in idiomas:
            f.append(f"{nombre}: language «{i}» is not in the piece; remove the section or add it to «Idiomas:» in ficha.md")
    for j in jerga(texto, prefijos):
        f.append(f"{nombre}: internal jargon «{j}»; move it to «## Uso interno» in ficha.md and remove it from the post")
    for m in HUECO.finditer(texto):
        f.append(f"{nombre}: template gap «{_hueco(m)}» left; write the text")
    for i in idiomas:
        t = sin_imagenes(partes.get(i, ""))
        if not t:
            continue
        if canal == "x":
            n_max, mp = regla(reglas, "x", "longitud"), regla(reglas, "x", "hilo_posts")
            url_peso, ancho = regla(reglas, "x", "url_peso"), regla(reglas, "x", "simbolo_ancho_peso")
            previo, posts = posts_x(t)
            if previo:
                f.append(f"{nombre} ({i}): text before «**1/**»; start every post with a marker (**1/**, **2/**…) "
                         "or move that text into the first post")
            if not mp["min"] <= len(posts) <= mp["max"]:
                f.append(f"{nombre} ({i}): {len(posts)} posts; a thread has {mp['min']} to {mp['max']} (**1/**, **2/**…); "
                         "split or merge the posts")
            for k, p in enumerate(posts, 1):
                n = longitud_x(p, url_peso, ancho)
                if n > n_max:
                    f.append(f"{nombre} ({i}) post {k}: {n} weighted characters (max {n_max}; a link counts "
                             f"{url_peso}, an emoji {ancho}); shorten it by {n - n_max}")
        elif canal == "linkedin":
            mx = regla(reglas, "linkedin", "longitud")
            if len(t) > mx:
                f.append(f"{nombre} ({i}): {len(t)} characters (max {mx}); shorten it by {len(t) - mx}")
        elif canal == "discord":
            mx = regla(reglas, "discord", "mensaje")
            for k, b in enumerate(re.split(r"(?m)^---\s*$", t), 1):
                if len(b.strip()) > mx:
                    f.append(f"{nombre} ({i}) message {k}: {len(b.strip())} characters (max {mx}); "
                             "split it with a line containing only ---")
        elif canal == "reddit":
            m = re.search(r"(?mi)^\*\*(?:Título|Titulo|Title)\s*:\*\*[ \t]*(.+)$", t)
            mx = regla(reglas, "reddit", "titulo")
            if not m:
                f.append(f"{nombre} ({i}): no title; add a line «**Título:** …» (or «**Title:** …»)")
            elif len(m.group(1).strip()) > mx:
                f.append(f"{nombre} ({i}): title of {len(m.group(1).strip())} characters (max {mx}); shorten it")
    return f


def comprobar_reddit(ficha):
    f = []
    for etiqueta, nombres in (("Subreddit", ("Subreddit", "Subreddits")), ("Normas leídas", ("Normas leídas", "Normas leidas")),
                              ("Autopromoción", ("Autopromoción", "Autopromocion"))):
        v = campo(ficha, *nombres)
        if not v or v == "…":
            f.append(f"ficha.md: reddit.md needs «{etiqueta}:» in ficha.md; paste the subreddit rules and write the "
                     f"«{etiqueta}:» line")
        elif etiqueta == "Normas leídas":
            m = FECHA.search(v)
            try:
                date.fromisoformat(m.group(0))
            except (AttributeError, ValueError):
                f.append(f"ficha.md: «Normas leídas:» «{v}» has no valid AAAA-MM-DD date; write the day you read the rules")
    return f


def canales_de_celda(celda: str) -> list:
    return [c for c in (x.strip("`*_ ").lower() for x in re.split(r"[,;\s]+", celda)) if c]


def comprobar_imagenes(carpeta, ficha, texto_canales, idiomas, reglas, prefijos=()):
    f = []
    orden = f"{RENDER} {carpeta}"
    tabla = tabla_imagenes(ficha)
    if tabla is None:
        f.append("ficha.md: no «## Imágenes» section; add the table | Imagen | Texto alternativo | Canales |")
        tabla = {}
    # the `Imagen:` lines of each channel
    lineas, pares = {}, set()
    for canal, texto in texto_canales.items():
        for m in IMAGEN.finditer(texto):
            ruta = m.group(1).strip().strip("`*_ ")
            if not RENDERS.match(ruta):
                f.append(f"{canal}.md: «Imagen: {ruta}» is not a render; point to medios/<name>{formatos(reglas, canal)[0]} "
                         "(or .pdf)")
            else:
                lineas.setdefault(canal, [])
                if ruta not in lineas[canal]:
                    lineas[canal].append(ruta)
                if not (carpeta / ruta).is_file():
                    f.append(f"{canal}.md: «Imagen: {ruta}» does not exist; render it ({orden})")
    for canal, rutas in lineas.items():
        for ruta in rutas:
            if not (carpeta / ruta).is_file():
                continue
            if ruta not in tabla:
                f.append(f"{canal}.md: «{ruta}» is not in «## Imágenes» of ficha.md; add a row with its alt text")
            elif canal not in canales_de_celda(tabla[ruta][1]):
                f.append(f"{canal}.md: «{ruta}» is not listed for «{canal}» in «## Imágenes» of ficha.md; add «{canal}» "
                         "to the Canales cell of its row")
            pares.add((canal, ruta))
    # the rows of `## Imágenes`
    for ruta, (alt, celda) in tabla.items():
        if not ruta.startswith("medios/"):
            continue
        porIdioma = alt_por_idioma(alt)
        for i in idiomas:
            if not porIdioma.get(i) or porIdioma[i] == "…":
                f.append(f"ficha.md: «{ruta}» has no alt text in «{i}»; write «{i}: …» in its alt cell (es: … / en: …)")
        for j in jerga(alt, prefijos):
            f.append(f"ficha.md: alt text of «{ruta}» has internal jargon «{j}»; remove it")
        if not (carpeta / ruta).is_file():
            f.append(f"ficha.md: «{ruta}» does not exist; render it ({orden})")
        elif ruta.endswith(".webp"):
            mini = ruta.replace(".webp", "-mini.webp")
            if not (carpeta / mini).is_file():
                f.append(f"ficha.md: «{ruta}» has no -mini.webp; render it again ({orden})")
            elif dimensiones(carpeta / mini) is None:
                f.append(f"{mini}: not a valid image; render it again ({orden})")
        for c in canales_de_celda(celda):
            if c in texto_canales and ruta not in lineas.get(c, []):
                f.append(f"ficha.md: «{ruta}» lists channel «{c}» but {c}.md has no «Imagen: {ruta}» line; add the line "
                         f"or remove «{c}» from the Canales cell")
            if c in texto_canales and (carpeta / ruta).is_file():
                pares.add((c, ruta))
    for canal, ruta in sorted(pares):
        f += comprobar_archivo(carpeta / ruta, ruta, canal, tabla.get(ruta, ("", ""))[0], reglas, orden)
    listadas = set(tabla)
    medios = carpeta / "medios"
    sueltas = [x for e in ("webp", "png", "jpg", "gif", "pdf") for x in medios.glob(f"*.{e}")]
    for img in sorted(sueltas):
        if not img.name.endswith("-mini.webp") and f"medios/{img.name}" not in listadas:
            f.append(f"medios/{img.name}: not in «## Imágenes» of ficha.md; add a row with its alt text or delete the file")
    fuente = medios / "fuente"
    for s in sorted(fuente.glob("*")):
        suf = s.suffix.lower()
        if suf in (".html", ".svg") and "{{" in s.read_text(encoding="utf-8", errors="replace"):
            f.append(f"medios/fuente/{s.name}: template gaps {{{{…}}}} left; fill them and render again")
        if suf in FUENTES and not any((medios / f"{s.stem}{e}").is_file() for e in (".webp", ".pdf")):
            f.append(f"medios/fuente/{s.name}: not rendered; run {orden}")
    return f


def comprobar_archivo(ruta, rel, canal, alt, reglas, orden):
    f = []
    if rel.endswith(".pdf"):
        if canal != "linkedin":
            return [f"{canal}.md: «{rel}» is a PDF and only LinkedIn takes a document; use a "
                    f"{formatos(reglas, canal)[0]} render"]
        peso, mx = ruta.stat().st_size, regla(reglas, "linkedin", "documento_bytes")
        if peso > mx:
            f.append(f"{rel}: {peso} bytes (LinkedIn max {mx}); export a lighter PDF")
        pags, mp = paginas_pdf(ruta), regla(reglas, "linkedin", "documento_paginas")
        if pags is None:
            f.append(f"{rel}: the page count cannot be read; render the PDF again ({orden})")
        elif pags > mp:
            f.append(f"{rel}: {pags} pages (LinkedIn max {mp}); cut the carousel")
        return f
    permitidos = formatos(reglas, canal)
    if Path(rel).suffix.lower() not in permitidos:
        f.append(f"{canal}.md: «{rel}» is a {Path(rel).suffix.lower()} and {canal} takes {', '.join(permitidos)}; "
                 f"point to medios/<name>{permitidos[0]} (the render writes it)")
    peso, mx = ruta.stat().st_size, regla(reglas, canal, "imagen_bytes")
    if mx and peso > mx:
        f.append(f"{rel}: {peso} bytes (max {mx} for {canal}); lower the quality or the size and render again")
    dim, mpx = dimensiones(ruta), regla(reglas, canal, "imagen_pixeles")
    if dim is None:
        f.append(f"{rel}: not a valid image; render it again ({orden})")
    elif mpx and dim[0] * dim[1] >= mpx:
        f.append(f"{rel}: {dim[0]}x{dim[1]} = {dim[0] * dim[1]} pixels (must be under {mpx} for {canal}); scale it down")
    amax = regla(reglas, canal, "alt_max")
    if amax:
        for i, t in alt_por_idioma(alt).items():
            if len(t) > amax:
                f.append(f"ficha.md: alt text «{i}» of «{rel}» has {len(t)} characters (max {amax} for {canal}); shorten it")
    return f


def comprobar(carpeta: Path, reglas=None, prefijos=()) -> list:
    try:
        reglas = reglas or cargar_reglas()
        validar_reglas(reglas)
    except ReglasIncompletas as e:
        return [str(e)]
    carpeta = Path(carpeta)
    f = []
    if not carpeta.is_dir():
        return ["the folder does not exist; create it as <dir>/AAAA-MM-DD/NN-<tema>"]
    padre = carpeta.resolve().parent.name
    try:
        ok_fecha = bool(FECHA.fullmatch(padre)) and bool(date.fromisoformat(padre))
    except ValueError:
        ok_fecha = False
    if not CARPETA_PIEZA.match(carpeta.resolve().name) or not ok_fecha:
        f.append("folder name: expected <dir>/AAAA-MM-DD/NN-<tema> (e.g. 2026-10-25/01-release); rename the folder")
    if not (carpeta / "ficha.md").is_file():
        f.append("no ficha.md; create it from the piece template (facts with their source)")
    mds = sorted(p.stem for p in carpeta.glob("*.md") if p.name != "ficha.md")
    if not (carpeta / "ficha.md").is_file():
        if not mds:
            f.append("no channel file; add <canal>.md (x, reddit, linkedin, discord)")
        return f
    ficha = (carpeta / "ficha.md").read_text(encoding="utf-8")
    for m in HUECO.finditer(ficha):
        f.append(f"ficha.md: template gap «{_hueco(m)}» left; write the text")
    if not re.search(r"(?m)^##\s+Publicado\s*$", ficha):
        f.append("ficha.md: no «## Publicado» section; add the table | Canal | Idioma | Fecha | Enlace |")
    pedidos = canales_pedidos(ficha)
    if not pedidos:
        f.append("ficha.md: no channels under «## Canales»; list one channel per line (x, reddit, linkedin, discord…)")
    for c in pedidos:
        if not (carpeta / f"{c}.md").is_file():
            f.append(f"{c}.md: listed under «## Canales» but missing; write it or remove the line")
    for c in mds:
        if c not in pedidos:
            if c in CONOCIDOS:
                f.append(f"{c}.md: channel not requested; delete the file or list «{c}» under «## Canales» in ficha.md")
            else:
                f.append(f"{c}.md: unknown channel file; list it under «## Canales» in ficha.md or delete the file")
    activos = [c for c in pedidos if (carpeta / f"{c}.md").is_file()]
    textos = {c: (carpeta / f"{c}.md").read_text(encoding="utf-8") for c in activos}
    declarados = [x.strip() for x in re.split(r"[,\s]+", campo(ficha, "Idiomas")) if x.strip()]
    if not declarados:
        f.append('no languages: add "Idiomas: es, en" to ficha.md')
    idiomas = declarados or sorted({i for t in textos.values() for i in secciones(t)}, key=IDIOMAS.index)
    for c in activos:
        f += comprobar_canal(c, textos[c], idiomas, reglas, prefijos)
    if "reddit" in activos:
        f += comprobar_reddit(ficha)
    f += comprobar_imagenes(carpeta, ficha, textos, idiomas, reglas, prefijos)
    return list(dict.fromkeys(f))


def piezas(arg: Path) -> list:
    """A piece folder, or the pieces below a date folder or the whole <dir>."""
    if (arg / "ficha.md").is_file() or not arg.is_dir():
        return [arg]
    hijos = sorted(p for p in arg.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))
    out = []
    for h in hijos:
        if CARPETA_PIEZA.match(h.name) or (h / "ficha.md").is_file():
            out.append(h)
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", h.name):
            out += piezas(h)
    return out or [arg]


USO = ("usage: comprobar.py [--prefijos-tarea A,B,...] <dir>/AAAA-MM-DD/NN-<tema> [...]  "
       "(e.g. docs/difusion/2026-10-25/01-release; --prefijos-tarea adds the task-id prefixes of the project, e.g. INS,FLU)")


def main(args: list) -> int:
    args, prefijos = list(args), []
    while args and args[0].startswith("--"):
        opcion = args.pop(0)
        valor = opcion.partition("=")[2] if "=" in opcion else (args.pop(0) if args else "")
        if opcion.partition("=")[0] != "--prefijos-tarea":
            print(f"unknown option {opcion.partition('=')[0]}. {USO}")
            return 2
        prefijos += [x.strip().upper() for x in valor.split(",") if x.strip()]
        if not prefijos or not all(re.fullmatch(r"[A-Z][A-Z0-9]*", x) for x in prefijos):
            print(f"--prefijos-tarea needs prefixes of letters and digits separated by commas (INS,FLU). {USO}")
            return 2
    if not args:
        print(USO)
        return 2
    try:
        reglas, hay = cargar_reglas(), False
    except ReglasIncompletas as e:
        print(e)
        return 1
    for a in args:
        for p in piezas(Path(a)):
            for problema in comprobar(p, reglas, prefijos):
                hay = True
                print(f"{p}: {problema}")
    if not hay:
        print("OK")
    return 1 if hay else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
