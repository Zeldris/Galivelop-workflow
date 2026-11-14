# Release de GitHub `v0.6.0` (textos)

- **Etiqueta:** `v0.6.0`, sobre `a1a9705` (subida a `main` el 2026-11-14).
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.

```text
Galivelop-workflow v0.6.0
```

````markdown
## Galivelop-workflow v0.6.0 — 2026-11-14

**ES** · [English below](#en)

Menor de gasto y calidad: métricas de tokens, modelo y esfuerzo por agente, revisión por bloques, un check rápido y
un `.claude/gw.json` completo.

### Métricas y modelos

- **Métricas de tokens:** el gancho `Stop` apunta por sesión los tokens por modelo, rama, tarea y subagente en
  `docs/metrics/ledger.jsonl`. `scripts/metrics.py` hace informes por periodo, comparaciones, precios con fecha y
  señales de calidad junto al gasto. La skill `gw-metrics` los explica.
- **Modelos:** `models.disabled` y `scripts/models.py` apagan modelos. Cada subagente lleva su modelo y su esfuerzo.
  `doctor.py` avisa de las variables globales que los pisan.

### Revisión y check

- `/code-review` en cada bloque cerrado de una rama larga, con aviso del `commit-msg` por tamaño.
  `review-scope.py` deja fuera lo copiado tal cual del flujo.
- **Check más rápido:** `scripts/test-run.py` corre la suite en paralelo (de 556 s a 352 s). El `pre-push` de una
  rama corre solo los tests del cambio. Con el check ya en verde en caché sobre el mismo árbol, no repite los tests
  relacionados rápidos.

### Orquestación y herramientas

- **Subagente ligero `gw-worker`.** `gw-orchestrate-dealer` reparte los hallazgos por grupo de archivos.
- `roadmap.py show|done|list`, `ci-status.py --failed` y `backport.sh`.
- `apply.py` pone la `version` del `.claude/gw.json` del proyecto en la del flujo.

### Proyectos y configuración

- `ownedFiles` para los archivos del flujo que el proyecto hizo suyos, y `ciOnPush`.
- Cada umbral, ruta o aviso fijo en el código es ahora una clave de `.claude/gw.json` con su valor por defecto.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. Las claves
nuevas del config son opcionales.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.6.0/CHANGELOG.md).

<a id="en"></a>

**EN**

A spend-and-quality minor: token metrics, model and effort per agent, review by blocks, a fast check and a complete
`.claude/gw.json`.

### Metrics and models

- **Token metrics:** the `Stop` hook records per session the tokens by model, branch, task and subagent in
  `docs/metrics/ledger.jsonl`. `scripts/metrics.py` makes period reports, comparisons, dated prices and quality
  signals next to the spend. The `gw-metrics` skill explains them.
- **Models:** `models.disabled` and `scripts/models.py` turn models off. Every subagent carries its own model and
  effort. `doctor.py` warns of the global variables that override them.

### Review and check

- `/code-review` at each closed block of a long branch, with a size warning from `commit-msg`. `review-scope.py`
  leaves out the unchanged workflow copies.
- **A faster check:** `scripts/test-run.py` runs the suite in parallel (556 s down to 352 s). A branch's `pre-push`
  runs only the change's tests. With the check already green in cache on the same tree, it does not repeat the fast
  related tests.

### Orchestration and tools

- **A light `gw-worker` subagent.** `gw-orchestrate-dealer` deals findings out by group of files.
- `roadmap.py show|done|list`, `ci-status.py --failed` and `backport.sh`.
- `apply.py` sets the `version` in the project's `.claude/gw.json` to the workflow's.

### Projects and configuration

- `ownedFiles` for the workflow files a project has made its own, and `ciOnPush`.
- Every threshold, path or warning that was hard-coded is now a `.claude/gw.json` key with its default.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. The new config
keys are optional.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.6.0/CHANGELOG.md).
````
