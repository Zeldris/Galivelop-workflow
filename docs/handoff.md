# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.5` «Base»: `ccr-d1e2d496-0vzck8`** (2026-11-02; creada desde `version/1.0.0` en `a61cdc5`; hace de `version/0.5.0` (H-13) mientras la sesión solo pueda subir a esta rama). **No hay `0.4.4`** (usuario, 2026-11-03: «publicamos la 0.5, ya directamente»): sus arreglos salen en la `0.5.0` y `ccr-6dfbc880-ddr41g` queda sin uso. `version/1.0.0` se queda con el diseño (`docs/design/`). `main` = `eeec886` = **`0.5.1`** (2026-11-05; etiqueta `v0.5.1` pendiente, ver «Siguiente paso») |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). Los arreglos del CI de Ubuntu y macOS (`66a4ecd`) están en esta rama; `main` (`0e04504`, `v0.4.3`) sigue en rojo en el CI hasta la `0.5.0` |
| Fase en curso | **6 cerrada**; `0.4.1` en `main` (2026-10-26). La `0.4` es la última menor `0.x` (usuario, 2026-10-25, plan §7): solo parches `0.4.x`, y lo nuevo de una recogida va a la `1.0.0`. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | `0.4.2` en `main` (`8a6f367`, 2026-10-27), con confirmación del usuario: fases 1-3 hechas, marca de revisión `8a6f367`. **Comprobado solo en local** (confirmado por el usuario): el CI de Actions no arranca (sin cuota); el check completo del `pre-push` pasó en verde para la rama y para `main` (con `version.py --release`). Textos de la release en `docs/records/release-v0.4.2.md` (en la rama `ccr-6dfbc880-ddr41g`) |
| Siguiente paso | **`0.5.1` en `main`** (`eeec886`, 2026-11-05). **Pendiente: la etiqueta `v0.5.1`**: desde la nube dio 403; se lanza desde una sesión local (`git fetch origin && git tag v0.5.1 eeec886 && git push origin v0.5.1`, que dispara `release.yml`) o la crea el usuario a mano con `docs/records/release-v0.5.1.md`. Después, la `0.6` en una sesión nueva (retro R7), empezando por su recogida (`gw-harvest`). Presupuesto de compactaciones: 2 |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [x] 6. Piloto: Tarkor e instalador (2026-10-23; private-project-1, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Lanzamiento (antes «Público»; plan §9, A7)

## Para la próxima publicación

**Política de versiones** (usuario, 2026-11-01, plan §7): solo la última menor publicada recibe parches (hoy la `0.4`);
los evolutivos van a la siguiente menor (la `0.5`, en esta rama). La `1.0` es el Management Center y sale cuando está
hecho lo que le asigna el roadmap; la §10 mide la madurez de la `1.x`. Cada versión se publica en este repo
(público), a lo sumo una al día.

La release `v0.4.0` la creó el usuario a mano (2026-10-25), con los textos de `docs/records/release-v0.4.0.md`. La
sesión en la nube no puede subir etiquetas (403 del proxy) y sin cuota de Actions `release.yml` no corre. Para la siguiente: `release.yml` con
lanzamiento manual desde Actions que cree la etiqueta.

## Hecho (5 últimas)

1. 2026-11-05 — 0.5.1 en main (eeec886); etiqueta v0.5.1 pendiente desde local (403 en la nube); filas E28-E31 en la 0.9; AGENTS.md: preguntar siempre cómo crear la release
2. 2026-11-05 — E20: revisión contra main: el robo del cerrojo va bajo un mutex y nunca borra uno vivo; private-check sale 2 si falla; el pre-push distingue hallazgo, cerrojo ocupado y fallo; D52 cuenta toda forma real de llamar a un script viejo (mentions_script)
3. 2026-11-05 — E23: SC2015 de check-green.sh y pre-push arreglado (el shellcheck 0.11 local no lo da y el del CI sí; para la retro: igualar versiones)
4. 2026-11-05 — E26: red-without-fix.sh salta textos y datos (nonTestExtensions), falla cerrada si no lee la clave
5. 2026-11-05 — D52: apply.py conserva un script viejo solo si se llama por .claude/gw/scripts/<viejo> o $var/<viejo>

## Pendiente

- **Leves de la revisión contra `main` de la `0.5.1` (2026-11-05, no bloquean; `review-main-0.5.1.md` y `review-E20-lock.md` en el scratchpad de la sesión):** `check.sh` exige que el registro y el cerrojo se puedan escribir (falla con un `.git` de solo lectura o un `GW_CHECK_LOG` dentro del árbol); `before-stop` calla el aviso de commits sin subir si el verde es de otro worktree o `-dirty` con el mismo HEAD; la exención de la marca podría apuntarla `reviewed.sh`, y `epoch` + `has` leen la caché dos veces. E20: un cerrojo con `proc_start` `?` (sin `ps`) no caduca nunca (decidir caducidad por edad con clave en `gw.json`); un mutex `check.lock.steal` cuyo dueño muere antes de escribir su pid queda hasta borrarlo a mano; un `ln` que falla por permisos se cuenta como carrera; un error de `amend_advice` que no sea `CheckError` sale con 2; con varias refs el cerrojo nombra el sha y el log de la primera; sin test del borrado del log del `pre-push` con Ctrl-C/TERM. D52: la doc de `apply` (es/en) no se repasó para `mentions_script`.
- **Leves de la oleada 1 de la `0.5.1` (2026-11-04, no bloquean; revisiones en el scratchpad de la sesión):** E20: el registro se trunca en cada check del mismo sha (y el `-dirty` se comparte) y crece sin límite ni clave; TERM espera a que acabe la orden en curso; un `GW_CHECK_LOG` fuera del directorio de git no se limpia; con fifo y `tee` las órdenes pierden el TTY y los colores; `kill -0` ve vivo a un zombi sin recoger; sin test de `tests/check.sh` (probado a mano). E25: una frase que parezca prosa (mayúscula, sin dígitos) pasa en un `.md`; el aviso recorta la línea a 40 caracteres y lista hasta 15. D47: el consejo propone `git add -A` antes del `--amend` (mete cambios ajenos); con un sha suelto en `--ref`, la orden deja HEAD separado. `REVIEW.md` no existe aunque `AGENTS.md` y `gw-orchestrate-dealer` lo citan. Leves de D45 y D46 (2026-11-05): D46 cuenta un `.bak` (p. ej. `docs/traspaso.md.bak`) como uso de un nombre viejo, y un salto de línea dentro de una ruta descuadra la lectura de `git grep -z`; revisiones en el scratchpad de la sesión (`review-D45.md`, `review-D46.md`). Leve de E23: `check-green.sh inputs <dir>` acepta una subcarpeta del repo (solo compara el git common dir; arreglo: exigir que `--show-toplevel` sea el `pwd -P` de `<dir>`); ningún llamador la pasa (`review-E23.md`). Leves de la recogida de cierre (2026-11-05): E26: añadir una extensión de código (p. ej. `py`) a `nonTestExtensions` en un `gw.json` sin commit apaga la guarda (configurable a propósito; decidir si `config-guard` protege la clave); sin test de `--fix-at` con extensión saltada. D51: la normalización de `\` en `arrives_by_folder_move` no tiene test (`review-E26.md`, `review-D51.md`).
- **Para la retro de la `0.5.1`, oleada 2 (2026-11-04):** el cerrojo del check es uno por repo (`git-common-dir`): con dos worktrees, el segundo check sale con 3 y cada check completo tarda ~25 min, así que las oleadas en paralelo se serializan en el check; además `check.lock` es un symlink a un destino inexistente y `[ -e ]` da falso (hay que usar `[ -L ]`). El CI de 746f33b y c6c4f15 dio rojo por shellcheck: el del CI (más viejo) marca SC2317 donde el local 0.11.0 marca SC2329, así que el check local no lo vio; arreglado desactivando los dos (E20). El CI de d3920fd dio rojo por una prueba inestable: `ci-status.py` buscaba «422» en todo el mensaje de error, ruta incluida, y el SHA aleatorio de la prueba (`95422b…`) lo contenía; ahora solo mira la salida de `gh`/`curl` (D18, con prueba que no depende del SHA). El check de f4b1e01 dio rojo por otra carrera: `test_a_kill_releases_the_lock` mandaba TERM en cuanto había cerrojo, y si llegaba antes de que arrancara `sleep 30`, bash lo retenía hasta el final (el leve de E20 «TERM espera a la orden en curso»); la prueba espera ahora la salida del comando (E20).
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
- **Leves de D11/D12/D15/D16 (2026-11-02, no bloquean):** `commit-message.py`: con `core.commentChar=auto` los
  comentarios quedan como último párrafo y dan «no Refs trailer» (le pasaba ya al de firmas); `refsSources` no se
  valida (`..`, rutas absolutas). `merge-branch.sh`: si git no ve el último párrafo como trailers, sus `Refs:` se
  pierden sin aviso; `get taskId` no distingue «sin definir» de «ilegible». `version.py`: `BREAKING CHANGE:` en prosa
  del último párrafo cuenta. Líneas de más de 120 caracteres en README y `contributing.md`. Revisiones en el
  scratchpad de la sesión (no subidas).
- **Leves de A9 (2026-11-02):** si la punta de la rama protegida trae un `schemaVersion` más nuevo, el `pre-push` avisa con el texto genérico «… is invalid; this push can fix it» (la política sigue fallando cerrada); el mensaje de `schemaVersion` no entero sugiere `config.py validate` sin `--root`.
- **Test intermitente en el CI (2026-11-02):** `test_hooks.PrePushWorktree.test_interrupting_the_hook_removes_its_worktree` dio `TimeoutExpired` (30 s) en Ubuntu sobre `f047f1c` (macOS cancelado); el mismo código pasó en los CI siguientes (`aae2a96`, `8937979`). Va a los arreglos del CI del parche `0.4.4` (subir el límite o esperar a la señal, no a reloj).
- **Para la retro de A8 (2026-11-02):** el subagente del trozo 3 dejó ~49 bucles `until grep -q '^EXIT'` colgados y dos checks completos a la vez (los tests de interrupción fallaron por carga); se cortaron a mano. Propuesta: el encargo de `gw-orchestrate-dealer` limita a una espera en segundo plano por orden larga y prohíbe `pkill -f` amplio.
- **Menores de la revisión de la caché del `check` (P3, 2026-10-26)**: el límite de los archivos ignorados (`check.sh`
  corre con `.env` y generados de la copia; antes, una subida con copia sucia comprobaba en un worktree limpio) está
  documentado en `config.md`, `troubleshooting.md` y el CHANGELOG. Posible mejora: que `merge-branch.sh` también apunte el verde
  (hoy solo lo apuntan `check.sh` y el propio `pre-push`).
- **Sin firmas de Claude** (usuario, 2026-10-26): commits y PR a nombre de `Zeldris`, sin trailers ni pies de Claude;
  desde la `1.0.0` lo comprueba el `commit-msg` (`agentSignatures: false`). Desde `f2da5d5` (excluido) ya va así; el
  historial anterior de la rama y de `main` lleva autor Claude y trailers: reescribirlo exige force-push, solo si el
  usuario lo pide. Límites conocidos del gancho: con git anterior a 2.45 y `core.commentString` puesto, lee ese valor
  aunque git use `#` (las tijeras no se reconocerían); `--amend` de un commit antiguo con firma se rechaza hasta
  quitarla (coherente); el autor del commit no se comprueba, solo el mensaje.
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
- `recover.py` (`fit_log`): recorta por el principio del conjunto de secciones, así que una primera sección larga se come antes la «Pendiente»; si la cabecera y la cola ya pasan del tope, la nota de recorte se emite igual y `capped()` corta el puntero a `--buscar`.
- `harvest.py`: un `\r` suelto desalinea los números de línea con los del diff; un archivo renombrado desde la última recogida vuelve a dar todas sus ideas; una línea borrada de una propuesta no la marca como cambiada (no dicho en la docstring).
- `--name-only` sin `core.quotepath=false` en `prepush-branches.sh`, `is-code.sh`, `reviewed.sh`, `version.py` y `harvest.py`: una ruta de `log` con acentos no coincide.
- `subagent-cap.py` cuenta doble (y `config-guard.py` y `before-stop.py` preguntan dos veces) si el gancho está a la vez en el plugin (`hooks/hooks.json`) y en el `.claude/settings.json` del proyecto.
- `doctor.py` (~línea 512): la orden que arregla los caracteres invisibles convierte CRLF en LF y no entrecomilla la ruta.
- `config-guard.py`: `git -C <dir> checkout .` resuelve `.` contra la raíz del proyecto (falso positivo) y volcar un árbol sobre la raíz (`cp -r x/. .`, `rsync -a x/ ./`) no se ve.
- `read_event()`/`ask()` están copiados en los tres ganchos nuevos (`config-guard.py`, `before-stop.py`, `subagent-cap.py`): llevarlos a un módulo junto a `config.py`.
- `apply.py` notas personales (revisión de 2522f37): una nota que cada proyecto adapta imprime su línea `diff` en cada ejecución; un fork renombrado o un clon sin `.claude-plugin/plugin.json` recibiría notas.
- `doctor.py` (revisión de cf57265): `media_folder()` no tiene efecto (con nota cuenta su existencia; `Folder:` nunca se consulta) y su regex `\s*` cruza el salto de línea; `playwright_found()` mira el cwd (con `--root` desde otra carpeta, WARN falso; cwd borrado = traceback); `skill tests` solo mira `*.py` de primer nivel (no `.mjs`; `_util.py` exige test); un `docs/difusion/` ajeno a la skill dispara los avisos de herramientas.
- `doctor.py` (`media tools`) no comprueba la versión de Node ni que Chromium esté instalado para Playwright (solo que `playwright` resuelva); `playwright_found` no mira las carpetas globales de Node.
- El render real (`RenderReal` en `test_render.py`) no lo cubre el CI: el CI no tiene Playwright, Chromium ni
  ImageMagick y añadirlos gasta cupo de Actions. Se corre en local (`GW_PLAYWRIGHT_DIR` + `magick` con WebP) antes de
  tocar `render.mjs` o las fuentes de la plantilla; sin ellos esos casos se saltan.
- Menores de la revisión de render.mjs (gw-media-content), no se revisan otra vez en esta tanda: ImageMagick
  interpreta `[]*?` en nombres; solo se limita el ancho (capturas muy altas superan los píxeles de LinkedIn y el máximo
  de WebP); `antes.png`/`despues.png` usados por `antes-despues.html` se renderizan como capturas; el fallo de
  `chromium.launch` por librerías del sistema sugiere `install` en vez de `install-deps`; los errores de `magick` no
  dan orden; renders a medias quedan mezclados; no comprueba la versión de Node; una fuente pedida por nombre en una
  carpeta de fecha exige que exista en todas las piezas.
- Menores de la revisión de los arreglos de cifras.py (gw-media-content), no se revisan otra vez en esta tanda: el
  lector de TOML no entiende cadenas multilínea (`"""…version = …"""` dentro de `[project]` da esa versión); en un
  repo bare dice «not inside a git repository»; un `OSError` al leer el archivo de versión (permisos, enlace roto) da
  traceback en vez de salir con 2 y la orden.
- Menores de la revisión de los arreglos 2a de comprobar.py, no se revisan otra vez en esta tanda: nombres de imagen
  como `x.ui.webp` se toman por sufijo de idioma; los códigos de idioma no se comprueban contra la lista ISO real.
- Menores de la revisión de comprobar.py (gw-media-content), no se revisan otra vez en esta tanda: marca C sin
  leyenda en §5 y título de Reddit fuera de §5.2; los límites NV/C fallan sin decir que no están verificados; render
  sin fuente y falta de medios/fuente/ pasan; el alt `es: Sí / no: nada` se parte mal.
- [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) revisado (2026-10-25): 4 propuestas sin
  propuestas en `docs/proposals/2026-10-25-codegraph.md`: P2 (comprobador genérico del mapa, `scripts/agent-map.py`)
  y P3 (anti-patrones en `writing-for-agents`)
  aplicadas; P1 (gancho que inyecta la fila del mapa) y P4 (probar
  la herramienta en WMF) sin decidir, se recomienda aplazar. Al aplicar en WMF: declarar
  `agentMap.prefixes` `{"b/": "backend/src/", "f/": "frontend/src/"}` antes de cambiar su comprobador por este.
- Diez repos de una lista de X revisados (2026-10-25): 10 propuestas en `docs/proposals/2026-10-25-repos-x.md`. P4
  (regex), P5 (`recover.py`: tope de 9.500 caracteres y fragmentos como datos) y P7 (skills e instrucciones)
  aplicadas (P4 y P7 en eea8892) y el arreglo posterior (gancho de `main` con tabuladores y saltos escapados; ZWJ en
  emojis; gancho de PR en 8f4150b, 16f6cbd y efc72c9); P1 gancho `Stop`, P2 guarda de config, P3 tope de subagentes, P6 dealer, P8 disparo de skills
  y P9 `REVIEW.md` aplicadas (2026-10-25); P10 apuntada en el plan. Todas hechas.

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/proposals/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Menores de la revisión de la tanda A (no se revisan otra vez en este PR): `non_capturing` toca paréntesis en
  comentarios `(?x)`/`(?#…)`; `--ran-one` cuenta dos veces si el ejecutor repite el nombre del test en el resumen;
  `header_version` solo mira las 5 primeras líneas.
- Menores de la revisión de la tanda B: sin python3, `review-before-main.sh` deja pasar
  `gh api …/pulls -f title=` (crear el PR por la API; el hueco ya existía) y bloquea `gh pr view 3 && echo create`
  (exceso de celo).
- Menores de la revisión del vigilante (89fdf09): el KILL de los 5 s podría dar con un pgid reutilizado (se acepta:
  el vigilante se detiene si la orden acaba antes).
- Menores de la revisión de la tanda E: el aviso de ventanas mezcladas de `gw-opt-tokens/medir.py` salta con un
  `/compact` manual o una etapa muy corta; `gw-opt-ai/medir.py` ignora un `app.turn` 0 o vacío y su clave sintética
  choca con una tarea llamada «turn»; `instant` descarta sin avisar un `ts` que `fromisoformat` no lee (Python <3.11);
  `quality_bench.py` envía un `format` de texto como `json_schema` con la API openai y `pairs` pisa en silencio un
  modelo repetido en dos `outputs.jsonl`.
- Menor de la revisión antes de `main`: `checkWrapper` se aplica en tres sitios (`pre-push` y `merge-branch.sh` con
  `sed`, `config.py` con `shlex`) y la plantilla de CI no lo aplica: que lo construya solo `config.py`.
- Menores de la revisión de los arreglos antes de `main` (3b47af1): un push muerto en el mismo namespace deja su
  worktree 24 h (guardar `hostname:pid` en el marcador); `worktreeDir` con `~` o `..` no se valida en `config.py`;
  `cksum` de 32 bits puede juntar dos repos en una carpeta (el borrado sigue exigiendo 24 h y proceso muerto);
  `update_pull_request` con `state:open` y sin `base` no se juzga como reapertura; `compare.py default_root` da
  traceback sin git y, desde la caché del plugin, cae al cwd (exigir `--root`).
- Menores de la revisión del flujo 0.3.0 que hizo el portal (P5 de `docs/proposals/2026-10-23-portal-galivelop.md`):
  `config.py related` acepta un `cwd` con `..` o absoluto en `relatedTests` (que `validate` lo rechace);
  `session-start.sh`: `kill -- -$wd` no es un grupo y el `sleep` del vigilante queda vivo hasta el tope;
  `review-before-main.sh` sondea `gh api repos/<o>/<r>` en cada llamada y juzga cambios de título o base de un PR
  cerrado; `doctor.py` da por bueno un `npm run check` citado en un comentario (y avisos del glosario repetidos por
  mayúsculas, por comprobar); `validate` no avisa de un `worktreeDir` dentro del repo ni de un `checkWrapper` que
  limpia el entorno. Con la config de la punta de `main` rota, `pre-push` y el gancho fallan cerrados a propósito: se
  sale con un PR revisado que la arregle, o la persona sube a mano.
- P2 de `docs/proposals/2026-10-23-portal-galivelop.md` (`ci.setup`/`ci.after` y `apply.py --update` sin pisar un
  `comprobar.yml` con pasos propios): aplazada a la siguiente versión.
- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.
- La `1.0.0` solo como plugin (decidido 2026-10-22): en la Fase 9, plugin como única distribución hacia fuera y
  ganchos de git desde el plugin (sin probar); en la Fase 10, licencia de la `1.0.0` (abierta) y el portal quita su
  copia del flujo desde una sesión suya. Su historial seguirá teniendo la copia `0.2.0` (MIT).

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
