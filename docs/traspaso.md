# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-6dfbc880-ddr41g`; `main` = `ea81c9f` = **release `v0.3.0`** (2026-10-23). `claude/galivelop-workflow-inicio` está **obsoleta** (se quedó en `0f36412`): no se trabaja en ella |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **6 cerrada** y `0.3.0` publicada en `main` (2026-10-23); P7 del instalador aplicada en la rama (`0.4.0`, sin publicar); recogida de la `0.4.0` hecha y decidida (P1, P3, P4, P5 aplicadas; P2 aplazada). Próxima: **7. Rodaje etapa 1** |
| Último punto estable | `4e49033` (2026-10-25): fase 1 antes de `main` cerrada (arreglos de la revisión en `5b1676f`, `c80b184`, `cb748bc`, `4b39f0a`) y retro de la fase 2 escrita; el detalle de la `0.4.0`, en el CHANGELOG, «Hecho» y `git log` |
| Siguiente paso | **Publicar la `0.4.0` en `main` (el usuario lo pidió el 2026-10-25; la recogida desde `v0.3.0` ya está: `docs/propuestas/2026-10-25-*.md`).** Fase 1 (código) hecha: `/code-review` del diff contra `origin/main` y arreglos de lo serio y medio, con la revisión de esos arreglos y los suyos (guardia-config, antes-de-parar, commit-msg, recuperar, recoger); los menores, en «Pendiente». Fase 2 en curso: retro `docs/registros/retro-2026-10-25-antes-de-main-0-4-0.md` con P1-P7, **aprobadas todas** por el usuario (2026-10-25); P3, P4 y P6 aplicadas; P1+P2 (`bitacora.py`), P5 (`doctor.py`) y P7 (`pre-push` + `antes-de-parar.py`) repartidas a subagentes. Luego la fase 3 (`/code-review` de lo que traiga, `bash scripts/revisado.sh` y la subida a `main`). Después, la release de GitHub. Aplazada a la Fase 7: P3 de Labs (`to-spec`, `wayfinder`) |

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

`0.4.0`: abierta hasta el 2026-10-30 (usuario, 2026-10-23); antes de publicarla, otra pasada de `gw-harvest` sobre lo de
esa semana.

Subida a `main` en espera (usuario, 2026-10-25): las tres fases y la publicación se deciden cuando esté subido lo de
la sesión local y cerrada la parte 2b de `gw-media-content`. Mientras el CI no arranque (sin cuota de Actions), vale el
check en local sobre el mismo commit (`bash tests/comprobar.sh`), y se apunta como «comprobado solo en local».
Parte 2b cerrada (b5c1e31). La sesión local está acabando sus ajustes y subirá la `0.4.0` a `main`; cuando llegue,
se preparan los textos de la release de GitHub (el usuario avisa).

`0.2.0` publicada (etiqueta y release a mano en GitHub, título `Galivelop-workflow vX.Y.Z`, notas de la entrada del CHANGELOG). Para la siguiente: `release.yml` con lanzamiento manual desde Actions que cree la etiqueta (la
sesión en la nube no puede subir etiquetas: 403 del proxy).

## Hecho (5 últimas)

1. 2026-10-25 — Arreglos de la revisión de `recoger.py` (`c80b184`): `git()` decodifica con `errors="replace"` (un `.md` del proyecto que no es UTF-8 tumbaba la recogida entera); `git diff` con `--no-color --no-ext-diff --no-textconv` (con `color.diff=always` las ideas nuevas se perdían sin avisar) y un diff sin `@@` (binario) cuenta el archivo entero; `--update-state` sin `Path.is_relative_to` (Python 3.9+). Tests primero (3 casos).
2. 2026-10-25 — Arreglos de la revisión de `guardia-config.py` y `commit-msg`: `sudo -uroot` (valor pegado) ya no se come la orden y solo la última letra de un grupo consume la palabra siguiente; el valor de una opción de `rsync`/`cp`/`install` (`--exclude .claude`, `-m`, `-o`, `-S`…) no cuenta como destino; `dd of=` se clasifica; `git restore --staged` (sin `--worktree`), `git rm --cached` y `git clean -n` no son escritura; en `cp`/`install`/`ln`/`rsync` solo el destino se escribe (leer o copiar desde `.claude`/`.githooks` se permite; `mv` y `rsync --remove-source-files` sí escriben el origen); `commit-msg` nombra la ruta original en su error de normalización y usa `core.quotepath=false` (un `log` con acentos se saltaba en silencio). Tests primero, un caso por borde.
3. 2026-10-25 — Arreglos de la revisión antes de `main` (recuperar, recoger): `recuperar.py --estado` ya no pierde lo de después de la bitácora (recuento de archivos sin subir, últimos commits, avisos como «sesión abierta fuera del repo» y el puntero a `--buscar`): lo que se recorta es la sección de la bitácora (se conserva su principio, con una línea que dice que se cortó y qué archivo leer entero) y el tope de 9.500 caracteres queda como último recurso; `recoger.py` con una recogida anterior solo da las ideas cuyas líneas se añadieron o cambiaron desde ella (`git diff -U0`), no repite una línea «Propuesta para el flujo» dentro de una sección «Para Galivelop-workflow» y mide con `expandtabs()` también las líneas de continuación. Tests primero, un caso por borde (3 en `test_sesion.py`, 6 en `test_recoger.py`).
4. 2026-10-25 — Arreglos de la revisión antes de `main` (guardia, parar, commit-msg): `guardia-config.py` pregunta si el destino de `cp`/`install`/`rsync`/`ln`/`mv` (último argumento o `-t`) es `.claude` o `.claude/gw`, y por `git checkout|restore` con `.` o con esas carpetas (el doc de cabecera no decía nada: queda dicho); mira dentro de `sudo -u X`, `env -u X`, `nice -n N`, `timeout`, `xargs -I{}`… con la lista de `revision-antes-de-main.sh`, y de `> f cmd`; `antes-de-parar.py` en la rama protegida no manda `git push` y avisa (`systemMessage`, no bloquea: Claude no puede arreglarlo sin la confirmación de la persona, y el gancho es un recordatorio); `commit-msg` normaliza `log` (`./docs/x.md`, `a//b`) antes de comparar. Tests primero, un caso por borde.
5. 2026-10-25 — Arreglos de la revisión de las notas personales: `--check` no falla por una nota que falta (la informa fuera de la deriva); se rechazan con aviso los nombres `*.gw-nuevo` y los de archivos del flujo (sin mirar mayúsculas, también opcionales y de configuración); `OSError` al leer origen o destino, carpeta ilegible o que es un archivo y `GW_NOTAS_PERSONALES` relativa dan línea limpia o ruta absoluta; `is_workflow_repo` falla cerrado; `test_plantillas.py` fija `GW_NOTAS_PERSONALES`; docs de `config.md`, `aplicar.md` ↔ `apply.md`.

## Pendiente

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
