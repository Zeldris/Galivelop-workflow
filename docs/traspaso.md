# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | Correcciones `0.4.x`: `ccr-6dfbc880-ddr41g`. **Evolutivos y novedades: `version/1.0.0`** (usuario, 2026-10-26; creada desde `ccr-6dfbc880-ddr41g`; los parches `0.4.x` se fusionan también en ella; sus evolutivos, en `docs/registros/pendiente-1.0.0.md` de esa rama). `main` = `56212e8` = **`0.4.1`** (2026-10-26); la `0.4.0` tiene etiqueta y release `v0.4.0` sobre `d7dd18f` (a mano por el usuario). `claude/galivelop-workflow-inicio` está **obsoleta** (se quedó en `0f36412`): no se trabaja en ella |
| Check | `bash tests/comprobar.sh` en verde (**comprobado solo en local**: sin cuota de Actions el CI no arranca, confirmado por el usuario); `main` (`56212e8`) comprobado en local el 2026-10-26 |
| Fase en curso | **6 cerrada**; `0.4.1` en `main` (2026-10-26). La `0.4` es la última menor `0.x` (usuario, 2026-10-25, plan §7): solo parches `0.4.x`, y lo nuevo de una recogida va a la `1.0.0`. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | `0.4.1` en `main` (`56212e8`, 2026-10-26), con confirmación del usuario: fases 1-3 hechas, marca de revisión `a3cc2dc`. **Comprobado solo en local** (confirmado por el usuario): el CI de Actions no arranca (sin cuota); el check completo del `pre-push` pasó en verde sobre `56212e8` para la rama y para `main` (con `version.py --release`). Textos de la release en `docs/registros/release-v0.4.1.md` |
| Siguiente paso | Propuestas de la segunda recogida decididas (2026-10-27, «tu recomendación»): parche `0.4.2` con INS P8, VeriNews P3, P4 y P11 (Java en `mapa-agente.py`), en curso con subagentes en worktrees; los evolutivos, a `pendiente-1.0.0.md` en `version/1.0.0` tras fusionar el parche; WMF P5 y el resto de P11, descartados. Luego: versión `0.4.2`, CHANGELOG, check y, con confirmación del usuario, las tres fases hacia `main`. Pendiente aparte: la etiqueta `v0.4.1` sobre `56212e8` y su release, a mano por el usuario |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [x] 6. Piloto: Tarkor e instalador (2026-10-23; VeriNews, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

**Política de versiones** (usuario, 2026-10-25, plan §7): la `0.4` es la última menor `0.x`, la estable antes de la `1.0`.
Cada recogida reparte lo que trae: las correcciones van a un parche `0.4.x` (que se fusiona también en la rama de la
`1.0.0`, `version/1.0.0`) y los evolutivos se apuntan para la `1.0.0`, nunca una `0.5`. La `1.0.0`+ es la línea que crece. Por
decidir: si la `1.0.0` llega a `main` antes de cumplir la §10.

La release `v0.4.0` la creó el usuario a mano (2026-10-25), con los textos de `docs/registros/release-v0.4.0.md`. La
sesión en la nube no puede subir etiquetas (403 del proxy) y sin cuota de Actions `release.yml` no corre. Para la siguiente: `release.yml` con
lanzamiento manual desde Actions que cree la etiqueta.

## Hecho (5 últimas)

1. 2026-10-26 — Segunda recogida (`gw-harvest`) sobre los cinco proyectos: propuestas en `docs/propuestas/2026-10-26-{instalador-wmf-tarkor-2,world-maker-fantasy-2,portal-galivelop-2,verinews_ai,sin-novedades-2}.md` y `estado.json` al día; labs sin novedades. Por decidir con el usuario.
2. 2026-10-26 — Fase 2 del parche `0.4.1`: `/opt-tokens` (P1-P4: `gw-harvest` clona sin registrar y verifica en paralelo; encargo a ~25 llamadas) y `/retro` aprobada entera: P1 y P2 en `orchestrate-dealer`, P4 en `CLAUDE.md`, P5 en `AGENTS.md`; P3 (caché del check en el `pre-push`) a la `1.0.0`. Regla nueva: commits y PR a nombre de `Zeldris`, sin firmas de Claude.
3. 2026-10-26 — Rama `version/1.0.0` creada desde `ccr-6dfbc880-ddr41g` para ir llevando lo de la `1.0.0` (plan §7 ES/EN); el parche `0.4.1`, aplazado.
4. 2026-10-25 — Entrada `0.4.0` del CHANGELOG con fecha (llegó a `main` como «Unreleased» y `release.yml` la habría rechazado); `version.py --release` exige ya fecha y relleno (`changelog_check`, test primero: sin el arreglo falla); política de versiones (la `0.4` solo parches, lo nuevo a la `1.0.0`) en el plan §7 ES/EN, `AGENTS.md` y `contribuir`/`contributing`; textos de la release en `docs/registros/release-v0.4.0.md`; el usuario publicó la release `v0.4.0` sobre `d7dd18f`.
5. 2026-10-25 — Fase 3 antes de la `0.4.0`: revisión de los commits de la fase 2 (un medio y cinco menores). Arreglados `bitacora.py done`, que ya conserva un párrafo libre al final de «Hecho», y `es-codigo.sh`, que con `| head -1` y una salida mayor que el búfer de la tubería fallaba con 141 (intermitente en el `pre-push`); los menores, en «Pendiente».

## Pendiente

- **P3 de la retro del parche `0.4.1`, para la `1.0.0`** (evolutivo, aprobado 2026-10-26): el `pre-push` no repite
  un check ya en verde sobre el mismo árbol. Guarda en el directorio común de git un hash del árbol del commit y de las
  órdenes de `check` solo si sale en verde, y `tests/comprobar.sh` también apunta su verde; tests: árbol distinto,
  órdenes distintas y check en rojo (no se guarda). Ahorra 12-15 min por subida tras un check en verde.
- **Sin firmas de Claude** (usuario, 2026-10-26): commits y PR a nombre de `Zeldris`, sin trailers ni pies de Claude
  (`AGENTS.md`, «Mensajes de commit»). Desde `f2da5d5` (excluido) ya va así; el historial anterior de la rama y de `main`
  lleva autor Claude y trailers: reescribirlo exige force-push, solo si el usuario lo pide. Para la `1.0.0`
  (evolutivo): opción del flujo para los proyectos (`gw.json`) con comprobación en `commit-msg`/`pre-push` que
  rechace autor o trailers del agente, y quitar la mención a «líneas de atribución» de plantillas y `aplicar`/`apply`.
- Menores de la revisión de la `0.4.1` (2026-10-26): `rojo-sin-arreglo` (`test_re`) da falsos positivos («it (»,
  «test(», `def testable`, comentarios que se describen a sí mismos, como los del propio script); `NOT_STARTED` del
  gancho de fusión solo reconoce dos frases exactas de GitHub (falta «billing», «account is locked»); `cloud_start`
  silencia también la pista «pass it explicitly» (decisión aprobada, Portal P1) y conviene centralizarlo en `find()`
  y `opened_outside()`.
- Menores de la retro antes de la `0.4.0` (2026-10-25): `bitacora.py` no entiende bloques de código dentro de
  «Hecho», iguala los huecos en blanco entre entradas y mide cada celda por separado (dos de 790 en una fila pasan);
  `doctor.py` (`ci access`) da por bueno un token sin comprobarlo y no reconoce `ssh.github.com:443` ni GHE; el
  marcador de `pre-push` no cubre un pid reutilizado tras `kill -9`, ni las ventanas antes y después del gancho, ni
  `git push origin HEAD:otra` (mismo sha, otra rama).
- Menores de la revisión de la fase 3 antes de la `0.4.0`: `bitacora.py done` con viñetas (`- `) añade la entrada
  debajo y no recorta; el aviso «glued» propone `check` sobre el temporal de los ganchos (`gw-commit-msg.*`,
  `gw-log.*`), ya borrado; `prepush-ramas.sh` repite los avisos de `check` en cada commit de la subida; `antes-de-parar.py`
  lee solo 4096 bytes de la marca (`git push --all` de unas 55 ramas); la marca es una por directorio común de git (dos
  worktrees que suben a la vez se pisan).
- `recuperar.py` (`fit_log`): recorta por el principio del conjunto de secciones, así que una primera sección larga se come antes la «Pendiente»; si la cabecera y la cola ya pasan del tope, la nota de recorte se emite igual y `capped()` corta el puntero a `--buscar`.
- `recoger.py`: un `\r` suelto desalinea los números de línea con los del diff; un archivo renombrado desde la última recogida vuelve a dar todas sus ideas; una línea borrada de una propuesta no la marca como cambiada (no dicho en la docstring).
- `--name-only` sin `core.quotepath=false` en `prepush-ramas.sh`, `es-codigo.sh`, `revisado.sh`, `version.py` y `recoger.py`: una ruta de `log` con acentos no coincide.
- `tope-subagentes.py` cuenta doble (y `guardia-config.py` y `antes-de-parar.py` preguntan dos veces) si el gancho está a la vez en el plugin (`hooks/hooks.json`) y en el `.claude/settings.json` del proyecto.
- `doctor.py` (~línea 512): la orden que arregla los caracteres invisibles convierte CRLF en LF y no entrecomilla la ruta.
- `guardia-config.py`: `git -C <dir> checkout .` resuelve `.` contra la raíz del proyecto (falso positivo) y volcar un árbol sobre la raíz (`cp -r x/. .`, `rsync -a x/ ./`) no se ve.
- `read_event()`/`ask()` están copiados en los tres ganchos nuevos (`guardia-config.py`, `antes-de-parar.py`, `tope-subagentes.py`): llevarlos a un módulo junto a `config.py`.
- `aplicar.py` notas personales (revisión de 2522f37): una nota que cada proyecto adapta imprime su línea `diff` en cada ejecución; un fork renombrado o un clon sin `.claude-plugin/plugin.json` recibiría notas.
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
  propuestas en `docs/propuestas/2026-10-25-codegraph.md`: P2 (comprobador genérico del mapa, `scripts/mapa-agente.py`)
  y P3 (anti-patrones en `writing-for-agents`)
  aplicadas; P1 (gancho que inyecta la fila del mapa) y P4 (probar
  la herramienta en WMF) sin decidir, se recomienda aplazar. Al aplicar en WMF: declarar
  `agentMap.prefixes` `{"b/": "backend/src/", "f/": "frontend/src/"}` antes de cambiar su comprobador por este.
- Diez repos de una lista de X revisados (2026-10-25): 10 propuestas en `docs/propuestas/2026-10-25-repos-x.md`. P4
  (regex), P5 (`recuperar.py`: tope de 9.500 caracteres y fragmentos como datos) y P7 (skills e instrucciones)
  aplicadas (P4 y P7 en eea8892) y el arreglo posterior (gancho de `main` con tabuladores y saltos escapados; ZWJ en
  emojis; gancho de PR en 8f4150b, 16f6cbd y efc72c9); P1 gancho `Stop`, P2 guarda de config, P3 tope de subagentes, P6 dealer, P8 disparo de skills
  y P9 `REVIEW.md` aplicadas (2026-10-25); P10 apuntada en el plan. Todas hechas.

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Menores de la revisión de la tanda A (no se revisan otra vez en este PR): `non_capturing` toca paréntesis en
  comentarios `(?x)`/`(?#…)`; `--ran-one` cuenta dos veces si el ejecutor repite el nombre del test en el resumen;
  `header_version` solo mira las 5 primeras líneas.
- Menores de la revisión de la tanda B: sin python3, `revision-antes-de-main.sh` deja pasar
  `gh api …/pulls -f title=` (crear el PR por la API; el hueco ya existía) y bloquea `gh pr view 3 && echo create`
  (exceso de celo).
- Menores de la revisión del vigilante (89fdf09): el KILL de los 5 s podría dar con un pgid reutilizado (se acepta:
  el vigilante se detiene si la orden acaba antes).
- Menores de la revisión de la tanda E: el aviso de ventanas mezcladas de `opt-tokens/medir.py` salta con un
  `/compact` manual o una etapa muy corta; `opt-ai/medir.py` ignora un `app.turn` 0 o vacío y su clave sintética
  choca con una tarea llamada «turn»; `instant` descarta sin avisar un `ts` que `fromisoformat` no lee (Python <3.11);
  `quality_bench.py` envía un `format` de texto como `json_schema` con la API openai y `pairs` pisa en silencio un
  modelo repetido en dos `outputs.jsonl`.
- Menor de la revisión antes de `main`: `checkWrapper` se aplica en tres sitios (`pre-push` y `fusionar.sh` con
  `sed`, `config.py` con `shlex`) y la plantilla de CI no lo aplica: que lo construya solo `config.py`.
- Menores de la revisión de los arreglos antes de `main` (3b47af1): un push muerto en el mismo namespace deja su
  worktree 24 h (guardar `hostname:pid` en el marcador); `worktreeDir` con `~` o `..` no se valida en `config.py`;
  `cksum` de 32 bits puede juntar dos repos en una carpeta (el borrado sigue exigiendo 24 h y proceso muerto);
  `update_pull_request` con `state:open` y sin `base` no se juzga como reapertura; `compare.py default_root` da
  traceback sin git y, desde la caché del plugin, cae al cwd (exigir `--root`).
- Menores de la revisión del flujo 0.3.0 que hizo el portal (P5 de `docs/propuestas/2026-10-23-portal-galivelop.md`):
  `config.py related` acepta un `cwd` con `..` o absoluto en `relatedTests` (que `validate` lo rechace);
  `session-start.sh`: `kill -- -$wd` no es un grupo y el `sleep` del vigilante queda vivo hasta el tope;
  `revision-antes-de-main.sh` sondea `gh api repos/<o>/<r>` en cada llamada y juzga cambios de título o base de un PR
  cerrado; `doctor.py` da por bueno un `npm run check` citado en un comentario (y avisos del glosario repetidos por
  mayúsculas, por comprobar); `validate` no avisa de un `worktreeDir` dentro del repo ni de un `checkWrapper` que
  limpia el entorno. Con la config de la punta de `main` rota, `pre-push` y el gancho fallan cerrados a propósito: se
  sale con un PR revisado que la arregle, o la persona sube a mano.
- P2 de `docs/propuestas/2026-10-23-portal-galivelop.md` (`ci.setup`/`ci.after` y `aplicar.py --update` sin pisar un
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
