# Release de GitHub `v0.4.0` (textos)

- **Etiqueta:** `v0.4.0`, sobre `d7dd18f` (publicada a mano por el usuario, 2026-10-25).
- **Título:** `Galivelop-workflow v0.4.0`
- **Cuerpo:** lo que va entre las dos rayas de abajo. La entrada completa está en el CHANGELOG.

---

## Galivelop-workflow v0.4.0 — 2026-10-25

**ES** · [English below](#en)

La `0.4` es la versión estable antes de la `1.0`. Desde ahora solo recibe correcciones (`0.4.x`); los evolutivos
y las novedades van a la `1.0.0`, que es la que seguirá creciendo.

### Ganchos nuevos

- **`Stop` (`antes-de-parar.py`):** no deja a Claude terminar con commits sin subir ni con cambios sin confirmar si la
  bitácora no está entre ellos, y nombra la orden que lo arregla. Si le falta un dato, nunca bloquea: avisa.
- **`guardia-config.py` (`PreToolUse`):** pide confirmación antes de escribir en `.claude/settings.json`,
  `.claude/gw.json`, `.githooks/` o `.claude/gw/scripts/`, tanto con una edición como con una orden de Bash. Las
  lecturas pasan sin preguntar.
- **`tope-subagentes.py`:** al llegar a `subagentCap` llamadas a subagentes en una sesión (30 por defecto, clave nueva
  del config), y cada 10 más, pide comprobar que no están en bucle.
- **`commit-msg`:** corre `bitacora.py check` al hacer el commit, sin esperar al `pre-push`.

### Skills

- **`gw-media-content` y `gw-media-content-now`:** proponen y producen publicaciones del proyecto para X, Reddit,
  LinkedIn y Discord, más los canales que declare el proyecto. Cada pieza lleva textos por canal e idioma, e imágenes.
  El render real necesita Playwright e ImageMagick con WebP, y el CI no lo cubre.
- **`wait-what`** (de mattpocock/skills): pedir que se vuelva a explicar algo.
- **`orchestrate-dealer`:**
  - comprueba las precondiciones antes de repartir;
  - cancela lo que depende de un trozo que falló dos veces;
  - los encargos llevan `Files:`/`Create:`, su tope y qué hacer si se rechaza el push;
  - las respuestas llevan `EVIDENCE:` o `NOT_TESTABLE:`.
- **`writing-for-agents`:** consultas de activación en `evals/triggers.json`. Las plantillas de **`REVIEW.md`** acaban
  con `SHIP` / `SHIP WITH FIXES` / `DO NOT SHIP`.

### Publicar versiones

- **Cada versión empieza con una recogida** (`gw-harvest`). `version.py --release` no deja publicar sin ella, ni con
  la entrada del CHANGELOG sin fecha o a medias.
- Si el CI no arranca (sin cuota de Actions), vale el check en local sobre el mismo commit, **solo con confirmación**
  de la persona, y se apunta como «comprobado solo en local».
- Con `requireRetro` y la persona ausente, se deja todo listo y se para antes de `revisado.sh`.

### Comprobaciones

- **`mapa-agente.py`** (clave `agentMap`): comprueba que existe todo lo que cita el mapa para agentes.
- **`doctor.py`** avisa de:
  - caracteres invisibles o bidi en `AGENTS.md`, `CLAUDE.md` y `SKILL.md`;
  - un `AGENTS.md`/`CLAUDE.md` demasiado largo;
  - scripts de skills sin test (`skill tests`);
  - herramientas de `gw-media-content` que faltan (`media tools`);
  - un CI que el agente no puede leer (`ci access`).

  Además, respeta las reglas `!` del `.gitignore`.
- **`bitacora.py`:** tope de tamaño por celda y forma de «Hecho» en el `check`, y la orden nueva `bitacora.py done`.
- **`recuperar.py`:**
  - recorta su salida a 9.500 caracteres y lo dice;
  - sanea los fragmentos de `--buscar`;
  - avisa si cae en el registro de otra sesión.
- **`revision-antes-de-main.sh`:**
  - ya no se atasca con órdenes largas (antes tenía un regex cuadrático);
  - reconoce `gh pr merge|create` escrito con tabuladores, con continuaciones de línea, con opciones entre medias o
    tras prefijos (`nice -n 5`, `timeout -s KILL 5`, `env -u X`…).
- **`recoger.py`:** informa también de las líneas «Propuesta para el flujo» de las bitácoras.

### Otros cambios

- **Notas personales:** `aplicar.py` lleva los archivos de `~/.claude/gw/notas/` al `.claude/gw/` de cada proyecto.
  Nunca pisa uno distinto.
- Se pide `/clear` también al cerrar cada tarea o PR; las fases antes de `main` quedan en la plantilla de la
  bitácora; `aplicar.md` explica cómo fusionar muchos `.gw-nuevo`.
- Arreglos:
  - `pre-commit` ya no toma por clave una palabra que solo acaba en un prefijo de clave;
  - `es-codigo.sh` ya no falla con 141 cuando se corta su salida;
  - un emoji compuesto (👩‍💻) ya no da `FAIL`.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update` (o `python3 <flujo>/scripts/aplicar.py <proyecto>`), y luego
`python3 .claude/gw/scripts/doctor.py`. Las claves nuevas del config (`subagentCap`, `agentMap`) son opcionales.
Los ganchos nuevos entran en `.claude/settings.json`: `doctor.py` avisa si queda una entrada antigua duplicada.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.0/CHANGELOG.md).

<a id="en"></a>

**EN**

`0.4` is the stable release before `1.0`. From now on it only gets fixes (`0.4.x`); new features and improvements go
to `1.0.0`, the line that will keep growing.

### New hooks

- **`Stop` (`antes-de-parar.py`):** does not let Claude finish with unpushed commits or with uncommitted changes when
  the log is not among them, and names the command that fixes it. When it is missing data it never blocks: it warns.
- **`guardia-config.py` (`PreToolUse`):** asks for confirmation before writing to `.claude/settings.json`,
  `.claude/gw.json`, `.githooks/` or `.claude/gw/scripts/`, whether through an edit or a Bash command. Reads go
  through without asking.
- **`tope-subagentes.py`:** at `subagentCap` subagent calls in a session (30 by default, a new config key), and every
  10 after that, asks to check they are not looping.
- **`commit-msg`:** runs `bitacora.py check` at commit time, without waiting for `pre-push`.

### Skills

- **`gw-media-content` and `gw-media-content-now`:** propose and produce posts about the project for X, Reddit,
  LinkedIn and Discord, plus any channels the project declares. Each piece comes with texts per channel and language,
  and images. The real render needs Playwright and ImageMagick with WebP, and CI does not cover it.
- **`wait-what`** (from mattpocock/skills): ask for something to be explained again.
- **`orchestrate-dealer`:**
  - checks preconditions before dealing work out;
  - cancels whatever depends on a chunk that failed twice;
  - briefs carry `Files:`/`Create:`, their cap and what to do when a push is rejected;
  - replies carry `EVIDENCE:` or `NOT_TESTABLE:`.
- **`writing-for-agents`:** trigger queries in `evals/triggers.json`. The **`REVIEW.md`** templates end with `SHIP` /
  `SHIP WITH FIXES` / `DO NOT SHIP`.

### Releasing

- **Every version starts with a harvest** (`gw-harvest`). `version.py --release` blocks a release without one, and
  also one whose CHANGELOG entry is undated or unfinished.
- When CI does not start (no Actions quota), the check passed locally on the same commit counts, **only with the
  person's confirmation**, and is logged as "checked only locally".
- With `requireRetro` and the person away, everything is left ready and the work stops before `revisado.sh`.

### Checks

- **`mapa-agente.py`** (`agentMap` key): checks that everything the agent map cites exists.
- **`doctor.py`** warns about:
  - invisible or bidi characters in `AGENTS.md`, `CLAUDE.md` and `SKILL.md`;
  - an `AGENTS.md`/`CLAUDE.md` that is too long;
  - skill scripts with no test (`skill tests`);
  - missing tools for `gw-media-content` (`media tools`);
  - a CI the agent cannot read (`ci access`).

  It also honours the `.gitignore` `!` rules.
- **`bitacora.py`:** a size cap per cell and a shape check for "Done" in `check`, and the new `bitacora.py done`
  command.
- **`recuperar.py`:**
  - caps its output at 9,500 characters and says so;
  - sanitises `--buscar` fragments;
  - warns when it falls back to another session's transcript.
- **`revision-antes-de-main.sh`:**
  - no longer stalls on long commands (it used to have a quadratic regex);
  - catches `gh pr merge|create` written with tabs, with line continuations, with options in between or behind
    prefixes (`nice -n 5`, `timeout -s KILL 5`, `env -u X`…).
- **`recoger.py`:** also reports the "Proposal for the workflow" lines in the logs.

### Other changes

- **Personal notes:** `aplicar.py` copies the files in `~/.claude/gw/notas/` to each project's `.claude/gw/`. It never
  overwrites one that differs.
- `/clear` is also suggested when each task or PR closes; the phases before `main` are now in the log template;
  `apply.md` explains how to merge many `.gw-nuevo` files.
- Fixes:
  - `pre-commit` no longer mistakes a word that merely ends in a key prefix for a key;
  - `es-codigo.sh` no longer fails with 141 when its output is cut short;
  - a compound emoji (👩‍💻) no longer gives `FAIL`.

### Updating a project

From a session in the project, the `gw-update` skill (or `python3 <workflow>/scripts/aplicar.py <project>`), then
`python3 .claude/gw/scripts/doctor.py`. The new config keys (`subagentCap`, `agentMap`) are optional. The new hooks go
into `.claude/settings.json`: `doctor.py` warns about an older duplicated entry.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.0/CHANGELOG.md).

---
