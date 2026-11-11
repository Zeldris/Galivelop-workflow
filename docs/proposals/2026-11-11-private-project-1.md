# Harvest private-project-1 — 2026-11-11

De `aefe95ab` a `1f98db62` (`scripts/harvest.py`). 7 commits: mantenimiento de dependencias (MT-1…MT-8), la fase A
del 1.11 y la skill propia de avisos de actualización. Sin skills ni scripts del flujo cambiados; lo nuevo sale de 5
retros. Recogida de cierre de la `0.6` (H18).

## P1. Aviso al leer entera la bitácora o el `log`

- **Source:** `docs/records/retro-2026-11-05-fase-a-1-11.md` T1 @ `f1ddfbc` y `docs/records/retro-2026-11-09-mt-seguridad.md` R1 @ `7bbbf70` (retro)
- **What changes:** un gancho `PreToolUse` (lectura o `cat`/`head`/`tail` del archivo `log`) que avisa y apunta a
  `recover.py --state` y `handoff.py`; archivos vigilados configurables en `.claude/gw.json`.
- **Why it is general:** en el proyecto, 19 lecturas enteras de la bitácora costaron ~371k tokens; pasa en cualquier
  proyecto con bitácora larga.
- **Version bump:** minor
- **Status:** proposed

## P2. `measure.py --since` elige la sesión que cubre el periodo

- **Source:** `docs/records/retro-2026-11-05-fase-a-1-11.md` R3 @ `f1ddfbc` (retro)
- **What changes:** `skills/gw-opt-tokens/scripts/measure.py` toma hoy la sesión más reciente y `--since` solo filtra
  respuestas; con `--since`, debe escoger (o sumar) las sesiones cuyo rango cubre el periodo. Caso en `test_measure.py`.
- **Why it is general:** es un fallo de medida en cualquier proyecto que mida un periodo pasado.
- **Version bump:** patch
- **Status:** proposed

## P3. `handoff.py close-row` y `set-row` aceptan la rama igual

- **Source:** `docs/records/retro-2026-11-07-scout-updates.md` R1 @ `359b18d` (retro)
- **What changes:** `close-row` toma la rama posicional y `--text`; `set-row`, el texto posicional y `--branch`. Que
  los dos acepten ambas formas y el uso lo diga claro; tests en `tests/test_utils.py`.
- **Why it is general:** mezclarlas dio un error en uso real; la orden es la misma en todos los proyectos.
- **Version bump:** patch
- **Status:** proposed

## P4. `gw-scout-updates` con 2 subagentes en vez de 4

- **Source:** `docs/records/retro-2026-11-07-scout-updates.md` R2 @ `359b18d` (retro)
- **What changes:** el paso 3 de `skills/gw-scout-updates/SKILL.md` agrupa focos (dependencias + runtimes; IA +
  infraestructura) y recalcula la estimación. Ahorro medido ~136k por pasada.
- **Why it is general:** el coste de arranque por subagente se paga en cualquier proyecto; la cobertura la vigila
  `compare.py --report`.
- **Version bump:** patch
- **Status:** proposed

## P5. Aviso automático de sello caducado de `gw-scout-updates`

- **Source:** `docs/records/retro-2026-11-09-mt-java21.md` R3 @ `4f53b6c` (retro)
- **What changes:** `compare.py` ya detecta `changed`/`unsealed` a mano; `doctor.py` (o el check) lo llamaría y
  avisaría «re-sella con gw-scout-updates».
- **Why it is general:** un informe sellado sobre archivos que cambiaron después engaña en cualquier proyecto.
- **Version bump:** minor
- **Status:** proposed

## P6. El `pre-commit` rechaza un autor Claude con `agentSignatures: false`

- **Source:** `docs/records/retro-2026-11-09-mt-java21.md` T1 @ `4f53b6c` (retro)
- **What changes:** hoy solo avisa `session-start.sh`; `templates/githooks/pre-commit` rechazaría autor o committer
  `Claude <noreply@anthropic.com>` con el motivo y la orden `git config user.name/email`; test en `tests/test_hooks.py`.
  Ya pedida en `docs/proposals/2026-10-26-private-project-1.md` (P2): segunda vez que sale.
- **Why it is general:** la regla «sin firmas» es del flujo y hoy no la comprueba ningún gancho.
- **Version bump:** minor
- **Status:** proposed

## P7. Revisión de diffs triviales sin subagente; arreglos de la fase 1 a uno barato

- **Source:** `docs/records/retro-2026-11-09-mt-node24.md` T2 @ `dc816ce` y `docs/records/retro-2026-11-05-fase-a-1-11.md` T2 @ `f1ddfbc` (retro)
- **What changes:** en `skills/gw-selector/SKILL.md` y la fase 1 de `AGENTS.md`: un diff sin código fuente y de
  pocas líneas (umbral configurable) se revisa en la sesión principal; los arreglos de un `/code-review`, a un
  subagente `sonnet`.
- **Why it is general:** evita ~68k de arranque de subagente para un diff trivial en cualquier proyecto.
- **Version bump:** minor
- **Status:** proposed

## Stays in the project

- `docs/records/retro-2026-11-07-scout-updates.md` T2 y R3, `docs/records/retro-2026-11-09-mt-seguridad.md` R2-R4:
  notas locales (su `gw-opt-tokens.md`, hitos de seguridad, despliegue propio).

## Already here

- `docs/records/retro-2026-11-07-scout-updates.md` T1 (check callado): `scripts/check.sh --quiet` / `GW_CHECK_QUIET`.
