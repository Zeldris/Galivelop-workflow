# Patrones opcionales

> [English](../en/patterns.md)

Formas de trabajar que el flujo permite pero no impone. Ninguna es necesaria para aplicarlo ([aplicar](aplicar.md)); se
adoptan cuando el proyecto las pide. Todas se apoyan en lo mismo: lo que no está subido no existe, la bitácora dice por
dónde se iba y un script, no una opinión, decide si algo puede subir.

## Tarea semanal programada

Una sesión que arranca sola cada semana (una «tarea programada» de Claude Code) para un trabajo repetible: poner al
día dependencias, revisar enlaces rotos, pasar `scout-updates`, limpiar la bitácora. El flujo **no incluye** el
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
- **Al parar**, el gancho `Stop` (`antes-de-parar.py`) no deja acabar con commits sin subir ni con cambios sin la
  bitácora; si no puede comprobarlo (sin git, sin config), avisa en vez de bloquear. Mientras un `pre-push` corre
  (su marca `gw-push-en-curso`, en el directorio común de git, con su pid vivo, de menos de una hora y el sha del
  `HEAD` actual entre los shas locales que lista) tampoco bloquea: avisa de que se está subiendo este commit y de que
  no se suba otra vez (dos pushes a la vez se pisan); espera y mira `git status -sb`. Una marca de otra rama o de un
  `HEAD` anterior (commits hechos después de empezar el push), con pid muerto, vieja o ilegible bloquea como siempre.
  No cuenta como cambio sin commitear lo no versionado bajo `.claude/worktrees/` (los worktrees aislados de Claude Code).
- **Al tocar la configuración del flujo**, el gancho `PreToolUse` `guardia-config.py` pide permiso a la persona antes de
  editar `.claude/settings.json`, `.claude/gw.json`, `.githooks/` o `.claude/gw/scripts/` (con `Edit`, `Write` o una
  orden de `Bash` que escriba ahí); si no entiende la entrada, también pregunta. Para regenerar la copia aplicada:
  `python3 scripts/aplicar.py .`.
- **Al repartir a subagentes**, el gancho `PreToolUse` `tope-subagentes.py` cuenta los `Agent`/`Task` de la sesión y,
  al llegar a `subagentCap` (30 por defecto) y cada 10 después, pide a la persona que compruebe que no están en bucle
  (`opt-tokens`); nunca bloquea.
- **Al empezar**, la sesión nueva lee la bitácora y comprueba que el último commit coincide con lo que dice; no
  pregunta por dónde iba. Tras un `/clear` o una compactación, `recuperar.py --estado` se lo recuerda.
- Al cerrar la rama, `bitacora.py close-row <rama>` deja su fila como «fusionada, rama terminada» para que la rama
  protegida no herede un «Siguiente» viejo.
- **Bitácora corta, con o sin `logRows`:** `bitacora.py check --strict` falla si una celda de la tabla de estado pasa de
  800 caracteres o si «Hecho (5 últimas)» tiene más de 5 elementos, mal numerados o pegados en una línea (sin
  `--strict` solo avisa con `WARNING:`). `bitacora.py done "texto"` añade el elemento `1.` con la fecha, renumera y
  quita los que sobran, sin tocar el resto del archivo.

## Sesión local que no puede crear PRs

Hay entornos (un portátil sin `gh`, una consola) donde la sesión puede trabajar y subir ramas, pero no crear el PR. Se
reparte así:

1. La sesión local termina el trabajo y pasa la revisión (`/code-review`, y si hay `retro`, también). Después escribe
   la descripción del PR con la skill `pr` en `docs/registros/pr/<rama>.md`.
2. En su fila de la bitácora deja **«PR listo»** con el título, y lo sube **todo en el último commit** de la rama.
3. Una **sesión en la nube** (con herramienta de GitHub) comprueba que nada va detrás de ese commit (`git log
   <commit>..origin/<rama>` vacío), corre `bash .claude/gw/scripts/revisado.sh` para dejar la marca del mismo commit,
   crea el PR con esa descripción y sigue con el CI y, cuando la persona lo confirme, la fusión.

El gancho de PR bloquea crear o fusionar sin la marca del mismo commit, de modo que un descuido (algo subido después
de «PR listo») sale como bloqueo y no como código sin revisar.

## Contenido para redes

Dos skills preparan, **sin publicar**, publicaciones sobre el proyecto: `gw-media-content` propone hasta 10 (tipo de post,
gancho, redes, hechos con su fuente) y `gw-media-content-now` produce una pieza en una carpeta con fecha: un archivo por
canal y por idioma, más las imágenes. Redes de partida: X, Reddit, LinkedIn y Discord; el proyecto puede declarar otras
(*canales extra*). Los límites por red están en `reglas.json`, marcados `P` (verificado), `S` (según la fuente) o `NV` (sin
verificar: se avisa al apoyarse en uno). La persona publica; ninguna skill lo hace.

Necesitan Python 3 y git para las cifras (`cifras.py`). El render de imágenes (`render.mjs`) necesita además Node con
Playwright e ImageMagick con WebP; `comprobar.py` se puede correr sin ellos, y **el render real no lo cubre el CI**
(sus tests usan un doble salvo donde haya Chromium). Si el proyecto tiene la nota o la carpeta de la skill, `doctor.py`
avisa de lo que falte (`media tools`).

Sin nota del proyecto rigen los valores por defecto (y se dice una vez). Para cambiarlos, `.claude/gw/gw-media-content.md`,
una línea `clave: valor` por dato (las claves, las de la tabla de `skills/gw-media-content/nota.md`, en inglés); el flujo no
la crea ni la pisa. Un *canal extra* se declara con `límite: N` (comprobado con `--limite <canal>=N`) o con
`formato: propio` y `plantilla: <ruta>` (su archivo lo consume otro sistema; comprobado con `--formato-propio <canal>`).
Ejemplo genérico:

```
Folder: docs/difusion
Languages: es, en
Channels: x, reddit, linkedin, discord
Extra channels:
- mastodon: límite: 500; tono: cercano
- portal: formato: propio; plantilla: docs/difusion/portal.json
Palette: --fondo #101418; --acento #4cc38a
Screenshots: arrancar la app (npm run dev), abrir /panel, captura de la ventana a 1280x720
Task prefixes: INS,FLU   (se pasa a comprobar.py --prefijos-tarea)
Reddit: r/ejemplo, reglas pegadas por la persona el 2026-10-25: «sin autopromoción más de una vez al mes; etiqueta [Proyecto]»
```

## Recoger mejoras de vuelta

El flujo aprende de los proyectos que lo usan. Hay dos mitades:

- **Empuja el proyecto.** Una `retro` que descubre una mejora **general** (de una skill, un script, una plantilla, una
  regla de `AGENTS.md`) no parchea la copia local, que la próxima actualización pisaría: la propone al flujo, como
  incidencia o PR en este repo, o la deja en el archivo de la retro bajo un encabezado
  `## Para Galivelop-workflow` (o `## For Galivelop-workflow`).
- **Tira el flujo.** Desde este repo, la skill `gw-harvest` recorre los proyectos conectados que tengan
  `.claude/gw.json`. La parte mecánica la hace `python3 scripts/recoger.py <proyecto>...` (copias del flujo editadas,
  skills nuevas, secciones de retros, commits desde la última recogida); el agente solo decide qué es general y escribe
  `docs/propuestas/AAAA-MM-DD-<repo>.md`. **Nunca aplica nada sin confirmación**: lo aprobado entra como un cambio
  normal con entrada en el CHANGELOG y nueva versión ([contribuir](contribuir.md)).

Los proyectos se leen, no se modifican, desde la sesión que recoge.
