# Harvest private-project-1 — 2026-11-03

De `693ec58d` a `5a7401fb` (`scripts/harvest.py`). 8 commits; sin cambios propios en skills ni scripts del flujo.

Sin skills ni scripts del flujo cambiados en el proyecto; las skills `opt-ai`, `opt-tokens`, `orchestrate-dealer` y `selector` son copias viejas con otro nombre de las `gw-*` actuales (no son propuesta). Los hallazgos reales son las ideas de las retros.

## P1. Aviso de presupuesto de compactaciones superado

- **Source:** `docs/registros/retro-2026-11-02-ar5.md` (G2), `retro-2026-11-02-ar3.md` (R1) y `retro-2026-10-27-hito-1.9.md` (T1/R2) @ `5a7401f` (retro)
- **What changes:** `recover.py --state` (tras compactar) lee el presupuesto de compactaciones que el log fija para la tarea (formato fijo, p. ej. `Compaction budget: N`, que la skill `gw-selector` ya manda escribir) y, si el contador de la tarea lo supera, dice «presupuesto superado: sube y pide `/clear` o reparte con `gw-orchestrate-dealer`». Hoy solo imprime «compare with the budget» (`scripts/recover.py` ~l. 380) y nada lo comprueba; `gw-selector` y `handoff.py` fijarían el formato.
- **Why it is general:** tres retros distintas lo piden; en una sola tarea hubo 11 compactaciones sin aviso. Cualquier proyecto con el presupuesto del `gw-selector` tiene el mismo hueco.
- **Version bump:** minor
- **Status:** aprobada (2026-11-03) → B14

## P2. Test del check: `class …(TestCase)` después de `unittest.main()`

- **Source:** `docs/registros/retro-2026-11-02-ar5.md` (G1) @ `5a7401f` (retro)
- **What changes:** una comprobación de `ast` (pocas líneas) en el check de tests de Python del flujo que falle si un archivo de tests define una `TestCase` después de la llamada a `unittest.main()`: esa clase nunca corre y el check sigue en verde. Con su caso en `tests/`.
- **Why it is general:** el fallo es silencioso (tests que parecen existir y no corren) y cualquier proyecto con tests `unittest` puede caer; el flujo lo usa también aquí.
- **Version bump:** minor
- **Status:** aprobada (2026-11-03) → E19

## P3. `handoff.py close-row --text` comprueba el límite de 600

- **Source:** `docs/registros/retro-2026-11-02-ar6.md` (R3a) @ `5a7401f` (retro)
- **What changes:** `cmd_close_row` aplica el mismo tope (`LIMIT`) y el mismo escape de `|` que `cmd_set_row`: si `--text` pasa de 600, no toca el archivo y dice la orden que arregla. Hoy `scripts/handoff.py` (~l. 648) no comprueba nada y lo rechaza después el `commit-msg`/pre-push.
- **Why it is general:** `set-row` ya lo hace (propuesta P7 anterior); `close-row` quedó sin ello. Es el mismo contrato en dos órdenes.
- **Version bump:** patch
- **Status:** no elegida (2026-11-03)

## P4. Aviso de ramas remotas con commits fuera de `main` al empezar

- **Source:** `docs/registros/retro-2026-11-02-flujo-v043.md` (R1) @ `5a7401f` (retro)
- **What changes:** `session-start.sh` (o `recover.py --state`) lista en una línea cada rama remota con commits no integrados en la rama protegida y cuántos (tope ~10, como ya hace `prepush-branches.sh` para los choques de ids), para que la sesión no dé por hecho que todo está en `main`.
- **Why it is general:** el flujo trabaja por relevos con varias ramas subidas; el síntoma (suponer que todo está fusionado) no depende del proyecto. Coste: una llamada a `git for-each-ref` + `rev-list --count` por rama; solo aviso.
- **Version bump:** minor
- **Status:** aprobada (2026-11-03) → D40

## P5. Antes de subir, correr los tests relacionados sobre lo tocado

- **Source:** `docs/registros/retro-2026-11-02-ar6.md` (R3b) @ `5a7401f` (retro)
- **What changes:** el paso «commit en cada punto estable» de `AGENTS.md`/plantilla del flujo (y `docs/es|en/config.md`, `relatedTests`) nombra correr los `relatedTests` sobre los archivos tocados antes del commit, no solo en el `pre-push`. Texto; sin código nuevo (`related-tests.sh` ya existe).
- **Why it is general:** el `pre-push` rechazó tres subidas por tests que esa orden habría visto antes; vale para todo proyecto con `relatedTests`.
- **Version bump:** patch
- **Status:** no elegida (2026-11-03)

## Stays in the project

- `docs/registros/retro-2026-11-02-ar7.md` (R4): `cobertura.py` rechaza una fase ✅ sin «retro ✅» y `cerrar.py` avisaría; ambos son scripts del proyecto (no existen en el flujo), así que el aviso va allí.
- `docs/registros/retro-2026-10-27-hito-1.9.md` (R1): `fusionar.sh` con `--ff-only`; el flujo fusiona con `--no-ff` y mensaje propio a propósito (`scripts/merge-branch.sh` l. 106: deja rastro de cada rama de subagente); es preferencia, no fallo general.
- `docs/registros/retro-2026-11-02-ar8.md`, `retro-2026-11-03-ar21.md` (salvo `research`, abajo): trabajo propio del proyecto (admin, modelos de Groq, SSRF), sin idea para el flujo.
- Commits `fix(ia)`, `fix(admin)`, `fix(publicaciones)`, `feat(sesion)`, etc. (AR-1…AR-22): código de producto, no del flujo.
- `docs/registros/retro-2026-11-02-flujo-v043.md`: las otras tres propuestas de esa tanda (`test_re`, aviso de `/home/user`, filas «Tarea en curso») ya están en `docs/proposals/2026-10-26-private-project-1.md` y en el flujo (véase abajo).

## Already here

- `.claude/skills/{opt-tokens,orchestrate-dealer,selector,opt-ai}/SKILL.md`: copias viejas con otro nombre de `skills/gw-opt-tokens`, `gw-orchestrate-dealer`, `gw-selector`, `gw-opt-ai`.
- `.claude/skills/{gw-init,gw-media-content,gw-media-content-now,gw-update,pr,retro}` y `.claude/gw/scripts/{config.py,doctor.py,session-start.sh}`: iguales a versiones anteriores del flujo (0.4.3), sin cambios del proyecto.
- `docs/registros/retro-2026-10-27-hito-1.9.md` (T2): el diff resumido por archivo y la fusión sin leer el diff entero, en `skills/gw-orchestrate-dealer/SKILL.md` (l. 29 `git diff --stat`, l. 78-80 formato `DONE/COMMIT/EVIDENCE`, l. 88 `git log -1 --stat`).
- `docs/registros/retro-2026-10-27-hito-1.9.md` (R4): leves pendientes de la rama, resuelto de otro modo en `skills/gw-orchestrate-dealer/SKILL.md` l. 118-119 (los leves van al log y no se revisan de nuevo en el PR).
- `docs/registros/retro-2026-11-03-ar21.md` (`research`): `skills/research/SKILL.md` ya lanza la investigación en un agente en segundo plano que escribe el `.md`; lo que falta (modelo barato / umbral de 3 búsquedas) es una afinación menor que se puede ver con `gw-opt-tokens` si el usuario la quiere.
- `docs/registros/retro-2026-11-02-flujo-v043.md` (aviso `/home/user`): `scripts/session-start.sh` l. 47-62 y `scripts/session_log.py` (`cloud_start`).
