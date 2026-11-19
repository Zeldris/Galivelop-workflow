# Release de GitHub `v0.8.1` (textos)

- **Etiqueta:** `v0.8.1`, sobre `4ca45d0`, el commit de `main` de la subida del 2026-11-19.
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** no todavía; el usuario decidió (2026-11-19) que la publique el agente desde una sesión local (`gh release create v0.8.1 --target 4ca45d0`, con estos textos).

```text
Galivelop-workflow v0.8.1
```

````markdown
## Galivelop-workflow v0.8.1 — 2026-11-19

**ES** · [English below](#en)

Parche de la recogida de apertura de la `0.9`: arreglos de instalación, revisión, bitácora y medidas.

- Instalación (D128-D131): `apply.py --update` quita el gancho del flujo que la plantilla registra en el mismo evento
  con otro matcher (la `0.8.0` dejaba `whole-read.py` dos veces) y `doctor.py` falla con el mismo `command` dos veces
  en un evento; escribe `pendingFile` en el `gw.json` del proyecto al migrar la bitácora, o avisa con la clave y la
  orden; `AGENTS.md.gw-new` se genera con el `gw.json` ya migrado; las plantillas de `AGENTS.md` ponen
  `Findings:`/`Retries:` en el último párrafo, con los demás trailers.
- Revisión (D132, D141): `review-scope.py` en un proyecto sin `--workflow` ni `GW_WORKFLOW` busca la copia del flujo
  (claves nuevas `workflowClone` y `workflowRepository`) o falla con la orden, en vez de tomarse el proyecto por
  flujo; el `Findings:` de un commit de merge cierra el bloque de revisión y cuenta en `metrics.py quality` (antes
  `--no-merges` lo ignoraba y `recover.py --state` avisaba de una revisión ya hecha).
- Bitácora y commits (D133-D135, D140): `recover.py --state` con `agentSignatures: false` recuerda que no van firmas
  del agente y que los trailers van juntos al final; el error de `handoff.py next-id` con un prefijo no admitido
  nombra los válidos y `--id-regex`/`taskId`, y `--plan` vale tras el subcomando; `handoff.py check` rechaza perder la
  fila «Tarea en curso» respecto a `HEAD` sin cierre de rama; tras un rechazo de `pre-commit`, el aviso dice repetir
  el mismo `git commit -m …`.
- Agentes y medidas (D136-D139): `merge-branch.sh` deja para la siguiente pasada un worktree bloqueado por un agente
  vivo en vez de fallar; `doctor.py` avisa de `branchCheck: related` con `relatedTests` vacío; `measure.py` sin
  `--since` empieza en el último `/clear` o compactación, y con `--since` prefiere la sesión de la carpeta del repo.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. Claves nuevas
en `.claude/gw.json`, con su valor por defecto: `workflowClone` (`"../Galivelop-workflow"`) y `workflowRepository`
(`"https://github.com/Zeldris/Galivelop-workflow"`): dónde busca `review-scope.py` la copia del flujo.

<a id="en"></a>

**EN**

Patch from the `0.9` opening harvest: fixes to install, review, log and measures.

- Install (D128-D131): `apply.py --update` drops a workflow hook the template registers in the same event with
  another matcher (`0.8.0` left `whole-read.py` twice) and `doctor.py` fails on the same `command` twice in one event;
  it writes `pendingFile` to the project's `gw.json` when it migrates the log, or warns with the key and the command;
  `AGENTS.md.gw-new` is rendered with the already migrated `gw.json`; the `AGENTS.md` templates put
  `Findings:`/`Retries:` in the last paragraph, with the other trailers.
- Review (D132, D141): `review-scope.py` in a project with no `--workflow` nor `GW_WORKFLOW` looks for the workflow
  copy (new keys `workflowClone` and `workflowRepository`) or fails with the command, instead of taking the project
  as the workflow; a `Findings:` on a merge commit ends the review block and counts in `metrics.py quality` (before,
  `--no-merges` ignored it and `recover.py --state` warned of a review already done).
- Log and commits (D133-D135, D140): `recover.py --state` with `agentSignatures: false` reminds that no agent
  signatures go in and the trailers go together at the end; the `handoff.py next-id` error for a prefix not accepted
  names the valid ones and `--id-regex`/`taskId`, and `--plan` works after the subcommand; `handoff.py check` rejects
  losing the "Task in progress" row against `HEAD` without a branch close; after a `pre-commit` rejection, the warning
  says to repeat the same `git commit -m …`.
- Agents and measures (D136-D139): `merge-branch.sh` leaves a worktree locked by a live agent for the next pass
  instead of failing; `doctor.py` warns on `branchCheck: related` with empty `relatedTests`; `measure.py` with no
  `--since` starts at the last `/clear` or compaction, and with `--since` prefers the repo folder's session.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. New keys in
`.claude/gw.json`, with their defaults: `workflowClone` (`"../Galivelop-workflow"`) and `workflowRepository`
(`"https://github.com/Zeldris/Galivelop-workflow"`): where `review-scope.py` looks for the workflow copy.
````
