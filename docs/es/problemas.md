# Problemas conocidos

> [English](../en/troubleshooting.md)

Qué hacer cuando algo del flujo no funciona. Los mensajes de los scripts salen en inglés y terminan con la orden que
arregla el fallo; aquí están agrupados por origen para encontrarlos por lo que se ve. Para empezar, casi siempre:

```bash
python3 .claude/gw/scripts/doctor.py
```

## Ganchos de Claude Code

| Síntoma | Causa | Arreglo |
|---|---|---|
| Un gancho no se ejecuta | JSON inválido en `.claude/settings.json`, evento o matcher mal escrito (distinguen mayúsculas: `bash` ≠ `Bash`), archivo de ajustes equivocado, sesión sin reiniciar | `/hooks` muestra lo cargado; `python3 -m json.tool .claude/settings.json`; reinicia la sesión |
| «No pasa nada» con salida 0 | Un gancho que sale con 0 y sin texto no se ve ni aprueba ni bloquea | Para bloquear, salida 2 con el motivo en `stderr` (como hacen los del flujo); para depurar, escribe a un log |
| Un gancho no bloquea | Está en `PostToolUse` o `SessionStart`, que no pueden bloquear | Ponlo en `PreToolUse` |
| En la nube no corren los ganchos del proyecto | La sesión tiene **varios repos**: no carga los ganchos de `.claude/settings.json` de ninguno | Una sesión, un repo; si hay que mezclar, ejecuta a mano lo que haría el gancho (ver más abajo) |
| En la nube no aparece el plugin | La nube ignora `extraKnownMarketplaces` y `enabledPlugins` del repo | Por eso el flujo se **copia** en el repo (`aplicar.py`), sin depender del plugin |
| Marketplace privado falla en local | Sin credencial de git no interactiva | `gh auth login && gh auth setup-git`, o SSH con agente |
| El script no encuentra el repo | La nube arranca en `/home/user`; ni `$CLAUDE_PROJECT_DIR` ni el directorio actual son la raíz | Los scripts del flujo ya sacan la raíz de su ruta o de `git rev-parse --show-toplevel`; los tuyos, también |

## `doctor.py`: cada `FAIL` y `WARN`

| Comprobación | Qué dice | Arreglo |
|---|---|---|
| `config` (FAIL) | `.claude/gw.json` falta, no es JSON o no cumple el esquema (clave desconocida, vacía…) | `python3 .claude/gw/scripts/config.py validate` dice la línea; claves en [config](config.md); si falta, aplica el flujo ([aplicar](aplicar.md)) |
| `hooks-path` (FAIL) | `core.hooksPath` sin poner: los ganchos de git del flujo no corren | `git config core.hooksPath .githooks` |
| `hooks-path` (WARN) | Lo usa otro gestor (husky, lefthook…): los ganchos del flujo solo corren si se encadenan | Añade a `pre-push` y `pre-commit` del gestor: `"$(git rev-parse --show-toplevel)/.githooks/<hook>" "$@" \|\| exit 1` |
| `githook pre-push` / `pre-commit` (FAIL) | Falta el archivo o no es ejecutable | `/gw-update`; o `chmod +x .githooks/<hook>` (en Windows, `git update-index --chmod=+x .githooks/<hook>`) |
| `githook …` (WARN) | Versión distinta de la de `.claude/gw.json` | `/gw-update` |
| `log` (FAIL) | La bitácora no existe, o no tiene línea de «Siguiente paso»/«Next step» | Créala con `/gw-update`; añade la línea al archivo que dice `log` |
| `log` (OK/FAIL) | «Siguientes pasos» / «Next steps» en plural también cuenta como línea de siguiente paso | — |
| `glossary` (WARN) | El mismo `**Término**:` aparece dos veces en `GLOSSARY.md` | Fusiona las entradas en una |
| `ignored` (FAIL) | Git ignora un archivo del flujo, o el de `reviewMark`: el commit lo dejaría fuera | Añade `!<ruta>` a `.gitignore` y comprueba `git check-ignore -v <ruta>` |
| `settings <evento>` (WARN) | Una orden de gancho ejecuta un script del flujo (por su cabecera `# galivelop-workflow v…`) desde fuera de `.claude/gw/scripts/`; un script propio con el mismo nombre no avisa | Borra esa entrada de `.claude/settings.json` |
| `check command` (FAIL) | La primera palabra de una orden de `check` no está en el `PATH` ni es un archivo del repo | Instala esa herramienta o corrige `check` en `.claude/gw.json` |
| `install command` (WARN) | Lo mismo para `install` | Igual |
| `ci` (WARN) | No hay ningún workflow en `.github/workflows` | `mkdir -p .github/workflows && cp <flujo>/templates/github/comprobar.yml .github/workflows/` |
| `settings` (FAIL) | Falta `.claude/settings.json` o es JSON inválido | `/gw-update`; corrígelo y comprueba con `python3 -m json.tool` |
| `settings SessionStart` (FAIL) | Una entrada sin `matcher` corre en cada arranque, reanudación, `clear` y `compact`; o una con `compact` ejecuta algo que no es `recuperar.py --estado` | Dale `"matcher": "startup\|resume\|clear"`; mueve esa orden a una entrada sin `compact` |
| `settings <evento>` (FAIL) | Una orden de gancho apunta a un archivo que no existe | `/gw-update` restaura los scripts; o corrige la orden |
| `settings PreToolUse` (FAIL) | Falta el gancho que guarda crear y fusionar PR (`revision-antes-de-main.sh`) | Añádelo desde `templates/claude/settings.json` (`/gw-update`) |
| `agents` (FAIL) | No hay `AGENTS.md` ni `CLAUDE.md` | `/gw-init` |
| `agents` (WARN) | Ninguno menciona `orchestrate-dealer`: la sesión podría no repartir a subagentes | Añade a `AGENTS.md`: «El trabajo de más de un paso se reparte a subagentes (skill `orchestrate-dealer`); la sesión principal planea, decide y revisa.» |
| `skills` (WARN) | Skills copiadas con versión distinta de la de `gw.json` | `/gw-update` |
| `session` (WARN) | La última sesión se abrió fuera del repo y puede no haber cargado `.claude/settings.json` | Reabre Claude Code desde el repo: `cd <repo> && claude` |
| `compaction` (WARN) | Sesión en la nube sin `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en su entorno: arranca en `/home/user` (y a menudo con varios repos), no carga `.claude/settings.json` y el contexto crece sin tope | Añade `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` a las variables del entorno de la nube (menú del entorno → Edit); las sesiones nuevas lo cogen |

## Al subir (`pre-push`)

El `pre-push` dice qué commits sube, o que no hay nada nuevo (¿se te olvidó `git commit`?). Si rechaza el push,
el último renglón es la orden que lo arregla.

| Mensaje | Causa | Arreglo |
|---|---|---|
| `check failed on <sha>: '<orden>'` | Falla una orden de `check` **en el commit que se sube** (no en tu copia de trabajo); el log completo está en la ruta que imprime | Reprodúcelo con la misma orden, arregla, commit y push; `--no-verify` solo para un commit `WIP:` en rojo |
| `the push adds *.rej / *.orig leftovers` | Restos de un parche o una fusión | `git rm -- <archivo> && git commit` |
| `the push has conflict markers` | Quedaron `<<<<<<<` o `>>>>>>>` en lo que se sube | Resuelve y `git commit -a` |
| `the pushed commit has no review mark` / `the review mark … is not an ancestor` / `code changed after the review mark` | Subida directa a la rama protegida con código sin revisar | `/code-review` del diff contra `origin/<rama protegida>`, sube los arreglos, luego `bash .claude/gw/scripts/revisado.sh && git push` |
| `…this clone is shallow…` / `is not a commit in this clone` | Clon superficial (típico en la nube): la marca o la rama remota quedan fuera de la historia | `git fetch --deepen=200 origin <rama>` y repite |
| `the remote <rama> is at <sha>, which this clone does not have` | Falta el último commit de la rama protegida | La orden de `git fetch` que imprime |
| `cannot read '<clave>' from .claude/gw.json` | Config inválida | `python3 .claude/gw/scripts/config.py validate` |
| `the workflow scripts are missing` | Falta `.claude/gw/scripts/` | `/gw-update` |
| `prepush-ramas.sh refused the push` | Con `logRows`: una fila de la bitácora ajena, demasiado larga, o tareas cerradas sin pasar a «Hecho» | Lo que imprime; una fila compartida: `BITACORA_COMPARTIDA=1 git push` |
| `the related tests failed` | Fallan los `relatedTests` | Arréglalos o ajusta la clave |
| El `pre-push` no se ejecuta | `core.hooksPath` sin poner o de otro gestor; sin bit de ejecución (Windows) | `git config core.hooksPath .githooks`; `git update-index --chmod=+x .githooks/pre-push` |

## Crear o fusionar un PR (`revision-antes-de-main.sh`)

Es el gancho `PreToolUse` que guarda `create_pull_request`, `merge_pull_request` y `gh pr create|merge`. Falla
**cerrado**: si no puede comprobar, bloquea y dice por qué. Un push directo a la rama protegida lo guarda el `pre-push`, en los dos modos de `pushToProtected`.

| Bloqueo | Causa | Arreglo |
|---|---|---|
| `Blocked: … has no review mark` / `… not an ancestor` / `code changed after the review mark` | El PR trae código que no cubre la marca de revisión del **mismo commit** | `/code-review` del diff, sube arreglos, `bash .claude/gw/scripts/revisado.sh`, `git push` |
| `Blocked: CI of PR #N is not green` / `could not verify CI` | El CI no pasó o no se pudo leer | Espera o arregla el CI; autenticación: `gh auth login` o `export GITHUB_TOKEN=…` |
| `cannot read PR #N` / `cannot query origin` | Sin red o sin credencial | Autentícate y repite; se bloquea porque no pudo comprobar |
| `the PR head … is not in this clone` | Clon superficial o rama sin traer | `git fetch --deepen=200 origin <rama>` |
| `no open PR for <rama>` / `without a PR number` | Fusionar sin número ni PR abierto de la rama | Pasa el número: `gh pr merge <número>` |
| `requireRetro is on and the branch adds no retro-*.md…` (de `revisado.sh`) | Con `requireRetro`, falta una retro con decisión de la persona | `/retro`, presenta, aplica lo aprobado, anota el estado y repite `revisado.sh` |
| `revisado: the tree has uncommitted…` / `HEAD is not what origin/<rama> has` / `the branch does not include the latest origin/<protegida>` | La marca solo se escribe sobre lo ya subido y al día | Commit y push; `git merge origin/<protegida>`; revisa de nuevo y marca |
| `the check could not run… Install python3 3.8+` | Falta `python3` | Instala Python 3.8 o superior |

**Sesión de varios repos (nube).** No carga los ganchos del proyecto. Antes de crear o fusionar un PR a la rama
protegida, comprueba a mano lo que ese gancho comprobaría: la marca de `revisado.sh` del mismo commit y el CI en
verde, y `git config core.hooksPath .githooks` antes del primer commit.

## Sesión abierta fuera del repo

Si Claude Code se abre en otra carpeta (la que contiene varios repos, la de usuario), no carga el
`.claude/settings.json` del proyecto: ni el tope de compactación, ni el gancho de inicio, ni el guardián de PR.
`doctor.py` lo detecta («the newest session transcript is in …»); `session-start.sh` solo avisa («this session was
started in …») cuando se carga, es decir, cuando la sesión se abre en una subcarpeta del repo, no fuera de él.
Arreglo: reabrir desde el repo (`cd <repo> && claude`). Mientras tanto: `git config core.hooksPath .githooks` y
comprobación manual antes de subir a la rama protegida.

Abierta fuera del repo, el aviso de `session-start.sh` **no puede salir**, porque el gancho tampoco se carga; la
comprobación fiable es `python3 .claude/gw/scripts/doctor.py`. Sin compactación, el contexto crece sin tope y es casi todo el
gasto: al cerrar cada fase, bitácora al día y `/clear`.

**En la nube** la sesión siempre arranca en `/home/user`, así que reabrir desde el repo no es posible: el tope de
compactación va en las variables del entorno de la nube (`CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`; `doctor.py` avisa
si falta), y tras una compactación se corre a mano `python3 .claude/gw/scripts/recuperar.py --estado`.

## Skills con el mismo nombre en varios repos de la sesión

Si se añaden a la sesión otros repos y se registran como raíz (en la nube, `register_repo_root`), sus
`.claude/skills/` entran también, y una skill homónima de otro repo (`retro`, `selector`…) puede tapar la del
proyecto. Arreglo: los repos que solo se leen **no se registran**; basta clonarlos y leerlos con un subagente. Si ya
están registrados, invoca la skill del proyecto comprobando la ruta que muestra al cargarse (`Base directory`).

Al aplicar el flujo en la nube pasa lo mismo con el repo del flujo: clónalo con `git clone` si es público, o, si se
añade con `add_repo`, no lo registres como raíz y comprueba con `ls` la ruta que devuelve (puede venir en minúsculas
y no existir).

## Modo automático de Claude Code

El clasificador del modo automático puede pedir permiso, o rechazar, al editar `.claude/settings.json`,
`.claude/gw/scripts/` y `.githooks/`: justo lo que escriben `/gw-init` y `/gw-update`, así que el fallo sale a mitad de la
aplicación. `aplicar.py` imprime un aviso («Claude Code's auto mode may ask for permission…»).

- **Pide permiso a la persona antes** de ejecutar `aplicar.py`, o que la persona lo ejecute en su terminal:
  `python3 <flujo>/scripts/aplicar.py <proyecto>`.
- Tras una llamada rechazada o interrumpida, `git status` y `git diff` antes de repetirla: puede haber escrito la mitad.
- Es idempotente: repetirlo completa lo que falte.

## Gestores de ganchos, clones y sistemas

| Síntoma | Causa | Arreglo |
|---|---|---|
| Aviso «another hook manager installed hooks» al empezar | Hay ganchos propios en `.git/hooks` o `core.hooksPath` de otro gestor | El aviso trae la línea para encadenar; ver [aplicar](aplicar.md#proyectos-existentes) |
| «La marca no es antecesora» sin motivo | Clon superficial | `git fetch --deepen=200 origin <rama>` |
| El script falla solo en macOS | La `bash` de macOS es la 3.2: sin `mapfile` ni arrays asociativos | Escribir para bash 3.2 (el CI corre también en macOS) |
| Fallos raros en Windows | Finales de línea CRLF en scripts; enlaces simbólicos | `.gitattributes` con `*.sh text eol=lf` (y `*.py`, `.githooks/*`); usa **Git Bash o WSL**, no `cmd` ni PowerShell; sin enlaces simbólicos |
| `CLAUDE.md` existe y `AGENTS.md` no se lee | Claude solo lee `AGENTS.md` si no hay `CLAUDE.md` | `@AGENTS.md` en `CLAUDE.md` (lo hace la plantilla) |
| Fallan las órdenes de `install` al empezar | `session-start.sh` las corre solo en la nube y si cambió el lockfile | El aviso da el log y la orden para correrlas a mano |
| `aplicar.py --check` sale 1 | La copia difiere del flujo, hay un `*.gw-nuevo` o un archivo que el flujo ya no tiene | Mira lo impreso; `/gw-update`; resuelve y borra los `*.gw-nuevo` |

Si un fallo no está aquí, anótalo: `/retro` lo recoge en su sección «Para Galivelop-workflow» y llega a este archivo
([patrones](patrones.md#recoger-mejoras-de-vuelta)).
