# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.5` «Base»: `ccr-d1e2d496-0vzck8`** (2026-11-02; creada desde `version/1.0.0` en `a61cdc5`; hace de `version/0.5.0` (H-13) mientras la sesión solo pueda subir a esta rama). **No hay `0.4.4`** (usuario, 2026-11-03: «publicamos la 0.5, ya directamente»): sus arreglos salen en la `0.5.0` y `ccr-6dfbc880-ddr41g` queda sin uso. `version/1.0.0` se queda con el diseño (`docs/design/`). `main` = `eeec886` = **`0.5.1`** (2026-11-05; etiqueta y release `v0.5.1` publicadas desde una sesión local) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). Los arreglos del CI de Ubuntu y macOS (`66a4ecd`) están en esta rama; `main` (`0e04504`, `v0.4.3`) sigue en rojo en el CI hasta la `0.5.0` |
| Fase en curso | **6 cerrada**; `0.4.1` en `main` (2026-10-26). La `0.4` es la última menor `0.x` (usuario, 2026-10-25, plan §7): solo parches `0.4.x`, y lo nuevo de una recogida va a la `1.0.0`. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | `0.4.2` en `main` (`8a6f367`, 2026-10-27), con confirmación del usuario: fases 1-3 hechas, marca de revisión `8a6f367`. **Comprobado solo en local** (confirmado por el usuario): el CI de Actions no arranca (sin cuota); el check completo del `pre-push` pasó en verde para la rama y para `main` (con `version.py --release`). Textos de la release en `docs/records/release-v0.4.2.md` (en la rama `ccr-6dfbc880-ddr41g`) |
| Siguiente paso | **B1-B8, B10, B11 y E21 hechas (2026-11-09)**; **B16, D42, E22, B18, D48 y D43 hechas (2026-11-10)**. **Revisión de bloque hecha (2026-11-10)** sobre `origin/main...cb071d6`; el siguiente bloque se mide desde su commit (`Findings: 4`). **D49 y D53 hechas (2026-11-10).** **Siguiente:** el resto de pendientes de la `0.6` (`docs/roadmap.md`), empezando por D54; la tabla determinista espera a 4 semanas de libro. Presupuesto de compactaciones: 1 |

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

1. 2026-11-10 — D53: clave `ownedFiles` (patrones `fnmatch` relativos a la raíz; `config.py` rechaza rutas absolutas y `..`; ayudante `config.owned`). `apply.py`: un archivo propio que existe y difiere no se escribe ni recibe `.gw-new` y no es desvío (`--check` sale 0; línea `owned by the project (ownedFiles): …`); si falta, se crea; un `.gw-new` sobrante da aviso, no pendiente; uno que el flujo ya no tiene no es huérfano. `doctor.py`: un gancho propio con otra cabecera es `ok`, y las skills propias no cuentan como desfasadas. Esquema, plantilla `gw.json`, config.md y apply.md (es/en); 7 tests.
2. 2026-11-10 — D49: el `pre-push` de una rama que no es la protegida corre solo los `relatedTests` (`branchCheck: related`, por defecto); corre el `check` completo si los commits nuevos de esa rama tocan `.claude/gw.json` o una ruta de `fullCheckPaths` (cambio de entorno; por defecto `.githooks/`, `.claude/gw/`, `settings.json` y `.github/workflows/`), si `relatedTests` no tiene órdenes o con `branchCheck: full`; la protegida, siempre completo. Decide `config.py push-scope`; el gancho separa `checkout_at` de `run_checks`. Aquí, `relatedTests` = `tests-for.py --run`. `AGENTS.md` y plantillas (es/en), config.md, roadmap; 6 tests (`PrePushBranchCheck`, `test_push_scope_…`).
3. 2026-11-10 — Revisión del bloque (`origin/main...cb071d6`, 4 de 10 hallazgos): `handoff.py archive` sin `.claude-plugin/plugin.json` (un proyecto) toma la etiqueta `vX.Y.Z` más alta; `tests-for.py` acepta rutas por un enlace simbólico a la raíz; `metrics.py` falla si `git interpret-trailers` falla; `config.py` lee el esquema una vez por proceso (`_section`). 3 tests; config.md es/en.
4. 2026-11-10 — D43: `scripts/change-size.py`, desde el `commit-msg` (solo aviso; si falta el script, falla): líneas del commit preparado (> `changeSize.commit`, 400) y del bloque abierto (> `block`, 1000: commits de la rama tras el último con `Findings:`, más lo preparado), sin binarios, `exclude`, `linguist-generated` ni el lado menor de un par. Aquí, `exclude` suma `.claude/skills/` y `.gitattributes` marca `docs/mkt` y el libro. 13 tests en `test_change_size.py`.
5. 2026-11-10 — D48: `handoff.py next-id <prefijo> [--fetch]` da el siguiente id libre (uno más que el mayor que abre el plan en la copia, el índice o cualquier rama local o remota; funciona sin `logRows`; sin plan o si falla el `--fetch`, falla). `free_id` entiende ids sin guion (`D12` → `D13`; antes `clash` sugería `D12-1`). `plan: [docs/roadmap.md]` en el `gw.json` de este repo; `AGENTS.md`, roadmap, config.md y mapa; 4 tests en `test_utils.py` (clase `HandoffNextId`).

## Pendiente

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
- **A10, leves de la revisión (no bloquean):** el conversor Markdown pierde el `#` de `# Learn C#`, anida mal `***x***`, parte una tabla con `|` dentro de código, toma `2024.` al principio de línea por lista, aplana las listas anidadas y deja el markup del título; dos fuentes con el mismo idioma y nombre chocan; Playwright se resuelve global. De la segunda revisión: la reescritura de rutas de la CSS solo cubre `url(...)` en minúsculas con comillas iguales (no `@import "x.css"`, `URL(…)`, `url("it's.png")` ni `image-set("x.png" 1x)`), y el énfasis entra en el `href` de un enlace (`[a](https://x.com/*a*b*)`).
- **A10, leve:** el enlace de idioma de la cabecera de cada hoja (`[English](../en/…md)`) sale en el HTML y el PDF apuntando a un `.md` que no está junto al HTML; quitarlo o reescribirlo a `.html` en `mkt-sheet.py`.
- **Bloque I (cerrado 2026-11-08):** las respuestas del `grilling` están en `docs/design/I-lifecycle.md`; la `0.7` empieza por C11 (toca `commit-msg`, D43 y `trace.py`), luego C13 y C12. Las claves nuevas (`taskRecord`, `approvals.maxAgeDays`, `privateNames`…) no existen aún en `config.py` ni en `docs/es/config.md`: se crean con la tarea que las use.
- **Archivado (2026-11-10):** 19 elemento(s) de versiones ya publicadas (≤ 0.5.1) en [handoff-archive.md](records/handoff-archive.md)
- **Leves de D11/D12/D15/D16 (2026-11-02, no bloquean):** `commit-message.py`: con `core.commentChar=auto` los
  comentarios quedan como último párrafo y dan «no Refs trailer» (le pasaba ya al de firmas); `refsSources` no se
  valida (`..`, rutas absolutas). `merge-branch.sh`: si git no ve el último párrafo como trailers, sus `Refs:` se
  pierden sin aviso; `get taskId` no distingue «sin definir» de «ilegible». `version.py`: `BREAKING CHANGE:` en prosa
  del último párrafo cuenta. Líneas de más de 120 caracteres en README y `contributing.md`. Revisiones en el
  scratchpad de la sesión (no subidas).
- **Leves de A9 (2026-11-02):** si la punta de la rama protegida trae un `schemaVersion` más nuevo, el `pre-push` avisa con el texto genérico «… is invalid; this push can fix it» (la política sigue fallando cerrada); el mensaje de `schemaVersion` no entero sugiere `config.py validate` sin `--root`.
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
