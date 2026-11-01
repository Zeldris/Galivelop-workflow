# Referencias para el bloque D: Aider, Graphify, worktrees de Claude Code y convenciones de commits

Fecha: 2026-11-01. Investigación de solo lectura para `docs/diseno/README.md` (bloque D: git, entornos, releases,
tags en commits, trazabilidad). Lo marcado **[NC]** no se pudo confirmar. Nada se ha ejecutado ni instalado.

**Límite de acceso:** en esta sesión `aider.chat`, `conventionalcommits.org`, `semver.org` y `git-scm.com` no
resuelven (fuera de los dominios permitidos). Se ha leído lo mismo en su fuente primaria de GitHub (`raw.githubusercontent.com`:
fuentes de las páginas de aider, de la especificación de Conventional Commits, de semver y de git). Los resúmenes
salen de un modelo pequeño que lee la página, así que las citas literales son las que se marcan entre comillas.

## 1. Aider

### Commits
- Cada edición del modelo se commitea sola con mensaje descriptivo; si el archivo tenía cambios previos, primero
  commitea esos «con un mensaje descriptivo». `--no-auto-commits` lo apaga.
- El mensaje lo escribe el `--weak-model` a partir de los diffs y la conversación, por defecto en formato
  Conventional Commits; `--commit-prompt` cambia el prompt.
- Atribución: si el cambio es de aider, añade «(aider)» al nombre de autor y de committer; si solo commitea cambios
  sucios previos, solo al committer. Opciones: `--no-attribute-author`, `--no-attribute-committer`,
  `--attribute-commit-message-author` (prefijo «aider: »), `--attribute-commit-message-committer`,
  `--attribute-co-authored-by` (trailer `Co-authored-by`, que desactiva el sufijo salvo que se pida).
- Comandos: `/diff` (cambios desde el último mensaje), `/undo` (descarta el último commit de aider), `/commit`.
- Fuente: `aider/website/docs/git.md`.

### Diffs (formatos de edición)
- `whole` (archivo entero), `diff` (bloques SEARCH/REPLACE con marcas tipo conflicto de merge), `diff-fenced`
  (ruta dentro de la valla; para Gemini), `udiff` (diff unificado simplificado; reduce el «lazy coding» en la familia
  GPT-4 Turbo), `editor-diff`/`editor-whole` (modo architect: un modelo describe, otro edita). Aider elige el formato
  por modelo y `--edit-format` lo fuerza. No consta en la página el mapa completo modelo-formato **[NC]**.
- Fuente: `aider/website/docs/more/edit-formats.md`.

### Repo map
- Tree-sitter saca definiciones y referencias de cada archivo; un grafo (archivo = nodo, dependencia = arista) las
  ordena con «un algoritmo de ranking de grafos» y se envían solo las mejores que caben en `--map-tokens` (1k por
  defecto; crece si no hay archivos en el chat). Que el algoritmo sea PageRank no consta en estas páginas **[NC]**.
- Fuentes: `docs/repomap.md` y el post `_posts/2023-10-22-repomap.md`.

### Ideas para tags/trazabilidad (bloque D)
1. **Distinguir quién hizo el commit sin firmas de modelo.** Nuestra regla prohíbe `Co-Authored-By`/`Claude-Session`
   (`agentSignatures: false`). Aider resuelve la misma necesidad con un marcador opcional y apagable en autor/committer
   o en trailer. Si se quiere saber qué commits fueron de un subagente, mejor un trailer propio (`Agent: dealer`) o
   la rama (`worktree-agent-*`) que una firma; decisión del usuario, no dato.
2. **Mensaje estructurado y generado barato:** un modelo débil redacta el mensaje desde el diff. Encaja con
   «lo mecánico a modelos baratos»; el flujo ya exige `Siguiente:` en la última línea, que se podría seguir
   exigiendo con un prompt fijo y comprobando con `commit-msg`.
3. **Commit previo de lo sucio:** aider separa «lo que había» de «lo que hizo él». Análogo útil para los
   relevos: un commit `WIP:` aparte antes de empezar un encargo.
4. **`/undo` = un commit por edición.** Con un commit por cambio es trivial revertir; nuestro `fusionar.sh` hace
   `merge --no-ff` y deja `git reset --hard HEAD^1` como deshacer; coherente.
5. **Repo map ≈ nuestro `mapa-agente.md`, pero calculado.** Ver sección 2.

## 2. Graphify (Graphify-Labs/graphify)

- **Qué es:** skill `/graphify` que convierte un proyecto (código, docs, esquemas SQL, configs, PDF, imágenes,
  audio/vídeo) en un grafo de conocimiento consultable. Licencia Apache-2.0 y MIT. Muy extendido (~140k estrellas,
  2.727 commits en la rama v8 según la página); la fecha del último commit no consta **[NC]**.
- **Construcción:** código con AST de tree-sitter (~40 lenguajes), sin LLM y en local; docs/PDF/imágenes/audio pasan
  por una pasada semántica con el modelo del asistente o una clave de API. Aristas etiquetadas `EXTRACTED` (explícita)
  o `INFERRED`; comunidades con Leiden (o Louvain de networkx); sin vectores ni embeddings.
- **Salidas** (`graphify-out/`): `graph.html`, `GRAPH_REPORT.md`, `graph.json`. CLI `graphify query|path|explain`;
  MCP opcional; ganchos para Claude Code y Gemini CLI que empujan al agente a consultar el grafo; ganchos de git
  que reconstruyen en commit y cambio de rama; `graphify prs` para PR. Los **commits no son un tipo de nodo** descrito
  en el README (solo disparan reconstrucción) **[NC: no se revisó el código]**.
- Parte de la página promociona Graphify Cloud (de pago); las cifras de benchmark son suyas, sin verificar.

### Comparación con lo nuestro
| | `scripts/mapa-agente.py` + `mapa-agente.md` | codegraph (`docs/propuestas/2026-10-25-codegraph.md`) | Graphify |
|---|---|---|---|
| Qué relaciona | contrato -> definición -> implementación, escrito a mano | símbolos y llamadas del código | código + docs + configs + medios |
| Quién lo mantiene | persona/agente; el script solo comprueba que las rutas existen | índice automático (SQLite) | reconstrucción automática |
| Coste | cero, sin dependencias | ~50 MB, telemetría, `curl\|sh` | dependencias pesadas, pasada LLM para docs |
| Sirve para commits/tareas | no | no | no de serie **[NC]** |

Conclusión: ninguno modela la relación **doc <-> bitácora <-> commit <-> PR <-> tarea**, que es lo que pide el bloque D.
Esa relación es pequeña y cabe en texto estructurado (id de tarea en rama, mensaje y bitácora) que un script
comprueba; no justifica un grafo externo. Graphify/codegraph servirían, si acaso, para el «contexto barato» del
código, y arrastran los mismos problemas de la nube (índice que no sobrevive al contenedor, instalación). Lo
aprovechable: **el etiquetado de aristas por procedencia** (`EXTRACTED` frente a `INFERRED`) para que el flujo distinga
un vínculo escrito por una persona/gancho de uno deducido; y el **informe corto** (`GRAPH_REPORT.md`) como forma de
resumen para agentes, que ya imitamos con `recuperar.py --estado`.

## 3. Worktrees de Claude Code frente a `fusionar.sh`

### Lo que trae de serie (https://code.claude.com/docs/en/worktrees)
- `claude --worktree <nombre>` crea `.claude/worktrees/<nombre>/` en la rama `worktree-<nombre>`; sin nombre, uno
  aleatorio. `EnterWorktree`/`ExitWorktree` lo hacen dentro de la sesión. `--worktree "#1234"` o URL de PR/MR
  crea el worktree desde esa PR (`.claude/worktrees/pr-1234`).
- **Subagentes:** «pide worktrees para tus agentes» o `isolation: worktree` en el frontmatter del subagente. Cada
  uno recibe un worktree temporal; se borra solo si acaba sin cambios; con cambios queda hasta que un barrido
  periódico (`cleanupPeriodDays`) pueda quitarlo sin perder trabajo (nunca con archivos sucios o commits sin subir).
- Base: `worktree.baseRef` = `"fresh"` (rama por defecto remota; por defecto) o `"head"` (el HEAD local, con commits
  sin subir). No admite un nombre de rama. Para el flujo, que trabaja en ramas como `version/1.0.0`, haría falta `"head"`.
- Limpieza al salir: limpio -> se borra (si no tiene nombre; con nombre pregunta); con trabajo -> pregunta;
  estado no verificable -> pregunta. En `-p` no limpia.
- Aislamiento reforzado: bloquea ediciones y comandos que apunten al checkout principal (incluidas redirecciones
  de git); no controla `cp` ni redirecciones de shell.
- `.worktreeinclude` copia archivos ignorados (`.env`); bloqueos `git worktree lock` mientras corre el agente; marcador
  en los metadatos para el barrido; ganchos `WorktreeCreate`/`WorktreeRemove` que sustituyen la lógica.
- Ojo: un subagente en worktree no carga el `CLAUDE.md` ni `.claude/rules/` de la raíz del worktree al leer ahí
  (los toma de la conversación principal); los ganchos conservan `${CLAUDE_PROJECT_DIR}` en el checkout original.

### Lo que hace `scripts/fusionar.sh` (leído)
`git merge --no-ff <rama> -m`, luego los comandos `check` del config y los `relatedTests`; si todo pasa, `git worktree
remove` (sin force) y `git branch -d`, solo para ramas `worktree-agent-*` o con worktree bajo `.claude/worktrees/`;
nunca la actual, la protegida ni `claude/*`. Si el check falla, la fusión ya está hecha y avisa de
`git reset --hard HEAD^1`. Conflicto: deja la fusión abierta.

### Qué sobraría, qué cambiaría
- **Sobra (a medio plazo):** la creación y borrado de worktrees de subagente que el flujo hiciera a mano
  (`orchestrate-dealer` ya delega en el Agent tool); el nombre `worktree-agent-*` y `.claude/worktrees/` que
  `fusionar.sh` reconoce coinciden con lo que Claude Code crea, así que la limpieza del script solapa con el barrido
  de Claude Code. Dejarla es inocuo: `fusionar.sh` limpia antes y al instante, sin esperar `cleanupPeriodDays`.
- **Sigue haciendo falta:** la fusión con check y tests relacionados, el `--no-ff` (deja traza de la rama de cada
  subagente en el historial, útil para trazabilidad), el deshacer, y la regla «merge, nunca rebase». Claude Code no
  trae nada de esto: solo aísla.
- **Cambia / a vigilar:**
  1. `worktree.baseRef` por defecto es `fresh` (rama por defecto del remoto, `main`), no la rama de trabajo:
     un subagente de `version/1.0.0` arrancaría sin los commits de la rama. El flujo debería fijar `"head"` en
     `templates/claude/settings.json` o seguir mandando al subagente `git fetch` + `reset --hard origin/<rama>`, como
     hace hoy la plantilla de `orchestrate-dealer` (que parte de «un worktree limpio»). **[NC: no se ha probado
     qué ocurre con `isolation: worktree` y una rama de trabajo sin subir.]**
  2. Un subagente con cambios deja su worktree hasta el barrido; `fusionar.sh` debe seguir llamándose para
     que no queden ramas colgando (el barrido quita el worktree, no necesariamente la rama).
  3. `${CLAUDE_PROJECT_DIR}` y los ganchos: nuestros ganchos ya calculan la raíz desde la ruta del script o
     `git rev-parse --show-toplevel`, que es justo lo que Claude Code recomienda (leer `cwd` del JSON).
  4. Nombrar ramas de subagente con la tarea (p. ej. `worktree-agent-T12-...`) daría trazabilidad gratis; el nombre
     de `--worktree <nombre>` es libre. **[NC: si el subagente con `isolation` permite elegir el nombre]**.
  5. Los worktrees de PR (`--worktree "#N"`) sirven para la fase de revisión de código contra un PR concreto.

## 4. Convenciones de commits y versiones (base para el bloque D)

### Conventional Commits 1.0.0
- Cabecera `<tipo>[(ámbito)][!]: <descripción>`, cuerpo y pies tras línea en blanco. `feat` -> MINOR, `fix` -> PATCH,
  `!` o pie `BREAKING CHANGE:` -> MAJOR; otros tipos (`docs`, `chore`, `refactor`, `test`, `perf`…) sin efecto de
  versión. Los pies usan guion en lugar de espacios (`Reviewed-by`). Fuente: repositorio
  `conventional-commits/conventionalcommits.org`, `content/v1.0.0/index.md`.
- Encaje: hoy el primer renglón del flujo es «`Fase 1: …`» y, en proyectos, «con los identificadores de tareas».
  Un tipo (`fix`, `feat`, `docs`…) cubre justo el «fix, evo…» que pide el bloque D; el ámbito puede ser la tarea.

### Trailers de git
- Pares `Clave: valor` al final del mensaje, tras una línea en blanco; la clave es ASCII alfanumérica con guiones;
  los valores pueden seguir en líneas con sangría. `git interpret-trailers --trailer 'Refs: T-12'` los añade,
  `--parse` los lee; `trailer.<alias>.*` fija dónde y si se repiten (`ifExists`, `where`). Fuente:
  `Documentation/git-interpret-trailers.adoc`. `git commit --trailer` y `git log --format='%(trailers)'` **[NC]**:
  la página que se leyó no los documenta (existen en git reciente, pero no se ha comprobado aquí contra
  `git-commit(1)`; compruébese con `git commit -h` en la versión mínima que se soporte, y con bash 3.2/macOS).
- Encaje: los trailers son legibles por script sin analizar prosa; el hook `commit-msg` puede exigirlos
  (`Tarea:`, `Refs:`) y `bitacora.py` puede cruzarlos con las filas de la bitácora.

### Semver 2.0.0
- `MAJOR.MINOR.PATCH`; `0.y.z` = desarrollo inicial, nada es estable; los prelanzamientos (`-rc.1`) van por debajo
  de la versión normal; los metadatos de build (`+sha`) no cuentan en la precedencia. Fuente:
  `semver/semver`, `semver.md`.

### release-please y changesets
- **release-please:** deduce la versión de los Conventional Commits desde el último release PR fusionado, abre un
  PR de release con el changelog, y al fusionarlo crea etiqueta y GitHub Release. Estado en
  `.release-please-manifest.json` y `release-please-config.json`; etiquetas `<componente>-v<versión>` (con
  `include-component-in-tag: false` -> `vX.Y.Z`); `bump-minor-pre-major` y `bump-patch-for-minor-pre-major` regulan
  los saltos antes de 1.0.0. Necesita etiquetas para localizar el release anterior. Fuente: `docs/manifest-releaser.md`.
- **changesets:** cada cambio aporta un archivo con tipo semver y texto de changelog; `changeset version` los consume,
  sube versiones y escribe el changelog; `changeset publish` publica. No todo cambio exige uno. La página está
  marcada como obsoleta (remite a changesets.dev) **[NC: detalles de la guía vigente]**. Fuente:
  `docs/intro-to-using-changesets.md`.

### Ideas concretas para el bloque D
1. **Tipo en el primer renglón** (Conventional Commits) como el «tag de nivel» del commit: `fix|feat|docs|chore|…`;
   `!` o `BREAKING CHANGE` -> salto mayor. Hoy `version.py --release` ya fuerza entrada de CHANGELOG; los tipos
   permitirían **calcular** el salto sugerido (como release-please) y avisar si el commit contradice la versión.
2. **Id de tarea en trailer**, no en prosa: `Tarea: T-12` (o `Refs:`), validado por `commit-msg` contra las filas
   de la bitácora (`logRows`/`taskId` ya existen en el config). Un mismo id en rama, commit, fila de bitácora,
   PR y doc da el hilo que pide «que un implicado nunca se pierda».
3. **Entorno como rama + etiqueta:** semver con prerelease para entornos (`v1.0.0-rc.1` en `uat`, `v1.0.0` en
   `main`), siguiendo el principio de «ni la 0.5 ni más ramas» del plan; solo si el usuario adopta `dev/uat/prod`.
4. **Un solo sitio para la versión** (ya: `plugin.json`). Si se adopta cálculo automático, que sea una orden de
   `version.py` que *propone* y el usuario confirma, no un bot que publica; changesets/release-please asumen CI de
   publicación y el flujo hace la release a mano (etiqueta y release las crea el usuario).
5. **Procedencia del vínculo** (de Graphify): en el índice de trazabilidad distinguir «declarado» (trailer, id en la
   bitácora) de «deducido» (mismo archivo tocado); solo lo declarado cuenta para las comprobaciones.
6. **Rama de subagente con la tarea en el nombre** y `fusionar.sh` copia el id de tarea al commit de fusión (trailer),
   para que el `--no-ff` enlace subagente, tarea y PR.
7. **Sin firmas de modelo (regla vigente):** nada de `Co-Authored-By`/`Claude-Session`; la autoría de agente, si se
   quiere, va en un trailer neutro del propio flujo (`Agente: orchestrate-dealer`) o en el nombre de rama. Decisión
   pendiente del usuario.
8. **Roles/entornos (bloque D, MMC):** no hay estándar en estas referencias para «rol por entorno»; es configuración
   propia (`gw.json`) con ramas protegidas por entorno; GitHub lo hace con *branch protection*/*environments* **[NC: no
   revisado aquí]**.

## Fuentes
- Aider git: https://github.com/Aider-AI/aider/blob/main/aider/website/docs/git.md (web: https://aider.chat/docs/git.html, no accesible)
- Aider edit formats: https://github.com/Aider-AI/aider/blob/main/aider/website/docs/more/edit-formats.md
- Aider repo map: https://github.com/Aider-AI/aider/blob/main/aider/website/docs/repomap.md y
  https://github.com/Aider-AI/aider/blob/main/aider/website/_posts/2023-10-22-repomap.md
- Aider repo: https://github.com/Aider-AI/aider
- Graphify: https://github.com/Graphify-Labs/graphify
- Worktrees de Claude Code: https://code.claude.com/docs/en/worktrees
- Conventional Commits 1.0.0: https://github.com/conventional-commits/conventionalcommits.org/blob/master/content/v1.0.0/index.md (web: https://www.conventionalcommits.org/en/v1.0.0/)
- git interpret-trailers: https://github.com/git/git/blob/master/Documentation/git-interpret-trailers.adoc
- Semver 2.0.0: https://github.com/semver/semver/blob/master/semver.md (web: https://semver.org/)
- release-please: https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md
- Changesets: https://github.com/changesets/changesets/blob/main/docs/intro-to-using-changesets.md
- Locales: `docs/mapa-agente.md`, `docs/diseno/README.md` (bloque D), `scripts/fusionar.sh`,
  `skills/orchestrate-dealer/SKILL.md`, `scripts/mapa-agente.py`, `docs/propuestas/2026-10-25-codegraph.md`
