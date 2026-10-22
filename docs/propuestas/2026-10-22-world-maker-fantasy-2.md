# Harvest world-maker-fantasy — 2026-10-22 (segunda del día)

De `11a201b7` a `76ec6aeb` (`scripts/recoger.py`, 99 commits). Tercera recogida. El diff de `orchestrate-dealer`
(+84 −86) sigue siendo casi todo traducción y notas del proyecto (ya clasificado en
[`2026-10-22-world-maker-fantasy.md`](2026-10-22-world-maker-fantasy.md)); lo nuevo en este tramo es un solo commit,
`e5e3413b` (+11 −4), con cuatro ideas de la retro previa al PR que la usuaria aprobó allí (T1, T2, R1, R2). Su
`/opt-tokens` de 24 h: los subagentes son el 78 % de la entrada (155 M: 103 M opus, 52 M sonnet), ~52k de arranque
por subagente. Las cuatro tocan sobre todo `skills/orchestrate-dealer` y caben en un único patch.

## P1. Los arreglos que salen de una revisión van con `sonnet`; el revisor sigue en `opus` (T1, QA-201)

- **Source:** `.claude/skills/orchestrate-dealer/SKILL.md` (paso 2) @ `e5e3413b` (skill); retro `docs/registros/retro-2026-10-22-frontend-improvements.md` (T1) @ `2b97eff3`
- **What changes:** paso 2 de `skills/orchestrate-dealer/SKILL.md` y la fila «Closed plan, scoped implementation» de `skills/selector/SKILL.md`: los arreglos de una revisión (el revisor ya cerró el plan: sitio y qué cambiar) van con `sonnet`; `opus` solo si hay que depurar algo no obvio.
- **Why it is general:** tres agentes de arreglos con `opus` gastaron 7,4 M de entrada cada uno. El flujo dice «sonnet para implementar», pero no nombra los arreglos de una revisión y el agente los trata como trabajo de criterio.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P2. Un arreglo de un archivo con el sitio ya dado por el revisor lo hace la principal (T2, QA-202)

- **Source:** `.claude/skills/orchestrate-dealer/SKILL.md` (paso 1) @ `e5e3413b` (skill); retro (T2) @ `2b97eff3`
- **What changes:** una línea en el paso 1 («Split»): un arreglo de un solo archivo cuyo sitio ya señala el revisor no es un trozo; lo hace la principal, con sus tests.
- **Why it is general:** un subagente paga ~52k al arrancar y en Tarkor hizo 70-80 llamadas para lo que la principal cerró en ~10. Es el contrapeso de «la principal no lee más de 200 líneas»: hoy ninguna skill dice cuándo repartir no compensa.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P3. En la fase 1 previa al PR, solo lo grave (R1, QA-203)

- **Source:** `.claude/skills/orchestrate-dealer/SKILL.md` («Rules») @ `e5e3413b` (skill); retro (R1) @ `2b97eff3`
- **What changes:** regla nueva en `skills/orchestrate-dealer/SKILL.md` y una frase en la fase 1 de `templates/*/AGENTS.md` y `docs/es/flujo.md` ↔ `docs/en/workflow.md`: antes del PR se arregla lo grave o medio y lo que el propio arreglo rompe; lo leve se anota como pendiente en la bitácora y no vuelve a revisarse en ese PR (`/code-review --max-findings all` sigue sirviendo para anotarlo).
- **Why it is general:** cada arreglo se revisaba otra vez y traía hallazgos nuevos; el bucle revisión-arreglo no tenía límite y el PR crecía hasta ser difícil de revisar.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## P4. El encargo comprueba la rama de partida del worktree (R2, QA-204)

- **Source:** `.claude/skills/orchestrate-dealer/SKILL.md` (plantilla del encargo) @ `e5e3413b` (skill); retro (R2) @ `2b97eff3`
- **What changes:** primera línea de la plantilla del encargo: si `git log -1` no coincide con `origin/<branch>`, `git fetch origin <branch> && git reset --hard origin/<branch>` antes de nada (solo en un worktree recién creado y limpio).
- **Why it is general:** varios worktrees de agentes salieron de `main` y no de la rama de trabajo; pasa en cualquier proyecto que use `isolation: "worktree"`. La plantilla da la rama pero no manda comprobarla.
- **Version bump:** patch
- **Status:** aprobada (2026-10-22)

## Stays in the project

- R4 (QA-205): test intermitente del cronista (`decisionesFaccion`/`deudaDeVida`): mecánica del juego.
- R5 (QA-206): `fusionar.sh` y su error de `getcwd` al borrar el worktree en el que se lanza: script del proyecto
  (el flujo no lo tiene; ver P7 de `2026-10-21-world-maker-fantasy.md`).
- R6 (QA-207): `medir.py` da 382k de contexto medio de toda la sesión frente a ~110k por tramos. Puede afectar al
  `medir.py` de `skills/opt-tokens`; no se analiza en la retro. Se mira en la próxima recogida.
- R3 (recordar el castellano tras compactar): rechazada por la usuaria en Tarkor.
- Notas QA-xxx, P-números, `escenario.sh`, `orden.sh`, `docs/registros/*`: producto y pruebas del juego.

## Already here

- Tandas de 6-8, tope de ~60 llamadas, `SendMessage` para retomar, estado fuera de git, `recuperar.py --estado` en el
  encargo, revisión sin worktree: recogidos en `2026-10-22-world-maker-fantasy.md` y aplicados.
