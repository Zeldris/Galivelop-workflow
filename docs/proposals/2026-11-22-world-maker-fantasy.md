# Harvest world-maker-fantasy — 2026-11-22

De `59a496f7` a `5590cdab` (`scripts/harvest.py`). 161 commits; skills y scripts iguales a `da1a462` (`0.8.1`) salvo
el parche local de `test_measure.py`. Lo nuevo sale de 3 retros (`retro-2026-11-19-gw-update-0.8.1.md`,
`retro-2026-11-20-ronda-local-2.md` y otra).

## P1. `scope-guard.py`: los archivos de cierre cuentan como del flujo

- **Source:** `docs/records/retro-2026-11-20-ronda-local-2.md` @ `93dacb2c` (retro)
- **What changes:** `flow_files()` de `scripts/scope-guard.py` incluye `roadmapFiles` y `pendingFile`.
- **Why it is general:** cerrar cualquier tarea toca el roadmap y los pendientes: ~120 desviaciones falsas en una rama.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D149

## P2. `scope-guard` dice por qué no saltó lo vendored

- **Source:** `docs/records/retro-2026-11-19-gw-update-0.8.1.md` C1 @ `ce2a060d` (retro)
- **What changes:** sin clon del flujo, `vendored_set()` vacío da una sola línea con la clave (`workflowClone`) o la
  orden que lo arregla, en vez de callar.
- **Why it is general:** sin `workflowClone` en la nube salieron 108 avisos de alcance de copias del flujo (B44 no
  saltaba nada).
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D150

## P3. `doctor.py` avisa si `.claude/agents/gw-worker.md` está ignorado

- **Source:** `docs/records/retro-2026-11-20-ronda-local-2.md` @ `93dacb2c` (retro)
- **What changes:** la ruta entra en `MUST_BE_TRACKED` de `scripts/doctor.py`; `apply.py` añade `!.claude/agents/` si
  el `.gitignore` tiene `.claude/*`.
- **Why it is general:** un `.gitignore` con `.claude/*` dejó el `gw-worker` (B28) fuera de git sin aviso.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D159

## P4. `measure.py` midió la sesión de otra rama

- **Source:** `docs/records/retro-2026-11-20-ronda-local-2.md` @ `93dacb2c` (retro)
- **What changes:** con la sesión nueva por debajo de `minCalls`, el fallback de B29 midió una sesión de otra rama;
  sospecha: `branch_of()` toma el último `gitBranch`. Arreglo con un test del caso real; va con D144 (antes «D142»).
- **Why it is general:** la medición de `gw-opt-tokens` sale de otra sesión y lo dice como si fuera la correcta.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D151

## P5. `handoff.py set-row`/`close-row` ponen la fecha de hoy en «Actualizado»

- **Source:** `docs/records/retro-2026-11-19-gw-update-0.8.1.md` C2 @ `ce2a060d` (retro)
- **What changes:** al reescribir la fila de la rama, actualizan también «Actualizado/Updated».
- **Why it is general:** hoy el `commit-msg` rechaza el commit siguiente por la fecha vieja; rechazo evitable.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D154

## P6. Aviso falso de `Findings:` (E60)

- **Source:** `docs/records/retro-2026-11-19-gw-update-0.8.1.md` C3 @ `ce2a060d` (retro)
- **What changes:** `findingsWords` por defecto sin «hallazgo(s)»/«finding(s)» sueltos (quedan «arreglos de la
  revisión»/«review fixes»), o solo mira el asunto.
- **Why it is general:** un aviso que salta por la prosa enseña a ignorar el de verdad.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D155

## P7. Marca de tarea vieja o cerrada

- **Source:** C1b de `retro-2026-11-19-gw-update-0.8.1.md` y «Marca de tarea vieja» de
  `retro-2026-11-20-ronda-local-2.md` (retro)
- **What changes:** el aviso de `scope-guard` en `pre-commit` propone `task.py current <id>` cuando el `Refs:` nombra
  otra tarea, y `gw-update` limpia o avisa de la marca de una tarea cerrada antes de `--update`.
- **Why it is general:** 35 y 108 avisos de alcance falsos; B46 solo limpia la marca con `close-row`.
- **Version bump:** minor
- **Status:** aprobada (2026-11-22) → E80

## Joined to another proposal

- `test_measure.py` con el flujo instalado (parche local reaplicado dos veces): con
  `2026-11-22-instalador-wmf-tarkor.md` P1. Va con él un leve: `handoff.py check <ruta>` compara con la bitácora de
  `HEAD` aunque se le pase otra ruta.

## Stays in the project

- `content` estrechado a sus carpetas; C4 (`workflowClone` frente a `GW_WORKFLOW` por máquina, aplazado); C5
  (desconectar Claude Docs); commits de producto (QA-514 a QA-520).

## Already here

- Salto de lo vendored en `scope-guard`: B44 (lo que falta es P2). Filtro por `gitBranch`: B29 (lo que falla es P4).
  Limpiar la marca al cerrar: B46.
