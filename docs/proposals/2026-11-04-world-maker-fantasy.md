# Harvest world-maker-fantasy — 2026-11-04

De `7dee044c` a `b995f816` (`scripts/harvest.py`). 164 commits, casi todos del juego; sin cambios en skills ni scripts
del flujo. Lo general sale de `docs/registros/retro-2026-11-03-ronda-puerta.md`.

## P1. Revisión por bloques en una rama larga

- **Source:** `AGENTS.md` y `.claude/gw/opt-tokens.md` @ `dc799b50` (retro, QA-292)
- **What changes:** en una rama larga, la fase 1 (`/code-review`) se adelanta a cada bloque cerrado (o cada N
  commits), solo del diff desde la última revisión; la de antes de `main` revisa lo que queda. Va en la fila «Closing
  a block or phase» de `skills/gw-selector/SKILL.md` y en «Ramas y `main`» de la plantilla de `AGENTS.md`.
- **Why it is general:** una sola revisión de 152 commits dejó módulos sin mirar, y el revisor lo dijo; le pasa a
  cualquier rama larga.
- **Version bump:** minor
- **Status:** aprobada (2026-11-04) → B18

## P2. `handoff.py next-id <prefijo>`: el siguiente id libre antes de numerar

- **Source:** `tools/roadmap/siguiente-id.py` @ `dc799b50` (script del proyecto, QA-290)
- **What changes:** un subcomando que reutiliza `free_id` de `scripts/handoff.py` (hoy solo lo usa `clash` en el
  `pre-push`) para dar el siguiente id libre mirando la copia y las ramas remotas, antes de dar de alta la tarea.
- **Why it is general:** la rama renumeró dos veces (QA-259 → 263 → 268) porque otra rama ya usaba el número; el
  `pre-push` lo detecta, pero tarde.
- **Version bump:** minor
- **Status:** aprobada (2026-11-04) → D48

## P3. Lo que se prueba con un doble lleva también una prueba con lo real

- **Source:** `tools/qa/humo-driver.sh` y `.github/workflows/ci.yml` @ `c70da9ce` (QA-291)
- **What changes:** una nota en `docs/es/patterns.md` (y en) y, si se quiere, una regla `(criterio)` en las
  plantillas de `REVIEW.md`: un componente probado con un doble tiene una prueba de humo con el real, que se omite en
  local si falta y falla en el CI.
- **Why it is general:** cuatro fallos (P400, P407 dos veces, P409) venían del driver real que los tests sustituían.
- **Version bump:** patch (solo documentación)
- **Status:** aprobada (2026-11-04) → E24

## Stays in the project

- `tools/roadmap/cobertura.py`, `cerrar.py` y la regla «SIN HITO: 0»: roadmap propio del juego.
- `escenario.sh`, `humo-driver.sh` y la recarga del driver: dependen del juego.
- Lo demás del rango: combate, cronista y compañeros.
