# Harvest world-maker-fantasy — 2026-11-14

De `3a10a3fa` a `19d8c523` (`scripts/harvest.py`). 14 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro (`docs/records/retro-2026-11-14-gw-update-0.6.md`). Recogida de la `0.7` (H20).

## P1. `Findings:` y `Retries:` fuera del último párrafo de trailers no cuentan

- **Source:** `docs/records/retro-2026-11-14-gw-update-0.6.md` R1 @ `4c60fc47` (retro; el caso, `f68916df`)
- **What changes:** el `commit-msg` (`templates/githooks/commit-msg`) rechaza una línea `Findings:` o `Retries:` a
  principio de línea fuera del último párrafo, con la orden que lo arregla (júntalo con `Refs:` y `Siguiente:`),
  con su test. Lo mismo trae private-project-2 (P1 de su archivo).
- **Why it is general:** git solo lee como trailers el último párrafo: con `Findings:` suelto, `change-size.py`
  (`block()`) y `recover.py --state` avisan de «review overdue» con la revisión hecha y `metrics.py quality` pierde
  los hallazgos. Ningún gancho lo coge hoy.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D97

## P2. El aviso de nombres viejos de `apply.py --update` no toca el texto histórico

- **Source:** `docs/records/retro-2026-11-14-gw-update-0.6.md` R4 @ `4c60fc47` (retro)
- **What changes:** `plan_legacy_names` (`scripts/apply.py`) deja fuera los `roadmapFiles` (tareas cerradas, texto
  histórico) y no propone un nombre nuevo que no existe en el proyecto. En WMF, la actualización cambió en
  `roadmap-front.md` `fusionar.sh` → `merge-branch.sh` y `mapa-agente.py` → `agent-map.py`, que allí no existen; la
  fase 1 tuvo que devolver el archivo.
- **Why it is general:** cualquier proyecto con tareas cerradas que citan nombres viejos recibe el mismo cambio
  equivocado.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D100

## P3. El ledger de métricas sin commits propios

- **Source:** `docs/records/retro-2026-11-14-gw-update-0.6.md` R3 @ `4c60fc47` (retro; commits de ruido `92c6e7fb`,
  `1be821e4`)
- **What changes:** lo que `metrics.record` apunta entra en el siguiente commit de trabajo (el `pre-commit` lo añade)
  en vez de en un commit «registro de tokens» propio. B32 (`merge=union` en los proyectos) quita los choques, no el
  ruido.
- **Why it is general:** cada sesión de cada proyecto deja hoy al menos un commit que solo trae el ledger.
- **Version bump:** minor
- **Status:** aprobada (2026-11-14) → B36

## Stays in the project

- R2 (MCP de Playwright apagado por defecto, `QA-335`): `.mcp.json` y ajustes del proyecto.
- `ciNodeDirs` en su `gw.json`: clave del proyecto, el flujo no la lee.
- `43a6e4fd`, `1f9cc325`: tests del proyecto sobre el flujo instalado.

## Already here

- P1-P5 de `docs/records/propuestas-flujo.md` (cosecha del 2026-11-02): recogidas en
  `2026-11-03-world-maker-fantasy.md`; P20 (`legacyNamesSkip`) ya está en `scripts/apply.py`.
