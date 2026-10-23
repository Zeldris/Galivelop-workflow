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
| `requireRetro` | `revisado.sh` exige una `retro` con la decisión de la persona en la rama antes de marcar; lee todo el párrafo de `**Estado:**` y acepta aplicada, rechazada, aplazada, decidida o aprobada; `revisado.sh --footer "Siguiente: …"` añade esa línea al commit de la marca; los ficheros sin seguimiento no cuentan como cambios | `false` (también en `templates/gw.json`; `--init --require-retro true` lo activa) | `true` | `revisado.sh`, skill `retro` |
| `roadmap` | Reservada para el módulo opcional de hitos; ningún script la lee todavía | `false` | `false` | (nadie aún) |
| `selector` | `{ "cases": [ { "case", "skill", "sessionModel", "subagentModel" } ] }`: filas propias del proyecto para el `selector` | sin filas | `{"cases": [{"case": "Migración de datos", "skill": "orchestrate-dealer", "sessionModel": "Opus"}]}` | skill `selector` |
| `logSections` | Encabezados de las secciones de la bitácora que `recuperar.py --estado` devuelve tras compactar o `/clear` (sin `logRows`) | `[]`: la primera sección y la que se llame «Pendiente»/«Pending» | `["Estado actual", "Pendiente"]` | `recuperar.py` |
| `designReferences` | Productos, marcos o estándares con los que se contrasta cada propuesta de diseño | `[]` | `["WCAG 2.2", "Material Design 3"]` | skills `grilling` y `selector` |
| `protectedPaths` | Prefijos de ruta que un agente (`CLAUDECODE=1`) no puede commitear: borradores de otras personas | `[]` | `["docs/borradores/"]` | `.githooks/pre-commit` |
| `staleRefs` | Expresiones (sin distinguir mayúsculas) que no deben aparecer en `docs/` ni en los README: una tarea renombrada, una fase borrada | `[]` | `["fase 9 \\(vieja\\)"]` | `enlaces-md.py` |
| `checkWrapper` | Prefijo literal de cada orden de `check` y de `relatedTests` (p. ej. `docker compose run --rm app`); con `cwd` en una entrada se envuelve `bash -c 'cd <cwd> && <orden>'` | `""` (sin prefijo) | `"docker compose run --rm app"` | `pre-push`, `tests-relacionados.sh` |
| `relatedTests` | `{ "fast": [...], "slow": [...] }`: las pruebas de lo que cambia. Cada entrada es una orden (texto) o `{ "command", "paths", "cwd" }`: `paths` es una expresión que filtra los archivos cambiados y `cwd` una carpeta desde la que corre la orden (`{files}` va relativo a ella). `fast` corre en cada push; `slow`, solo si algún archivo cambiado (de su ámbito) sigue existiendo; `{files}` se sustituye por los archivos cambiados | sin órdenes | `{"fast": [{"command": "npx vitest related {files}", "paths": "\\.tsx?$", "cwd": "web"}], "slow": []}` | `tests-relacionados.sh` (lo llama el `pre-push`) |
| `worktreeLinks` | Rutas (relativas, sin `..`) de la copia principal que el `pre-push` enlaza en el worktree temporal donde corre el `check`; las que no existen se omiten y nunca se pisa una ruta del commit | `["node_modules", ".venv"]` | `["node_modules", "backend/node_modules", ".env"]` | `pre-push` |
| `plan` | Archivos o carpetas de plan o roadmap donde las tareas se tachan o marcan | `[]` | `["docs/producto/21-roadmap.md"]` | `bitacora.py` |
| `taskId` | Expresión de los identificadores de tarea | `[A-Z]{2,5}-\\d+` | `"(INS\|FLU)-\\d+"` (los grupos con captura se tratan como sin captura) | `bitacora.py` |

## Notas

- **`check` es una lista de órdenes**, no un script único: cada una se ejecuta con `bash -c` en la raíz del commit que
  se sube. Una que no existe la detecta `doctor.py` antes de que falle un push. El `pre-push` les pasa
  `GW_PUSH_PROTECTED=true` cuando la subida va a la rama protegida (`false` si no; fuera del gancho, sin definir): así
  una orden puede correr solo antes de `main`, p. ej. `[ "${GW_PUSH_PROTECTED:-}" != true ] || <orden>`.
- **El `check` corre en un worktree temporal** cuando la copia de trabajo no está limpia (o la subida no es lo que hay
  en ella): vive en `<git-dir común>/gw-pre-push/wt.XXXXXX.d`, nunca en `$TMPDIR`, y se borra en toda salida (también
  con Ctrl-C o `kill`). Si un push muere sin poder limpiar, el siguiente borra los worktrees huérfanos; dos pushes a
  la vez no se pisan. Lo enlazado desde la copia principal lo dice `worktreeLinks`. El registro de una orden fallida
  se conserva (`full log: <ruta>`); si pasa, se borra.
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
