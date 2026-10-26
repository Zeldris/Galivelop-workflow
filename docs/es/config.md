# Configuración: `.claude/gw.json`

> [English](../en/config.md)

Todo lo que cambia de un proyecto a otro, y nada más. Solo `scripts/config.py` lo lee (un dato, un sitio); el resto
de scripts le piden las claves. Se valida contra [`schema/gw.schema.json`](../../schema/gw.schema.json): una clave
desconocida o mal escrita es un error, y los scripts **fallan cerrados** (salida 2) con la orden que lo comprueba:

```bash
python3 .claude/gw/scripts/config.py validate     # ¿es válido?
python3 .claude/gw/scripts/config.py get check    # valor de una clave (con su valor por defecto)
```

El ejemplo completo y comentable está en [`templates/gw.json`](../../templates/gw.json); `aplicar.py --init` lo
rellena con las banderas ([aplicar](aplicar.md)). Las listas se escriben como arrays JSON. Las expresiones regulares
usan la sintaxis de Python y, en JSON, la barra invertida se duplica (`"\\.md$"`).

## Claves obligatorias

| Clave | Qué es | Defecto | Ejemplo | La leen |
|---|---|---|---|---|
| `version` | Versión del flujo con la que se aplicó al proyecto (`X.Y.Z`). Se sube a mano tras `/gw-update` | (sin defecto) | `"0.1.0"` | `session-start.sh` y `doctor.py` (avisan si la copia no coincide), `aplicar.py` |
| `language` | Idioma de plantillas y respuestas: `es` o `en` | (sin defecto) | `"es"` | `aplicar.py` (qué plantillas copia), `revisado.sh` (idioma del mensaje) |
| `log` | Ruta de la bitácora, desde la raíz del repo | (sin defecto; `--init` pone `docs/traspaso.md` en es y `docs/handoff.md` en en) | `"docs/traspaso.md"` | `recuperar.py`, `doctor.py`, `prepush-ramas.sh`, `aplicar.py` |
| `protectedBranch` | La rama que solo recibe código revisado | (sin defecto) | `"main"` | `pre-push`, `revision-antes-de-main.sh`, `revisado.sh`, `fusionar.sh`, plantillas y CI |
| `pushToProtected` | Cómo entra el código: `direct` (push directo) o `pr` (por pull request: además, el gancho `PreToolUse` guarda crear y fusionar PR). En los dos, el `pre-push` exige la marca de revisión a todo push directo que traiga código | (sin defecto) | `"pr"` | `pre-push`, `revision-antes-de-main.sh` |
| `check` | Órdenes que se ejecutan **en orden** sobre el commit que se sube; todas deben pasar. Al menos una | (sin defecto) | `["npm run check"]` | `pre-push`, `fusionar.sh`, `doctor.py`, CI |
| `reviewMark` | Archivo versionado con el sha del commit revisado | (sin defecto; `--init` pone `docs/registros/revisado.txt`) | `"docs/registros/revisado.txt"` | `revisado.sh` (lo escribe), `es-codigo.sh`, `pre-push`, `revision-antes-de-main.sh` |
| `content` | Expresiones regulares (sobre rutas relativas) de lo que **es contenido, no código**: no necesita `/code-review` (no van scripts ni lo que un agente lee como instrucciones: sube sin marca) | (sin defecto; puede ser `[]`, entonces todo es código; `--init` pone `^docs/`, los `.md` de documentación de la raíz (también sus traducciones, `README.es.md`, y `CHANGELOG.md`) y los `.md` de `.claude/skills/`) | `["^docs/", "^README\\.md$"]` | `es-codigo.sh`, y con él `pre-push` y `revision-antes-de-main.sh` |

## Claves opcionales

| Clave | Qué es | Defecto | Ejemplo | La leen |
|---|---|---|---|---|
| `$schema` | Ruta o URL del esquema, para el editor | – | `"gw/schema/gw.schema.json"` | el editor |
| `visibleLanguages` | Idiomas en los que debe existir todo texto que vea la usuaria | `[]` | `["es", "gl", "en"]` | `REVIEW.md` (lo aplican `/code-review` y los agentes) |
| `logRows` | Bitácora con **una fila por rama**, de como mucho 600 caracteres: cada rama escribe solo en la suya | `false` | `true` | `bitacora.py`, `prepush-ramas.sh`, `recuperar.py` |
| `install` | Órdenes que instalan dependencias (en la nube y en el CI) | `[]` | `["npm ci"]` | `session-start.sh` (solo en la nube y si cambió el lockfile), CI, `doctor.py` |
| `ciInstall` | Órdenes de instalación solo para el CI: la plantilla de CI corre estas en lugar de `install`. Sin la clave, el CI corre `install`; con `[]`, no instala nada. No aparece en `templates/gw.json` a propósito (un `[]` copiado desactivaría la instalación del CI) | sin clave (el CI usa `install`) | `["npm ci --ignore-scripts"]` | CI (`comprobar.yml`) |
| `setup` | Órdenes que corren en la nube **después** de `install`, una tras otra en el mismo gancho de inicio (los ganchos de `SessionStart` corren en paralelo, así que el orden vive aquí): una compilación, una semilla de datos. Se repiten cuando se repite `install` (cambió un lockfile o la lista). Si una falla o pasa de `GW_COMMAND_TIMEOUT` segundos (900 por defecto), el gancho lo cuenta con la orden a mano y para; la siguiente sesión reintenta. La plantilla de CI no corre `setup` El límite lo aplica un vigilante en bash (no hace falta `timeout`, así que vale en macOS): la orden corre en su propio grupo de procesos y, pasado el límite, todo el grupo recibe TERM y, unos segundos después, KILL. Un proceso que se desprende del grupo (`setsid`, un demonio) puede sobrevivir. | `[]` | `["cargo build"]` | `session-start.sh`, `doctor.py` |
| `requireRetro` | `revisado.sh` exige una `retro` con la decisión de la persona en la rama antes de marcar; lee todo el párrafo de `**Estado:**` y acepta aplicada, rechazada, aplazada, decidida o aprobada; `revisado.sh --footer "Siguiente: …"` añade esa línea al commit de la marca; los ficheros sin seguimiento no cuentan como cambios; con la persona ausente, la retro queda con `**Estado:** pendiente` (`revisado.sh` la rechaza) y se para: su decisión es el único paso que falta | `false` (también en `templates/gw.json`; `--init --require-retro true` lo activa) | `true` | `revisado.sh`, skill `retro` |
| `agentSignatures` | Con `false`, el gancho `commit-msg` rechaza un mensaje que lleve firma de agente: un `Co-Authored-By:` que nombre a Claude o Anthropic (sin distinguir mayúsculas), `Claude-Session:`, «Generated with/by [Claude Code» o un enlace `claude.ai/code/session`; un coautor humano pasa. Ignora las líneas de comentario (`core.commentChar`) y lo que va tras la línea de tijeras de `git commit --verbose`; también se comprueba en un merge y se salta durante un rebase. Solo cubre el mensaje del commit, no la descripción de un PR | `true` (también en `templates/gw.json`; `--init --agent-signatures false` lo pone a `false`) | `false` | `templates/githooks/commit-msg` |
| `roadmap` | Reservada para el módulo opcional de hitos; ningún script la lee todavía | `false` | `false` | (nadie aún) |
| `selector` | `{ "cases": [ { "case", "skill", "sessionModel", "subagentModel" } ] }`: filas propias del proyecto para el `selector` | sin filas | `{"cases": [{"case": "Migración de datos", "skill": "orchestrate-dealer", "sessionModel": "Opus"}]}` | skill `selector` |
| `logSections` | Encabezados de las secciones de la bitácora que `recuperar.py --estado` devuelve tras compactar o `/clear` (sin `logRows`) | `[]`: la primera sección y la que se llame «Pendiente»/«Pending» | `["Estado actual", "Pendiente"]` | `recuperar.py` |
| `designReferences` | Productos, marcos o estándares con los que se contrasta cada propuesta de diseño | `[]` | `["WCAG 2.2", "Material Design 3"]` | skills `grilling` y `selector` |
| `protectedPaths` | Prefijos de ruta que un agente (`CLAUDECODE=1`) no puede commitear: borradores de otras personas | `[]` | `["docs/borradores/"]` | `.githooks/pre-commit` |
| `staleRefs` | Expresiones (sin distinguir mayúsculas) que no deben aparecer en `docs/` ni en los README: una tarea renombrada, una fase borrada. Admite también `{ "patterns": [...], "skip": [globs] }`: `skip` lista archivos o carpetas (rutas del repo; `*` no cruza carpetas, `**` sí, una `/` final es toda la carpeta) que no se revisan, además de la bitácora y `.claude/`, que siempre se saltan (p. ej. los `retro-*.md`, que citan rutas antiguas). Un glob que no coincide con nada no hace nada Los globs admiten solo `*`, `**` y `?` (sin corchetes ni la semántica de gitignore): `*` y `?` no cruzan carpetas, `**` sí; una entrada sin comodines (`docs/registros`, con o sin `/` final) es ese archivo o esa carpeta con todo lo que hay debajo, y `docs/**` incluye también `docs`; una `/` inicial se ignora. | `[]` | `["fase 9 \\(vieja\\)"]` o `{"patterns": ["fase 9"], "skip": ["docs/registros/retro-*.md"]}` | `enlaces-md.py` |
| `linkRoots` | Carpetas (relativas, sin `..`) cuyos Markdown escriben los enlaces relativos desde la raíz del repo y no desde su carpeta (p. ej. una descripción de PR guardada); `enlaces-md.py` los resuelve así. `.` es todo el repo `/` inicial resuelve desde la raíz del repo; un enlace que sale del repo se avisa, no se mira en el disco. | `[]` | `["docs/prs"]` | `enlaces-md.py` |
| `agentMap` | `{ "path", "prefixes", "roots" }`: el mapa para agentes que comprueba `mapa-agente.py`. `path` es el archivo (relativo, sin `..`; sin la clave, `docs/mapa-agente.md`, y si ese no existe el script lo dice y sale en 0; un `path` declarado que no existe es un error). `prefixes` asigna un prefijo corto a su carpeta real (`{"b/": "backend/src/"}`: `` `b/a.ts#f` `` se mira en `backend/src/a.ts`). `roots` lista carpetas de primer nivel que cuentan como ruta aunque ya no existan (así una carpeta borrada o renombrada se avisa en vez de pasar por texto). Una ruta del mapa (`` `ruta` ``, `` `ruta#nombre` `` o un enlace Markdown) tiene que existir, y `nombre` tiene que estar definido en ese archivo. | `{}` (mapa en `docs/mapa-agente.md`, sin prefijos ni raíces) | `{"path": "docs/mapa.md", "prefixes": {"b/": "backend/src/"}, "roots": ["backend"]}` | `mapa-agente.py` |
| `scoutDir` | Carpeta (relativa, sin `..`) donde `scout-updates` guarda su memoria: `architecture.md`, `proposals.md` y los informes. | `.claude/gw/scout` | `"docs/scout"` | `scout-updates` (`compare.py`) |
| `checkWrapper` | Prefijo de cada orden de `check` y de `relatedTests` (p. ej. `docker compose run --rm app`): siempre se ejecuta `<prefijo> bash -c '<orden>'` (con `cd <cwd> &&` dentro si la entrada lleva `cwd`), así que cubre también una orden compuesta (`a && b`). La plantilla de CI no aplica `checkWrapper`: es para el equipo local (p. ej. un sandbox); los runners de CI no lo necesitan. | `""` (sin prefijo) | `"docker compose run --rm app"` | `pre-push`, `tests-relacionados.sh` |
| `relatedTests` | `{ "fast": [...], "slow": [...] }`: las pruebas de lo que cambia. Cada entrada es una orden (texto) o `{ "command", "paths", "cwd" }`: `paths` es una expresión que filtra los archivos cambiados y `cwd` una carpeta desde la que corre la orden (`{files}` va relativo a ella). `fast` corre en cada push; `slow`, solo si algún archivo cambiado (de su ámbito) sigue existiendo; `{files}` se sustituye por los archivos cambiados | sin órdenes | `{"fast": [{"command": "npx vitest related {files}", "paths": "\\.tsx?$", "cwd": "web"}], "slow": []}` | `tests-relacionados.sh` (lo llama el `pre-push`) |
| `worktreeLinks` | Rutas (relativas, sin `..`) de la copia principal que el `pre-push` enlaza en el worktree temporal donde corre el `check`; las que no existen se omiten y nunca se pisa una ruta del commit | `["node_modules", ".venv"]` | `["node_modules", "backend/node_modules", ".env"]` | `pre-push` |
| `worktreeDir` | Carpeta (absoluta o relativa a la raíz del repo) bajo la que el `pre-push` crea sus worktrees temporales, para un sandbox que no ve `$TMPDIR` (p. ej. Flatpak); si es relativa, conviene que esté en `.gitignore` y fuera de `.git/` | `""` (`${TMPDIR:-/tmp}`) | `".cache/gw-worktrees"` | `pre-push` |
| `plan` | Archivos o carpetas de plan o roadmap donde las tareas se tachan o marcan | `[]` | `["docs/producto/21-roadmap.md"]` | `bitacora.py` |
| `taskId` | Expresión de los identificadores de tarea | `[A-Z]{2,5}-\\d+` | `"(INS\|FLU)-\\d+"` (los grupos con captura se tratan como sin captura) | `bitacora.py` |
| `subagentCap` | Entero ≥ 1: subagentes (llamadas a `Agent`/`Task`) que una sesión lanza antes de que el gancho `PreToolUse` `tope-subagentes.py` pregunte a la persona si no están en bucle, y otra vez cada 10 (nunca bloquea). Si el config no se puede leer, vale el defecto | `30` | `50` | `tope-subagentes.py` |

## Notas

- **`check` es una lista de órdenes**, no un script único: cada una se ejecuta con `bash -c` en la raíz del commit que
  se sube. Una que no existe la detecta `doctor.py` antes de que falle un push. El `pre-push` les pasa
  `GW_PUSH_PROTECTED=true` cuando la subida va a la rama protegida (`false` si no; fuera del gancho, sin definir): así
  una orden puede correr solo antes de `main`, p. ej. `[ "${GW_PUSH_PROTECTED:-}" != true ] || <orden>`.
- **El `check` corre en un worktree temporal** cuando la copia de trabajo no está limpia (o la subida no es lo que hay
  en ella): vive en `${TMPDIR:-/tmp}/gw-pre-push-wt-<uid>-<id del repo>/wt.XXXXXX.d` (o bajo `worktreeDir`; carpeta con permisos 700, y un symlink en su lugar se rechaza), nunca dentro
  de `.git/` (jest y otras herramientas ignoran toda ruta con un segmento `/.git/`), y se borra en toda salida
  (también con Ctrl-C o `kill`). Si un push muere sin poder limpiar, el siguiente borra los worktrees huérfanos de más
  de 24 h cuyo proceso ya no existe; dos pushes a la vez no se pisan. Al cambiar `worktreeDir`, la carpeta anterior ya no se limpia: bórrala a mano. Lo enlazado desde la copia principal lo dice `worktreeLinks`. El registro de una orden fallida
  se conserva (`full log: <ruta>`); si pasa, se borra.
- **El `pre-push` no repite un `check` que ya pasó en verde.** La clave es el árbol del commit que se sube, las
  órdenes de `check` y `checkWrapper`; se apunta en `<directorio común de git>/gw-check-verde` (los worktrees
  enlazados la comparten), caduca a las 24 h y guarda las últimas 50. Si la clave está, el `pre-push` dice
  `check already green on this tree…` y se salta el `check` (los `relatedTests` corren igual); si no, corre el
  `check` y, en verde, lo apunta (si corrió en la propia copia, solo si la dejó limpia). Quien lo apunta antes es
  `bash .claude/gw/scripts/check.sh` (`scripts/check.sh` en este repo): corre el `check` sobre la copia de trabajo y,
  si pasa y el árbol (lo que commitearía `git add -A`) no cambió durante la ejecución, apunta el verde; así la subida
  no lo repite. Un `check` pasado a mano (p. ej. `bash tests/comprobar.sh`) no apunta nada. Límites: una subida a la
  rama protegida nunca lee ni escribe la caché; no se apunta nada con entradas `assume-unchanged` o `skip-worktree`
  (sparse checkout) ni con un submódulo con cambios; cualquier fallo de la caché solo significa que el `check` corre;
  `check.sh` corre con los archivos ignorados de la copia de trabajo (`.env`, generados), mientras que antes una
  subida con la copia sucia comprobaba en un worktree limpio. `GW_CHECK_CACHE=0` la desactiva (`GW_CHECK_CACHE=0 git
  push` corre el `check` aunque esté apuntado).
- **`pushToProtected`** dice cómo entra hoy el código en la rama protegida. Un push directo que trae código pide
  siempre la marca en el `pre-push`, con `direct` y con `pr`; con `pr`, además, el gancho de PR la pide al crear o
  fusionar el pull request. El config se lee del commit que se sube, no de la copia de trabajo; para la rama
  protegida, `content` y `reviewMark` salen de su punta remota (de lo que se sube solo si aún no tiene config, con
  un aviso), y la rama es protegida si lo dice cualquiera de las dos o la copia de trabajo: un commit no puede
  relajar la regla que lo juzga.
- **`content` y la marca.** Un cambio que solo toca archivos de `content` no necesita revisión; cualquier otro, sí.
  `revisado.sh` escribe en `reviewMark` el commit revisado y la marca debe ser antecesora de lo que se sube y no tener
  código después. `.claude/gw.json`, `.claude/settings.json`, `.claude/gw/` y `.githooks/` son siempre código, diga
  lo que diga `content`. Para ver cómo se clasifica una ruta y por qué:
  `bash .claude/gw/scripts/es-codigo.sh --explicar <ruta>...`.
- **`logRows`** va con la plantilla de bitácora de filas (`| **Tarea en curso · \`rama\`** | … |`); el push comprueba
  que cada rama escribe solo en su fila, que toda fila «Tarea en curso» lleva su rama y que cada tarea cerrada en el
  plan consta en «Hecho»: tachada allí, o nombrada en una línea que empieza por fecha (un punto sin tachar no basta).
- Tras actualizar el flujo, sube `version` a mano (`/gw-update` lo hace): ese número es lo que `doctor.py`
  compara con las cabeceras copiadas.

## Notas personales

Si tienes notas que deben llegar a todos los proyectos donde aplicas el flujo, guárdalas **fuera de cualquier
repo**, en `~/.claude/gw/notas/` (otra carpeta con la variable de entorno `GW_NOTAS_PERSONALES`). `aplicar.py` las
lleva a `<proyecto>/.claude/gw/<nombre>`:

- Solo archivos normales directamente en esa carpeta, con nombre `[A-Za-z0-9][A-Za-z0-9._-]*`; no se miran
  subcarpetas, enlaces simbólicos ni archivos ocultos. Si la carpeta no existe, no pasa nada y no se dice nada.
- Si la nota falta en el proyecto, se crea (y se avisa como «personal note»). Si es idéntica, nada. Si **difiere**,
  nunca se sobrescribe ni se deja un `.gw-nuevo` (el proyecto puede haberla adaptado a propósito): se imprime una
  línea con `diff <origen> <destino>` en cada ejecución. `--check` **no falla** ni por una nota que falta (solo dice
  «would create personal note …») ni por una que difiere.
- Una nota se salta con un `WARNING` y la orden de renombrarla cuando su nombre acaba en `.gw-nuevo` (`doctor.py` lo
  toma por una propuesta pendiente), cuando es el de un archivo del flujo en `.claude/gw/` (se compara sin mirar
  mayúsculas y aunque ese archivo no esté instalado: `opt-tokens.md`, `opt-ai.md`, `scout-updates.md`, `scripts`,
  `schema`…) o cuando su destino no es un archivo normal. Una carpeta de notas ilegible o que es un archivo, y una
  nota que no se puede leer, también avisan (una carpeta ausente, no).
- Nunca se aplican al propio repo del flujo: nada personal va a él. `--sin-notas-personales` las salta en una
  ejecución. Una `GW_NOTAS_PERSONALES` relativa se resuelve desde la carpeta donde se lanza.
