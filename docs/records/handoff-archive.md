# Hand-off archive

Items moved out of the hand-off log by `handoff.py archive`; this file is not read at session start.

## 2026-11-09 — from docs/handoff.md

- **Para la retro de la `0.5.1`, oleada 2 (2026-11-04):** el cerrojo del check es uno por repo (`git-common-dir`): con dos worktrees, el segundo check sale con 3 y cada check completo tarda ~25 min, así que las oleadas en paralelo se serializan en el check; además `check.lock` es un symlink a un destino inexistente y `[ -e ]` da falso (hay que usar `[ -L ]`). El CI de 746f33b y c6c4f15 dio rojo por shellcheck: el del CI (más viejo) marca SC2317 donde el local 0.11.0 marca SC2329, así que el check local no lo vio; arreglado desactivando los dos (E20). El CI de d3920fd dio rojo por una prueba inestable: `ci-status.py` buscaba «422» en todo el mensaje de error, ruta incluida, y el SHA aleatorio de la prueba (`95422b…`) lo contenía; ahora solo mira la salida de `gh`/`curl` (D18, con prueba que no depende del SHA). El check de f4b1e01 dio rojo por otra carrera: `test_a_kill_releases_the_lock` mandaba TERM en cuanto había cerrojo, y si llegaba antes de que arrancara `sleep 30`, bash lo retenía hasta el final (el leve de E20 «TERM espera a la orden en curso»); la prueba espera ahora la salida del comando (E20).
- **Leves de la revisión contra `main` de la `0.5.1` (2026-11-05, no bloquean; `review-main-0.5.1.md` y `review-E20-lock.md` en el scratchpad de la sesión):** `check.sh` exige que el registro y el cerrojo se puedan escribir (falla con un `.git` de solo lectura o un `GW_CHECK_LOG` dentro del árbol); `before-stop` calla el aviso de commits sin subir si el verde es de otro worktree o `-dirty` con el mismo HEAD; la exención de la marca podría apuntarla `reviewed.sh`, y `epoch` + `has` leen la caché dos veces. E20: un cerrojo con `proc_start` `?` (sin `ps`) no caduca nunca (decidir caducidad por edad con clave en `gw.json`); un mutex `check.lock.steal` cuyo dueño muere antes de escribir su pid queda hasta borrarlo a mano; un `ln` que falla por permisos se cuenta como carrera; un error de `amend_advice` que no sea `CheckError` sale con 2; con varias refs el cerrojo nombra el sha y el log de la primera; sin test del borrado del log del `pre-push` con Ctrl-C/TERM. D52: la doc de `apply` (es/en) no se repasó para `mentions_script`.
- **Leves de la oleada 1 de la `0.5.1` (2026-11-04, no bloquean; revisiones en el scratchpad de la sesión):** E20: el registro se trunca en cada check del mismo sha (y el `-dirty` se comparte) y crece sin límite ni clave; TERM espera a que acabe la orden en curso; un `GW_CHECK_LOG` fuera del directorio de git no se limpia; con fifo y `tee` las órdenes pierden el TTY y los colores; `kill -0` ve vivo a un zombi sin recoger; sin test de `tests/check.sh` (probado a mano). E25: una frase que parezca prosa (mayúscula, sin dígitos) pasa en un `.md`; el aviso recorta la línea a 40 caracteres y lista hasta 15. D47: el consejo propone `git add -A` antes del `--amend` (mete cambios ajenos); con un sha suelto en `--ref`, la orden deja HEAD separado. `REVIEW.md` no existe aunque `AGENTS.md` y `gw-orchestrate-dealer` lo citan. Leves de D45 y D46 (2026-11-05): D46 cuenta un `.bak` (p. ej. `docs/traspaso.md.bak`) como uso de un nombre viejo, y un salto de línea dentro de una ruta descuadra la lectura de `git grep -z`; revisiones en el scratchpad de la sesión (`review-D45.md`, `review-D46.md`). Leve de E23: `check-green.sh inputs <dir>` acepta una subcarpeta del repo (solo compara el git common dir; arreglo: exigir que `--show-toplevel` sea el `pwd -P` de `<dir>`); ningún llamador la pasa (`review-E23.md`). Leves de la recogida de cierre (2026-11-05): E26: añadir una extensión de código (p. ej. `py`) a `nonTestExtensions` en un `gw.json` sin commit apaga la guarda (configurable a propósito; decidir si `config-guard` protege la clave); sin test de `--fix-at` con extensión saltada. D51: la normalización de `\` en `arrives_by_folder_move` no tiene test (`review-E26.md`, `review-D51.md`).
- **Para la retro de la `0.5.1` (2026-11-04):** (1) una tarea sin id (la P5) hizo que el subagente tomara uno prestado (E24): el `commit-msg` exige el id en el roadmap y el encargo no puede tocarlo; el id se da antes de repartir. (2) Un subagente corrió una orden sin `cd` en el worktree de otro (sin daño): el encargo pide rutas absolutas. (3) Los tests de interrupción del `pre-push` fallaron por carga con tres agentes a la vez y pasaron solos.
- **Leves de la recogida de la `0.5` (2026-11-04, no bloquean):** D39: carrera entre sesiones al limpiar contadores
  (el tope llega tarde, nunca se salta). D37: ejemplos literales en retros viejas. D32: el CI necesita
  `fetch-depth: 0` para la historia publicada. D38: quitado el test de la marca no escribible. D34 se aparta de P4:
  todo `WIP:` pasa (con la bitácora y sin `handoff.py check`) y todo lo demás falla cerrado; con el config roto, un
  WIP puede llevar rutas protegidas. D33: `pull` mira solo lo ya traído, falsos positivos con cambios sin commit,
  sesión abierta en un worktree, rutas entre comillas del parche preguntan (límites en `docs/es/patterns.md`). D35:
  el clon queda en HEAD separado. D36: la pista dice `Siguiente:` también en inglés. B14: el formato en negrita o
  en singular no se reconoce; sin test del tope de 5 s de git. E19: va en el `check` de la plantilla (se quita si el
  usuario prefiere).
- **Para la retro de la `0.5`, recogida (2026-11-04):** (15) un push y una fusión con check en paralelo dieron
  «Terminated»; (16) una cadena de seis `merge-branch.sh` (~25 min cada uno) no cabe en las 2 h de una tarea en
  segundo plano: se fusionó en serie sin check y un solo check al final, en un worktree aparte; (17) el rojo de D34
  (un test que esperaba el texto viejo) solo se vio corriendo los tests de los ganchos a mano (otra vez el punto 12);
  (18) la revisión halló una regresión de D36 que sus tests no cubrían: el commit de la marca no se probó con el
  `commit-msg` estricto; (19) el check largo de `e1f312f` dio rojo solo por una copia sin refrescar, y se leyó «exit 0»
  de un resumen en vez del final del registro.
- **Leves de la oleada 3 de la `0.5` (2026-11-03, no bloquean):** D21: los patrones de firma de
  `agent-signatures.py` replican el `grep -iE` de `templates/githooks/commit-msg` sin test de paridad (unificarlos
  pide pasar ese tramo a Python); si `shlex` falla el motivo no lo dice; `gh pr create` citado en otro texto de la
  orden hace leer `-F`/`-t` de git como de gh; ~65 ms por llamada a Bash (diferir `import config`); un proyecto con la
  entrada del matcher viejo la conservaría junto a la nueva (`apply.py` fusiona por matcher + orden; inocuo, sin
  publicar). D19: el `name:` con expresión del job solo tiene test de texto, sin probar en Actions. Revisiones en el
  scratchpad de la sesión.
- **Para la retro de la `0.5`, oleada 3 (2026-11-03):** (12) `merge-branch.sh` sigue sin enseñar el fallo del check
  (solo las últimas líneas, todas `OK`): que use `check.sh --quiet` y muestre su resumen; (13) los subagentes que
  tocan `scripts/` olvidan refrescar `.claude/gw/scripts/` y un e-mail de prueba no `example.com` lo para
  `private-check`: que el encargo pida `test_reviewed.py` y `test_private_check.py` entre los tests relacionados;
  (14) el gancho `Stop` insiste en subir mientras corre el check de una fusión.
- **Leves de la oleada 2 de la `0.5` (2026-11-03, no bloquean):** E17: dos `check.sh --quiet` a la vez mezclan el
  registro; falta `check.sh <rev>` (comprobar una revisión concreta, INS P12). D24: el aviso no lista las
  resoluciones de conflictos de las fusiones. D25: `enclosing` mira las líneas de HEAD y no las del commit del
  arreglo; en un clon superficial `--fix-at` necesita `git fetch --deepen`. D29: una entrada `cwd` sin `paths`
  corre siempre. D30: `ruta:línea` no se reconoce; un clon superficial puede no tener los nombres viejos. Revisiones
  en el scratchpad de la sesión.
- **Para la retro de la `0.5`, oleada 2 (2026-11-03):** (7) el check completo tarda 25-30 min (1233 tests): las
  esperas en segundo plano necesitan 2 h de tope, no 20 min; (8) un `pkill -f` amplio mató el check del `pre-push`;
  (9) un monitor que buscaba `^EXIT` dio un falso atasco; (10) `merge-branch.sh` borra su registro y solo enseña 20
  líneas: el SC2015 de E17 obligó a repetir el check entero para verlo (que deje el registro o use `--quiet`); (11)
  cada fusión más su subida son dos checks completos (~55 min).
- **Leves de la oleada 1 de la `0.5` (2026-11-03, no bloquean):** `ci-status.py`: comodines en `ciIgnore`, argparse
  sale 2 con un uso malo sin decirlo, `doctor` sin su propia prueba de acceso al CI. D31: `merge --squash` y casos de
  cherry-pick, CRLF y espacios sin test. D26-D28: las fusiones squash no se detectan (sin documentar); un `cd a && cd
  b` encadenado no se sigue; rutas `\` de Windows en `worktreeLinks`; faltan tests de worktree detached y prunable.
  D22-D23: `rewrite_row` busca filas en todo el archivo y no solo en la tabla; bitácora no UTF-8 da traceback; escape
  de `\|` incompleto; ninguna skill ni plantilla llama a `set-row`. Revisiones en el scratchpad de la sesión.
- **Para la retro de la `0.5` (2026-11-03):** (1) los worktrees de `isolation: worktree` nacen en `origin/main`, no
  en HEAD (los agentes se movieron a mano; D6, `worktree.baseRef`); (2) la regla del encargo «una espera por orden
  larga» no bastó: ~32 esperas duplicadas en segundo plano; hace falta un gancho o un tope real; (3) varios checks
  completos a la vez saturan la máquina de 4 núcleos: los arreglos se piden sin check completo y lo corre
  `merge-branch.sh`; (4) el scratchpad compartido: un agente pisó los archivos de otro; nombres únicos por agente;
  (5) `pkill` denegado a los agentes, usaron TaskStop; (6) el `pre-push` repitió el check tras `merge-branch.sh`
  (ya apuntado: que `merge-branch.sh` apunte el verde).
- **Test intermitente en el CI (2026-11-02):** `test_hooks.PrePushWorktree.test_interrupting_the_hook_removes_its_worktree` dio `TimeoutExpired` (30 s) en Ubuntu sobre `f047f1c` (macOS cancelado); el mismo código pasó en los CI siguientes (`aae2a96`, `8937979`). Va a los arreglos del CI del parche `0.4.4` (subir el límite o esperar a la señal, no a reloj).
- **Leves del `/code-review` de `0.4.2`** (2026-10-27, no bloquean): (1) los commits de fusión `d714267`, `9112a44`,
  `b4ec2eb` y `8b0260c` no llevan `Siguiente:` (ya subidos; el mensaje que propone `merge-branch.sh`, a la retro);
  (2) `handoff.py check` sin `--at` da la pista de commit y la ayuda del principio no menciona `--at`; (3) la regla
  QUOTED del `pre-commit` bloquea etiquetas de i18n (una clave `openaiKey` cuyo valor es el texto «Clave de OpenAI»;
  lo sufrió esta misma bitácora); (4)
  `related-tests.sh` se presenta como «pre-push: related tests» también cuando lo llama `merge-branch.sh`.
- Menores de la revisión de la `0.4.1` (2026-10-26): `red-without-fix` (`test_re`) da falsos positivos («it (»,
  «test(», `def testable`, comentarios que se describen a sí mismos, como los del propio script); `NOT_STARTED` del
  gancho de fusión solo reconoce dos frases exactas de GitHub (falta «billing», «account is locked»); `cloud_start`
  silencia también la pista «pass it explicitly» (decisión aprobada, Portal P1) y conviene centralizarlo en `find()`
  y `opened_outside()`.
- Menores de la retro antes de la `0.4.0` (2026-10-25): `handoff.py` no entiende bloques de código dentro de
  «Hecho», iguala los huecos en blanco entre entradas y mide cada celda por separado (dos de 790 en una fila pasan);
  `doctor.py` (`ci access`) da por bueno un token sin comprobarlo y no reconoce `ssh.github.com:443` ni GHE; el
  marcador de `pre-push` no cubre un pid reutilizado tras `kill -9`, ni las ventanas antes y después del gancho, ni
  `git push origin HEAD:otra` (mismo sha, otra rama).
- Menores de la revisión de la fase 3 antes de la `0.4.0`: `handoff.py done` con viñetas (`- `) añade la entrada
  debajo y no recorta; el aviso «glued» propone `check` sobre el temporal de los ganchos (`gw-commit-msg.*`,
  `gw-log.*`), ya borrado; `prepush-branches.sh` repite los avisos de `check` en cada commit de la subida; `before-stop.py`
  lee solo 4096 bytes de la marca (`git push --all` de unas 55 ramas); la marca es una por directorio común de git (dos
  worktrees que suben a la vez se pisan).
- Menores de la revisión del flujo 0.3.0 que hizo el portal (P5 de `docs/proposals/2026-10-23-portal-galivelop.md`):
  `config.py related` acepta un `cwd` con `..` o absoluto en `relatedTests` (que `validate` lo rechace);
  `session-start.sh`: `kill -- -$wd` no es un grupo y el `sleep` del vigilante queda vivo hasta el tope;
  `review-before-main.sh` sondea `gh api repos/<o>/<r>` en cada llamada y juzga cambios de título o base de un PR
  cerrado; `doctor.py` da por bueno un `npm run check` citado en un comentario (y avisos del glosario repetidos por
  mayúsculas, por comprobar); `validate` no avisa de un `worktreeDir` dentro del repo ni de un `checkWrapper` que
  limpia el entorno. Con la config de la punta de `main` rota, `pre-push` y el gancho fallan cerrados a propósito: se
  sale con un PR revisado que la arregle, o la persona sube a mano.

## 2026-11-10 — from docs/handoff.md

- **Revisión de bloque (2026-11-10), no aplicados:** el ledger por rama cuenta dos veces una sesión que pasa por dos ramas (B2); `archive` toma cualquier `X.Y` por versión (`0.5 MB`); `change-size.py` en un `--amend` mide solo lo preparado.

## 2026-11-11 — from docs/handoff.md

- **A10, leves de la revisión (no bloquean):** el conversor Markdown pierde el `#` de `# Learn C#`, anida mal `***x***`, parte una tabla con `|` dentro de código, toma `2024.` al principio de línea por lista, aplana las listas anidadas y deja el markup del título; dos fuentes con el mismo idioma y nombre chocan; Playwright se resuelve global. De la segunda revisión: la reescritura de rutas de la CSS solo cubre `url(...)` en minúsculas con comillas iguales (no `@import "x.css"`, `URL(…)`, `url("it's.png")` ni `image-set("x.png" 1x)`), y el énfasis entra en el `href` de un enlace (`[a](https://x.com/*a*b*)`).
- **A10, leve:** el enlace de idioma de la cabecera de cada hoja (`[English](../en/…md)`) sale en el HTML y el PDF apuntando a un `.md` que no está junto al HTML; quitarlo o reescribirlo a `.html` en `mkt-sheet.py`.
- **Leves de A9 (2026-11-02):** si la punta de la rama protegida trae un `schemaVersion` más nuevo, el `pre-push` avisa con el texto genérico «… is invalid; this push can fix it» (la política sigue fallando cerrada); el mensaje de `schemaVersion` no entero sugiere `config.py validate` sin `--root`.
- Menores de la revisión de la tanda E: el aviso de ventanas mezcladas de `gw-opt-tokens/medir.py` salta con un
  `/compact` manual o una etapa muy corta; `gw-opt-ai/medir.py` ignora un `app.turn` 0 o vacío y su clave sintética
  choca con una tarea llamada «turn»; `instant` descarta sin avisar un `ts` que `fromisoformat` no lee (Python <3.11);
  `quality_bench.py` envía un `format` de texto como `json_schema` con la API openai y `pairs` pisa en silencio un
  modelo repetido en dos `outputs.jsonl`.
- Menores de la revisión de los arreglos antes de `main` (3b47af1): un push muerto en el mismo namespace deja su
  worktree 24 h (guardar `hostname:pid` en el marcador); `worktreeDir` con `~` o `..` no se valida en `config.py`;
  `cksum` de 32 bits puede juntar dos repos en una carpeta (el borrado sigue exigiendo 24 h y proceso muerto);
  `update_pull_request` con `state:open` y sin `base` no se juzga como reapertura; `compare.py default_root` da
  traceback sin git y, desde la caché del plugin, cae al cwd (exigir `--root`).
