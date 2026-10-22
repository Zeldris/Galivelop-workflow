# Aplicar el flujo a un proyecto (guía para el agente)

> [English](../en/apply.md)

Esta es la guía que sigue un agente de IA para aplicar Galivelop-workflow a un proyecto, **nuevo** (lo recomendado) o
**existente** (sección propia, más abajo). Lo que exige criterio lo decide el agente con la persona; lo demás lo hace
un script (`scripts/aplicar.py`) y lo comprueba otro (`scripts/doctor.py`). Si la sesión usa Claude Code, la skill
`/gw-init` es un envoltorio fino de esta guía.

El resultado vive **en el repo del proyecto** (scripts, skills, ganchos, plantillas), así que funciona también en
sesiones en la nube, que no cargan plugins declarados en el repo.

## 0. Antes de empezar

1. El proyecto está clonado y es un repo git (`git init` si es nuevo).
2. Este repo, el del flujo, está clonado junto al proyecto, o la persona lo ha añadido a la sesión. Desde aquí se
   llama `<flujo>`.
3. **La sesión está abierta con el proyecto como carpeta de trabajo.** Abierta en otra carpeta no carga
   `.claude/settings.json` (ni los ganchos). Si no es así, pide a la persona que la reabra desde el proyecto.
4. `git status` limpio en el proyecto, o la persona sabe qué hay sin subir. Los archivos generados (`__pycache__/`,
   `node_modules/`, `target/`, salidas de compilación) están en `.gitignore`: correr el check no debe ensuciar el árbol.
5. git tiene identidad para los commits (`git config user.name` y `user.email`); ponla si la máquina es nueva.
6. `python3` 3.8 o superior, `git` y `bash` disponibles (en Windows, Git Bash o WSL: ver
   [problemas](problemas.md)).

Criterio de fin: puedes ejecutar `python3 <flujo>/scripts/aplicar.py --help` y `git -C <proyecto> status` sin error.

## 1. Decidir lo que exige criterio

Reúne estos datos **antes** de ejecutar nada. Todo va a `.claude/gw.json` (cada clave, en [config](config.md)).

| Dato | Cómo se decide |
|---|---|
| Idioma (`language`: `es` o `en`) | El de la persona y el de la documentación del proyecto; manda sobre las plantillas y las respuestas |
| Ruta de la bitácora (`log`) | Por defecto `docs/traspaso.md` (es) o `docs/handoff.md` (en); si el proyecto ya tiene una, esa |
| Orden de instalación (`install`) | Se infiere (abajo); vacío si no hay dependencias |
| Orden(es) de comprobación (`check`) | Se infiere (abajo); **al menos una**, es lo que corre el `pre-push` y el CI |
| Rama protegida (`protectedBranch`) | La que despliega o publica: `git symbolic-ref --short refs/remotes/origin/HEAD`; si falla (remoto nuevo o local), `git remote show origin \| sed -n 's/.*HEAD branch: //p'`; si no, pregunta a la persona |
| Subir a ella (`pushToProtected`) | `direct` si se hace push directo; `pr` si solo entra por pull request |
| Contenido (`content`) | Expresiones regulares de lo que **no** es código y no necesita `/code-review`: docs, datos, textos |
| Retro obligatoria (`requireRetro`) | Pregunta: «¿`/retro` en cada subida a la rama protegida, o solo en cambios grandes?». En cada subida: `--require-retro true` (`revisado.sh` no marca sin una retro decidida en la rama); si no, `false` |
| Idiomas visibles y referencias de diseño (`visibleLanguages`, `designReferences`) | Solo si el proyecto los tiene: `--visible-language` y `--design-reference`, una bandera por valor |
| Skills opcionales | `opt-ai` (modelos de IA locales) y `scout-updates` (revisar actualizaciones); solo si la persona las pide |

**Inferir `install` y `check`.** Mira el archivo de construcción y propón órdenes que existan de verdad:

| Archivo | `install` | `check` (la más completa que haya) |
|---|---|---|
| `package.json` | `npm ci` (o `pnpm i --frozen-lockfile`, `yarn --frozen-lockfile` según el lockfile) | el script `check`, o `lint` + `test`: `npm run check` |
| `pyproject.toml` | `pip install -e .[dev]` o `uv sync` | `pytest`, más `ruff check .` si está configurado |
| `Cargo.toml` | (vacío) | `cargo clippy -- -D warnings` y `cargo test` |
| `pom.xml` | (vacío) | `mvn -q verify` |
| `go.mod` | (vacío) | `go vet ./...` y `go test ./...` |
| `Makefile` | (vacío) | `make check` o `make test`, si el objetivo existe (`make -n check`) |

Reglas:

- Lee los scripts del archivo de construcción y **ejecuta la orden de `check` una vez** para ver que funciona y cuánto
  tarda. Una orden que no existe o no pasa se detecta tarde y estorba en cada push.
- **Si hay duda, pregunta a la persona**; no inventes una orden. Con varios candidatos, ofrécelos numerados.
- Un proyecto sin tests: `check` puede ser un linter o un `bash -n`; dilo y apúntalo como deuda en la bitácora.
- `content` se propone leyendo el árbol: `^docs/`, `^public/`… (en JSON, la barra se escribe doble). **Lo que sea
  `content` sube sin marca:** no pongas ahí scripts ni lo que un agente lee como instrucciones (un `AGENTS.md` en una
  subcarpeta, una plantilla de prompt). Cuando dudes, deja menos: lo que cuenta como código se revisa. Los `.md` de
  las skills copiadas (`^\.claude/skills/.*\.md$`) se revisan en el repo del flujo y están en el `content` por
  defecto de la plantilla; déjalos (sus scripts, no).
  Los scripts de `.claude/gw/` **no** van en `content`: son los ganchos que guardan la rama, y un cambio en ellos se
  revisa como cualquier código.

Criterio de fin: tienes una respuesta (o una pregunta hecha a la persona) por cada fila de la tabla, y `check` se
ha ejecutado una vez.

## 2. Aplicar

Desde la raíz del proyecto o indicándola; las banderas salen de `--help`. `--check-command`, `--install` y
`--content` **se repiten**: una bandera por orden o regex (dos checks = dos `--check-command`). Sin `--content`, vale
el de la plantilla (`^docs/`, los `.md` de la raíz que son documentación y los `.md` de las skills copiadas):

```bash
python3 <flujo>/scripts/aplicar.py <proyecto> --dry-run --init --language es \
  --log docs/traspaso.md --install "npm ci" --check-command "npm run lint" --check-command "npm test" \
  --protected-branch main --push-to-protected direct
```

`--dry-run` imprime el plan sin escribir. Cuando sea el que quieres, repite la misma orden **sin** `--dry-run`.

Opciones: `--review-mark RUTA` (por defecto `docs/registros/revisado.txt`), `--with opt-ai` y `--with scout-updates`.
`--init` solo escribe `.claude/gw.json` si no existe, lo valida y aplica como siempre.

Qué hace (el detalle completo, en `--help`): copia `scripts/` a `.claude/gw/scripts/`, las skills a
`.claude/skills/`, los ganchos de git a `.githooks/`, el CI a `.github/workflows/comprobar.yml`; **fusiona** en
`.claude/settings.json` los ganchos de Claude Code y `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` sin quitar nada; crea
`AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, `GLOSSARY.md` y la bitácora si faltan; y pone `core.hooksPath=.githooks` si
nadie más lo usa. **Nunca hace commit.** Es idempotente: ejecutarlo dos veces no cambia nada.

**Modo automático de Claude Code.** El clasificador del modo automático puede pedir permiso al editar
`.claude/settings.json`, `.claude/gw/scripts/` y `.githooks/`, y el fallo aparece a mitad de la aplicación. `aplicar.py`
lo avisa justo antes de escribirlos. **Pide permiso a la persona antes** de lanzarlo (o que lo lance ella en su
terminal con la misma orden) en vez de reintentar a ciegas; tras un rechazo, `git status` y `git diff` antes de
repetir.

Criterio de fin: la orden termina sin error y sabes qué se creó, qué se actualizó y qué quedó como `*.gw-nuevo`.

## 3. Revisar cada `*.gw-nuevo` con la persona

Cuando un archivo ya existe y es del proyecto (un `AGENTS.md`, un `CLAUDE.md` sin la marca
`galivelop-workflow`), `aplicar.py` **no lo toca**: deja al lado `<archivo>.gw-nuevo` con la propuesta.

```bash
git -C <proyecto> ls-files --others --exclude-standard | grep '\.gw-nuevo$'
```

Para cada uno:

1. Muestra a la persona qué trae la propuesta que el archivo no tiene (`git diff --no-index <archivo> <archivo>.gw-nuevo`).
2. **`AGENTS.md` y `CLAUDE.md`: fusiona a mano**, bloque a bloque. Las reglas del proyecto se quedan; se añaden los
   bloques del flujo (inicio de sesión, relevos, comprobar, commits, ramas). `CLAUDE.md` acaba con `@AGENTS.md` más
   lo propio de Claude. Mantén la marca `<!-- galivelop-workflow vX.Y.Z -->` de la primera línea.
3. Otros archivos: acepta la propuesta entera (`mv <archivo>.gw-nuevo <archivo>`) solo si la persona lo confirma.
4. Borra el `.gw-nuevo` al terminar. `aplicar.py --check` lo cuenta como diferencia mientras exista.

Rellena también los huecos de la bitácora (como mínimo rama, fase y siguiente paso; el resto de secciones puede
quedarse como viene hasta que haya algo que escribir) y añade las reglas propias del proyecto en las secciones
«Reglas del proyecto» de `REVIEW.md` y `AGENTS.md` y sus términos en `GLOSSARY.md`: el flujo nunca vuelve a escribir
esos archivos.

**`REVIEW.md` y `GLOSSARY.md` que ya existían:** `aplicar.py` no los toca, pero imprime su diferencia con la plantilla
mientras no lleven la marca de la versión actual. Pasa a mano lo que les falte (por ejemplo, las reglas «bash 3.2»,
«traído de otro repo: contratos de este» e «idiomas visibles» de `REVIEW.md`) y pon en su primera línea
`<!-- galivelop-workflow vX.Y.Z -->`; desde entonces el diff ya no sale.

Criterio de fin: no queda ningún `*.gw-nuevo`, ni diff impreso de `REVIEW.md`/`GLOSSARY.md`, y la bitácora tiene una línea de siguiente paso.

## 4. Comprobar con `doctor.py`

```bash
python3 <proyecto>/.claude/gw/scripts/doctor.py
```

Imprime `OK`, `WARN` o `FAIL` por comprobación, y con cada problema la orden que lo arregla. Repite (arreglar,
volver a correr) hasta que **no quede ningún `FAIL`**; los `WARN` se explican a la persona (qué significa cada uno,
en [problemas](problemas.md)). Con `--json` sale legible por máquina.

Criterio de fin: `doctor.py` sale con código 0.

## 5. Commit y subida

`aplicar.py` terminó imprimiendo un commit sugerido:

```bash
git add -A && git commit -m "Flujo Galivelop-workflow v0.1.0" -m "Siguiente: <próximo paso concreto>"
```

Sustituye la última línea por el paso concreto de verdad (el que la bitácora declara) y añade las líneas de
atribución que pida el proyecto en el mismo bloque final. El commit ya pasa por el nuevo `pre-commit` (rechaza
secretos y, para agentes, las `protectedPaths`); si se para, lee su mensaje. Después, `git push -u origin <rama>`: el nuevo `pre-push`
corre el `check` sobre el commit que se sube; si falla, se arregla y se vuelve a subir (nunca con `--no-verify`, salvo
un `WIP:` en rojo).

Si el proyecto tiene CI, comprueba que el workflow `Comprobar` pasa. Node, Python y Java se instalan solos si están
`package.json`, `pyproject.toml`/`requirements*.txt` o `pom.xml`/`build.gradle*`; otra cadena de herramientas
(rust-toolchain…) hay que añadirla, como dice la cabecera de `comprobar.yml`.

Criterio de fin: el push ha subido, `doctor.py` sigue en verde y la bitácora dice lo que sigue.

## 6. Comprobar que la protección funciona

En la rama de trabajo, haz commit de un cambio pequeño de código e intenta subirlo directamente a la rama protegida,
en simulacro (el `pre-push` corre igual, no se sube nada aunque pasara, y el modo automático de Claude Code no lo
bloquea como bloquea la subida real a la rama protegida):

```bash
git push --dry-run origin HEAD:<protectedBranch>
```

Con cualquier `pushToProtected` **tiene que rechazarse**, con uno de estos dos motivos: «the pushed commit has no
review mark» (no hay marca) o «code changed after the review mark» (hay marca y código detrás). Con `pr`, la misma
comprobación ocurre además al crear o fusionar el pull request. Después quita el commit de prueba
(`git reset --hard HEAD~1`, solo si no se ha subido a ningún sitio). La entrada normal es `/code-review`, arreglos,
`bash .claude/gw/scripts/revisado.sh` y la subida.

Criterio de fin: el simulacro se rechazó por uno de esos dos motivos y el commit de prueba ya no está.

## Proyectos existentes

Lo anterior vale igual; estos son los puntos que cambian.

**Gestor de ganchos ya instalado (husky, lefthook, pre-commit…).** `aplicar.py` no pisa `core.hooksPath` si lo
usa otro, y `doctor.py` y el aviso de inicio de sesión lo dicen. **Se encadena, no se sobrescribe.** Añade como
última línea de `pre-push` y `pre-commit` del gestor (con `<hook>` el nombre del archivo):

```bash
"$(git rev-parse --show-toplevel)/.githooks/<hook>" "$@" || exit 1
```

El `pre-push` del flujo lee por la entrada estándar las líneas de referencias de git: si el gestor no las reenvía
(en lefthook, `use_stdin: true`), no verá qué se sube. Compruébalo con un push real: debe imprimir
`pre-push: pushing N commit(s)`.

**`CLAUDE.md` o `AGENTS.md` existentes.** Se fusionan a mano (paso 3). Si solo hay `CLAUDE.md` con lo propio de
Claude, deja ese texto y pasa las reglas compartidas a `AGENTS.md`. Si el proyecto ya tiene una regla distinta para
algo que el flujo dice (ramas, mensajes de commit), **gana la del proyecto**: se anota la diferencia en la fusión.

**Un check o lint en rojo al adoptar.** No bloquees el primer push ni lo apagues. Dos caminos:

1. Arreglarlo antes, como una tarea propia, si es pequeño.
2. Si es deuda grande, abre una **tarea de deuda** en la bitácora y haz que `check` revise **solo lo que cambia
   mientras esa tarea siga abierta**: p. ej. un script que corre el linter sobre
   `git diff --name-only origin/<rama protegida>...HEAD`. Al cerrar la deuda, `check` vuelve a revisar todo. Así lo
   nuevo ya sale limpio sin bloquear el resto.

**Una bitácora que ya existe.** Si el proyecto ya tiene una, ponla en `log` (es lo que lee todo el flujo) y añade
a mano lo que falte de la plantilla: estado actual con siguiente paso, hecho reciente, pendiente y cómo comprobar el
estado. `doctor.py` exige una línea de «Siguiente paso»/«Next step».

**CI existente.** `comprobar.yml` es un workflow más; si el proyecto ya corre su check, deja uno de los dos para no
duplicarlo, pero conserva el paso del `pre-commit` de la rama base sobre el PR.

**Rama protegida con varias personas.** El `pre-push` pide la marca a todo push directo con código; con
`pushToProtected: pr`, además, el gancho de `PreToolUse` la pide al crear y fusionar pull requests. Elige según cómo
entra el código ya hoy.

## Lo que el agente no hace

- No registra como raíz de la sesión los repos que solo lee (el del flujo incluido): sus skills homónimas taparían
  las del proyecto ([problemas](problemas.md)).
- No ejecuta `aplicar.py --update` ni sobrescribe archivos del proyecto sin que la persona lo pida.
- No inventa `install` ni `check`: si no puede ejecutarlo, pregunta.
- No hace commit ni push antes de pasar `doctor.py` sin `FAIL`.
- No sube a la rama protegida sin confirmación de la persona.
- No usa `git push --no-verify` ni `git config core.hooksPath` apuntando a otro sitio para saltarse un gancho.
- No borra archivos que el flujo avisa que ya no tiene: los informa a la persona.
- No modifica otros repos: el del flujo se lee, nunca se edita desde la sesión del proyecto.
- No copia el `.claude/settings.json` de otro proyecto: lo fusiona `aplicar.py`.
