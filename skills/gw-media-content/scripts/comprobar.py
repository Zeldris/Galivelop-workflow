#!/usr/bin/env python3
"""gw-media-content: checks a piece folder before anything is published.

    python3 comprobar.py <dir>/AAAA-MM-DD/NN-<tema> [more folders]

A folder argument may also be a date folder or the whole <dir> (default docs/difusion): every piece below it is
checked. No config: the per-network limits are read from ../reglas.json.

Piece layout:
    ficha.md              facts with their source; sections `## Canales` (one channel per line), `## Imágenes`
                          (table: Imagen | Texto alternativo `es: ... / en: ...` | Canales), `## Publicado`;
                          optional line `Idiomas: es, en`; for reddit.md a `## Reddit` block with the lines
                          `Subreddit:`, `Normas leídas:` (AAAA-MM-DD) and `Autopromoción:`
    <canal>.md            one per channel in `## Canales`, with a `## es` / `## en` section per language;
                          `Imagen: medios/<name>.webp` lines say which render goes with the post
    medios/fuente/        sources: .html .svg .png .jpg .jpeg
    medios/               renders: <name>.webp + <name>-mini.webp, or <name>.pdf (LinkedIn document carousel)
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
FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
CARPETA_PIEZA = re.compile(r"^\d{2}-[a-z0-9][a-z0-9-]*$")
HUECO = re.compile(r"\{\{[^}]*\}\}|(?m:(?:^|\s)…(?:\s|$))|<tema>|AAAA-MM-DD")
IMAGEN = re.compile(r"(?mi)^[ \t>*_-]*Imagen:[ \t]*(.*)$")
# Internal jargon: finding numbers (P3, F12), task ids (QA-215), branch names, WIP: markers.
NO_TAREAS = {"GPT", "UTF", "ISO", "HTTP", "SHA", "RFC", "CVE", "USB", "COVID", "MP", "AAA", "SO", "TLS", "ES", "EN"}
JERGA = re.compile(
    r"\b[PF]\d{1,3}\b|\b[A-Z]{2,5}-\d{1,5}\b|\b(?:claude|feat|fix|chore|hotfix|release)/[\w./-]*\w|\bccr-[\w-]*\w|\bWIP:"
)


def cargar_reglas(ruta=REGLAS) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def regla(reglas: dict, canal: str, clave: str):
    """Value of a rule, or None when the channel or the rule is not in reglas.json."""
    return reglas.get(canal, {}).get(clave, {}).get("valor")


def jerga(texto: str) -> list:
    return sorted({m.group(0) for m in JERGA.finditer(texto) if m.group(0).split("-")[0] not in NO_TAREAS})


def peso_x(c: str) -> int:
    """twitter-text weight: ranges 0-4351, 8192-8205, 8208-8223 and 8242-8247 weigh 1, the rest 2."""
    o = ord(c)
    if o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247:
        return 1
    return 2


def longitud_x(texto: str, url_peso: int = 23, ancho_peso: int = 2) -> int:
    """X's weighted count: a link is url_peso; emoji and wide characters weigh ancho_peso (variation selectors and
    joined emoji parts weigh 0)."""
    texto = unicodedata.normalize("NFC", URL.sub("x" * url_peso, texto))
    total, unir = 0, False
    for c in texto:
        if c == "️" or unir:
            unir = False
            continue
        unir = c == "‍"
        total += ancho_peso if peso_x(c) == 2 else 1
    return total


def secciones(texto: str) -> dict:
    """Splits a channel file by its `## es` / `## en` headings."""
    partes, actual = {}, None
    for linea in texto.splitlines():
        m = re.match(r"^##\s+(" + "|".join(IDIOMAS) + r")\s*$", linea.strip())
        if m:
            actual = m.group(1)
            partes[actual] = []
        elif actual:
            partes[actual].append(linea)
    return {k: "\n".join(v) for k, v in partes.items()}


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


def posts_x(seccion: str) -> list:
    """Each post starts with **n/**; without markers the whole section is one post."""
    trozos = re.split(r"(?m)^\*\*\d+/\*\*\s*", sin_imagenes(seccion))
    if len(trozos) == 1:
        return [trozos[0].strip()] if trozos[0].strip() else []
    return [t.strip() for t in trozos[1:] if t.strip()]


# ---- image headers (no Pillow) ----

def dimensiones(ruta: Path):
    """(width, height) of a WebP, PNG or JPEG, or None if the header is not understood."""
    d = ruta.read_bytes()
    try:
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", d[16:24])
        if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
            tipo = d[12:16]
            if tipo == b"VP8X":
                return (1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little"))
            if tipo == b"VP8L" and d[20] == 0x2F:
                bits = int.from_bytes(d[21:25], "little")
                return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
            if tipo == b"VP8 " and d[23:26] == b"\x9d\x01\x2a":
                return (int.from_bytes(d[26:28], "little") & 0x3FFF, int.from_bytes(d[28:30], "little") & 0x3FFF)
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
                    return (w, h)
                i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    except (struct.error, IndexError):
        pass
    return None


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

def comprobar_canal(canal, texto, idiomas, reglas):
    f = []
    nombre = canal + ".md"
    partes = secciones(texto)
    for i in idiomas:
        if not partes.get(i, "").strip():
            f.append(f"{nombre}: no «## {i}» section; add it with the post in that language")
    for i in partes:
        if i not in idiomas:
            f.append(f"{nombre}: language «{i}» is not in the piece; remove the section or add it to «Idiomas:» in ficha.md")
    for j in jerga(texto):
        f.append(f"{nombre}: internal jargon «{j}»; move it to «## Uso interno» in ficha.md and remove it from the post")
    for m in HUECO.finditer(texto):
        f.append(f"{nombre}: template gap «{m.group(0).strip()}» left; write the text")
    for i in idiomas:
        t = sin_imagenes(partes.get(i, ""))
        if not t:
            continue
        if canal == "x":
            n_max, mp = regla(reglas, "x", "longitud"), regla(reglas, "x", "hilo_posts") or {}
            posts = posts_x(t)
            if mp and not mp["min"] <= len(posts) <= mp["max"]:
                f.append(f"{nombre} ({i}): {len(posts)} posts; a thread has {mp['min']} to {mp['max']} (**1/**, **2/**…); "
                         "split or merge the posts")
            for k, p in enumerate(posts, 1):
                n = longitud_x(p, regla(reglas, "x", "url_peso") or 23, regla(reglas, "x", "simbolo_ancho_peso") or 2)
                if n_max and n > n_max:
                    f.append(f"{nombre} ({i}) post {k}: {n} weighted characters (max {n_max}; a link counts "
                             f"{regla(reglas, 'x', 'url_peso')}, an emoji 2); shorten it by {n - n_max}")
        elif canal == "linkedin":
            mx = regla(reglas, "linkedin", "longitud")
            if mx and len(t) > mx:
                f.append(f"{nombre} ({i}): {len(t)} characters (max {mx}); shorten it by {len(t) - mx}")
        elif canal == "discord":
            mx = regla(reglas, "discord", "mensaje")
            for k, b in enumerate(re.split(r"(?m)^---\s*$", t), 1):
                if mx and len(b.strip()) > mx:
                    f.append(f"{nombre} ({i}) message {k}: {len(b.strip())} characters (max {mx}); "
                             "split it with a line containing only ---")
        elif canal == "reddit":
            m = re.search(r"(?mi)^\*\*(?:Título|Titulo|Title)\s*:\*\*[ \t]*(.+)$", t)
            mx = regla(reglas, "reddit", "titulo")
            if not m:
                f.append(f"{nombre} ({i}): no title; add a line «**Título:** …» (or «**Title:** …»)")
            elif mx and len(m.group(1).strip()) > mx:
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


def comprobar_imagenes(carpeta, ficha, texto_canales, idiomas, reglas):
    f = []
    tabla = tabla_imagenes(ficha)
    if tabla is None:
        f.append("ficha.md: no «## Imágenes» section; add the table | Imagen | Texto alternativo | Canales |")
        tabla = {}
    for ruta, (alt, _) in tabla.items():
        if not ruta.startswith("medios/"):
            continue
        porIdioma = alt_por_idioma(alt)
        for i in idiomas:
            if not porIdioma.get(i) or porIdioma[i] == "…":
                f.append(f"ficha.md: «{ruta}» has no alt text in «{i}»; write «{i}: …» in its alt cell (es: … / en: …)")
        for j in jerga(alt):
            f.append(f"ficha.md: alt text of «{ruta}» has internal jargon «{j}»; remove it")
        if not (carpeta / ruta).is_file():
            f.append(f"ficha.md: «{ruta}» does not exist; render it (node render.mjs {carpeta})")
        elif ruta.endswith(".webp") and not (carpeta / ruta.replace(".webp", "-mini.webp")).is_file():
            f.append(f"ficha.md: «{ruta}» has no -mini.webp; render it again (node render.mjs {carpeta})")
    for canal, texto in texto_canales.items():
        for m in IMAGEN.finditer(texto):
            ruta = m.group(1).strip().strip("`*_ ")
            if not re.match(r"^medios/[^/]+\.(webp|pdf)$", ruta):
                f.append(f"{canal}.md: «Imagen: {ruta}» is not a render; point to medios/<name>.webp (or .pdf)")
                continue
            if not (carpeta / ruta).is_file():
                f.append(f"{canal}.md: «Imagen: {ruta}» does not exist; render it (node render.mjs {carpeta})")
                continue
            if ruta not in tabla:
                f.append(f"{canal}.md: «{ruta}» is not in «## Imágenes» of ficha.md; add a row with its alt text")
            f += comprobar_archivo(carpeta / ruta, ruta, canal, tabla.get(ruta, ("", ""))[0], reglas)
    listadas = set(tabla)
    medios = carpeta / "medios"
    for img in sorted(list(medios.glob("*.webp")) + list(medios.glob("*.pdf"))):
        if not img.name.endswith("-mini.webp") and f"medios/{img.name}" not in listadas:
            f.append(f"medios/{img.name}: not in «## Imágenes» of ficha.md; add a row with its alt text or delete the file")
    fuente = medios / "fuente"
    for s in sorted(fuente.glob("*")):
        suf = s.suffix.lower()
        if suf in (".html", ".svg") and "{{" in s.read_text(encoding="utf-8", errors="replace"):
            f.append(f"medios/fuente/{s.name}: template gaps {{{{…}}}} left; fill them and render again")
        if suf in FUENTES and not any((medios / f"{s.stem}{e}").is_file() for e in (".webp", ".pdf")):
            f.append(f"medios/fuente/{s.name}: not rendered; run node render.mjs {carpeta}")
    return f


def comprobar_archivo(ruta, rel, canal, alt, reglas):
    f = []
    if rel.endswith(".pdf"):
        if canal != "linkedin":
            return [f"{canal}.md: «{rel}» is a PDF and only LinkedIn takes a document; use a .webp render"]
        peso, mx = ruta.stat().st_size, regla(reglas, "linkedin", "documento_bytes")
        if mx and peso > mx:
            f.append(f"{rel}: {peso} bytes (LinkedIn max {mx}); export a lighter PDF")
        pags, mp = paginas_pdf(ruta), regla(reglas, "linkedin", "documento_paginas")
        if pags is None:
            f.append(f"{rel}: the page count cannot be read; render the PDF again (node render.mjs)")
        elif mp and pags > mp:
            f.append(f"{rel}: {pags} pages (LinkedIn max {mp}); cut the carousel")
        return f
    peso, mx = ruta.stat().st_size, regla(reglas, canal, "imagen_bytes")
    if mx and peso > mx:
        f.append(f"{rel}: {peso} bytes (max {mx} for {canal}); lower the quality or the size and render again")
    dim, mpx = dimensiones(ruta), regla(reglas, canal, "imagen_pixeles")
    if mpx:
        if dim is None:
            f.append(f"{rel}: image size cannot be read; render it again (node render.mjs)")
        elif dim[0] * dim[1] >= mpx:
            f.append(f"{rel}: {dim[0]}x{dim[1]} = {dim[0] * dim[1]} pixels (must be under {mpx} for {canal}); scale it down")
    amax = regla(reglas, canal, "alt_max")
    if amax:
        for i, t in alt_por_idioma(alt).items():
            if len(t) > amax:
                f.append(f"ficha.md: alt text «{i}» of «{rel}» has {len(t)} characters (max {amax} for {canal}); shorten it")
    return f


def comprobar(carpeta: Path, reglas=None) -> list:
    reglas = reglas or cargar_reglas()
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
        f.append(f"ficha.md: template gap «{m.group(0).strip()}» left; write the text")
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
    idiomas = declarados or sorted({i for t in textos.values() for i in secciones(t)}, key=IDIOMAS.index)
    for c in activos:
        f += comprobar_canal(c, textos[c], idiomas, reglas)
    if "reddit" in activos:
        f += comprobar_reddit(ficha)
    f += comprobar_imagenes(carpeta, ficha, textos, idiomas, reglas)
    return f


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


def main(args: list) -> int:
    if not args:
        print("usage: comprobar.py <dir>/AAAA-MM-DD/NN-<tema> [...]  (e.g. docs/difusion/2026-10-25/01-release)")
        return 2
    reglas, hay = cargar_reglas(), False
    for a in args:
        for p in piezas(Path(a)):
            for problema in comprobar(p, reglas):
                hay = True
                print(f"{p}: {problema}")
    if not hay:
        print("OK")
    return 1 if hay else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
