# Harvest private-project-6 — 2026-11-18

De `46248251` a `61ce5096` (`scripts/harvest.py`). 164 commits; sin skills ni scripts del flujo cambiados (un
script coincidente por nombre, `gimg/doctor.py`, ver «Stays in the project»). Lo nuevo sale de 7 retros (la de la
tanda L8 no trae nada; la de `hoja-datos` @ `98c1d30` es la de la actualización a `0.8.0`). Recogida de apertura de la `0.9` (2026-11-18).

## P1. `handoff.py` rechaza una tabla de estado que pierde una fila

- **Source:** `docs/records/retro-2026-11-16-barrido-b.md` P1 @ `33dab49` (retro)
- **What changes:** `scripts/handoff.py` (su comprobación de la tabla, hoy solo filas mal formadas, largas o repetidas)
  rechaza también una fila `Tarea en curso` que desaparece respecto a `HEAD` sin que la rama se haya cerrado; con su
  caso en `tests/`.
- **Why it is general:** un script que edita la bitácora puede pegar dos filas y perder una sin que ningún check lo
  vea; pasó y solo lo halló la revisión por casualidad.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → D135

## P2. La plantilla del encargo del dealer cubre el defecto en el archivo hermano

- **Source:** `docs/records/retro-2026-11-16-barrido-b.md` P4 @ `33dab49` (retro)
- **What changes:** la plantilla del encargo de `skills/gw-orchestrate-dealer/SKILL.md` añade «si el mismo defecto
  está en otro archivo que tocas, arréglalo también o dilo» y «devuelve, por cada punto, si lo hiciste entero o en
  parte».
- **Why it is general:** un barrido dejó un leve a medias y otro duplicado en un archivo tocado; costó un segundo
  subagente.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → E69

## P3. `gw-selector` y el gancho de inicio recomiendan el `gw-worker` para barridos y arreglos de revisión

- **Source:** `docs/records/retro-2026-11-16-barrido-brand.md` P1 @ `1fcb048` y
  `docs/records/retro-2026-11-17-barrido-color.md` P1 @ `110621c` (retros; la misma idea dos veces)
- **What changes:** `skills/gw-selector/SKILL.md`, al empezar un barrido o los arreglos de una revisión con 2 o más
  puntos, recomienda repartirlo a un `gw-worker` y no hacerlo en la principal; el aviso de `scripts/session-start.sh`
  lo repite. Hoy `scripts/subagent-cap.py` solo avisa cuando ya se lanza un `general-purpose`.
- **Why it is general:** la sesión principal hace el barrido ella misma (dos veces seguidas) con el coste de contexto
  que el reparto evita.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → E68

## P4. `whole-read.py` puede rechazar rutas, no solo avisar

- **Source:** `docs/records/retro-2026-11-16-fm-recortar.md` G1 @ `71c535f` (retro)
- **What changes:** `scripts/whole-read.py` y `scripts/config.py` aceptan una clave nueva (p. ej. `wholeReadDenyPaths`,
  con su orden alternativa) cuyas rutas se rechazan al leerlas enteras; `docs/es/config.md` y `docs/en/config.md` la
  explican, con tests.
- **Why it is general:** sin ella, un proyecto que quiere un rechazo (no un aviso) necesita su propio
  `leer-entero.py` junto al del flujo.
- **Version bump:** minor
- **Status:** aprobada (2026-11-18) → E70

## P5. `merge-branch.sh` distingue un worktree bloqueado por un agente vivo

- **Source:** `docs/records/retro-2026-11-16-fm-recortar.md` G2 @ `71c535f` (retro)
- **What changes:** `scripts/merge-branch.sh`, cuando `git worktree remove` falla con «locked» (un agente vivo), dice
  que se limpiará al acabar el agente (o lo deja en una lista para la siguiente pasada) en vez de sugerir
  `git worktree remove --force`; con su caso en los tests.
- **Why it is general:** hoy el aviso propone `--force`, justo lo que no se debe hacer con un agente vivo.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → D136

## P6. `doctor.py` avisa de `branchCheck: related` con `relatedTests` vacío

- **Source:** `docs/records/retro-2026-11-16-fm-recortar.md` G3 @ `71c535f` (retro)
- **What changes:** `scripts/doctor.py` avisa cuando `branchCheck` es `related` y `relatedTests` no tiene órdenes
  (el `pre-push` corre entonces el check entero sin que nadie lo haya elegido); con su caso en los tests.
- **Why it is general:** la configuración por defecto de todo proyecto nuevo cae en ese caso hasta que rellena
  `relatedTests`.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → D137

## Joined to another proposal

- `.claude/settings.json` registra `whole-read.py` dos veces para `Read` tras la `0.8.0` (retro `hoja-datos` @
  `98c1d30`, revisión de la fase 3): instalador-wmf-tarkor P1 (`2026-11-18-instalador-wmf-tarkor.md`).

## Already here

- W1 (`red-without-fix.sh` sin `git stash`): D98 (`scripts/red-without-fix.sh` copia los archivos aparte); ya en
  `docs/proposals/2026-11-14-private-project-6.md` P1.
- W2 (check de «Al empezar» filtrado): `scripts/check.sh --quiet` y `checkTailLines`
  (`docs/proposals/2026-11-14-private-project-6.md`).
- W3 (tope de llamadas en el encargo) y su repetición en la retro `hoja-datos` (un encargo de arreglos sin tope hizo
  92 llamadas): la plantilla del encargo de `skills/gw-orchestrate-dealer/SKILL.md` ya lo lleva («At ~25 tool calls,
  commit…», l. 70) además del tope de ~30 del paso 2; el encargo de 92 llamadas no salió de esa plantilla.
- W4 (rechazar autor o committer `noreply@anthropic.com`): `authorDeny` (E41, E55) en `.claude/gw.json`,
  `scripts/agent-signatures.py` y el aviso de `scripts/session-start.sh` (D21).
- Barrido B P2 (registro de tokens sin ensuciar el árbol): B36 (el `pre-commit` lo añade al siguiente commit) y
  `scripts/before-stop.py`, que ya no cuenta `metrics.ledger` como árbol sucio.
- El `tests-for.py --run` sin `tests/__init__.py` (retro de la tanda L8): lo lleva el proyecto en su «Pendiente»,
  sin propuesta todavía.

## Stays in the project

- Los barridos de `gimg/brand.py`, el validador `SquareTests`, la regla de `REVIEW.md` y el resto de las tandas de
  imágenes y marca.
- `gimg/doctor.py`: choque de nombre con `scripts/doctor.py` del flujo; es el diagnóstico del producto, no una copia.
