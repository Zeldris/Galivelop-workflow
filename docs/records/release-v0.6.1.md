# Release de GitHub `v0.6.1` (textos)

- **Etiqueta:** `v0.6.1`, sobre `d28a1a1` (subida a `main` el 2026-11-14; excepción a A-6 aprobada por el usuario).
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Desde local:** `git fetch origin main && git tag v0.6.1 d28a1a1 && git push origin v0.6.1`, que lanza
  `release.yml`; o a mano, `gh release create v0.6.1 --title "<título>" --notes-file <cuerpo>`.

```text
Galivelop-workflow v0.6.1
```

````markdown
## Galivelop-workflow v0.6.1 — 2026-11-14

**ES** · [English below](#en)

Parche de la `0.6` con los arreglos de la recogida `0.7` y las mejoras de la retro del propio parche.

### Pendientes fuera de la bitácora

- «Pendiente» sale de la bitácora a su propio archivo (`pendingFile`, por defecto `docs/records/pending.md`). La
  bitácora deja un puntero con la cuenta, y `handoff.py check --strict` exige que esté al día.
- `handoff.py move-pending` traslada lo que haya, y `archive` trabaja sobre ese archivo.

### Commits y tests

- El `commit-msg` rechaza `Findings:` y `Retries:` fuera del último párrafo de trailers. Al cerrar una fase o una
  versión con el presupuesto de compactaciones superado, pide `/clear`.
- `red-without-fix.sh` ya no usa `git stash`: aparta el arreglo en una copia bajo `.git`.
- `tests-for.py --run` pasa shellcheck a los `.sh` del cambio.
- `roadmap.py check`, en el check, exige los mismos ids por versión en cada idioma del roadmap.

### Aplicación, recogida y skills

- `apply.py` no avisa de nombres viejos en el roadmap ni propone nombres que no existen.
- `harvest.py` solo saca ideas de las líneas añadidas en el rango.
- `doctorTestDirsIgnore` incluye `.claude/skills` por defecto.
- `gw-update` sigue la skill de la etiqueta destino y abre el PR tras las tres fases.
- `gw-orchestrate-dealer` dice dónde viven los tests de cada capa y pide la subida final en primer plano.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. Para sacar los
pendientes de la bitácora, `python3 .claude/gw/scripts/handoff.py move-pending`; la clave `pendingFile` es opcional.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.6.1/CHANGELOG.md).

<a id="en"></a>

**EN**

A `0.6` patch with the fixes from the `0.7` harvest and the improvements from the patch's own retro.

### Pending items out of the hand-off log

- "Pending" moves out of the hand-off log into its own file (`pendingFile`, by default `docs/records/pending.md`).
  The log keeps a pointer with the count, and `handoff.py check --strict` requires it to be current.
- `handoff.py move-pending` moves the existing items, and `archive` works on that file.

### Commits and tests

- The `commit-msg` hook rejects `Findings:` and `Retries:` outside the last trailer paragraph. When a phase or
  version closes with the compaction budget spent, it asks for `/clear`.
- `red-without-fix.sh` no longer uses `git stash`: it sets the fix aside in a copy under `.git`.
- `tests-for.py --run` runs shellcheck on the changed `.sh` files.
- `roadmap.py check`, part of the check, requires the same ids per version in every language of the roadmap.

### Apply, harvest and skills

- `apply.py` no longer warns about old names in the roadmap nor proposes names that do not exist.
- `harvest.py` only takes ideas from the lines added in the range.
- `doctorTestDirsIgnore` includes `.claude/skills` by default.
- `gw-update` follows the skill of the target tag and opens the PR after the three phases.
- `gw-orchestrate-dealer` says where each layer's tests live and asks for the final push in the foreground.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. To move pending
items out of the log, `python3 .claude/gw/scripts/handoff.py move-pending`; the `pendingFile` key is optional.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.6.1/CHANGELOG.md).
````
