# Harvest private-project-1 — 2026-11-05

De `5a7401fb` a `a048746e` (`scripts/harvest.py`). 1 commit: la actualización del proyecto al flujo v0.5.0 (`/gw-update`), con sus parches locales repuestos.

Sin skills del flujo cambiadas ni skills nuevas. Los scripts que difieren son `red-without-fix.sh` (un parche local, P1) y `tools/qa/check.sh` (script propio del proyecto, no copia del flujo).

## P1. `red-without-fix.sh`: no buscar código de test en textos y datos

- **Source:** `.claude/gw/scripts/red-without-fix.sh` (bloque `case "$f" in *.properties | *.json | *.md | …`, antes de calcular `hit`) @ `a048746e` (script)
- **What changes:** al comprobar si un archivo del arreglo toca código de test, saltar los archivos de texto y datos (`*.properties`, `*.json`, `*.md`, `*.yml`, `*.yaml`, `*.txt`, `*.csv`): no llevan tests y su prosa casa con `test_re` (p. ej. «improve it (URL…)» casa con `it(`), de modo que el arreglo de un texto se rechaza con exit 2 sin motivo. Lista de extensiones configurable (clave de `.claude/gw.json`), con su caso en `tests/` (un `.md` con `it (` en un arreglo no se rechaza; un `.py` con `def test_` sí).
- **Why it is general:** cualquier proyecto cuyo arreglo sea un texto, un JSON o un Markdown (idiomas, configuración, docs) cae en el falso positivo; el proyecto lo parcheó a mano y el parche se pierde en cada `/gw-update`.
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → E26

## Stays in the project

- `tools/qa/check.sh`: el check del proyecto (nombre homónimo del `scripts/check.sh` del flujo, pero distinto).
- `.githooks/commit-msg` (llamada a `tools/qa/sin-firma-claude.py`, que comprueba también que el autor no sea Claude): el flujo solo mira el mensaje (`agentSignatures`); la comprobación del autor ya está pedida en `docs/proposals/2026-10-26-private-project-1.md` (P2).
- `csk-` en `KEY_FORMATS` (clave de un proveedor de IA propio) y `frontend/package.json` en `check.yml`: parches locales ya propuestos en `docs/proposals/2026-10-26-private-project-1.md` (P3 y el apartado de menores).
- `docs/records/retro-2026-11-04-gw-update-050.md` R1 y R5 y el resto del commit: tests y renombrados del proyecto; R2, R3 y R4 ya están aplicadas en el flujo (v0.5.0).

## Already here

- `.claude/gw/scripts/*` y `.claude/skills/gw-*`: copias del flujo 0.5.0 (iguales a `e766106`/`73b2a23`), sin cambios del proyecto.
