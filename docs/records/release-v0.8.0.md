# Release de GitHub `v0.8.0` (textos)

- **Etiqueta:** `v0.8.0`, sobre `b3825b8`, el commit de `main` de la subida del 2026-11-18.
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** 2026-11-18 por el agente desde una sesión local (`gh release create`, a petición del usuario), con estos textos.

```text
Galivelop-workflow v0.8.0
```

````markdown
## Galivelop-workflow v0.8.0 — 2026-11-18

**ES** · [English below](#en)

Versión «Preguntas y otros agentes» publicada con lo hecho; el front y lo de las webs pasan a la nueva `0.9`
«Front» y la «Estable» a la `0.10`.

### Preguntas y modos

- `docs/questions.md` y `questions.py` (`add`, `answer`, `list`, `count`): lista numerada con recomendación, el
  usuario responde por número; un subagente nunca pregunta, devuelve la pregunta.
- Skill `gw-mode` y `mode.py` como interruptor de `modes.questions`; `questions-guard.py`; `careful.py` pide
  confirmación antes de una orden destructiva (`modes.careful`).
- Cuatro modos: SDD siempre, DDD con dominio, TDD con comportamiento testeable y exploración solo en `spike/<tema>`.

### Ficha de tarea y alcance

- Ficha `docs/tasks/<id>.md` con criterios, `Files` y decision log; `handoff.py close-row` exige casillas con test.
- Ramas `spike/<tema>` que no se fusionan en una rama de trabajo; `scopeGuard` avisa o bloquea fuera de `Files` y
  apunta las desviaciones para la retro.

### Trazas, bitácora, subida y CI

- `trace.py`, `handoff.py preflight`, `add-pending` y `add-decision`; el `pre-push` avisa de un CI en rojo.
- `check.yml` reutilizable (`workflow_call`) llamado desde `release.yml`; `push.sh` reintenta y confirma con
  `git ls-remote`.
- Fragmentos de CHANGELOG por rama (`changelog.d/`) y contrato de revisión con anclas.

### Pruebas, otros agentes y guías

- `test-run.py` reintenta y registra las pruebas inestables; `tests-for.py --run` con `testUnitTimeout`.
- `apply.py` copia las skills a `.agents/skills` (opencode, Codex) y guía `other-agents`.
- Avisos de lectura entera repetida, de contexto cerca de la ventana y de sellos caducados; `.gitignore` por stack y
  licencia doble en `gw-init`.
- Retro del sello: `scope-guard.py` y `review-scope.py --trivial` ignoran copias del flujo y versión estampada.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. Claves nuevas
en `.claude/gw.json`, con su valor por defecto: `questions.path` (`docs/questions.md`), `modes.questions` (`false`),
`modes.careful` (`true`), `modes.carefulExempt`, `modes.carefulWorktrees` (`[".claude/worktrees/"]`), `taskRecord`
(`enabled: false`), `spikeBranch` (`spike/`), `scopeGuard.mode` (`warn`), `scopeGuard.skipStamps` (`true`),
`scopeGuard.skipVendored` (`true`), `changelogFragments` (`true`), `changelogFragmentsDir` (`changelog.d`),
`flaky.retries` (`1`), `flaky.proposeAfter` (`3`), `testUnitTimeout` (`1800`), `agentsSkillsDir`
(`.agents/skills`), `handoff.lockWait` (`10`), `handoff.cellHardLimit` (`1600`), `prepushCiWarn` (`true`),
`prepushCiWarnTimeout` (`10`), `wholeReadRepeatOnly` (`true`), `wholeReadStaleDays` (`7`), `contextGuard.nearRatio`
(`0.8`) y `metrics.quality.findingsWords`.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.8.0/CHANGELOG.md).

<a id="en"></a>

**EN**

«Questions and other agents» release shipped with what was done; the front end and the web items move to the new
`0.9` «Front» and «Stable» to `0.10`.

### Questions and modes

- `docs/questions.md` and `questions.py` (`add`, `answer`, `list`, `count`): numbered list with a recommendation, the
  user answers by number; a subagent never asks, it returns the question.
- The `gw-mode` skill and `mode.py` as the switch of `modes.questions`; `questions-guard.py`; `careful.py` asks for
  confirmation before a destructive command (`modes.careful`).
- Four modes: SDD always, DDD with a domain, TDD with testable behavior and exploration only in `spike/<topic>`.

### Task record and scope

- Record `docs/tasks/<id>.md` with criteria, `Files` and a decision log; `handoff.py close-row` requires checkboxes
  with a test.
- `spike/<topic>` branches that cannot merge into a work branch; `scopeGuard` warns or blocks outside `Files` and
  records deviations for the retro.

### Traces, log, push and CI

- `trace.py`, `handoff.py preflight`, `add-pending` and `add-decision`; the `pre-push` warns about a red CI.
- Reusable `check.yml` (`workflow_call`) called from `release.yml`; `push.sh` retries and confirms with
  `git ls-remote`.
- Per-branch CHANGELOG fragments (`changelog.d/`) and a review contract with anchors.

### Tests, other agents and guides

- `test-run.py` retries and records flaky tests; `tests-for.py --run` with `testUnitTimeout`.
- `apply.py` copies skills to `.agents/skills` (opencode, Codex) and the `other-agents` guide.
- Warnings for repeated whole-file reads, context near the window and expired stamps; per-stack `.gitignore` and
  dual license in `gw-init`.
- Seal retro: `scope-guard.py` and `review-scope.py --trivial` ignore workflow copies and the stamped version.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. New keys in
`.claude/gw.json`, with their defaults: `questions.path` (`docs/questions.md`), `modes.questions` (`false`),
`modes.careful` (`true`), `modes.carefulExempt`, `modes.carefulWorktrees` (`[".claude/worktrees/"]`), `taskRecord`
(`enabled: false`), `spikeBranch` (`spike/`), `scopeGuard.mode` (`warn`), `scopeGuard.skipStamps` (`true`),
`scopeGuard.skipVendored` (`true`), `changelogFragments` (`true`), `changelogFragmentsDir` (`changelog.d`),
`flaky.retries` (`1`), `flaky.proposeAfter` (`3`), `testUnitTimeout` (`1800`), `agentsSkillsDir`
(`.agents/skills`), `handoff.lockWait` (`10`), `handoff.cellHardLimit` (`1600`), `prepushCiWarn` (`true`),
`prepushCiWarnTimeout` (`10`), `wholeReadRepeatOnly` (`true`), `wholeReadStaleDays` (`7`), `contextGuard.nearRatio`
(`0.8`) and `metrics.quality.findingsWords`.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.8.0/CHANGELOG.md).
````
