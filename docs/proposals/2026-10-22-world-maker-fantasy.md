# Harvest world-maker-fantasy — 2026-10-22

De `9cb05e50a063` a `11a201b7` (`scripts/recoger.py`, 61 commits). Segunda recogida. Las skills copiadas siguen
siendo `.claude/skills/<nombre>/SKILL.md`. El diff de `orchestrate-dealer` (+77 −74) es casi todo traducción y notas
del proyecto; lo nuevo y general desde `9cb05e5` son tres líneas (`29986476`) y se recogen en P1, P2 y P3. Dos retros
nuevas: `retro-2026-10-21-puerta-pruebas.md` y `retro-2026-10-22-pruebas-3-3.md`. No se repite nada de
`2026-10-21-world-maker-fantasy.md` ni de `2026-10-21-reparto.md`.

## P1. La revisión corta antes de seguir también vale sin worktree

- **Source:** `.claude/skills/orchestrate-dealer/SKILL.md` («Revisar lo que vuelve») y `docs/registros/retro-2026-10-21-puerta-pruebas.md` (propuesta 3, `QA-190`) @ 29986476 (skill, retro)
- **What changes:** en el paso «Review what returns» de `orchestrate-dealer`, la revisión corta de un subagente revisor (comparada con el contrato) se exige también al commit de un subagente que toca código **en la propia rama, sin worktree**, antes de seguir con el siguiente trozo, no solo a las ramas con worktree antes de fusionar.
- **Why it is general:** hoy la regla solo cubre ramas con worktree. Allí, el subagente de escenarios hizo commit directo en la rama y su código no se revisó hasta el `/code-review` final, que halló 11 fallos casi todos suyos.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P2. Tandas medidas por tamaño y por llamadas; capturas solo si el hallazgo es visual

- **Source:** `.claude/skills/orchestrate-dealer/SKILL.md` (pasos 1 y 2) y `retro-2026-10-21-puerta-pruebas.md` (propuesta 2, `QA-189`; medida) @ 29986476; confirmado en `retro-2026-10-22-pruebas-3-3.md` («Lo que funcionó») @ 11a201b7 (skill, retro)
- **What changes:** (a) en «Split», además del tope de ~60 llamadas, dimensionar el trozo de comprobación o prueba (6-8 puntos, no 11-14) y **partirlo al vuelo** si se acerca al tope: la mitad guarda el estado y la siguiente sigue; (b) en el encargo de un subagente que usa el navegador o el driver: capturar de pantalla solo si el hallazgo es visual, el resto por volcado de texto; (c) una línea equivalente en `opt-tokens` (imágenes como parte de lo que pesa el contexto de un subagente).
- **Why it is general:** medido en dos PR seguidos: con tandas de 11-14 se hicieron 87 y 99 llamadas con 15-19 capturas, ~95 % de lo que entró en el contexto; con 6-8 y partiéndolas, todas respetaron el tope de 60 (`opt-tokens`: 500 llamadas en 11 subagentes, contexto medio 56-84k). Nuestro tope de 60 está, pero no dice cómo dimensionar el trozo ni nada de capturas.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P3. El subagente lee su fila de la bitácora con `recuperar.py --estado`, no la bitácora entera

- **Source:** `.claude/skills/opt-tokens/proyecto.md` (viñeta «La bitácora entera en la principal», `QA-194`) y `retro-2026-10-21-puerta-pruebas.md` (propuesta 7) @ 29986476 (skill, retro)
- **What changes:** la plantilla de encargo de `orchestrate-dealer` dice «lee tu fila con `python3 .claude/gw/scripts/recuperar.py --estado`; el log entero solo al empezar una sesión nueva», y `opt-tokens` (cuerpo) añade «lecturas repetidas del log entero» a lo que busca en `LECTURAS POR ARCHIVO`.
- **Why it is general:** 12 lecturas de la bitácora, ~419k tokens arrastrados en una sesión. Tenemos `recuperar.py --estado` (plantilla `opt-tokens.md`) pero el encargo sigue diciendo «Read {log}» a secas, y la medida no señala este patrón.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P4. Un subagente cortado por el límite de la API se retoma, no se relanza

- **Source:** `docs/registros/retro-2026-10-22-pruebas-3-3.md` («Lo que funcionó», «Retomar con `SendMessage`») @ 11a201b7 (retro)
- **What changes:** una línea en `orchestrate-dealer` («Review what returns»): si un subagente se corta por límite de la API o del contexto sin devolver informe, se **continúa el mismo agente** con `SendMessage` (conserva lo leído y lo hecho) en vez de lanzar otro que empiece de cero; el estado en `log` y el commit siguen siendo el criterio de hecho. Un reintento tras un fallo real sigue subiendo de peldaño.
- **Why it is general:** distingue el corte externo (no es fallo del agente, no cuenta como reintento fallido) del fallo de verdad; no se perdió nada en la tanda cortada.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P5. El estado intermedio que guarda un subagente en el tope no se sube a git

- **Source:** `docs/registros/retro-2026-10-22-pruebas-3-3.md` (propuesta 5, `QA-199`, pendiente en el proyecto) y `367caf18` (quitó dos `.dump` de más) @ 11a201b7 (retro)
- **What changes:** en `orchestrate-dealer`, junto al tope de ~60 llamadas: lo que se guarda para que el siguiente siga (volcados, instantáneas, artefactos binarios) va a una carpeta ignorada (`logs/`); solo lo que el plan quiere conservar se sube, de forma explícita. El texto de estado sí va a la fila de `log`.
- **Why it is general:** cinco volcados de ~900 KB subieron en un PR y dos hubo que quitarlos, pero ya están en el historial para siempre. Cualquier proyecto con estado binario de pruebas tiene el riesgo. Lo mecánico (`guardar` a `logs/`, `--subir`) es del proyecto; la regla, no.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22; aplicada como regla en `orchestrate-dealer` aunque el proyecto aún no la ha probado)

## P6. `opt-ai`: una medida con muy pocos turnos no compara; cerrar con el banco

- **Source:** `docs/registros/retro-2026-10-22-pruebas-3-3.md` (propuesta 6, `QA-200`, aplicada) y `retro-2026-10-21-puerta-pruebas.md` («`/opt-ai` no midió nada: sin `IA_REGISTRO`») @ 11a201b7 (retro)
- **What changes:** en `skills/opt-ai/SKILL.md`: si el registro de la tanda tiene menos de ~8 turnos, no comparar con el banco de referencia; decirlo y proponer pasar el banco (`bench`) al cerrar la tanda. Y si no hay registro porque no estaba activado el registro de IA, avisarlo en la ronda siguiente, no en la retro. El caso ya está medio cubierto («si no hay registro, para»).
- **Why it is general:** 3 turnos dieron p50/p95 sin valor estadístico; sin la regla, `opt-ai` puede proponer cambios con una muestra de 3.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P7. `recoger.py` avisa si el clon va por detrás de su rama remota

- **Source:** esta misma recogida (la sesión del flujo, 2026-10-22): el clon de lectura seguía en `9cb05e5` aunque
  `origin/main` iba por `11a201b7`, y la primera pasada dijo «nothing new since the last harvest».
- **What changes:** `recoger.py` compara `HEAD` con la rama remota por defecto (`origin/HEAD` o `origin/main`) tras un
  `git fetch` de solo lectura y avisa (o recoge sobre la remota con `--remote`); `gw-harvest` lo pide en el paso 1.
- **Why it is general:** cualquier recogida sobre un clon viejo da un falso «nada nuevo».
- **Version bump:** patch
- **Status:** aprobada (2026-10-22; de la sesión del flujo)

## Se queda en el proyecto

- `tools/qa/marca-hallazgo.py` (`d993302f`…`dbd4d766`, `QA-195`): aviso de «reabierto» o «falta ver» que no cuenta como pendiente en el registro de pruebas de juego; formato de P-números del proyecto. La idea de fondo (escribir lo nuevo delante del estado viejo engaña a un contador) vale cuando un proyecto tenga un registro de hallazgos parseado; no hay equivalente en el flujo.
- `tools/qa/deck/*`, `_path.sh`, `juego.sh`, `relanza.sh`, `lanza.sh` (`77bc00fa`, `29986476`, `695dcf73`) y `tools/qa/tests/test_atajos_deck.py` (`QA-188`, `QA-192`, `QA-198`): atajos de su Steam Deck y su test («todo atajo a `psql` carga `_path.sh`»). Es entorno de su máquina.
- `tools/qa/escenario.sh`, `escenarios/` (`construir.sh`, `.dump`), `sql.sh`, `bench-ia.sh`, `comprobar-escenarios.sh`: escenarios y volcados del juego.
- Propuesta 2 de la retro del 3.3 (chuleta del driver en lugar de notas por tanda, `QA-196`): lo general («una sección de notas por tanda crece 12 líneas por PR y cada subagente la lee entera: reorganizarla por herramienta») es higiene del runbook de cada proyecto; sin implementar allí aún. Reconsiderar si vuelve a aparecer en otro repo.
- Propuesta 3 de la retro del 3.3 (permitir `escenario.sh dar` en `.claude/settings.json`): decisión del proyecto sobre su propio script.
- Propuesta 4 de la puerta de pruebas (`QA-191`, escenario con un solo capitán) y 6 (`QA-193`, forzar el azar): mecánica del juego.
- `.claude/skills/opt-tokens/proyecto.md`: medidas y rutas del proyecto (`estado.js`, `r.sh`, `panel.sh`); su parte general es P2 y P3.
- Tandas 1-14 del 3.3, P-números, `docs/registros/pr/`, `plan-comprobacion-3.3.md`, bandeja y construcción por oficio: producto y pruebas de juego.
- Nada nuevo en `.githooks/`, `.claude/hooks/`, `.claude/settings.json` ni `CLAUDE.md` desde `9cb05e5` (sin commits que los toquen).

## Ya está aquí

- Tope de ~60 llamadas por subagente con estado guardado para el siguiente: `orchestrate-dealer` (paso 1).
- `recuperar.py --estado` y `--buscar`: `scripts/recuperar.py` y `templates/es/opt-tokens.md`; falta solo citarlo en el encargo (P3).
- Revisión corta de subagente revisor contra el contrato antes de fusionar ramas con worktree: `orchestrate-dealer` (paso 3).
- Reglas de permiso en modo automático para ganchos y `settings.json`: `problemas.md`, `aplicar.md` (Instalador P3 de la recogida anterior).
- Que el `/code-review` previo al PR encuentre fallos reales y los arreglos se suban con su test (fase 1 de `AGENTS.md`): ya en la plantilla.
