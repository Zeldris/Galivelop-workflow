# Harvest world-maker-fantasy — 2026-11-15

De `19d8c523` a `b098334e` (`scripts/harvest.py`). 170 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 3 retros. Recogida de cierre de la `0.7` (usuario, 2026-11-15).

## P1. El gancho `Stop` cuenta como sin subir los commits de `main` traídos por merge

- **Source:** `docs/records/retro-2026-11-14-narrador-tiempos.md` G1 @ `00774bed` (retro)
- **What changes:** `scripts/before-stop.py` (`unpushed()`) cuenta `@{u}..HEAD` cuando hay upstream; tras traer
  `main` eso incluye commits que ya están en `origin/main` («323 commits not pushed»). Contar
  `@{u}..HEAD --not --remotes`, con su test.
- **Why it is general:** cada proyecto trae `main` por merge al empezar una tarea (`AGENTS.md`).
- **Version bump:** patch
- **Status:** aprobada (2026-11-15) → D110

## P2. Un rojo solo es «preexistente» si falla igual en la rama protegida

- **Source:** `docs/records/retro-2026-11-14-lote-j-a-main.md` R1 @ `abe73304` (retro)
- **What changes:** el encargo de `skills/gw-orchestrate-dealer/SKILL.md` dice que un test en rojo solo se da por
  preexistente si falla igual en `origin/<protegida>`, con la salida de las dos corridas, y que la sesión principal lo
  comprueba antes de aceptarlo.
- **Why it is general:** un subagente dio un fallo propio por preexistente sin comprobarlo; nada en la skill lo
  impide.
- **Version bump:** patch
- **Status:** aprobada (2026-11-15) → D112

## P3. Avisos de lectura por Bash, configurables

- **Source:** `docs/records/retro-2026-11-15-ronda-nube-a-main.md` R2 @ `299ce60b` (retro), con
  `tools/qa/aviso-lectura.py` @ `b52696a1` (la lección del heredoc, `a6d408da`)
- **What changes:** clave `readPointers` (`{"<ruta>": "<orden>"}`) en `.claude/gw.json`, y `scripts/whole-read.py`
  ampliado a `Bash` (`cat`, `sed`, `grep` sobre esas rutas, sin contar el cuerpo de un heredoc) que avisa con la orden
  que sustituye la lectura.
- **Why it is general:** casi todas las lecturas caras van por Bash, y `whole-read.py` (B26) solo mira `Read`. El
  portal lo confirma: con el gancho instalado, leyó la bitácora entera 32 veces (1,49M; ver
  `2026-11-15-portal-galivelop.md`).
- **Version bump:** minor
- **Status:** aprobada (2026-11-15) → E58

## P4. `handoff.py set-row` y `close-row` imprimen la fila y su tamaño frente al límite

- **Source:** `docs/records/retro-2026-11-14-lote-j-a-main.md` R4 @ `abe73304` (retro)
- **What changes:** `scripts/handoff.py` ya imprime el número de caracteres de la fila; imprime también la fila
  resultante y `n/límite`, en `set-row` y en `close-row`.
- **Why it is general:** evita releer la bitácora o hacer `git diff` tras cada cambio de fila (22 lecturas en la
  retro).
- **Version bump:** minor
- **Status:** aprobada (2026-11-15) → E61

## Already here

- G2 (`merge=union` del registro en `.gitattributes`): B32, `scripts/apply.py` (`gitattributes_line`). La entrada B2
  de `docs/records/pending.md` que dice que `apply.py` no lo hace ya no es cierta: se quita.

## Stays in the project

- Puerta de pruebas, tandas, lotes y P450: trabajo del juego.
