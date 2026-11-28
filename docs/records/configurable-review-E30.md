# E30 · Revisión de valores configurables: hallazgos

Auditoría de solo lectura (2026-11-28) de `scripts/`, `.githooks/` y sus esquemas, en cuatro partes (A-D). Cada
hallazgo lleva el id de su parte; el detalle fila a fila estuvo en los informes de trabajo y aquí queda lo decidido.
Cuenta: 91 filas, 43 «pasa a clave», 42 «se queda por contrato», 4 «ya configurable, falta documentar» y 2 cerradas
al comprobarlas.

## Comprobado al consolidar

- A15: el esquema ya declara `hookStdinWait` con `minimum` 0,1 y `maximum` 60; sin hallazgo.
- D1: `stopPushMarkerMaxAge` vale 3600 s (60 min) y es otro concepto que los 1440 min del `pre-push`: hace falta una
  clave propia.
- C4/C5: `protectedPaths` vale `[]` y `config-guard.py` y `review-before-main.sh` no la leen; sus listas protegen la
  instalación del flujo (seguridad), no son una preferencia del proyecto.
- D21: `modes.carefulExempt` ya está en `docs/es/config.md`; sin hallazgo.

## Ola 1: pasan a clave (propuesta, sin cambiar el comportamiento por defecto)

| Id | Qué | Clave y defecto |
|---|---|---|
| A1 | Programas cuyo texto entre comillas inversas cuenta como orden (`handoff.py` RUNNERS) | `runnableCommands`, la lista actual |
| A2 | Filas de la bitácora que cualquier commit puede tocar (FREE_ROWS) | `handoff.freeRows`, `["Actualizado","Updated","Tests"]` |
| A3 | Texto de fila cerrada por idioma (CLOSED_TEXT) | `handoff.closedText`, los actuales |
| A8 | Patrón de etiqueta de versión de `archive` (`v[0-9]*`) | `releaseTagPattern`, `v[0-9]*` |
| A10 | `origin/main` fijo en un mensaje de `handoff.py` | usar `protectedBranch` (ya clave) |
| B1-B3 | Tiempos de `scout compare` (60), ImageMagick (30) y `gh auth status` (10) en `doctor.py` | `doctor.timeoutSeconds.{scout,imagemagick,gh}` |
| B4 | Marcadores de stack del bloque `.gitignore` (`STACK_MARKERS`) | `gitignoreStackMarkers`, la tabla actual |
| C1 | `GIT_TIMEOUT` 10 s de `config-guard.py` | `configGuard.gitTimeout`, 10 |
| C2 | `review-before-main.sh` lanza git sin tiempo límite (un `fetch` colgado bloquea el gancho) | `reviewGitTimeout`, 120 (0 = sin límite) |
| C8 | `metrics.gitTimeout` solo la aplica `quality`; el resto de `metrics.py` usa 30 | ampliar su alcance, mismo defecto |
| C9 | Fila `metrics` de `config.md` sin `gitTimeout` en el defecto | solo documentación |
| C21 | Argumentos de Playwright fijos en `front.py` | `front.playwrightArgs`, los actuales |
| D1 | `-mmin +1440` del `pre-push` (marcadores de push huérfanos) | `pushMarkerOrphanMinutes`, 1440 |
| D2/D3/D5 | `GIT_TIMEOUT` 10 s de `task.py`, 30 s de `questions-guard.py`, 10 s de `context_guard.py` | `questions.gitTimeout` 30, `contextGuard.gitTimeout` 10, `taskRecord.gitTimeout` 10 |
| D4 | `VENDORED_TIMEOUT` 30 s de `scope-guard.py` | `scopeGuard.vendoredTimeout`, 30 |
| D13 | `head -n 5` de hallazgos en el `pre-commit` | leer `privateCheck.maxHits` (10) |
| D14 | Detectores de secretos del `pre-commit` (`KEY_FORMATS`, `PROVIDER`, `NAME`) | `privateCheck.keyFormats` y `secretNames`, solo **añaden** a los actuales |
| D15 | Dominios de correo siempre válidos (`example.*`) | `privateCheck.allowDomains`, los tres actuales |
| D18 | Nombres `gw-worker` y `gw-reviewer` en `subagent-cap.py` | `subagentCap.worker`, `subagentCap.reviewer` |
| D20 | `before-stop.py` fija `.claude/worktrees/` mientras `careful.py` lee `modes.carefulWorktrees` | leer la clave existente |
| D26 | Comandos que cuentan como lectura entera en `whole-read.py` | `wholeReadCommands`, la lista actual |
| D11, D27, D28 | `tail -n` fijos (30, 10, 5, 20) del log de un check fallido | reutilizar `checkTailLines` (40) |

## Ola 2: leves, a `pendingFile`

A7 (recortes de mensajes), B10 (tope de líneas de las skills aparte de `instructionLines`), C3 y D29 (`--deepen=200`),
C20 (`npm ci` sin límite de tiempo), D6, D7 (`CI_MARK_KEEP`), D9 (`--max-count=20`), D10, D12, D16 (8000 bytes
binario), D17, D19 (10 páginas de check-runs), D23, D24, D25 (recortes de presentación).

## Se quedan fijos (contrato o seguridad)

- C4/C5 (listas de rutas protegidas de `config-guard.py` y `review-before-main.sh`): protegen la instalación del
  flujo; hacerlas configurables permitiría debilitar el gancho. Tienen tres copias que pueden divergir: unificarlas
  en una constante compartida va a `pendingFile`.
- Parsers de shell, verbos de `gh`/`curl`, formatos de trailer, sufijos `.gw-new`/`.gw-tmp`, listas de archivos que
  instala el flujo, convenciones de Claude Code, especificaciones CSS y de herramientas, límites internos del
  analizador (`depth`) y listas del propio repo del flujo (`names-check.py`, `generated-copy.py`): A4-A6, A9, A11-A14,
  A16, A17, B5-B9, B11-B14, C6, C7, C10, C11, C14-C19, C22-C25, D8, D22, D30-D34.

## Ya configurable, falta documentar

C12 (`BASE_ENV` es el mínimo fijo de `ciLocalPassEnv`) y C13 (qué cubre `ciSystemCommands`: comprobar si cubre los
verbos de `PACKAGE_VERB`), más C9 de arriba. Comprobar A18 (cada clave de `SUBAGENT_KEYS` en `config.md`).

## Decisiones

Q-59..Q-64 respondidas, todas a (2026-11-28; `docs/questions.md`): una clave de tiempo por script con su defecto actual, `privateCheck.keyFormats`/`secretNames` solo añaden, los `tail -n` leen `checkTailLines`.
