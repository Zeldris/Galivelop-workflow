# Release de GitHub `v0.8.2` (textos)

- **Etiqueta:** `v0.8.2`, sobre `a725647`, el commit de `main` de la subida del 2026-11-22.
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** pendiente; la crea el usuario desde una sesión local (en la nube no se publican releases), con estos textos.

```text
Galivelop-workflow v0.8.2
```

````markdown
## Galivelop-workflow v0.8.2 — 2026-11-22

**ES** · [English below](#en)

Parche de la recogida H26.

### Cambios

- Selector (D142, D147): `gw-selector` se para cuando el modelo o el esfuerzo recomendado no coincide con el actual
  (en ambos sentidos; `unknown` no cuenta) y lee solo sus claves con `config.py get`; nuevo `models.py
  session-check`, llamado desde `session-start.sh`, avisa al arrancar o reanudar si el modelo de la sesión no es la
  familia de la última línea `Session:` o `Sesión:` (clave `models.sessionCheck`).
- Medición (D144, D145, D151): `measure.py` sin `--session` mide la sesión en curso (la más nueva de todas las
  carpetas; D139 solo desempata) y no cuenta registros de otra rama; `test_measure.py` pasa con el flujo instalado.
- Avisos (D149, D150): `scope-guard.py` cuenta `roadmapFiles` y `pendingFile` como archivos del flujo y, si no pudo
  saltar las copias del flujo, lo dice en una línea con la clave `workflowClone` o la orden.
- Check (D152, D160): `tests-for.py --run` no pasa shellcheck a las copias de `.claude/gw/`; `ci-local.py --record`
  no deja `.gw-ci/` en el árbol.
- Bitácora (D154, D157): `handoff.py set-row`/`close-row` ponen la fecha de hoy en «Actualizado»; `next-id` lee
  también `pendingFile`.
- Diagnóstico (D158, D159): `doctor.py` avisa si la carpeta de `workflowClone` no existe y si los agentes
  `gw-worker`/`gw-reviewer` están ignorados por el `.gitignore`.
- Subagentes (D146, D153): `gw-reviewer` ya no tiene la herramienta `Agent`; el encargo de `gw-orchestrate-dealer`
  pide probar cada test nuevo en rojo sin el arreglo con `red-without-fix.sh`.
- Plantillas e instalación (D148, D164): las plantillas de `AGENTS.md` no piden commit solo para el ledger de
  métricas; `apply.md` recomienda un repo por sesión en la nube.
- Aviso de `Findings:` (D155): el defecto de `metrics.quality.findingsWords` pasa a `["arreglos de la revisión",
  "review fixes"]`; «hallazgo» o «finding» sueltos ya no avisan. Quien contaba con ellos sin fijarlos en su `gw.json`
  pierde el aviso: añádalos ahí.
- Arranque (D156, D166): con `contextGuard.systemAdvice`, el aviso de arranque se mide sin la parte del sistema que el
  usuario no puede recortar; `recover.py --state` da las filas abiertas del roadmap en una rama `version/X.Y[.Z]`.
- `apply.py` (D161, D165): `--dry-run --summary` da un recuento por nombre viejo; el aviso de nombres viejos sugiere
  `legacyNamesSkip` cuando cita texto de otros repos.
- CI y retro (D162, D163): la plantilla `check.yml` no corre en un push que solo toca el ledger de métricas
  (`paths-ignore`, desde `metrics.ledger`); `retro` ya no da por hechos ids de letra.
- Revisión (retro del parche): la plantilla `REVIEW.md` pide un test con una muestra real para el código que lee lo
  que escribe un agente o una persona.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. Clave nueva en
`.claude/gw.json`, con su valor por defecto: `models.sessionCheck` (`true`). Cambia el defecto de
`metrics.quality.findingsWords` (arriba).

<a id="en"></a>
**EN**

Patch from the H26 harvest.

### Changes

- Selector (D142, D147): `gw-selector` stops when the recommended model or effort does not match the current one
  (both ways; `unknown` does not count) and reads only its keys with `config.py get`; new `models.py session-check`,
  called from `session-start.sh`, warns on start or resume when the session's model is not the family of the last
  `Session:` or `Sesión:` line (key `models.sessionCheck`).
- Measuring (D144, D145, D151): `measure.py` without `--session` measures the current session (the newest across
  all folders; D139 only breaks ties) and leaves out logs of another branch; `test_measure.py` passes with the
  workflow installed.
- Warnings (D149, D150): `scope-guard.py` counts `roadmapFiles` and `pendingFile` as workflow files and, when it
  could not skip the workflow copies, says so in one line with the `workflowClone` key or the command.
- Check (D152, D160): `tests-for.py --run` does not shellcheck the copies in `.claude/gw/`; `ci-local.py --record`
  leaves no `.gw-ci/` in the tree.
- Log (D154, D157): `handoff.py set-row`/`close-row` put today's date in «Updated»; `next-id` also reads
  `pendingFile`.
- Diagnostics (D158, D159): `doctor.py` warns when the `workflowClone` folder does not exist and when the
  `gw-worker`/`gw-reviewer` agents are git-ignored.
- Subagents (D146, D153): `gw-reviewer` no longer has the `Agent` tool; the `gw-orchestrate-dealer` brief asks to
  prove each new test red without the fix with `red-without-fix.sh`.
- Templates and install (D148, D164): the `AGENTS.md` templates ask for no commit only for the metrics ledger;
  `apply.md` recommends one repo per cloud session.
- `Findings:` warning (D155): the default of `metrics.quality.findingsWords` becomes `["arreglos de la revisión",
  "review fixes"]`; lone "hallazgo" or "finding" no longer warn. If you relied on them without setting them in your
  `gw.json`, add them there.
- Startup (D156, D166): with `contextGuard.systemAdvice`, the startup warning is measured without the system part the
  user cannot trim; `recover.py --state` lists the open roadmap rows on a `version/X.Y[.Z]` branch.
- `apply.py` (D161, D165): `--dry-run --summary` gives one count per legacy name; the legacy-names warning suggests
  `legacyNamesSkip` when it quotes other repos' text.
- CI and retro (D162, D163): the `check.yml` template does not run on a push that only touches the metrics ledger
  (`paths-ignore`, from `metrics.ledger`); `retro` no longer assumes letter ids.
- Review (patch retro): the `REVIEW.md` template asks for a test with a real sample for code that reads what an
  agent or a person writes.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. New key in
`.claude/gw.json`, with its default: `models.sessionCheck` (`true`). The default of `metrics.quality.findingsWords`
changes (above).

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.8.2/CHANGELOG.md).
````
