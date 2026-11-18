# Harvest private-project-2 — 2026-11-18

De `d7e9e7ad` a `02e3d6af` (`scripts/harvest.py`). 33 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 3 retros (`docs/records/retro-2026-11-14-f1-cierre.md`, `docs/records/retro-2026-11-16-gw-update-0.7.0.md`,
`docs/records/retro-2026-11-18-gw-update-0.8.0.md` @ `303db7e`).
Recogida de apertura de la `0.9` (2026-11-18).

## P1. `apply.py --update` no escribe `pendingFile` y `move-pending` aborta

- **Source:** `docs/records/retro-2026-11-16-gw-update-0.7.0.md` R1 @ `e11710d` (retro)
- **What changes:** la migración de `scripts/apply.py` escribe `pendingFile` (`docs/records/pending.md`, el de la
  plantilla) en el `gw.json` del proyecto cuando deja la bitácora apuntando a él; si no puede, el aviso nombra la
  clave y la orden que la añade (hoy `handoff.py move-pending` falla con «pendingFile is not set»).
- **Why it is general:** todo proyecto que actualiza desde una versión anterior a D104 se queda con la bitácora
  migrada y la clave sin escribir.
- **Version bump:** patch
- **Status:** proposed

## P2. `AGENTS.md.gw-new` lista el check viejo tras ampliarlo `apply.py`

- **Source:** `docs/records/retro-2026-11-16-gw-update-0.7.0.md` R2 @ `e11710d` (retro)
- **What changes:** `scripts/apply.py` renderiza la propuesta de `AGENTS.md` con el `gw.json` ya migrado (el `check`
  con `ci-local.py --validate`), o `scripts/doctor.py` avisa si la lista del check de `AGENTS.md` no casa con `check`.
- **Why it is general:** cualquier actualización que amplíe `check` deja la propuesta describiendo otro.
- **Version bump:** patch
- **Status:** proposed

## P3. `handoff.py next-id B` en un plan con ids `F1.x`

- **Source:** `docs/records/retro-2026-11-16-gw-update-0.7.0.md` R3 @ `e11710d` (retro)
- **What changes:** `scripts/handoff.py` (`cmd_next_id`): cuando el prefijo pedido no encaja con el patrón de ids
  del plan, el mensaje dice los prefijos que el plan sí admite y nombra `--id-regex`/`taskId`
  (ya existen, pero el error no los menciona); la skill `retro` permite nombrar la tarea sin id si
  el plan no admite `B`. `--plan` vale también tras el subcomando (lo pide private-project-5).
- **Why it is general:** un plan con ids propios (`F1.x`) no puede dar el id que la retro manda pedir.
- **Version bump:** patch
- **Status:** proposed

## P4. `measure.py` por defecto empieza en el último `/clear` o compactación

- **Source:** `docs/records/retro-2026-11-14-f1-cierre.md` (Para Galivelop-workflow) @ `a8d7807` (script)
- **What changes:** `skills/gw-opt-tokens/scripts/measure.py`: sin `--since`, si el archivo de la sesión es el mismo
  tras un `/clear`, el tramo empieza en el último `/clear` o la última compactación, en vez de las últimas 24 h
  (B29 y D70 cubren otros casos: la sesión anterior de la rama y elegir la sesión correcta).
- **Why it is general:** mezcla el tramo medido con el anterior y obliga a pasar `--since` a mano.
- **Version bump:** patch
- **Status:** proposed

## P5. `gw-update` pregunta antes de aplicar las claves nuevas que crean archivos fuera de `.claude/`

- **Source:** `docs/records/retro-2026-11-18-gw-update-0.8.0.md` P2 @ `303db7e` (retro)
- **What changes:** `skills/gw-update/SKILL.md` (paso 2, tras el ensayo): si el ensayo crea archivos fuera de
  `.claude/` por una clave nueva (en la `0.8.0`, `agentsSkillsDir`), la skill lo presenta como decisión antes de
  `--update` y da la clave que lo apaga; `apply.py --dry-run --summary` agrupa lo creado por la clave que lo pide.
- **Why it is general:** una clave nueva con valor por defecto llena carpetas del proyecto sin que nadie lo haya
  decidido; pasa en cada proyecto que actualiza.
- **Version bump:** patch
- **Status:** proposed

## Joined to another proposal

- `apply.py` fusiona ganchos por matcher y no por script (retro `gw-update-0.8.0` P1 @ `303db7e`):
  instalador-wmf-tarkor P1 (`2026-11-18-instalador-wmf-tarkor.md`), con el `FAIL` de `doctor.py` que también pide.
- `next-id` con ids `F1.x` (P3 de aquí) lo pide también private-project-5 (`2026-11-18-private-project-5.md`).

## Stays in the project

- R4 (barrido de los leves de `gdev/server.py`): tarea del plan del proyecto.
- Tokens de sesión, revisión de F1.5 y `gdev install`: producto del proyecto.

## Already here

- El gancho `Stop` que bloquea con un subagente en segundo plano escribiendo: D88 (`scripts/before-stop.py` ya no
  bloquea y avisa); la retro misma concluye que bastaba usar worktree, como manda `gw-orchestrate-dealer`. Lo mismo
  propone portal-galivelop de hoy (`2026-11-18-portal-galivelop.md`).
- El registro de tokens deja el árbol sucio entre turnos (retro `gw-update-0.8.0` P3): B36 (`metrics.py
  stage-ledger`, el `pre-commit` lo añade al siguiente commit) y `scripts/before-stop.py`, que no cuenta
  `metrics.ledger`. El aviso que queda es el del gancho `Stop` del entorno de la nube, que no es del flujo.

## Nothing new

- `private-project-4`: sin commits desde la última recogida.
- `labs-log-detective`: sin commits desde la última recogida.
