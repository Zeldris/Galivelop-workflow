# Release de GitHub `v0.6.2` (textos)

- **Etiqueta:** `v0.6.2`, sobre `cd856ca` (subida a `main` el 2026-11-15).
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Desde local (elegido por el usuario):** `git fetch origin main && git tag v0.6.2 cd856ca && git push origin v0.6.2`,
  que lanza `release.yml`; o a mano, `gh release create v0.6.2 --title "<título>" --notes-file <cuerpo>`.

```text
Galivelop-workflow v0.6.2
```

````markdown
## Galivelop-workflow v0.6.2 — 2026-11-15

**ES** · [English below](#en)

Parche de la `0.6` con los arreglos de la recogida de cierre de la `0.7` y las mejoras de la retro del propio parche.

### Subidas y ganchos

- `reviewed.sh` puede marcar la primera subida a una rama protegida que aún no existe en el remoto; cualquier otro
  fallo de `git ls-remote` falla cerrado.
- El gancho `Stop` ya no cuenta como sin subir los commits de la rama protegida traídos por merge.
- `version.py --release`, sin recogida, dice cómo traer solo su archivo desde la rama donde se hizo.

### Reparto a subagentes

- `merge-branch.sh --defer-check` fusiona y limpia sin check, para todas las ramas de una oleada salvo la última.
- `tests-for.py --run` pasa shellcheck antes de los tests y para en su fallo; `--why` dice qué regla de `testMap`
  trajo cada test.
- `subagent-cap.py` avisa de un `general-purpose` con `sonnet` y esfuerzo bajo o medio cuando existe `gw-worker`.
- `gw-orchestrate-dealer` pide shellcheck antes de cada commit, para con `TaskStop` al subagente cuyo informe
  aceptó, manda los arreglos tras la fusión a un subagente nuevo con el archivo de hallazgos y solo da un test por
  preexistente si falla igual en la rama protegida.

### Revisión y plantillas

- El revisor de la fase 1 recibe `pendingFile` para no repetir lo ya apuntado.
- La plantilla de `AGENTS.md` nombra `ci-status.py --failed` para leer un CI en rojo y dice que no se sigue el
  gancho `Stop` de la nube que pide firmar como Claude.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. No hay claves
nuevas en `.claude/gw.json`.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.6.2/CHANGELOG.md).

<a id="en"></a>

**EN**

A `0.6` patch with the fixes from the `0.7` closing harvest and the improvements from the patch's own retro.

### Pushes and hooks

- `reviewed.sh` can mark the first push to a protected branch that does not exist on the remote yet; any other
  `git ls-remote` failure fails closed.
- The `Stop` hook no longer counts as unpushed the protected branch's commits brought in by a merge.
- `version.py --release`, with no harvest, says how to bring only its file from the branch where it was made.

### Dealing to subagents

- `merge-branch.sh --defer-check` merges and cleans up without the check, for every branch of a wave but the last.
- `tests-for.py --run` runs shellcheck before the tests and stops on its failure; `--why` says which `testMap` rule
  brought each test.
- `subagent-cap.py` warns about a `general-purpose` with `sonnet` and low or medium effort when `gw-worker` exists.
- `gw-orchestrate-dealer` asks for shellcheck before each commit, stops with `TaskStop` the subagent whose report it
  accepted, sends the fixes after the merge to a new subagent with the findings file, and only takes a test as
  pre-existing if it fails the same on the protected branch.

### Review and templates

- The phase 1 reviewer gets `pendingFile` so it does not repeat what is already logged.
- The `AGENTS.md` template names `ci-status.py --failed` to read a red CI and says the cloud `Stop` hook that asks
  to sign as Claude is not followed.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. There are no new
keys in `.claude/gw.json`.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.6.2/CHANGELOG.md).
````
