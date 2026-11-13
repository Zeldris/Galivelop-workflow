# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.6` «Medir»: `ccr-d1e2d496-0vzck8`** (hace de `version/0.6.0` mientras la sesión solo pueda subir a esta rama). `main` = `2e55d66` = **`0.5.2`** (2026-11-12, etiqueta `v0.5.2`). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | `0.5.2` en `main` (`2e55d66`, 2026-11-12) |
| Siguiente paso | **`0.6.0`** en obra: todas sus filas hechas y recogida H19 hecha (2026-11-13). Sigue: los arreglos de H19 (D90-D93, B30), versión `0.6.0` con su CHANGELOG, repaso de documentación y fases 1-3 antes de `main`. |

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

**Política de versiones** (usuario, 2026-11-01, plan §7): solo la última menor publicada recibe parches (hoy la `0.5`);
los evolutivos van a la siguiente menor que no esté en obra (`docs/roadmap.md`). Cada versión se publica en este repo
(público), a lo sumo una al día. La sesión en la nube no puede subir etiquetas (403 del proxy): la release, a mano o
desde una sesión local.

## Hecho (5 últimas)

1. 2026-11-13 — H19 hecha: recogida de la `0.6.0` sobre los 6 proyectos de H18 (`docs/proposals/2026-11-13-*.md`): 12 propuestas aprobadas; los arreglos D90-D93 y B30, a la `0.6.0`; E48, D94-D96, E49 y B31, a la `0.7`; E50, a la `0.8`. private-project-1 y private-project-3, sin novedades.
2. 2026-11-13 — 2026-11-13 — **D81 hecha**: `scripts/backport.sh [--from <rama>] [--refs <id>] [<sha>...]` trae commits de la menor a la rama de un parche: cherry-pick en orden topológico con `-x` (`-m 1` en merges), choques solo de bitácora o roadmap resueltos con la versión del parche, vacíos saltados, parada con la orden en un choque de código y cuenta final de cada sha; con `--from`, los archivos de recogida de `proposalsDir` en un commit propio (`Refs:` solo con ids que acepta el `commit-msg` del parche). En la guía de parches (contributing es/en) y `agent-map.md`; 32 tests. Revisión con 3 arreglos (`Findings: 3`).
3. 2026-11-13 — 2026-11-13 — **D89 hecha**: `handoff.py` toma como publicada la etiqueta `vX.Y.Z` más alta aunque haya `plugin.json` (que en el repo del flujo cambia antes de publicar); sin etiquetas, `plugin.json`. `archive` ya no se adelanta. Test del caso y docs es/en (`logSize`).
4. 2026-11-13 — **E44 hecha**: clave `releaseCheckBranches` (por defecto `["version/*"]`, glob de shell; `[]` la apaga): en una rama que casa, `scripts/check.sh` corre el `check` con `GW_PUSH_PROTECTED=true`, así `version.py --release` (falta de recogida, CHANGELOG sin fecha) sale en rojo en la rama de versión y no en la subida a `main`. Solo en `check.sh`, no en el `pre-push` (no bloquea subidas a mitad de versión). En esquema, plantilla, `fullCheckSkipKeys`, docs es/en (config y contributing) y copias; tests de defecto, valor dado, `[]`, HEAD suelto y valor malo. Esta rama (`ccr-…`) no casa con el defecto.
5. 2026-11-13 — **A13 hecha** (trozo C7, cierre): claves `testScanSkipDirs`, `measure.{imageTokens,mixedRatio,minOutput,coldMs}` (leídas por `measure.py` de `gw-opt-tokens` y de `gw-opt-ai`, con el literal si falta config) y `mediaContent.maxSubjects` (`figures.py`), `measure` y `mediaContent` en `fullCheckSkipKeys`; `quality_bench.py` se deja como está (herramienta interna). Claves de A13 por grupo: C1 `checkReuse*`/`stopSeverity` y afines; C2 `changeSize.severity`, `commitTypes`, `commitWipPrefix`, `agent*`; C3 `contextGuard.*`, `subagent*`; C4 comandos, `retro`, `redWithoutFix`, `branchPrefixes`, `wholeRead*`; C5 `recover`, `handoff`, `taskId`; C6 `harvest`, `ci*`, `patchCommitTypes`, `metrics.gitTimeout`; C7 las de esta fila. Tests de defecto, valor dado y valor malo.

## Pendiente

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
- **B8:** un `git revert` no lleva `Refs:` (el `commit-msg` no lo pide al concluirlo), así que solo cuenta como retrabajo si se le añade; `Findings:` y `Retries:` los pone el agente a mano (ningún gancho los comprueba); `quality` lanza un `git interpret-trailers` por commit con «refs» (0,4 s con ~580 commits).
- **B4/B5:** los informes no se escriben solos (ni gancho ni CI): se piden con `--write`; `compare` solo imprime (no tiene `--write`).
- **B3:** el ledger no separa la escritura de caché de 5 minutos (1,25 × `input`) de la de 1 hora (2 ×): `cost_of` las cobra todas como de 5 minutos. `claude-haiku-5-5` tiene precio escalonado (más de 100K tokens de entrada cuesta más) y su `cacheRead` (0,1 × `input`) es una suposición: revisar la tabla cuando salga la siguiente.
- **B2:** `apply.py` no pone `merge=union` del ledger en el `.gitattributes` de los proyectos (aquí, a mano); el ledger de la última parada de una sesión en la nube se pierde si el contenedor muere antes del siguiente commit (lo apuntado queda; lo no apuntado no se recupera: el transcript ya no está).
- **Bloque I (cerrado 2026-11-08):** las respuestas del `grilling` están en `docs/design/I-lifecycle.md`; la `0.7` empieza por C11 (toca `commit-msg`, D43 y `trace.py`), luego C13 y C12. Las claves nuevas (`taskRecord`, `approvals.maxAgeDays`, `privateNames`…) no existen aún en `config.py` ni en `docs/es/config.md`: se crean con la tarea que las use.
- **Archivado (2026-11-10):** 19 elemento(s) de versiones ya publicadas (≤ 0.5.1) en [handoff-archive.md](records/handoff-archive.md)
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

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
