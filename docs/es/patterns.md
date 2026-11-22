# Patrones opcionales

> [English](../en/patterns.md)

Formas de trabajar que el flujo permite pero no impone. Ninguna es necesaria para aplicarlo ([aplicar](apply.md)); se
adoptan cuando el proyecto las pide. Todas se apoyan en lo mismo: lo que no está subido no existe, la bitácora dice por
dónde se iba y un script, no una opinión, decide si algo puede subir.

## Tarea semanal programada

Una sesión que arranca sola cada semana (una «tarea programada» de Claude Code) para un trabajo repetible: poner al
día dependencias, revisar enlaces rotos, pasar `gw-scout-updates`, limpiar la bitácora. El flujo **no incluye** el
encargo concreto: cada proyecto escribe el suyo.

Cómo se plantea, en genérico:

1. **Cada disparo, una sesión nueva** con el encargo completo (no puede suponer una conversación anterior): qué
   hacer, en qué rama, qué comprobar y cuándo parar.
2. **Empieza como cualquier sesión**: lee la bitácora, `git fetch`, trae la rama protegida y corre
   `python3 .claude/gw/scripts/doctor.py` y el `check`. Si algo está en rojo antes de tocar nada, lo apunta en la
   bitácora y para.
3. **Trabaja en su rama** (`claude/semanal-<fecha>`), con commits y push como siempre, y la bitácora al día.
4. **A la rama protegida, según la configuración** ([config](config.md)):
   - `pushToProtected: pr`: abre un pull request; el gancho de PR y el CI hacen de guardia y la persona decide.
   - `direct`: puede subir a la rama protegida **solo si la marca de revisión cubre el código** (el `pre-push` lo exige
     y falla cerrado). Si la tarea cambia código sin revisión, no sube: deja la rama con su bitácora para que una
     persona la revise. Un cambio solo de `content` no necesita marca (por eso en `content` no van scripts ni
     instrucciones para agentes).
5. **Termina con un informe corto** en la bitácora: qué hizo, qué dejó pendiente y el siguiente paso.

El encargo de la tarea (su runbook en `docs/`, o el prompt guardado) se ejecuta sin nadie delante: queda fuera de
`content` o se revisa como código, y cada cambio pasa por la revisión antes de que la tarea lo siga
([`REVIEW.md`](../../templates/es/REVIEW.md)).

Autorización: una tarea que sube a la rama protegida sin nadie delante merece escribirse como regla en `AGENTS.md`,
para que quede dicho quién lo permitió.

## Dos cuentas que se relevan

Dos cuentas (o dos personas, o una sesión local y otra en la nube) trabajan el mismo proyecto por turnos y a veces a
la vez.

- **Cada sesión, su propia rama.** Dos sesiones a la vez nunca suben a la misma. Si la rama de la bitácora ya la usa
  otra, crea `claude/<tema>` desde ella y apunta su fila en la bitácora.
- **Bitácora de filas** (`"logRows": true`): cada rama escribe solo en su fila «Tarea en curso · `<rama>`», de como
  mucho 600 caracteres. El `pre-push` rechaza tocar la fila de otra rama o una compartida; para una compartida
  (p. ej. añadir tu rama a «Ramas de trabajo»), `BITACORA_COMPARTIDA=1 git push`.
- **Merge, nunca rebase**, al empezar cada tarea (`git fetch origin <protegida>` y `git merge origin/<protegida>`):
  las ramas están subidas. Lo suyo vuelve a la rama principal por `git merge` antes del PR.
- **Al parar**, el gancho `Stop` (`before-stop.py`) no deja acabar con commits sin subir ni con cambios sin la
  bitácora; si no puede comprobarlo (sin git, sin config), avisa en vez de bloquear. Mientras un `pre-push` corre
  (su marca `gw-push-in-progress.<pid>`, en el directorio git de ese worktree, con su pid vivo, de menos de una hora y el sha del
  `HEAD` actual entre los shas locales que lista) tampoco bloquea: avisa de que se está subiendo este commit y de que
  no se suba otra vez (dos pushes a la vez se pisan); espera y mira `git status -sb`. Una marca de otra rama o de un
  `HEAD` anterior (commits hechos después de empezar el push), con pid muerto, vieja o ilegible bloquea como siempre.
  No cuenta como cambio sin commitear lo no versionado bajo `.claude/worktrees/` (los worktrees aislados de Claude Code).
- **Al tocar la configuración del flujo**, el gancho `PreToolUse` `config-guard.py` pide permiso a la persona antes de
  editar `.claude/settings.json`, `.claude/gw.json`, `.githooks/`, `.claude/gw/scripts/` o la carpeta de perfiles
  (`profiles.dir`, por defecto `.claude/gw/profiles/`) (con `Edit`, `Write` o una
  orden de `Bash` que escriba ahí, también `.claude/settings.local.json` y las mismas rutas en `.claude/worktrees/`;
  las órdenes de git que reescriben el árbol —`merge`, `checkout`, `switch`, `reset --hard`, `stash pop`,
  `rebase`, `cherry-pick`, `revert`, `apply`— preguntan solo si cambiarían una de esas rutas, o si no puede calcularlo; también `stash` y `clean -f` si hay algo protegido que tocarían, y los alias de git se siguen un nivel, con `!` o cadenas preguntando). `pull` pregunta siempre (lo que fusiona no se sabe hasta su `fetch`: mejor `git fetch` y luego `git merge`), y también `am`, `bisect`, `checkout-index`, `read-tree -u` y `stash branch`. Un `find` que borra o escribe desde la carpeta del proyecto pregunta salvo que solo filtre con `-name`/`-iname` y ningún nombre protegido encaje. Límites: `fetch && merge` en una sola orden se evalúa antes del `fetch`; con cambios sin commitear en una ruta protegida puede preguntar de más; y una sesión abierta dentro de un worktree no protege el `.claude` del repo principal. Un `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_CONFIG*` o `GIT_COMMON_DIR` asignado o exportado en cualquier parte de la orden (también dentro de `sh -c`) hace preguntar a todo git que reescriba el árbol. Sin vigilar: `clean -i`, `worktree add`, `find -exec sh -c`, `xargs rm` y los alias de más de un nivel. Si no entiende la entrada, también pregunta. Para regenerar la copia aplicada:
  `python3 scripts/apply.py .`.
  También pregunta antes de ejecutar `profile.py new|assign|role`, que escriben `.claude/gw.json` o un perfil.
- **Al repartir a subagentes**, el gancho `PreToolUse` `subagent-cap.py` cuenta los `Agent`/`Task` de la sesión y,
  al llegar a `subagentCap` (30 por defecto) y cada 10 después, pide a la persona que compruebe que no están en bucle
  (`gw-opt-tokens`); nunca bloquea. Si la llamada no lleva `model` (`inherit` no cuenta) y el `subagent_type` no fija el suyo en
  `.claude/agents/`, el mismo gancho avisa de que el subagente puede correr en el modelo de la sesión y de que lo
  elija con `gw-selector`; el aviso llega con el resultado, así que vale para las próximas llamadas (aviso, no bloqueo).
- **Al leer**, el gancho `PreToolUse` `whole-read.py` avisa (sin bloquear) de que un `Read` sin `offset`, `limit` ni
  `pages` toma entera la bitácora, su archivo o un archivo de `recordsDir` de más de `wholeReadWarnBytes` (20000 por
  defecto, `0` = no avisar), y apunta a `recover.py --state` o a `grep -n` y `Read` con `offset`/`limit`.
- **Al empezar**, la sesión nueva lee la bitácora y comprueba que el último commit coincide con lo que dice; no
  pregunta por dónde iba. Tras un `/clear` o una compactación, `recover.py --state` se lo recuerda.
- Al cerrar la rama, `handoff.py close-row <rama>` deja su fila como «fusionada, rama terminada» para que la rama
  protegida no herede un «Siguiente» viejo. Con un id de tarea que tiene ficha (`docs/tasks/<id>.md`), `close-row <id>`
  cierra la **tarea**: se niega, listando cada motivo, si falta alguna casilla de `Acceptance` sin marcar o sin test
  (`tests/test_X.py::Clase` o `== sección` del `check`, entre comillas invertidas) o si `Verification` no trae un
  commit existente y una orden; si todo está, marca `hecho` su fila en `roadmapFiles`. Si el nombre es a la vez rama e
  id, decide que exista la ficha (`--branch <rama>` fuerza la rama).
- **Con `logRows`, la fila propia a mitad de tarea:** `handoff.py set-row "texto"` reescribe la fila de la rama actual
  (`--branch <rama>` para otra) sin cerrarla, con el límite de 600 caracteres comprobado y sin escribir nada si la fila
  falta, el texto está vacío o ocupa más de una línea. Y el `pre-commit` corre `handoff.py own-row --staged`: si la
  bitácora preparada cambia la fila de otra rama o una fila compartida, el commit se para (antes solo lo veía el
  `pre-push`, con el commit ya hecho); en HEAD desacoplado avisa y pasa, y para una fila compartida a propósito,
  `GW_SHARED_LOG=1 git commit` y, al subir, `GW_SHARED_LOG=1 git push` (el `pre-push` vuelve a comprobar el commit).
- **Bitácora corta, con o sin `logRows`:** `handoff.py check --strict` falla si una celda de la tabla de estado pasa de
  800 caracteres o si «Hecho (5 últimas)» tiene más de 5 elementos, mal numerados o pegados en una línea (sin
  `--strict` solo avisa con `WARNING:`). `handoff.py done "texto"` añade el elemento `1.` con la fecha, renumera y
  quita los que sobran, sin tocar el resto del archivo. Si la bitácora pasa de `logSize` caracteres, `check` avisa y
  `handoff.py archive` mueve a `logArchive` los elementos de «Pendiente» de versiones ya publicadas (`--dry-run` solo
  muestra qué movería); tras compactar, `recover.py` solo devuelve la primera sección.

## Sesión local que no puede crear PRs

Hay entornos (un portátil sin `gh`, una consola) donde la sesión puede trabajar y subir ramas, pero no crear el PR. Se
reparte así:

1. La sesión local termina el trabajo y pasa la revisión (`/code-review`, y si hay `retro`, también). Después escribe
   la descripción del PR con la skill `pr` en `docs/records/pr/<rama>.md`.
2. En su fila de la bitácora deja **«PR listo»** con el título, y lo sube **todo en el último commit** de la rama.
3. Una **sesión en la nube** (con herramienta de GitHub) comprueba que nada va detrás de ese commit (`git log
   <commit>..origin/<rama>` vacío), corre `bash .claude/gw/scripts/reviewed.sh` para dejar la marca del mismo commit,
   crea el PR con esa descripción y sigue con el CI y, cuando la persona lo confirme, la fusión.

El gancho de PR bloquea crear o fusionar sin la marca del mismo commit, de modo que un descuido (algo subido después
de «PR listo») sale como bloqueo y no como código sin revisar.

## Contenido para redes

Dos skills preparan, **sin publicar**, publicaciones sobre el proyecto: `gw-media-content` propone hasta 10 (tipo de post,
gancho, redes, hechos con su fuente) y `gw-media-content-now` produce una pieza en una carpeta con fecha: un archivo por
canal y por idioma, más las imágenes. Redes de partida: X, Reddit, LinkedIn y Discord; el proyecto puede declarar otras
(*canales extra*). Los límites por red están en `rules.json`, marcados `P` (verificado), `S` (según la fuente) o `NV` (sin
verificar: se avisa al apoyarse en uno). La persona publica; ninguna skill lo hace.

Necesitan Python 3 y git para las cifras (`figures.py`). El render de imágenes (`render.mjs`) necesita además Node con
Playwright e ImageMagick con WebP; `check.py` se puede correr sin ellos, y **el render real no lo cubre el CI**
(sus tests usan un doble salvo donde haya Chromium). Si el proyecto tiene la nota o la carpeta de la skill, `doctor.py`
avisa de lo que falte (`media tools`).

Sin nota del proyecto rigen los valores por defecto (y se dice una vez). Para cambiarlos, `.claude/gw/gw-media-content.md`,
una línea `clave: valor` por dato (las claves, las de la tabla de `skills/gw-media-content/note.md`, en inglés); el flujo no
la crea ni la pisa. Un *canal extra* se declara con `limit: N` (comprobado con `--limit <canal>=N`) o con
`format: own` y `template: <ruta>` (su archivo lo consume otro sistema; comprobado con `--own-format <canal>`).
El canal `web` es la web del propio proyecto: `web.md` lleva un bloque JSON con `status` (`draft` hasta que la
persona escribe `ready`), `date`, el texto por idioma (`text`) y una entrada de muro opcional (`wall`) con sus imágenes; los idiomas
de la web pueden ser más que los de la pieza (`Web languages`, que se pasa con `--web-languages`). En la `0.x`, `web.md` lleva cada clave
dos veces, con el mismo valor: la inglesa y la española de antes (`estado`, `fecha`, `texto`, `muro`...), para no romper la web que lea las
viejas; `check.py` falla si no coinciden y las españolas se quitan en la `1.0`. Ejemplo genérico:

```
Folder: docs/media
Languages: es, en
Channels: x, reddit, linkedin, discord, web
Web languages: es, gl, en
Extra channels:
- mastodon: limit: 500; tone: cercano
- portal: format: own; template: docs/media/portal.json
Palette: --background #101418; --accent #4cc38a
Screenshots: arrancar la app (npm run dev), abrir /panel, captura de la ventana a 1280x720
Task prefixes: INS,FLU   (se pasa a check.py --task-prefixes)
Reddit: r/ejemplo, reglas pegadas por la persona el 2026-10-25: «sin autopromoción más de una vez al mes; etiqueta [Proyecto]»
```

## Lo probado con un doble, también con lo real

Un componente que los tests sustituyen por un doble (fake, mock, stub) tiene además una **prueba de humo contra el
real**: el doble solo repite lo que su autor creía del real, así que no ve el contrato que cambia, el argumento que el
real rechaza ni el formato que devuelve distinto. La prueba de humo arranca el componente real y hace una llamada de
punta a punta. Si falta el real (herramienta, servicio, credencial), se omite en local con el motivo; en el CI, falla.

## En el CI, la instalación falla en su propio paso

El script que instala o prepara el entorno (dependencias, herramientas, base de datos de pruebas) va en un paso del CI
propio, anterior al de los tests, no escondido dentro de ellos. Así un fallo de instalación se ve como lo que es, con su
salida, y no como un test en rojo que manda a buscar el fallo donde no está. La plantilla `templates/github/check.yml` ya
lo hace: el paso `Install` (`ciInstall`, o `install`) va antes del paso `Check`.

## Pruebas de front

Para un proyecto con interfaz web: Stylelint, layout, accesibilidad y capturas con Playwright, deterministas y sin
servicios de pago (E5, E7). Las normas de diseño se escriben como dato y el flujo genera de ahí las reglas y la matriz.

1. **Tokens:** un JSON en el formato W3C Design Tokens (grupos, hojas con `$value` y `$type`, alias `{grupo.token}`),
   con un grupo de breakpoints en `px`. `front.tokens` de `.claude/gw.json` apunta a él; sin él no corre nada
   ([config](config.md)).
2. **Plantilla:** copia `templates/front/` del flujo en la carpeta de `front.dir` y deja **dentro** de ella todo lo que
   importe `@playwright/test`, axe o Stylelint: `node_modules` solo se enlaza ahí (Q-38). Los paquetes se instalan
   fuera del árbol: `python3 .claude/gw/scripts/front.py install --browsers chromium`.
3. **Generar:** `front.py generate` escribe `tokens.css`, `_tokens.scss`, las reglas de Stylelint y los proyectos de
   Playwright; decláralos en `generated` para que el check los compare.
4. **Cuándo corre:** el `pre-push`, `front.py run fast` (sin las capturas, breakpoints principales); el cierre
   (`scripts/check.sh`) y el CI de la plantilla, `front.py run full` (todo, la matriz entera). `run full` solo en
   Linux o con Docker: en macOS sin Docker se niega, nunca da un verde falso.
5. **Capturas de referencia:** las pruebas `@visual` se comparan con capturas tomadas en Linux con la versión de
   Playwright fijada; `doctor.py` avisa de capturas de otra plataforma o versión y de las grandes fuera de Git LFS.

## Recoger mejoras de vuelta

El flujo aprende de los proyectos que lo usan. Hay dos mitades:

- **Empuja el proyecto.** Una `retro` que descubre una mejora **general** (de una skill, un script, una plantilla, una
  regla de `AGENTS.md`) no parchea la copia local, que la próxima actualización pisaría: la propone al flujo, como
  incidencia o PR en este repo, o la deja en el archivo de la retro bajo un encabezado
  `## Para Galivelop-workflow` (o `## For Galivelop-workflow`).
- **Tira el flujo.** Desde este repo, la skill `gw-harvest` recorre los proyectos conectados que tengan
  `.claude/gw.json`. La parte mecánica la hace `python3 scripts/harvest.py <proyecto>...` (copias del flujo editadas,
  skills nuevas, secciones de retros, commits desde la última recogida); el agente solo decide qué es general y escribe
  `docs/proposals/AAAA-MM-DD-<repo>.md`. **Nunca aplica nada sin confirmación**: lo aprobado entra como un cambio
  normal con entrada en el CHANGELOG y nueva versión ([contribuir](contributing.md)).

Los proyectos se leen, no se modifican, desde la sesión que recoge.
