#!/usr/bin/env python3
# galivelop-workflow v0.5.2
"""Fails when a NEW name in Spanish appears in the workflow's own files (A8: every name is in English).

Usage: python3 scripts/names-check.py

What is a name (the content of documents for people is not checked, only these):
  - the path of every file tracked by git (every folder and file name, docs/es/ included);
  - command-line options and subcommands: add_argument / add_parser in Python, case labels in shell;
  - names defined in Python (functions, classes, arguments, assigned variables, imports with `as`),
    found with `ast`;
  - functions and variables of shell scripts, and functions, variables and parameters of JavaScript (.mjs, .js);
  - keys of the workflow's JSON files (schema/, templates/, hooks/, skills/**);
  - CSS custom properties (--name:) in stylesheets, pages and scripts.

How it decides: the name is split into words (snake_case, kebab-case, camelCase, digits) and each word is looked
up in SPANISH_WORDS, a list of the repo's domain words in Spanish that are NOT also English words (real, final,
general, base, total, error, color, plan, idea, local... are deliberately absent). A letter with an accent or the
letter n with tilde in a name is Spanish too. To catch a word that slipped through, add it to SPANISH_WORDS.

Old names accepted on purpose (compatibility during 0.x, removed in 1.0) are NOT names that this repo defines in
code: they are strings in the migration tables of scripts/apply.py (OLD_SKILLS, OLD_SCRIPTS, OLD_SKILL_FILES,
OLD_FLAGS), scripts/config.py (LEGACY_PATHS) and the tests of those. A string is never a name for this check. What
is left (a legacy name that has to be a real option, a historic file) goes in EXCEPTIONS below, each with its
reason: the one list. A new entry needs a reason; an entry that no longer matches anything is reported, so the
list does not rot."""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# Spanish words of this repo's domain that are not English words (nor common English abbreviations: no `con`,
# `de`, `del`, `sin`, `solo`, `la`...). Plurals (-s, -es) are matched automatically.
SPANISH_WORDS = frozenset("""
abrir actualizar agente aguardar ahora ancho anadir antes anterior apuntar aplicar apunta archivo arreglo aviso
bajar barra bitacora bloque borrar buscar busca cabecera cada cadena cambiar cambio campo carga cargar carpeta
carrusel catalogo cerrar cierre cifra clave codigo comando comprobacion comprobado comprobar contar contenido copia
copiar correr crear cuando cuenta cuerpo dato datos decir desde despues devolver devuelve donde ejecutar ejemplo
empezar enlace enlaces entrada escribir estado explicar falla fallo falta fase fecha ficha filtrar fuente fusionar
guardia hasta hecho hoja hora idioma igual informe imprimir juntar lado leer limite linea lista llamar lleno mapa
marca marcado marcar medio medios medir mensaje migrar mismo mostrar nombre nota notas nuevo opcion opciones ordenar
orden otro otra para parar pegar pendiente personales plantilla poner por prefijo propuesta prueba quitar rama rango
recoger recogida recorte recortar recuperar reemplazar regla reglas registro relacionado relacionados reparto
repartir resultado resumen revisado revision rojo ruta salida salir separar siguiente sesion sufijo sumar tamano
tarea terminar texto tipo tope tras traspaso traer unir ultimo ultima umbral novedad palanca parche piloto segundo
segunda subida subir utilidades valor verde viejo visto volver
""".split())

# Old names accepted on purpose or historic files, with the reason. {kind: {name or path: reason}}. kind "path" is
# a tracked file path (exact); kind "name" is a defined name (exact). Nothing new goes here without a reason.
HISTORIC = "dated historic document (a record of what was decided then): its file name stays, links point to it"
OLD_OPTION = "test of an old Spanish name that is still accepted with a warning during 0.x (removed in 1.0)"
EXCEPTIONS = {
    "path": {
        "docs/proposals/2026-10-21-reparto.md": HISTORIC,
        "docs/proposals/2026-10-22-reparto.md": HISTORIC,
        "docs/proposals/2026-10-25-sin-novedades.md": HISTORIC,
        "docs/proposals/2026-10-26-sin-novedades.md": HISTORIC,
        "docs/proposals/2026-10-26-sin-novedades-2.md": HISTORIC,
        "docs/records/retro-2026-10-22-fase-5.md": HISTORIC,
        "docs/records/retro-2026-10-22-fases-0-4.md": HISTORIC,
        "docs/records/retro-2026-10-23-antes-de-main-0-3-0.md": HISTORIC,
        "docs/records/retro-2026-10-25-antes-de-main-0-4-0.md": HISTORIC,
        "docs/records/retro-2026-10-22-segunda-subida.md": HISTORIC,
        "docs/records/retro-2026-10-26-parche-0-4-1.md": HISTORIC,
        "docs/records/retro-2026-10-27-parche-0-4-2.md": HISTORIC,
        "docs/records/retro-2026-10-27-parche-0-4-3.md": HISTORIC,
        "docs/records/prompt-piloto-portal.md": HISTORIC,
        "docs/records/prompt-piloto-tarkor.md": HISTORIC,
        "docs/research/ref-agentic-openhands-palancas.md": HISTORIC,
    },
    "name": {
        "test_the_old_carrusel_prefix_is_a_carousel_with_a_warning": OLD_OPTION,
        "test_old_apuntar_option_warns_with_the_new_name_and_records": OLD_OPTION,
        "test_the_old_estado_flag_in_the_compact_hook_is_still_accepted": OLD_OPTION,
        "test_the_old_estado_json_is_read_with_a_warning_and_renamed_on_update": OLD_OPTION,
        "test_old_explicar_option_warns_with_the_new_name": OLD_OPTION,
        "test_old_rango_option_warns_with_the_new_name": OLD_OPTION,
    },
}

COPY_PREFIXES = (".claude/gw/", ".claude/skills/", ".githooks/")  # applied copy: derived from the sources
SKIP_CONTENT = (".md",)
ACCENTED = re.compile("[áéíóúñüÁÉÍÓÚÑÜ¿¡]")
WORD_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[a-z]+")


def words_of(name):
    out = []
    for chunk in re.split(r"[^A-Za-zÀ-ÿ]+", name):
        out.extend(w.lower() for w in WORD_RE.findall(chunk))
    return out


def spanish_word(word):
    if word in SPANISH_WORDS:
        return True
    return any(word.endswith(suf) and word[:-len(suf)] in SPANISH_WORDS for suf in ("s", "es"))


def spanish_reason(name):
    """Why `name` looks Spanish (the word or the accent), or None."""
    if ACCENTED.search(name):
        return "has an accented letter or a tilde"
    for word in words_of(name):
        if spanish_word(word):
            return f"has the Spanish word '{word}'"
    return None


class Report:
    def __init__(self):
        self.problems = []
        self.used = set()

    def name(self, kind, where, name, what):
        if name in EXCEPTIONS["name"]:
            self.used.add(("name", name))
            return
        reason = spanish_reason(name)
        if reason:
            self.problems.append(f"{where}: {what} '{name}' {reason}; use an English name")


def read_text(root, rel):
    try:
        return (Path(root) / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


# --- paths ---------------------------------------------------------------------------------------------------

def check_paths(rep, files):
    for rel in files:
        if rel in EXCEPTIONS["path"]:
            rep.used.add(("path", rel))
            continue
        for part in rel.split("/"):
            reason = spanish_reason(part)
            if reason:
                rep.problems.append(f"{rel}: path component '{part}' {reason}; rename the file or folder to English "
                                    f"(git mv)")
                break


# --- Python --------------------------------------------------------------------------------------------------

def _option_words(text):
    return text.lstrip("-")


def check_python(rep, rel, text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        line = f"{rel}:{getattr(node, 'lineno', 0)}"
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rep.name("py", line, node.name, "function")
        elif isinstance(node, ast.ClassDef):
            rep.name("py", line, node.name, "class")
        elif isinstance(node, ast.arg):
            rep.name("py", line, node.arg, "argument")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            rep.name("py", line, node.id, "variable")
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            rep.name("py", line, node.attr, "attribute")
        elif isinstance(node, ast.alias) and node.asname:
            rep.name("py", rel, node.asname, "import alias")
        elif isinstance(node, ast.ExceptHandler) and node.name:
            rep.name("py", line, node.name, "exception variable")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        rep.name("py", line, arg.value.lstrip("-"), "command-line option")
                for kw in node.keywords:
                    if kw.arg == "dest" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        rep.name("py", line, kw.value.value, "option destination")
            elif node.func.attr == "add_parser":
                for arg in node.args[:1]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        rep.name("py", line, arg.value, "subcommand")
                for kw in node.keywords:
                    if kw.arg == "aliases" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        for el in kw.value.elts:
                            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                rep.name("py", line, el.value, "subcommand")


# --- shell ---------------------------------------------------------------------------------------------------

HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][\w]*)\1")
SH_FUNC = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][\w:.-]*)\s*\(\)")
SH_ASSIGN = re.compile(r"^\s*(?:(?:local|declare|typeset|export|readonly)(?:\s+-[A-Za-z]+)*\s+)?([A-Za-z_]\w*)\+?=")
SH_DECL = re.compile(r"^\s*(?:local|declare|typeset|readonly)((?:\s+-[A-Za-z]+)*)\s+(.+)$")
SH_FOR = re.compile(r"^\s*for\s+([A-Za-z_]\w*)\s+in\b")
SH_READ = re.compile(r"\bread\b((?:\s+-\w+(?:\s+\d+)?)*)((?:\s+[A-Za-z_]\w*)+)")
SH_CASE = re.compile(r"^\s*(\(?)((?:--?[A-Za-z][\w-]*|[A-Za-z_][\w-]*|\*)(?:\|(?:--?[A-Za-z][\w-]*|[A-Za-z_][\w-]*|\*))*)\)")


def check_shell(rep, rel, text):
    terminator = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        where = f"{rel}:{lineno}"
        if terminator is not None:
            if raw.strip() == terminator:
                terminator = None
            continue
        code = raw.split(" #", 1)[0] if not raw.lstrip().startswith("#") else ""
        m = HEREDOC.search(code)
        if m:
            terminator = m.group(2)
        if not code.strip():
            continue
        for rx, what in ((SH_FUNC, "function"), (SH_ASSIGN, "variable"), (SH_FOR, "variable")):
            m = rx.match(code)
            if m:
                rep.name("sh", where, m.group(1), what)
        m = SH_DECL.match(code)
        if m:
            for tok in m.group(2).split():
                if re.match(r"^[A-Za-z_]\w*(=.*)?$", tok):
                    rep.name("sh", where, tok.split("=", 1)[0], "variable")
        m = SH_READ.search(code)
        if m:
            for tok in m.group(2).split():
                rep.name("sh", where, tok, "variable")
        m = SH_CASE.match(code)
        if m:
            for label in m.group(2).split("|"):
                if label != "*":
                    rep.name("sh", where, label.lstrip("-"), "case label (option or subcommand)")


# --- JavaScript ----------------------------------------------------------------------------------------------

JS_DECL = re.compile(r"\b(?:function|class)\s+([A-Za-z_$][\w$]*)")
JS_VAR = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)")
JS_DESTR = re.compile(r"\b(?:const|let|var)\s*[\[{]([^\]}=]*)[\]}]")
JS_PARAMS = re.compile(r"\bfunction\s*[\w$]*\s*\(([^)]*)\)|\(([^()]*)\)\s*=>")
JS_ARROW = re.compile(r"(?<![\w$)])([A-Za-z_$][\w$]*)\s*=>")


def _js_idents(chunk):
    for part in chunk.split(","):
        part = part.split("=", 1)[0].split(":")[-1].strip().lstrip(".")
        if re.fullmatch(r"[A-Za-z_$][\w$]*", part):
            yield part


def check_js(rep, rel, text):
    for lineno, raw in enumerate(text.splitlines(), 1):
        if raw.lstrip().startswith(("//", "*", "/*")):
            continue
        where = f"{rel}:{lineno}"
        for rx, what in ((JS_DECL, "function or class"), (JS_VAR, "variable"), (JS_ARROW, "parameter")):
            for m in rx.finditer(raw):
                rep.name("js", where, m.group(1), what)
        for m in JS_DESTR.finditer(raw):
            for ident in _js_idents(m.group(1)):
                rep.name("js", where, ident, "variable")
        for m in JS_PARAMS.finditer(raw):
            for ident in _js_idents(m.group(1) or m.group(2) or ""):
                rep.name("js", where, ident, "parameter")


# --- JSON keys and CSS variables -----------------------------------------------------------------------------

def _json_keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _json_keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _json_keys(value)


def check_json(rep, rel, text):
    try:
        data = json.loads(text)
    except ValueError:
        return
    seen = set()
    for key in _json_keys(data):
        if key not in seen:
            seen.add(key)
            rep.name("json", rel, key, "JSON key")


CSS_VAR = re.compile(r"(?<![\w-])--([A-Za-z][\w-]*)\s*:")


def check_css_vars(rep, rel, text):
    seen = set()
    for m in CSS_VAR.finditer(text):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            rep.name("css", rel, m.group(1), "CSS variable")


# --- driver --------------------------------------------------------------------------------------------------

JSON_DIRS = ("schema/", "templates/", "hooks/", "skills/")
CSS_EXTS = (".css", ".html", ".mjs", ".js", ".svg")


def kind_of(root, rel, text):
    if rel.endswith(".py"):
        return "py"
    if rel.endswith((".sh", ".bash")):
        return "sh"
    if rel.endswith((".mjs", ".js")):
        return "js"
    if "." not in Path(rel).name:
        first = text.split("\n", 1)[0]
        if first.startswith("#!") and "python" in first:
            return "py"
        if first.startswith("#!") and ("bash" in first or "sh" in first.split("/")[-1]):
            return "sh"
    return None


def check_files(root, files):
    """Problems (list of messages) for the given repo-relative files under `root`."""
    rep = Report()
    files = [f for f in files if not f.startswith(COPY_PREFIXES)]
    check_paths(rep, files)
    for rel in files:
        if rel.endswith(SKIP_CONTENT):
            continue
        text = read_text(root, rel)
        if text is None:
            continue
        kind = kind_of(root, rel, text)
        if kind == "py":
            check_python(rep, rel, text)
        elif kind == "sh":
            check_shell(rep, rel, text)
        elif kind == "js":
            check_js(rep, rel, text)
        if rel.endswith(".json") and rel.startswith(JSON_DIRS):
            check_json(rep, rel, text)
        if rel.endswith(CSS_EXTS):
            check_css_vars(rep, rel, text)
    if root_is_repo(root):  # the real repo: an exception that matches nothing is dead weight
        for kind in EXCEPTIONS:
            for name in EXCEPTIONS[kind]:
                if (kind, name) not in rep.used:
                    rep.problems.append(f"EXCEPTIONS in scripts/names-check.py lists the {kind} '{name}' that no "
                                        f"longer exists or is no longer Spanish; remove the entry")
    return rep.problems


def root_is_repo(root):
    return (Path(root) / "scripts" / "names-check.py").is_file()


def tracked_files(root):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, text=True)
    if out.returncode != 0:
        print("names-check: git ls-files failed; run it inside the repo", file=sys.stderr)
        sys.exit(2)
    return [f for f in out.stdout.split("\0") if f]


def main(argv=None):
    root = Path(__file__).resolve().parent.parent
    problems = check_files(root, tracked_files(root))
    for line in problems:
        print(f"names-check: {line}", file=sys.stderr)
    if problems:
        print(f"names-check: {len(problems)} Spanish name(s). Rename them to English; a legacy name accepted on "
              f"purpose goes in EXCEPTIONS in scripts/names-check.py with its reason.", file=sys.stderr)
        return 1
    print("names-check: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
