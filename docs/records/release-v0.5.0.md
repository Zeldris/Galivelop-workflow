# Release de GitHub `v0.5.0` (textos)

- **Etiqueta:** `v0.5.0`, sobre `7d61089` (la publica a mano el usuario).
- **Título:** `Galivelop-workflow v0.5.0`
- **Cuerpo:** lo que va entre las dos rayas de abajo. La entrada completa está en el CHANGELOG.

---

## Galivelop-workflow v0.5.0 — 2026-11-04

**ES** · [English below](#en)

La `0.5` «Base» es ya la última menor publicada: solo ella recibe parches (`0.5.x`) y los evolutivos van a la
siguiente menor; la `1.0` será el Management Center. No hubo `0.4.4`: sus arreglos salen aquí. Esta versión empieza
con la recogida H15 (`gw-harvest`), cuyas 13 propuestas aprobadas están dentro.

### Versiones y publicación

- **Regla de versiones (H14):** solo la última menor publicada recibe parches. `docs/roadmap.md` reparte por versión
  cada tarea del diseño y `docs/records/pending.md` lleva la versión en cada línea.
- **Plan para el repo público:** cada versión se publica aquí con etiqueta y release, licencia MIT, a lo sumo una
  publicación al día.
- **`version.py --suggest`:** sugiere el salto de versión desde la última etiqueta según los commits.
- **`version.py --release`:** comprueba que cada ruta citada en la entrada nueva del CHANGELOG existe.

### Comprobaciones y CI

- **`scripts/check.sh` y `check-green.sh`:** el `pre-push` no repite un `check` que ya pasó en verde sobre el mismo
  árbol; `GW_CHECK_CACHE=0` lo desactiva. Con `--quiet` guarda la salida y resume lo que falla.
- **`ci-local.py`:** corre en local el CI de GitHub Actions cuando GitHub no lo arranca; con `--record` deja la línea
  que acepta `review-before-main.sh`. Claves nuevas `ciLocalLog` y `ciLocalWorkflows`.
- **`ci-status.py`:** lee el estado de Actions de una rama o un commit; la clave `ciIgnore` lista los checks ajenos
  que no bloquean.
- **`private-check.py`:** nada privado en lo que se publica (claves, correos y nombres de `.claude/gw.local.json`);
  lo pasa el `pre-push` y la clave `privateCheck` lo ajusta.
- **`tests-after-main.py`:** falla si una `TestCase` va después de `unittest.main()`.
- **`ciPython`:** matriz de versiones de Python en la plantilla del CI.

### Mensajes de commit y ramas

- **`commit-msg`:** claves nuevas `commitFormat` (Conventional Commits), `commitRefs` (trailer `Refs:`),
  `refsSources`, `commitNext` (trailer `Siguiente:`/`Next:`) y `agentSignatures` (rechaza firmas del agente).
- **`agent-signatures.py`:** con `agentSignatures: false` bloquea firmas del agente en lo que se publica en GitHub.
- **`handoff.py clash`:** detecta un id de tarea que dos ramas dan de alta a la vez para tareas distintas.
- **`handoff.py closed --staged` y `own-row`:** el `pre-commit` comprueba la bitácora al hacer el commit.
- **`merge-branch.sh`:** reúne los `Refs:` en la fusión y limpia las ramas `agent/*`.

### Contexto y relevos

- **`recover.py --state`:** enseña los otros worktrees y las ramas remotas con trabajo sin fusionar, cuenta las
  compactaciones desde el inicio de la tarea y avisa si superan el presupuesto de la bitácora.
- **`subagent-cap.py`:** avisa al lanzar un subagente sin `model` y limpia sus contadores viejos.
- **`config-guard.py`:** protege también `settings.local.json` y los worktrees, y pregunta ante órdenes de git que
  cambiarían una ruta protegida.
- **`before-stop.py` y `commit-msg`:** el relevo `WIP:` sigue con un `gw.json` ilegible.

### Skills

- **`gw-` en las skills propias:** `gw-selector`, `gw-orchestrate-dealer`, `gw-opt-tokens`, `gw-opt-ai` y
  `gw-scout-updates`.
- **`gw-media-content`:** canal `web` opcional con un bloque `json` que lee la web del proyecto; carpeta por defecto
  `docs/media`.
- **`gw-orchestrate-dealer`:** ramas `agent/<id>-<tema>`, y los arreglos vuelven al subagente que escribió el trozo.
- **`gw-harvest`:** recogidas anonimizadas (`anonymize` en `.claude/gw.local.json`) y reconocimiento de nombres
  anteriores a A8.
- **Plantillas de `REVIEW.md`:** cada regla acaba en `(check: …)` o `(criterio)`.

### Nombres en inglés (A8)

- Scripts, opciones, variables, rutas y archivos del flujo y de este repo, en inglés (`handoff.py`, `before-stop.py`,
  `docs/handoff.md`, `docs/records/`, `recordsDir`, `proposalsDir`…). **`names-check.py`** impide nombres nuevos en
  español.
- **Compatibilidad en la `0.x`:** los nombres viejos se aceptan con un aviso en stderr y dejan de valer en la `1.0`.
- **`apply.py` (`/gw-update`):** migra un proyecto instalado sin duplicados; `--keep-paths` conserva las rutas viejas.
  La primera subida a `main` tras migrar lee la marca de revisión en su ruta nueva aunque `main` aún nombre la vieja.
- **`schemaVersion` (A9):** `.claude/gw.json` lleva la versión del formato; `config.py` migra uno antiguo en memoria
  y falla cerrado ante uno más nuevo.

### Arreglos de la recogida de la `0.5`

- **`config-guard.py`:** pregunta también ante `git pull`, `am`, `bisect`, `checkout-index`, `read-tree -u`,
  `stash branch` y los `find` que escriben y pueden alcanzar una ruta protegida.
- **`commit-msg`:** con el config roto, solo deja pasar un `WIP:` si `gw.json` falta o no es JSON; la marca de
  `reviewed.sh` pasa el `commit-msg` estricto.
- **`/gw-update`:** lleva el clon del flujo a la última etiqueta. **`reviewed.sh`** pone `Siguiente:` por defecto.
- **`pre-push`:** la marca de subida en curso se llama `gw-push-in-progress.<pid>` y `before-stop.py` la respeta.
- **`subagent-cap.py`:** la definición del agente del proyecto manda sobre la de usuario.
- **`tests-after-main.py`:** un archivo descubierto que no se analiza solo da aviso. Arreglos también en
  `harvest.py` y en los tests de `gw-opt-ai`.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update` (o `python3 <flujo>/scripts/apply.py <proyecto>`), y luego
`python3 .claude/gw/scripts/doctor.py`, que avisa de lo que falte migrar. Las claves nuevas del config son opcionales.
`apply` nunca sobrescribe un `REVIEW.md` existente: sus reglas nuevas se copian a mano.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.0/CHANGELOG.md).

<a id="en"></a>

**EN**

`0.5` "Base" is now the latest published minor: only it receives patches (`0.5.x`), and new features go to the next
minor; `1.0` will be the Management Center. There was no `0.4.4`: its fixes ship here. This version begins with the
H15 harvest (`gw-harvest`), whose 13 approved proposals are included.

### Versions and publishing

- **Versioning rule (H14):** only the latest published minor receives patches. `docs/roadmap.en.md` splits each design
  task by version and `docs/records/pending.md` carries the version on every line.
- **Plan for the public repo:** each version is published here with a tag and a release, MIT license, at most one
  release per day.
- **`version.py --suggest`:** suggests the version bump from the last tag based on the commits.
- **`version.py --release`:** checks that every path cited in the new CHANGELOG entry exists.

### Checks and CI

- **`scripts/check.sh` and `check-green.sh`:** the `pre-push` does not repeat a `check` that already passed on the
  same tree; `GW_CHECK_CACHE=0` turns it off. With `--quiet` it stores the output and summarizes what fails.
- **`ci-local.py`:** runs the GitHub Actions CI locally when GitHub does not start it; with `--record` it leaves the
  line that `review-before-main.sh` accepts. New keys `ciLocalLog` and `ciLocalWorkflows`.
- **`ci-status.py`:** reads the Actions status of a branch or commit; the `ciIgnore` key lists unrelated checks that
  do not block.
- **`private-check.py`:** nothing private in what gets published (keys, e-mails and names from
  `.claude/gw.local.json`); the `pre-push` runs it and the `privateCheck` key tunes it.
- **`tests-after-main.py`:** fails if a `TestCase` comes after `unittest.main()`.
- **`ciPython`:** Python version matrix in the CI template.

### Commit messages and branches

- **`commit-msg`:** new keys `commitFormat` (Conventional Commits), `commitRefs` (`Refs:` trailer), `refsSources`,
  `commitNext` (`Siguiente:`/`Next:` trailer) and `agentSignatures` (rejects agent signatures).
- **`agent-signatures.py`:** with `agentSignatures: false` it blocks agent signatures in what is published to GitHub.
- **`handoff.py clash`:** detects a task id that two branches create at the same time for different tasks.
- **`handoff.py closed --staged` and `own-row`:** the `pre-commit` checks the handoff log at commit time.
- **`merge-branch.sh`:** gathers the `Refs:` in the merge and cleans up `agent/*` branches.

### Context and handoffs

- **`recover.py --state`:** shows the other worktrees and remote branches with unmerged work, counts compactions
  since the start of the task and warns if they exceed the budget in the handoff log.
- **`subagent-cap.py`:** warns when a subagent is launched without `model` and cleans its old counters.
- **`config-guard.py`:** also protects `settings.local.json` and worktrees, and asks on git commands that would change
  a protected path.
- **`before-stop.py` and `commit-msg`:** the `WIP:` handoff goes on with an unreadable `gw.json`.

### Skills

- **`gw-` prefix on the workflow's own skills:** `gw-selector`, `gw-orchestrate-dealer`, `gw-opt-tokens`,
  `gw-opt-ai` and `gw-scout-updates`.
- **`gw-media-content`:** optional `web` channel with a `json` block read by the project's website; default folder
  `docs/media`.
- **`gw-orchestrate-dealer`:** `agent/<id>-<topic>` branches, and fixes go back to the subagent that wrote the piece.
- **`gw-harvest`:** anonymized harvests (`anonymize` in `.claude/gw.local.json`) and recognition of pre-A8 names.
- **`REVIEW.md` templates:** every rule ends in `(check: …)` or `(criterio)`.

### English names (A8)

- Scripts, options, variables, paths and files of the workflow and of this repo, in English (`handoff.py`,
  `before-stop.py`, `docs/handoff.md`, `docs/records/`, `recordsDir`, `proposalsDir`…). **`names-check.py`** prevents
  new Spanish names.
- **`0.x` compatibility:** old names are accepted with a stderr warning and stop working in `1.0`.
- **`apply.py` (`/gw-update`):** migrates an installed project without duplicates; `--keep-paths` keeps the old paths.
  The first push to `main` after migrating reads the review mark at its new path even if `main` still names the old one.
- **`schemaVersion` (A9):** `.claude/gw.json` carries the format version; `config.py` migrates an older one in memory
  and fails closed on a newer one.

### Fixes from the `0.5` harvest

- **`config-guard.py`:** also asks on `git pull`, `am`, `bisect`, `checkout-index`, `read-tree -u`, `stash branch`
  and on a writing `find` that can reach a protected path.
- **`commit-msg`:** with a broken config, only lets a `WIP:` through when `gw.json` is missing or not JSON; the
  `reviewed.sh` mark passes the strict `commit-msg`.
- **`/gw-update`:** moves the workflow clone to the latest tag. **`reviewed.sh`** sets `Next:` by default.
- **`pre-push`:** the push-in-progress mark is named `gw-push-in-progress.<pid>`, and `before-stop.py` respects it.
- **`subagent-cap.py`:** the project's agent definition wins over the user's.
- **`tests-after-main.py`:** a discovered file that does not parse only warns. Fixes in `harvest.py` and the
  `gw-opt-ai` tests too.

### Updating a project

From a session in the project, the `gw-update` skill (or `python3 <workflow>/scripts/apply.py <project>`), then
`python3 .claude/gw/scripts/doctor.py`, which warns about anything still to migrate. The new config keys are optional.
`apply` never overwrites an existing `REVIEW.md`: copy its new rules by hand.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.0/CHANGELOG.md).

---
