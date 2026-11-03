# Configuración: `.claude/gw.json`

> [English](../en/config.md)

Todo lo que cambia de un proyecto a otro, y nada más. Solo `scripts/config.py` lo lee (un dato, un sitio); el resto
de scripts le piden las claves. Se valida contra [`schema/gw.schema.json`](../../schema/gw.schema.json): una clave
desconocida o mal escrita es un error, y los scripts **fallan cerrados** (salida 2) con la orden que lo comprueba:

```bash
python3 .claude/gw/scripts/config.py validate     # ¿es válido?
python3 .claude/gw/scripts/config.py get check    # valor de una clave (con su valor por defecto)
```

El ejemplo completo y comentable está en [`templates/gw.json`](../../templates/gw.json); `apply.py --init` lo
rellena con las banderas ([aplicar](apply.md)). Las listas se escriben como arrays JSON. Las expresiones regulares
usan la sintaxis de Python y, en JSON, la barra invertida se duplica (`"\\.md$"`).

## Claves obligatorias

| Clave | Qué es | Defecto | Ejemplo | La leen |
|---|---|---|---|---|
| `version` | Versión del flujo con la que se aplicó al proyecto (`X.Y.Z`). Se sube a mano tras `/gw-update` | (sin defecto) | `"0.1.0"` | `session-start.sh` y `doctor.py` (avisan si la copia no coincide), `apply.py` |
| `language` | Idioma de plantillas y respuestas: `es` o `en` | (sin defecto) | `"es"` | `apply.py` (qué plantillas copia), `reviewed.sh` (idioma del mensaje) |
| `log` | Ruta de la bitácora, desde la raíz del repo | `docs/handoff.md`; si no existe y sí `docs/traspaso.md` (proyecto de la 0.4), esa (`doctor.py` avisa: `/gw-update`) | `"docs/handoff.md"` | `recover.py`, `doctor.py`, `prepush-branches.sh`, `apply.py` |
| `protectedBranch` | La rama que solo recibe código revisado | (sin defecto) | `"main"` | `pre-push`, `review-before-main.sh`, `reviewed.sh`, `merge-branch.sh`, plantillas y CI |
| `pushToProtected` | Cómo entra el código: `direct` (push directo) o `pr` (por pull request: además, el gancho `PreToolUse` guarda crear y fusionar PR). En los dos, el `pre-push` exige la marca de revisión a todo push directo que traiga código | (sin defecto) | `"pr"` | `pre-push`, `review-before-main.sh` |
| `check` | Órdenes que se ejecutan **en orden** sobre el commit que se sube; todas deben pasar. Al menos una | (sin defecto) | `["npm run check"]` | `pre-push`, `merge-branch.sh`, `doctor.py`, CI |
| `reviewMark` | Archivo versionado con el sha del commit revisado | `docs/records/reviewed.txt`; si no existe y sí `docs/registros/revisado.txt`, ese | `"docs/records/reviewed.txt"` | `reviewed.sh` (lo escribe), `is-code.sh`, `pre-push`, `review-before-main.sh` |
| `recordsDir` | Carpeta (relativa, sin `..` ni `/` final) donde las skills dejan sus informes: `retro-*.md`, los de `gw-opt-tokens` y `gw-opt-ai`, los textos de release | `docs/records`; si no existe y sí `docs/registros`, esa | `"docs/informes"` | `retro`, `gw-opt-tokens`, `gw-opt-ai` (leen `config.py get recordsDir`) |
| `proposalsDir` | Carpeta (relativa, sin `..` ni `/` final) donde `gw-harvest` escribe sus archivos `# Harvest` y `state.json`; `version.py --release` exige uno nuevo por versión | `docs/proposals`; si no existe y sí `docs/propuestas`, esa | `"docs/ideas"` | `gw-harvest`, `harvest.py`, `version.py` |
| `content` | Expresiones regulares (sobre rutas relativas) de lo que **es contenido, no código**: no necesita `/code-review` (no van scripts ni lo que un agente lee como instrucciones: sube sin marca) | (sin defecto; puede ser `[]`, entonces todo es código; `--init` pone `^docs/`, los `.md` de documentación de la raíz (también sus traducciones, `README.es.md`, y `CHANGELOG.md`) y los `.md` de `.claude/skills/`) | `["^docs/", "^README\\.md$"]` | `is-code.sh`, y con él `pre-push` y `review-before-main.sh` |

## Claves opcionales

| Clave | Qué es | Defecto | Ejemplo | La leen |
|---|---|---|---|---|
| `$schema` | Ruta o URL del esquema, para el editor | – | `"gw/schema/gw.schema.json"` | el editor |
| `schemaVersion` | Versión del formato de este archivo (entero). Sin ella vale 0 (escrito antes de la 0.5). Opcional durante la `0.x`; `apply.py --init` y `/gw-update` la escriben | `0` | `1` | `config.py` (migra en memoria), `apply.py` (escribe la migración), `doctor.py` (avisa si es vieja) |
| `visibleLanguages` | Idiomas en los que debe existir todo texto que vea la usuaria | `[]` | `["es", "gl", "en"]` | `REVIEW.md` (lo aplican `/code-review` y los agentes) |
| `keepLegacyPaths` | Con `true`, el proyecto conserva sus rutas españolas antiguas (`docs/traspaso.md`, `docs/registros/`, `docs/propuestas/`), escritas explícitas en este archivo, y `apply.py` no planea moverlas. Lo escribe `apply.py --keep-paths`; ponerlo a mano a `true` hace lo mismo | `false` | `true` | `scripts/apply.py` |
| `logRows` | Bitácora con **una fila por rama**, de como mucho 600 caracteres: cada rama escribe solo en la suya | `false` | `true` | `handoff.py`, `prepush-branches.sh`, `recover.py` |
| `install` | Órdenes que instalan dependencias (en la nube y en el CI) | `[]` | `["npm ci"]` | `session-start.sh` (solo en la nube y si cambió el lockfile), CI, `doctor.py` |
| `ciInstall` | Órdenes de instalación solo para el CI: la plantilla de CI corre estas en lugar de `install`. Sin la clave, el CI corre `install`; con `[]`, no instala nada. No aparece en `templates/gw.json` a propósito (un `[]` copiado desactivaría la instalación del CI) | sin clave (el CI usa `install`) | `["npm ci --ignore-scripts"]` | CI (`check.yml`) |
| `setup` | Órdenes que corren en la nube **después** de `install`, una tras otra en el mismo gancho de inicio (los ganchos de `SessionStart` corren en paralelo, así que el orden vive aquí): una compilación, una semilla de datos. Se repiten cuando se repite `install` (cambió un lockfile o la lista). Si una falla o pasa de `GW_COMMAND_TIMEOUT` segundos (900 por defecto), el gancho lo cuenta con la orden a mano y para; la siguiente sesión reintenta. La plantilla de CI no corre `setup` El límite lo aplica un vigilante en bash (no hace falta `timeout`, así que vale en macOS): la orden corre en su propio grupo de procesos y, pasado el límite, todo el grupo recibe TERM y, unos segundos después, KILL. Un proceso que se desprende del grupo (`setsid`, un demonio) puede sobrevivir. | `[]` | `["cargo build"]` | `session-start.sh`, `doctor.py` |
| `requireRetro` | `reviewed.sh` exige una `retro` con la decisión de la persona en la rama antes de marcar; lee todo el párrafo de `**Estado:**` y acepta aplicada, rechazada, aplazada, decidida o aprobada; `reviewed.sh --footer "Siguiente: …"` añade esa línea al commit de la marca; los ficheros sin seguimiento no cuentan como cambios; con la persona ausente, la retro queda con `**Estado:** pendiente` (`reviewed.sh` la rechaza) y se para: su decisión es el único paso que falta | `false` (también en `templates/gw.json`; `--init --require-retro true` lo activa) | `true` | `reviewed.sh`, skill `retro` |
| `agentSignatures` | Con `false`, el gancho `commit-msg` rechaza un mensaje que lleve firma de agente: un `Co-Authored-By:` con `noreply@anthropic.com` o que nombre a Claude Code, Opus, Sonnet, Haiku o Fable (sin distinguir mayúsculas), `Claude-Session:`, o una línea que empiece (tras un emoji) por «Generated with/by [Claude Code» o por un enlace `claude.ai/code/session`; un coautor humano (aunque se llame Claude) y un cuerpo que solo cite esos textos pasan. Ignora las líneas de comentario (`core.commentString` o `core.commentChar`) y lo que va tras la línea de tijeras de `git commit --verbose`; también se comprueba en un merge y se salta durante un rebase. El gancho `PreToolUse` `scripts/agent-signatures.py` aplica lo mismo, solo en columna 0 (una línea sangrada o dentro de un bloque de código ``` o ~~~ es una cita y pasa), más una línea que empiece por un enlace `claude.ai/code/session`, al texto que el agente publica en GitHub: título y cuerpo (`title`, `body`, `message`, `commit_title`, `commit_message`, `commitHeadline`, `commitBody`) de las herramientas de cualquier servidor MCP con `github` en el nombre (`create_pull_request`, `update_pull_request`, `merge_pull_request`, `enable_pr_auto_merge`, `add_issue_comment`, `update_issue_comment`, `issue_write`, `add_reply_to_pull_request_comment`, `add_comment_to_pending_review`, `pull_request_review_write`, `push_files`, `create_or_update_file`), y en Bash `gh pr create\|edit\|comment\|review\|merge`, `gh issue create\|comment\|edit`, `gh release create\|edit` y `gh api` (`--title`/`-t`, `--subject`, `--body`/`-b`, `--notes`/`-n`, también pegado como `-bTEXTO`; el contenido de `--body-file`/`-F`/`--notes-file`; los `clave=valor` de `-f`/`-F`/`--field`/`--raw-field`; con un archivo `-` se lee la orden entera, heredoc incluido); lo bloquea con el motivo y cómo arreglarlo. Con la clave ausente o `true` no hace nada. Además, `session-start.sh` avisa (sin bloquear) si `git config user.email` es `noreply@anthropic.com` con `false` | `true` (también en `templates/gw.json`; `--init --agent-signatures false` lo pone a `false`) | `false` | `templates/githooks/commit-msg` |
| `commitFormat` | `"free"` (cualquier primera línea) o `"conventional"`: el gancho `commit-msg` exige `tipo(ámbito)!: texto` (tipos `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`; ámbito y `!` opcionales; un espacio tras los dos puntos). Pasan `WIP: ` delante y las líneas que crea git (`fixup! `, `squash! `, `amend! `, `Revert "`, `Reapply "`, `Merge `). No se comprueba en merges, reverts ni cherry-picks en curso ni en un rebase | `"free"` | `"conventional"` | `scripts/commit-message.py`, `templates/githooks/commit-msg` |
| `commitRefs` | Con `true`, el gancho `commit-msg` exige en el bloque de trailers (el último párrafo, solo líneas `Clave: valor`) un `Refs: <id>` con uno o varios ids separados por comas (`Refs: D11, D12`; la línea puede repetirse), y cada id debe abrir una entrada (fila de tabla `\| D11 \|` o elemento de lista `- D11 …`, con o sin `[ ]`, negrita o tachado) con la forma de `taskId` en alguna de `refsSources`, **leída del índice** (un commit que añade el id puede citarlo; un cambio sin preparar no cuenta). Mismas excepciones que `commitFormat`. Además, un trailer `Agent: <skill>` es opcional y, con `agentSignatures: false`, no puede nombrar un modelo o proveedor (el valor se parte en trozos por lo que no sea letra o cifra; falla un trozo `claude`, `anthropic`, `opus`, `sonnet`, `haiku`, `fable`, `gpt`, `chatgpt`, `openai`, `gemini`, `llama`, `mistral`, `qwen`, `deepseek`, o que case con `gpt<cifra>…`, `o<cifras>` o `<cifras>o`) | `false` | `true` | `scripts/commit-message.py` |
| `commitNext` | Con `true`, el gancho `commit-msg` exige en el bloque de trailers un trailer de siguiente paso no vacío: `Siguiente:` con `language: "es"`, `Next:` con `en` (y con cualquier otro idioma). También lo exige un commit `WIP:`. Pasan `fixup! `, `squash! `, `amend! `, `Revert "`, `Reapply "` y `Merge `, y no se comprueba en merges, reverts ni cherry-picks en curso ni en un rebase; `merge-branch.sh` lo exige en su mensaje de merge y para antes de fusionar. Para un mensaje legítimo sin él: `GW_NO_NEXT=1 git commit …` (el error lo dice). No empeora lo de `core.commentChar=auto`: las líneas de comentario se quitan antes de leer los trailers | `false` (también en `templates/gw.json`) | `true` | `scripts/commit-message.py`, `scripts/merge-branch.sh` |
| `refsSources` | Archivos o carpetas (de una carpeta cuentan sus `.md` rastreados) donde viven los ids válidos de `Refs:` | `[]`: las de `plan` más `log` | `["docs/roadmap.md"]` | `scripts/commit-message.py` |
| `ciLocalLog` | Archivo Markdown (relativo a la raíz, sin `..`) donde `ci-local.py --record` deja una línea por cada vez que corre en local el CI de GitHub. Si el CI de un PR no arrancó (sin CI, o sin arrancar por facturación), `review-before-main.sh` acepta la línea verde más reciente cuyo commit es antecesor de la cabeza del PR, solo con contenido detrás y hecha con el árbol limpio; vale el de la configuración de la rama protegida. Nunca es código para `is-code.sh` | `docs/records/ci-local.md`; si no existe y sí `docs/registros/ci-local.md`, ese | `"ci/local.md"` | `ci-local.py`, `review-before-main.sh`, `is-code.sh` |
| `ciLocalWorkflows` | Workflows (rutas relativas a la raíz) que corre `ci-local.py`, sean cuales sean sus disparadores. Vacío: todos los `.github/workflows/*.yml\|yaml` que dispara el evento | `[]` | `[".github/workflows/ci.yml"]` | `ci-local.py` |
| `ciIgnore` | Nombres de checks de CI ajenos (nombre de un check-run o contexto de un estado de commit, p. ej. un despliegue) que no bloquean la fusión ni cuentan como CI del proyecto. Nombre exacto, o con `*` por cualquier texto (`vercel*`); distingue mayúsculas; sin regex. Uno ignorado solo se aparta: nunca vuelve verde un check del proyecto en rojo o pendiente, y un commit donde solo informaron checks ignorados cuenta como sin CI. Vale el de la configuración de la rama protegida. Si la rama protegida aún no tiene `gw.json`, vale el de la cabeza del PR. Un patrón amplio (`deploy-*`) aparta también un job propio con ese nombre. | `[]` | `["Vercel", "deploy-*"]` | `ci-status.py`, `review-before-main.sh` |
| `roadmap` | Reservada para el módulo opcional de hitos; ningún script la lee todavía | `false` | `false` | (nadie aún) |
| `selector` | `{ "cases": [ { "case", "skill", "sessionModel", "subagentModel" } ] }`: filas propias del proyecto para el `gw-selector` | sin filas | `{"cases": [{"case": "Migración de datos", "skill": "gw-orchestrate-dealer", "sessionModel": "Opus"}]}` | skill `gw-selector` |
| `logSections` | Encabezados de las secciones de la bitácora que `recover.py --state` devuelve tras compactar o `/clear` (sin `logRows`) | `[]`: la primera sección y la que se llame «Pendiente»/«Pending» | `["Estado actual", "Pendiente"]` | `recover.py` |
| `designReferences` | Productos, marcos o estándares con los que se contrasta cada propuesta de diseño | `[]` | `["WCAG 2.2", "Material Design 3"]` | skills `grilling` y `gw-selector` |
| `protectedPaths` | Prefijos de ruta que un agente (`CLAUDECODE=1`) no puede commitear: borradores de otras personas | `[]` | `["docs/borradores/"]` | `.githooks/pre-commit` |
| `staleRefs` | Expresiones (sin distinguir mayúsculas) que no deben aparecer en `docs/` ni en los README: una tarea renombrada, una fase borrada. Admite también `{ "patterns": [...], "skip": [globs] }`: `skip` lista archivos o carpetas (rutas del repo; `*` no cruza carpetas, `**` sí, una `/` final es toda la carpeta) que no se revisan, además de la bitácora y `.claude/`, que siempre se saltan (p. ej. los `retro-*.md`, que citan rutas antiguas). Un glob que no coincide con nada no hace nada Los globs admiten solo `*`, `**` y `?` (sin corchetes ni la semántica de gitignore): `*` y `?` no cruzan carpetas, `**` sí; una entrada sin comodines (`docs/registros`, con o sin `/` final) es ese archivo o esa carpeta con todo lo que hay debajo, y `docs/**` incluye también `docs`; una `/` inicial se ignora. | `[]` | `["fase 9 \\(vieja\\)"]` o `{"patterns": ["fase 9"], "skip": ["docs/records/retro-*.md"]}` | `md-links.py` |
| `linkRoots` | Carpetas (relativas, sin `..`) cuyos Markdown escriben los enlaces relativos desde la raíz del repo y no desde su carpeta (p. ej. una descripción de PR guardada); `md-links.py` los resuelve así. `.` es todo el repo `/` inicial resuelve desde la raíz del repo; un enlace que sale del repo se avisa, no se mira en el disco. | `[]` | `["docs/prs"]` | `md-links.py` |
| `agentMap` | `{ "path", "prefixes", "roots" }`: el mapa para agentes que comprueba `agent-map.py`. `path` es el archivo (relativo, sin `..`; sin la clave, `docs/agent-map.md`, y si ese no existe el script lo dice y sale en 0; un `path` declarado que no existe es un error). `prefixes` asigna un prefijo corto a su carpeta real (`{"b/": "backend/src/"}`: `` `b/a.ts#f` `` se mira en `backend/src/a.ts`). `roots` lista carpetas de primer nivel que cuentan como ruta aunque ya no existan (así una carpeta borrada o renombrada se avisa en vez de pasar por texto). Una ruta del mapa (`` `ruta` ``, `` `ruta#nombre` `` o un enlace Markdown) tiene que existir, y `nombre` tiene que estar definido en ese archivo. | `{}` (mapa en `docs/agent-map.md`, sin prefijos ni raíces) | `{"path": "docs/mapa.md", "prefixes": {"b/": "backend/src/"}, "roots": ["backend"]}` | `agent-map.py` |
| `scoutDir` | Carpeta (relativa, sin `..`) donde `gw-scout-updates` guarda su memoria: `architecture.md`, `proposals.md` y los informes. | `.claude/gw/scout` | `"docs/scout"` | `gw-scout-updates` (`compare.py`) |
| `checkWrapper` | Prefijo de cada orden de `check` y de `relatedTests` (p. ej. `docker compose run --rm app`): siempre se ejecuta `<prefijo> bash -c '<orden>'` (con `cd <cwd> &&` dentro si la entrada lleva `cwd`), así que cubre también una orden compuesta (`a && b`). La plantilla de CI no aplica `checkWrapper`: es para el equipo local (p. ej. un sandbox); los runners de CI no lo necesitan. | `""` (sin prefijo) | `"docker compose run --rm app"` | `pre-push`, `related-tests.sh` |
| `relatedTests` | `{ "fast": [...], "slow": [...] }`: las pruebas de lo que cambia. Cada entrada es una orden (texto) o `{ "command", "paths", "cwd" }`: `paths` es una expresión que filtra los archivos cambiados y `cwd` una carpeta desde la que corre la orden (`{files}` va relativo a ella). `fast` corre en cada push; `slow`, solo si algún archivo cambiado (de su ámbito) sigue existiendo o se borró alguno; `{files}` se sustituye por los archivos cambiados que existen (nunca por rutas borradas). Los borrados se deciden por entrada: si el ámbito (`paths`/`cwd`) de una entrada no coincide con ningún archivo existente pero sí con alguno borrado, se salta si su orden usa `{files}` (con un aviso) y corre si no lo usa | sin órdenes | `{"fast": [{"command": "npx vitest related {files}", "paths": "\\.tsx?$", "cwd": "web"}], "slow": []}` | `related-tests.sh` (lo llaman el `pre-push` y `merge-branch.sh`) |
| `worktreeLinks` | Rutas (relativas, sin `..`) de la copia principal que el `pre-push` enlaza en el worktree temporal donde corre el `check`; las que no existen se omiten y nunca se pisa una ruta del commit | `["node_modules", ".venv"]` | `["node_modules", "backend/node_modules", ".env"]` | `pre-push` |
| `worktreeDir` | Carpeta (absoluta o relativa a la raíz del repo) bajo la que el `pre-push` crea sus worktrees temporales, para un sandbox que no ve `$TMPDIR` (p. ej. Flatpak); si es relativa, conviene que esté en `.gitignore` y fuera de `.git/` | `""` (`${TMPDIR:-/tmp}`) | `".cache/gw-worktrees"` | `pre-push` |
| `plan` | Archivos o carpetas de plan o roadmap donde las tareas se tachan o marcan | `[]` | `["docs/producto/21-roadmap.md"]` | `handoff.py` |
| `taskId` | Expresión de los identificadores de tarea | `[A-Z]{2,5}-\\d+` | `"(INS\|FLU)-\\d+"` (los grupos con captura se tratan como sin captura) | `handoff.py` |
| `subagentCap` | Entero ≥ 1: subagentes (llamadas a `Agent`/`Task`) que una sesión lanza antes de que el gancho `PreToolUse` `subagent-cap.py` pregunte a la persona si no están en bucle, y otra vez cada 10 (nunca bloquea). Si el config no se puede leer, vale el defecto | `30` | `50` | `subagent-cap.py` |
| `instructionLines` | `{ "warn", "fail" }`, enteros ≥ 1 con `warn` ≤ `fail`: tope de líneas de `AGENTS.md` y `CLAUDE.md` (cada sesión los carga enteros). `doctor.py` avisa por encima de `warn` y falla por encima de `fail`; falta una parte, vale su defecto | `{"warn": 150, "fail": 250}` | `{"warn": 200, "fail": 300}` | `doctor.py` |
| `privateCheck` | Check de datos privados (E2) en el `pre-push` y en `--all`: `emails` (buscar correos) y `allowEmails` (direcciones que pueden publicarse; ya pasan solas `noreply@…`, `git@…`, `…@users.noreply.github.com` y los dominios `example`). `false` lo apaga. Los nombres privados van en `.claude/gw.local.json` (`{"privateNames": [...], "allowEmails": [...], "anonymize": {"<nombre>": "private-project-N"}}`), que nunca se sube: el `pre-commit` lo rechaza, `apply.py` lo pone en `.gitignore` y `config.py local` lo valida; sin él, los nombres no se miran (con aviso). `anonymize` (E3) da el alias público de cada nombre (cualquier grafía; vale como `privateNames`, no hace falta repetirlo): `harvest.py` lo imprime y lo guarda en el estado en lugar del nombre, y se niega a imprimir un proyecto con un nombre privado sin alias | `{"emails": true, "allowEmails": []}` | `{"allowEmails": ["yo@example.com"]}` | `private-check.py` (`pre-push`, `tests/check.sh`) |

**Rutas en inglés y compatibilidad (A8, 0.x).** `log`, `reviewMark`, `recordsDir`, `proposalsDir` y `ciLocalLog` ya no son obligatorias: si faltan en `gw.json` valen el defecto en inglés, salvo que no exista y sí exista el nombre español antiguo (una sola ruta, clave por clave), que se usa mientras no muevas el archivo; `doctor.py` lo avisa y `/gw-update` lo arregla. Un valor explícito en `gw.json` manda siempre. `config.py` es el único que lo resuelve (con `--rev`, mira el commit pedido).


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
  órdenes de `check` y `checkWrapper`; se apunta en `<directorio común de git>/gw-check-green` (los worktrees
  enlazados la comparten), caduca a las 24 h y guarda las últimas 50. Si la clave está, el `pre-push` dice `check
  already green on this tree…` y se salta el `check` (los `relatedTests` corren igual); si no, corre el `check` y, en
  verde, lo apunta (si corrió en la propia copia, solo si la dejó limpia). Quien lo apunta antes es `bash
  .claude/gw/scripts/check.sh` (`scripts/check.sh` en este repo): corre el `check` sobre la copia de trabajo y, si
  pasa y el árbol (lo que commitearía `git add -A`) no cambió durante la ejecución, apunta el verde; así la subida no
  lo repite. Al final imprime un resumen (cada orden, `ok`/`FAILED` y segundos); la salida de las órdenes sale en
  vivo, como siempre. Con `--quiet` (`-q`, o `GW_CHECK_QUIET=1`/`true`/`yes`) la salida va entera a `<git
  dir>/gw-check.log` (`GW_CHECK_LOG` cambia la ruta; una relativa cuenta desde el directorio actual y no puede caer
  dentro de la copia de trabajo, salvo ignorada por git) y solo se muestran, de la orden que falla, las últimas
  `GW_CHECK_TAIL` líneas (40) y la ruta del registro. Un `check` pasado a mano (p. ej. `bash tests/check.sh`) no
  apunta nada. Límites: una subida a la rama protegida nunca lee ni escribe la caché; no se apunta nada con entradas
  `assume-unchanged` o `skip-worktree` (sparse checkout) ni con un submódulo con cambios; cualquier fallo de la caché
  solo significa que el `check` corre; `check.sh` corre con los archivos ignorados de la copia de trabajo (`.env`,
  generados), mientras que antes una subida con la copia sucia comprobaba en un worktree limpio. `GW_CHECK_CACHE=0` la
  desactiva (`GW_CHECK_CACHE=0 git push` corre el `check` aunque esté apuntado).
- **`pushToProtected`** dice cómo entra hoy el código en la rama protegida. Un push directo que trae código pide
  siempre la marca en el `pre-push`, con `direct` y con `pr`; con `pr`, además, el gancho de PR la pide al crear o
  fusionar el pull request. El config se lee del commit que se sube, no de la copia de trabajo; para la rama
  protegida, `content` y `reviewMark` salen de su punta remota (de lo que se sube solo si aún no tiene config, con
  un aviso), y la rama es protegida si lo dice cualquiera de las dos o la copia de trabajo: un commit no puede
  relajar la regla que lo juzga.
- **`content` y la marca.** Un cambio que solo toca archivos de `content` no necesita revisión; cualquier otro, sí.
  `reviewed.sh` escribe en `reviewMark` el commit revisado y la marca debe ser antecesora de lo que se sube y no tener
  código después. Antes de marcar avisa (sin bloquear) de los archivos de código cambiados desde la marca anterior (o
  desde la bifurcación de la rama protegida, si no hay marca válida), para que los arreglos posteriores a la revisión no
  lleguen sin revisar; solo cuenta lo que cambió la propia rama, no lo que entró al fusionar la rama protegida.
  `.claude/gw.json`, `.claude/settings.json`, `.claude/gw/` y `.githooks/` son siempre código, diga
  lo que diga `content`. Para ver cómo se clasifica una ruta y por qué:
  `bash .claude/gw/scripts/is-code.sh --explain <ruta>...`.
- **`logRows`** va con la plantilla de bitácora de filas (`| **Tarea en curso · \`rama\`** | … |`); el push comprueba
  que cada rama escribe solo en su fila, que toda fila «Tarea en curso» lleva su rama y que cada tarea cerrada en el
  plan consta en «Hecho»: tachada allí, o nombrada en una línea que empieza por fecha (un punto sin tachar no basta).
  Esta última también la mira el `pre-commit`, sobre la bitácora preparada, para que el cierre se apunte en el mismo
  commit (y no con un `--amend` antes del push). Con `plan`, el push también rechaza un id de tarea que la rama da de
  alta y `origin/<protectedBranch>` usa para otra tarea (o un merge nuevo que dejó las dos con el mismo id), y avisa
  si choca con otra rama remota (`handoff.py clash`); el `pre-commit` de un merge con conflictos lo mira antes.
- Tras actualizar el flujo, sube `version` a mano (`/gw-update` lo hace): ese número es lo que `doctor.py`
  compara con las cabeceras copiadas.
- `schemaVersion` no es la versión del flujo, sino la del formato de `gw.json`, y solo sube cuando cambia su forma.
  Un proyecto viejo nunca se rompe en silencio: `config.py` migra en memoria un `schemaVersion` más antiguo que el
  del flujo (o ausente, que vale 0), de modo que todo lector ve la forma actual, también al leer el config de otro
  commit (`--rev`); `doctor.py` avisa y `/gw-update` (`apply.py`) escribe la migración en el archivo, en una sola
  escritura junto con los cambios de rutas, y `apply.py --check` la cuenta como pendiente. Uno **más nuevo** que el
  del flujo falla cerrado (salida 2) en todos los lectores: hay que actualizar el flujo (`/gw-update`, o
  `git -C <flujo> pull --ff-only`). Las migraciones están en `MIGRATIONS` de `scripts/config.py`.

## Notas personales

Si tienes notas que deben llegar a todos los proyectos donde aplicas el flujo, guárdalas **fuera de cualquier
repo**, en `~/.claude/gw/notas/` (otra carpeta con la variable de entorno `GW_PERSONAL_NOTES`). `apply.py` las
lleva a `<proyecto>/.claude/gw/<nombre>`:

- Solo archivos normales directamente en esa carpeta, con nombre `[A-Za-z0-9][A-Za-z0-9._-]*`; no se miran
  subcarpetas, enlaces simbólicos ni archivos ocultos. Si la carpeta no existe, no pasa nada y no se dice nada.
- Si la nota falta en el proyecto, se crea (y se avisa como «personal note»). Si es idéntica, nada. Si **difiere**,
  nunca se sobrescribe ni se deja un `.gw-new` (el proyecto puede haberla adaptado a propósito): se imprime una
  línea con `diff <origen> <destino>` en cada ejecución. `--check` **no falla** ni por una nota que falta (solo dice
  «would create personal note …») ni por una que difiere.
- Una nota se salta con un `WARNING` y la orden de renombrarla cuando su nombre acaba en `.gw-new` (`doctor.py` lo
  toma por una propuesta pendiente), cuando es el de un archivo del flujo en `.claude/gw/` (se compara sin mirar
  mayúsculas y aunque ese archivo no esté instalado: `gw-opt-tokens.md`, `gw-opt-ai.md`, `gw-scout-updates.md`, `scripts`,
  `schema`…) o cuando su destino no es un archivo normal. Una carpeta de notas ilegible o que es un archivo, y una
  nota que no se puede leer, también avisan (una carpeta ausente, no).
- Nunca se aplican al propio repo del flujo: nada personal va a él. `--no-personal-notes` las salta en una
  ejecución. Una `GW_PERSONAL_NOTES` relativa se resuelve desde la carpeta donde se lanza.
