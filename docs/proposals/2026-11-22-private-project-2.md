# Harvest private-project-2 — 2026-11-22

De `02e3d6af` a `d173bc5` (`scripts/harvest.py`). 68 commits; skills y scripts iguales a `da1a462` (`0.8.1`). Lo nuevo
sale de `docs/records/retro-2026-11-22-version-0.3.0.md` @ `93f23d3` (Ideas para Galivelop-workflow).

## P1. `gw-selector` lee la configuración por claves

- **Source:** `docs/records/retro-2026-11-22-version-0.3.0.md` G1 @ `93f23d3` (retro)
- **What changes:** `skills/gw-selector/SKILL.md` deja de mandar leer `.claude/gw.json` entero y usa
  `config.py get languages.docs.primary` y `config.py get selector.cases --json`.
- **Why it is general:** ~5,3k tokens por lectura; 106k arrastrados en una sesión de 22 llamadas. El selector corre al
  empezar cada tarea en todos los proyectos.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D147

## P2. El encargo de `gw-orchestrate-dealer` pide `red-without-fix.sh` por cada test nuevo

- **Source:** misma retro, G2 @ `93f23d3` (retro)
- **What changes:** la plantilla del encargo (y `templates/claude/agents/gw-worker.md`) pide correr
  `red-without-fix.sh "<orden>"` por cada test nuevo, con su salida en EVIDENCE.
- **Why it is general:** la regla está en `AGENTS.md` pero el encargo no la nombra; dos revisiones encontraron tests que
  pasaban sin su arreglo.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D153

## P3. La retro no da por hecho ids de letra

- **Source:** misma retro, G3 @ `93f23d3` (retro)
- **What changes:** `skills/retro/SKILL.md` dice usar el prefijo o esquema del proyecto (`taskId`/`--id-regex`) en vez
  de fijar `handoff.py next-id B`.
- **Why it is general:** con ids `F<n>.<m>` la orden de la retro falla. D134 ya mejoró el error; falta el texto.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D163

## P4. `ci-local.py --record` no deja `.gw-ci/` en el árbol

- **Source:** misma retro, G5 @ `93f23d3` (retro)
- **What changes:** el paso «pre-commit de la rama base» de `templates/github/check.yml` escribe en `$RUNNER_TEMP`, o
  `ci-local.py` borra lo que crea, o `dirty()` ignora `.gw-ci/`.
- **Why it is general:** la siguiente ejecución sale «(uncommitted changes)» y el gancho del PR rechaza la línea.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D160

## P5. Skill de revisión corta

- **Source:** misma retro, G4 @ `93f23d3` (idea de la persona, 2026-11-22)
- **What changes:** una skill para bloques pequeños: primero una pasada determinista (patrones conocidos, tests que
  pasan sin su arreglo) y luego una revisión ligera, con su fila en el selector, en vez de bajar el esfuerzo de
  `/code-review`.
- **Why it is general:** revisiones más baratas en cambios pequeños sin perder lo mecánico.
- **Version bump:** minor
- **Status:** aprobada (2026-11-22) → E82

## Stays in the project

- Nada: los commits F2.x son producto.

## Already here

- `changeSize.block` no ve un `Findings:` en su propio párrafo: D141 (`pending.md`, `0.10`).
