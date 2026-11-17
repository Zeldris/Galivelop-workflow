# Pendiente

Los evolutivos aprobados que esperan su versión: solo la última menor publicada recibe parches (plan §7), así que
cada uno va a la menor de su tema (H12, [`roadmap.md`](../roadmap.md)). Cada línea lleva su versión entre comillas
invertidas tras la casilla y apunta a su propuesta, que lleva el detalle; al aplicarla, se marca aquí con la fecha y el
commit, y la entrada va al CHANGELOG de esa versión. Lo marcado `[x]` se hizo en la rama `version/1.0.0` y sale con la
`0.5`.

Reparto: scripts, checks, config y git a la `0.5`; `orchestrate-dealer` y los encargos de revisión a la `0.7`
(junto a C10); instalación, plantillas y stacks a la `0.8` (junto a E4); textos de la documentación a la `0.9` (E8).

## De la recogida del 2026-10-27 (`private-project-2`)

P1-P4 salieron en el parche `0.4.3`.

- [ ] `0.8` · **private-project-2 P5**: `orchestrate-dealer`: si la revisión de toda la rama va justo después y ya está decidida, el último
  bloque no se revisa aparte. [`2026-10-27-private-project-2.md`](../proposals/2026-10-27-private-project-2.md)
- [x] `0.5` · **private-project-2 P6** (D18, 2026-11-03): `scripts/ci-estado.py`, que lee el estado de Actions de una rama o commit (token y `gh` de
  `revision-antes-de-main.sh`). [`2026-10-27-private-project-2.md`](../proposals/2026-10-27-private-project-2.md)
- [x] `0.5` · **private-project-2 P7** (D19, 2026-11-03): clave `ciPython` en `gw.json` con las versiones de Python que la plantilla del CI recorre en matriz.
  [`2026-10-27-private-project-2.md`](../proposals/2026-10-27-private-project-2.md)
- [ ] `0.8` · **private-project-2 P8**: `aplicar.py --init` añade un `.gitignore` por stack en un bloque con marca, sin pisar el existente.
  [`2026-10-27-private-project-2.md`](../proposals/2026-10-27-private-project-2.md)

## De la recogida del 2026-10-26

- [x] `0.5` · **WMF P2** (2026-10-26): `bitacora.py clash` detecta un id de tarea dado de alta a la vez en dos ramas para
  tareas distintas; lo corren el `pre-push` (contra `main` y los merges nuevos; aviso con otras ramas) y el
  `pre-commit` de un merge con conflictos. [`2026-10-26-world-maker-fantasy.md`](../proposals/2026-10-26-world-maker-fantasy.md)
- [x] `0.5` · **WMF P3** (2026-10-26): `recuperar.py --estado` enseña los otros worktrees con su rama y su fila de la bitácora.
  [`2026-10-26-world-maker-fantasy.md`](../proposals/2026-10-26-world-maker-fantasy.md)
- [x] `0.5` · **INS P3 (segunda parte)** (2026-10-26): `ci-local.py` corre el CI de GitHub en local y, con `--apuntar`, lo
  deja en `ciLocalLog`; el gancho de PR acepta esa línea verde si el CI no arrancó (la corrección mínima, en la `0.4.1`). [`2026-10-26-instalador-wmf-tarkor.md`](../proposals/2026-10-26-instalador-wmf-tarkor.md)
- [x] `0.5` · **INS P5** (2026-10-26): `recuperar.py` cuenta las compactaciones desde el inicio de la tarea (`merge-base` con la rama
  protegida), no de toda la sesión. [`2026-10-26-instalador-wmf-tarkor.md`](../proposals/2026-10-26-instalador-wmf-tarkor.md)
- [x] `0.5` · **INS P6** (2026-10-26): el `pre-commit` comprueba las tareas cerradas frente a «Hecho» (`bitacora.py closed --staged`).
  [`2026-10-26-instalador-wmf-tarkor.md`](../proposals/2026-10-26-instalador-wmf-tarkor.md)
- [x] `0.5` · **INS P7** (2026-10-26): cuatro frases en skills (`orchestrate-dealer`: buscar las otras apariciones de un fallo de patrón y
  repartir también los arreglos de la revisión; `pr`: `/clear` tras fusionar; revisión: hallazgos a un archivo).
  [`2026-10-26-instalador-wmf-tarkor.md`](../proposals/2026-10-26-instalador-wmf-tarkor.md)
- [x] `0.5` · **Portal P2** (2026-10-26): avisos y reglas (`pkill -f` se mata a sí mismo; runbooks de tareas programadas revisados como
  código; marcar en `REVIEW.md` los datos que caducan). [`2026-10-26-portal-galivelop.md`](../proposals/2026-10-26-portal-galivelop.md)
- [x] `0.5` · **Portal P3** (2026-10-26): `gw-media-content` deja un `web.md` opcional con el bloque del muro, en forma
  genérica (canal `web`: `estado`, `fecha`, `texto` por idioma, `muro`; `--idiomas-web`).
  [`2026-10-26-portal-galivelop.md`](../proposals/2026-10-26-portal-galivelop.md)

## De la recogida del 2026-10-26 (segunda)

Decididas el 2026-10-27; las correcciones (INS P8, private-project-1 P3, P4 y la parte Java de P11) salieron en la `0.4.2`.

- [x] `0.5` · **private-project-1 P1:** (D20, 2026-11-03) `ciIgnore`, estados de CI ajenos (p. ej. un despliegue) que no bloquean la fusión.
  [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [x] `0.5` · **private-project-1 P2:** (D21, 2026-11-03) firmas del agente también en el cuerpo de PR, issues y comentarios de GitHub, y aviso de un
  `user.email` `noreply@anthropic.com`. [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [x] `0.5` · **INS P12 + WMF P4:** (E17, 2026-11-03) el check en una orden con resumen y la salida recortada.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../proposals/2026-10-26-instalador-wmf-tarkor-2.md),
  [`2026-10-26-world-maker-fantasy-2.md`](../proposals/2026-10-26-world-maker-fantasy-2.md)
- [x] `0.5` · **INS P9:** (D22, 2026-11-03) `bitacora.py own-row --staged`, la propia fila comprobada al hacer el commit.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../proposals/2026-10-26-instalador-wmf-tarkor-2.md)
- [x] `0.5` · **private-project-1 P6:** (D24, 2026-11-03) `reviewed.sh` avisa del código sin revisar desde la última marca.
  [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [x] `0.5` · **private-project-1 P5:** (D25, 2026-11-03) `red-without-fix.sh --fix-at <commit>` y distinguir un rojo de compilación de uno de la
  aserción. [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [ ] `0.8` · **Portal P4:** `orchestrate-dealer`, los repos que solo se leen se clonan aparte y sin registrar.
  [`2026-10-26-portal-galivelop-2.md`](../proposals/2026-10-26-portal-galivelop-2.md)
- [x] `0.5` · **INS P10:** (D26, 2026-11-03) `doctor.py` avisa de worktrees ya fusionados.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../proposals/2026-10-26-instalador-wmf-tarkor-2.md)
- [x] `0.5` · **private-project-1 P7:** (D23, 2026-11-03) `bitacora.py set-row`. [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [x] `0.5` · **private-project-1 P8:** (D27, 2026-11-03) `doctor.py` avisa de `cd <carpeta> && …` sin `worktreeLinks`.
  [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [ ] `0.8` · **INS P11:** `scout-updates` lee la versión de Rust del proyecto.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../proposals/2026-10-26-instalador-wmf-tarkor-2.md)
- [ ] `0.8` · **private-project-1 P9:** el encargo de revisión lleva `git diff --stat`.
  [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [ ] `0.8` · **INS P13 + Portal P5:** en la plantilla de `REVIEW.md`, la regla de invariantes y el apartado «Navegadores».
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../proposals/2026-10-26-instalador-wmf-tarkor-2.md),
  [`2026-10-26-portal-galivelop-2.md`](../proposals/2026-10-26-portal-galivelop-2.md)
- [ ] `0.9` · **private-project-1 P10:** textos menores (`/clear` tras un commit `WIP:`, `perPage: 1`, `git fetch -q && git status -sb`).
  [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [x] `0.5` · **private-project-1 P11 (archivos borrados):** (D29, 2026-11-03) `related-tests.sh` incluye los archivos borrados en `{files}` o corre
  todo si un push solo borra. [`2026-10-26-private-project-1.md`](../proposals/2026-10-26-private-project-1.md)
- [x] `0.5` · **Del arreglo de INS P8** (arreglado en la `0.4.2`, `4aecf5c`): `prepush-ramas.sh` comprueba la bitácora como
  queda en la punta que se sube, así que un log malo en un commit intermedio se arregla con un commit nuevo encima.

## De la retro del parche `0.4.3`

- [x] `0.5` · **R1 (`version.py`, CHANGELOG):** (D30, 2026-11-03) comprobar que existe cada ruta del repo citada entre comillas invertidas en la
  entrada nueva del CHANGELOG (`docs/…`, `scripts/…`, `skills/…`), salvo las que llevan marcadores (`vX.Y.Z`). La
  entrada `0.4.3` citaba un archivo que solo estaba en `version/1.0.0` y lo cazó la revisión, no el check. Con su test.
  `retro-2026-10-27-parche-0-4-3.md` (rama `ccr-6dfbc880-ddr41g`).

## De la retro del parche `0.4.2`

[`retro-2026-10-27-parche-0-4-2.md`](retro-2026-10-27-parche-0-4-2.md), aprobadas por el usuario el 2026-10-27.

- [x] `0.5` · **P3 (`doctor.py`):** (D28, 2026-11-03) avisar de un `core.hooksPath` absoluto que apunta al `.githooks` del checkout principal
  (los worktrees correrían los ganchos de otra rama), con la orden que lo arregla
  (`git config core.hooksPath .githooks`). Test del aviso y de su motivo.
- [x] `0.5` · **P4 (`commit-msg`):** (D31, 2026-11-03) comprobar la línea `Siguiente:` en los mensajes, también los de fusión que escribe
  `fusionar.sh` (o que `fusionar.sh` la exija en su mensaje). Escape `GW_NO_NEXT=1` para un mensaje legítimo sin
  ella, y el aviso lo dice. Misma familia que la comprobación de firmas del agente.
- [ ] `0.4.4` · **P5 (regla QUOTED del `pre-commit`):** sin falsos positivos en `.md` (una etiqueta de traducción citada como
  ejemplo). Tests de los dos lados: un secreto real en un `.md` sigue bloqueado.

## De la retro del parche `0.4.1`

- [x] `0.5` · **P3** (2026-10-26, `4e3af46`, `b50ccb6`, `f50072e`): el `pre-push` no repite un check ya en verde sobre el
  mismo árbol y las mismas órdenes (caché en el directorio común de git, con tests de árbol distinto, órdenes
  distintas y rojo que no se guarda). Documentada en la `0.5.0` del CHANGELOG, `config.md`, `troubleshooting.md` y
  `AGENTS.md`; falta, como mejora posible, que `fusionar.sh` también apunte el verde.
  [`retro-2026-10-26-parche-0-4-1.md`](retro-2026-10-26-parche-0-4-1.md)

## Del usuario

- [x] `0.5` · **Autoría sin firmas** (2026-10-26, `7b3c91c`, `f7de072`, `7785a98`): `agentSignatures` en `gw.json` (por
  defecto `true`; este repo, `false`) y `aplicar --init --agent-signatures`; con `false`, el `commit-msg` rechaza un
  `Co-Authored-By` de Claude (`noreply@anthropic.com` o nombre de modelo), `Claude-Session`, «Generated with Claude
  Code» y el enlace de sesión a principio de línea, sin mirar comentarios ni lo que va tras las tijeras de
  `commit -v`; se salta en rebase. Plantillas `AGENTS.md`, `config`, `aplicar`, `problemas`, mapa y CHANGELOG.

## De recogidas anteriores

- [x] `0.5` · **Labs P3:** las skills `to-spec` y `wayfinder`, con un destino Markdown local por defecto. ✅ 2026-10-26:
  `docs/specs/<fecha>-<tema>.md` y `docs/mapas/<tema>.md` (cada ticket, una casilla); cambiable desde
  `.claude/gw/<skill>.md`; filas nuevas en el `selector`. [`2026-10-25-labs-log-detective.md`](../proposals/2026-10-25-labs-log-detective.md)

## Pendiente (de la bitácora)

- **D104-D108 y E62, «Todo configurable» (leves):** el aviso de `gw-worker` de E62 (`subagent-cap.py`) y el de `/clear` de D108 no tienen clave para apagarlos, `PHASE_KEYS` son fijas y la ruta `tests/shellcheck.sh` es fija en `tests-for.py`.
- **`commit-message.py` (leves):** `closing()` hace cuatro `git show` en cada commit aunque no se preparen roadmap ni bitácora; `VERSION_HEADING` es distinta de `roadmap.section_ids`.
- **0.6.1, revisión de D104-D108 (leves sin arreglar; detalle en el commit de la fusión):** D104: `apply.py` no siembra `pending.md` en los proyectos; `docs/*/patterns.md` no habla de `move-pending`; `recover.py` repite la expresión de sección de `handoff.py`. D105: `section_ids` salta la cabecera solo si es «Id», no compara las secciones sin versión y no captura `UnicodeDecodeError`. D106: falta un punto en la fila de `testMap` de `config.md` (es/en); con `testMap.command` vacío sale antes de shellcheck; no mira ganchos sin `.sh`; usa el `tests/shellcheck.sh` del proyecto instalado. D107: la subida final en primer plano del encargo choca con «el push va en segundo plano» de AGENTS.md (falta la excepción). (Lo de `handoff.py`, hecho en B38.)
- **0.6.1, revisión (leves sin arreglar):** D98, un directorio vacío o un cambio solo de modo no se aparta; no probado en un bash 3.2 real. D101, `git grep` sin timeout. D100, el test del punto 4 no es de punta a punta. D101, una idea que repite tal cual una línea que otro `.md` ya tenía en la última recogida se descarta como movida.
- **Herramientas (0.6.1):** `apply.py` avisa de que 3 plantillas de `.claude/gw/` (gw-opt-tokens.md, gw-opt-ai.md, gw-scout-updates.md) vienen de la v0.5.1; `tests-for.py --run` pasa de 25 min con agentes en paralelo; `test_hooks.PrePush` falla a ratos con carga.
- **D81:** la cuenta final de `backport.sh` usa `git cherry`, que no ve los merges ni un commit raíz (`c^` falla): esos salen como no traídos aunque estén en el parche (revisión de D81, leve).
- **A13 (C1):** `checkReuseTtl`/`checkReuseKeep` se leen del `gw.json` de la copia de trabajo, no del commit que se sube (`check-green.sh:41`; el `pre-push` usa `cfg_at`).
- **Error de proceso (2026-11-11):** los arreglos de la `0.5.2` se hicieron en la rama de la `0.6`. Para la retro: crear la rama del parche desde `main` antes de los arreglos (o pedirla al usuario), y un aviso en `commit-msg` o `merge-branch.sh` cuando una fila de parche cae en una rama con evolutivos de la menor siguiente.

- **E47:** la lista por defecto de `fullCheckSkipKeys` sale del check de este repo (un `check` que lea una la quita).
- **E46:** el índice de git copiado tiene datos de stat viejos: el primer `git status` de un test lo reescribe (un test que compare el índice lo lee después); quedan `/tmp/gw-check-fifo.*` de corridas del check (sin mirar de dónde).
- **D82:** con el clon del flujo o el árbol sucios, `review-scope.py` puede contar mal lo vendored; en `--trivial` un binario de código cuenta 0 líneas.
- **D84:** `Swatinem/rust-cache@v2` sin fecha ni fuente comprobada; el job `versions` corre solo en ubuntu.
- **E43:** `testMap` cuenta como corrido aunque solo corre en el `pre-push` de rama; rutas de Windows o absolutas no casan; un solo nivel de script; no poda `build`/`dist`/`target`, y el defecto `env` salta un `src/env` real.
- **D85:** las llamadas a git de `change-size.py` desde `recover.py` no tienen timeout; el patrón de importlib está duplicado (`harvest.py:55`).
- **B28:** `apply.py` no detecta agentes huérfanos en `.claude/agents/`.
- **B26:** en un worktree bajo `.claude/worktrees/`, las rutas se comparan con la raíz principal, no con la del worktree.
- **Dealer:** las filas del roadmap que marcan los subagentes chocan al fusionar (filas contiguas): las marca la sesión principal tras fusionar.
- **D76:** el `.steal` sin pid se descarta tras 1 s: con un `ps` lento, dos procesos pueden robar a la vez un candado vivo.
- **E38:** un valor de varias palabras con mayúsculas y sin dígitos sigue pasando como prosa en un `.md`.
- **E39:** la rama BSD de `script(1)` no se prueba en Linux.
- **D71:** `set-row` no acepta la rama como posicional (solo `--branch`).
- **D88:** un agente lanzado antes de la cola leída (`stopTranscriptBytes`) no se ve.
- **D55:** `roadmap.py` solo lee tablas (primera celda = id) y reescribe la última celda entera; la plantilla trae `roadmapFiles: []` (apagado).
- **E27:** solo para el repo del flujo (la plantilla de CI de un proyecto no la lee); al cambiar la clave, la nube no reinstala sola (el sello guarda la orden; avisa `tests/shellcheck.sh`).
- **B19:** es una regla de criterio de la skill (ningún script la comprueba); «idénticas» lo dice `apply.py --check`, que el agente corre antes del `/code-review`.
- **D54:** cambiar la clave no reescribe `check.yml` hasta `apply.py --update`; sin PR no hay CI («none», exit 1).
- **D53:** `fnmatch` deja que `*` cruce `/`; la plantilla `merged` (`AGENTS.md`, `CLAUDE.md`) también respeta `ownedFiles`; `doctor.py` solo lo mira en los ganchos y las skills (no en el CI ni en otros avisos de `/gw-update`).
- **D49:** el alcance sale de los archivos de los commits nuevos de cada rama; aquí, tocar `scripts/` toca su copia en `.claude/gw/` y corre el completo.
- **D48:** `next-id` solo ve los ids que abre una entrada del plan (línea sin sangría, como `clash`), no los que solo nombra un commit o la bitácora; sin `--fetch`, las ramas remotas son las del último `git fetch`.
- **D43:** el bloque es la suma de cada commit (una línea cambiada dos veces cuenta dos); una revisión de bloque sin hallazgos solo cuenta si algún commit lleva `Findings: 0`; con `--base` o sin `origin/<protegida>` ni local, el bloque no mira trailers o no se comprueba (nota); `linguist-generated` se lee del índice para lo preparado y del árbol de trabajo para los commits.
- **E22:** con el Python viejo solo corren los tests del cambio desde el upstream: una vez subido, ya no se repiten; las suites de ganchos lanzan los scripts con `python3` (el actual), así que esa parte no la cubre; el CI sigue con un solo Python (3.12).
- **E21:** `tests-for.py` no es un gancho: ningún check obliga a correrlo (lo pide el encargo del dealer); el mapa de este repo es el de la retro R2 más esquema, skills y plantillas; un test que solo importan otros (`test_utils.py`) se corre a sí mismo sin casos.
- **B11:** el modo restringido (`CLAUDE_CODE_SUBAGENT_MODEL` + `_FORCE` puestos por el flujo) queda para el bloque C; el aviso de `subagent-cap.py` llega con el resultado de la llamada, así que la primera llamada sin campos ya corrió con lo heredado.
- **B8:** un `git revert` no lleva `Refs:` (el `commit-msg` no lo pide al concluirlo), así que solo cuenta como retrabajo si se le añade; `Findings:` y `Retries:` los pone el agente a mano (el `commit-msg` solo avisa de un mensaje de arreglos de revisión sin `Findings:`, E60); `quality` lanza un `git interpret-trailers` por commit con «refs» (0,4 s con ~580 commits).
- **B4/B5:** los informes no se escriben solos (ni gancho ni CI): se piden con `--write`; `compare` solo imprime (no tiene `--write`).
- **B3:** el ledger no separa la escritura de caché de 5 minutos (1,25 × `input`) de la de 1 hora (2 ×): `cost_of` las cobra todas como de 5 minutos. `claude-haiku-5-5` tiene precio escalonado (más de 100K tokens de entrada cuesta más) y su `cacheRead` (0,1 × `input`) es una suposición: revisar la tabla cuando salga la siguiente.
- **B2:** el ledger de la última parada de una sesión en la nube se pierde si el contenedor muere antes del siguiente commit (lo apuntado queda; lo no apuntado no se recupera: el transcript ya no está).
- **Bloque I (cerrado 2026-11-08):** las respuestas del `grilling` están en `docs/design/I-lifecycle.md`; la `0.7` empieza por C11 (toca `commit-msg`, D43 y `trace.py`), luego C13 y C12. Las claves nuevas (`taskRecord`, `approvals.maxAgeDays`, `privateNames`…) no existen aún en `config.py` ni en `docs/es/config.md`: se crean con la tarea que las use.
- **Archivado (2026-11-10):** 19 elemento(s) de versiones ya publicadas (≤ 0.5.1) en [handoff-archive.md](handoff-archive.md)
- **Leves de D11/D12/D15/D16 (2026-11-02, no bloquean):** `commit-message.py`: con `core.commentChar=auto` los
  comentarios quedan como último párrafo y dan «no Refs trailer» (le pasaba ya al de firmas); `refsSources` no se
  valida (`..`, rutas absolutas). `merge-branch.sh`: si git no ve el último párrafo como trailers, sus `Refs:` se
  pierden sin aviso; `get taskId` no distingue «sin definir» de «ilegible». `version.py`: `BREAKING CHANGE:` en prosa
  del último párrafo cuenta. Líneas de más de 120 caracteres en README y `contributing.md`. Revisiones en el
  scratchpad de la sesión (no subidas).
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
- Menor de la revisión antes de `main`: `checkWrapper` se aplica en tres sitios (`pre-push` y `merge-branch.sh` con
  `sed`, `config.py` con `shlex`) y la plantilla de CI no lo aplica: que lo construya solo `config.py`.
- P2 de `docs/proposals/2026-10-23-portal-galivelop.md` (`ci.setup`/`ci.after` y `apply.py --update` sin pisar un
  `comprobar.yml` con pasos propios): aplazada a la siguiente versión.
- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.
- La `1.0.0` solo como plugin (decidido 2026-10-22): en la Fase 9, plugin como única distribución hacia fuera y
  ganchos de git desde el plugin (sin probar); en la Fase 10, licencia de la `1.0.0` (abierta) y el portal quita su
  copia del flujo desde una sesión suya. Su historial seguirá teniendo la copia `0.2.0` (MIT).
- Menores de la revisión de E52 (9158b78): el aviso «cannot read the vX template» recomienda `git fetch --tags`
  también cuando la causa es `render()` o un flujo sin git (que `template_at` devuelva la causa); `--summary` imprime
  `differs REVIEW.md` aunque la plantilla no cambiara entre vX y vY; los tests de vX se saltan sin las etiquetas
  locales (en el CI no, `fetch-depth: 0`): un repo de prueba con sus propias etiquetas.
- Menores de la revisión de B36 (f14a8ac): si una comprobación posterior del `pre-commit` falla, el libro de tokens
  se queda preparado en el índice; sus líneas cuentan para `changeSize`, que no lo excluye; `config.py validate`
  acepta un `metrics.ledger` fuera del repo (el gancho y `apply.py` ya lo saltan).
- Menores de la revisión de E41 (efa42c6): el código de salida 2 de `config.py author-check` se confunde con el de
  argparse (un `config.py` viejo tras un `/gw-update` a medias da «cannot read authorDeny» y salta el control; ahora
  también en `--range`); un patrón sin `@` solo mira el nombre y uno con `@` es correo exacto (pasan
  un correo de Anthropic con otro nombre y `x+claude@users.noreply.github.com`; ¿patrones de dominio?); un patrón que
  empieza o acaba en no-palabra (`[bot]`) nunca casa.
- Menores de la revisión de B37+E56+E57 (desde f18432c): `generated-copy.py` avisa de cualquier archivo bajo un prefijo
  de copia, aunque `apply.py` no lo copie (`WORKFLOW_ONLY_SCRIPTS`, otro `.json` de `schema/`, subcarpetas de
  `scripts/`, `.claude/skills/README.md`), y no avisa al editar `.claude/settings.json` (fusión con
  `templates/claude/settings.json`, no copia); `read_event()` va ya repetido en seis ganchos (un ayudante común en
  `config.py`); el escáner de `tests/test_waits.py` no ve un `wait(10)`/`join(5)` posicional, un plazo en dos líneas
  ni un sondeo cuyo `sleep(` cae a más de tres líneas.
- Menor de la revisión de D109 (`0.6.2`): una `refs/remotes/origin/<protegida>` caducada (la rama ya no existe en el
  remoto) solo cambia el texto del aviso de `reviewed.sh`, no la base; se acepta.
- Notas de D110 (`0.6.2`): con un upstream de remoto `.` no existe la ref `<remoto>/<protegida>` y `before-stop.py`
  cuenta solo `@{u}..HEAD`, como antes; un `GitError` de `unpushed()` va a avisos y deja parar (diseño anterior).
- Leves de la fase 1 de la `0.6.2` (`review-062.md`): L1, con `requireRetro` y sin la protegida en el remoto,
  `reviewed.sh` acepta cualquier retro de la historia, sin test; L2, la cabecera de `reviewed.sh` no cuenta la base
  de árbol vacío (D109); L3, `templates/es|en/AGENTS.md` describe el gancho `Stop` de la nube sin fecha ni fuente;
  L4, `docs/es|en/troubleshooting.md` cita el mensaje con «main» literal en vez de `<protegida>`/`<protected>`.
- Leves de D116/D118 (`0.6.2`): con shellcheck ausente en CI o en la nube, `tests-for.py --run` acaba diciendo «fix
  the .sh files and run again» cuando lo que toca es instalarlo (la orden sale antes, en stderr); la primera línea del
  docstring de `run_shellcheck` pasa de 120 caracteres.
- Leves de D119 (`0.6.2`): el aviso de `gw-worker` de `subagent-cap.py` solo va en la salida normal, no en el `ask`
  (sin `session_id`, `CannotCount`) ni en la denegación por tope (`subagentCapAction: deny`), aunque su docstring dice
  que las notas van en todo `ask`; falta una línea en blanco antes de `class CapOfOne` en `tests/test_subagent_cap.py`.
- (0.6.2, herramienta, leve) `scripts/test-run.py`: una subida de `507e042` falló con «ran 1928 tests, discovered 1924» sin ningún test en rojo y no se reprodujo (check entero en verde en `ede03d6`); el mensaje no dice qué unidad contó de más. Que liste las unidades cuyo recuento no casa con el descubierto.
- (fase 3 de la 0.7.1, leve) `scripts/ci-status.py` (D125), rama `--failed`: un job cancelado sin pasos no cuenta como `unstarted`, así que `failure_details` intenta leer su log y añade `(no log: … 404 …)` junto al aviso de relanzar; saltar en `--failed` los check-runs con aviso de relanzar o decir «no log: cancelled before any step ran».
- (fase 3 de la 0.7.1, leve) `scripts/version.py:512-516` (D124): al sellar, el aviso de recogida reutiliza el texto de `harvest_check`, que termina en «retry with this command: python3 scripts/version.py --release»; recién sellado, `--release` falla además por el CHANGELOG sin terminar. Que `harvest_check` reciba la orden de reintento (`retry=`) y al sellar diga «then commit it; `--release` checks it again before main».
- (revisión del bloque E58-E61 + B41, leve) `whole-read.py` corre en cada `Read` y cada `Bash` (matcher `^(Read|Bash)$`): un arranque de Python por llamada; medir su coste y, si pesa, filtrar antes (por ejemplo, saltar en el propio gancho las órdenes sin `cat`/`sed`/`nl`/… sin cargar el config).
- (revisión del bloque E58-E61 + B41, leve) Configurabilidad: el remoto `origin` que nombra la línea de `recover.py --state` y la carpeta de estado de `whole-read.py` (`$TMPDIR`) van fijos; pasarlos a claves de `.claude/gw.json` si un proyecto lo pide.
- [ ] `0.8` · **Revisión D94 n.º 5**: `push.sh` llama a `git ls-remote` sin tiempo límite; con la red colgada se queda esperando tras cada intento (candidato: clave `pushLsRemoteTimeout`).
- [ ] `0.8` · **Revisión D94 n.º 7**: `config.push_retry_delays()` no la usa nadie (push.sh lee con `get`, que ya valida con el esquema): quitarla con su test, o que `get` la use.
- [ ] `0.8` · **Revisión D94 n.º 8**: los mensajes de `before-stop.py`, `recover.py`, `reviewed.sh` y `review-before-main.sh` (y sus copias en `.claude/gw/scripts`) siguen mandando `git push -u origin <rama>` en vez de `push.sh`; alinearlos con `AGENTS.md` y las plantillas.
- [ ] `0.8` · **Revisión D95 n.º 5**: `split_lines` elige CRLF si alguna línea lo tiene y reescribe todas así (y quita las líneas en blanco del final); `done` conserva el de cada línea (candidato: respetar el fin de cada línea).
- [ ] `0.8` · **Revisión D95 n.º 9**: `add-pending` y `add-decision` leen, cambian y reescriben sin cerrojo: dos a la vez (subagentes o ganchos) pierden un ítem aunque ambos informen de éxito (candidato: cerrojo sobre el archivo, como el de `check.sh`).
- [ ] `0.8` · **Revisión D95 n.º 11**: `log_is_english` relee la bitácora en cada llamada que lo necesita (eficiencia, resuelto en parte: ya solo se llama al crear algo).
- `0.8`: `handoff.cellHardLimit` menor que `cellLimit` no se valida (revisión de D96, hallazgo 5): `config.py validate` debería rechazarlo o avisar.
- `0.8`: `tests/check.sh` corre `handoff.py check` dos veces (`check --strict` y dentro de `preflight`; revisión de D61, hallazgo 6): dejar una sola pasada.
- D62 (revisión n.º 3, 0.8): el aviso de CI del `pre-push` lanza `ci-status.py` con `start_new_session`; con Ctrl-C, ci-status y `gh`/`curl` siguen huérfanos hasta `ciStatusTimeout`: matar el grupo en un try/finally.
- D62 (revisión n.º 5, 0.8): el aviso de CI del `pre-push` deduplica por sha remoto y nombra solo la primera rama; agrupar las ramas por sha y nombrarlas todas.
- D62 (revisión n.º 8, 0.8): la orden del aviso de CI del `pre-push` usa una ruta relativa a la raíz; desde un subdirectorio no se encuentra: dar la ruta absoluta.
- D62 (revisión n.º 9, 0.8): si `config.py` no lee `prepushCiWarn` o su timeout, el aviso de CI se apaga sin decir nada; sacar una línea con `config.py validate`.
