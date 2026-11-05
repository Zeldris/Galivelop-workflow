# Release de GitHub `v0.5.1` (textos)

- **Etiqueta:** `v0.5.1`, sobre `eeec886` (se sube desde una sesión local, que dispara `release.yml`, o la crea el usuario a mano).
- **Título:** el del bloque de abajo.
- **Cuerpo:** el del segundo bloque. La entrada completa está en el CHANGELOG.

## Título

```text
Galivelop-workflow v0.5.1
```

## Cuerpo

```markdown
## Galivelop-workflow v0.5.1 — 2026-11-05

**ES** · [English below](#en)

Parche de la `0.5` «Base»: arreglos de la recogida de inicio de la `0.5.1`, de la recogida de cierre (opcional) y de
la retro de la `0.5.0`. Lo evolutivo de esas recogidas va a la `0.6`.

### Check y subidas

- **`check.sh` (E20, E23):** registro fijo en `.git/gw/check-<sha>.log`, cerrojo con dueño (el robo de uno caducado
  va bajo un mutex y nunca borra uno vivo) y una línea final `CHECK ok|FAILED` con las secciones que fallaron;
  `merge-branch.sh` lo usa y apunta el verde. La caché del verde incluye los archivos ignorados que lee el check
  (`checkCacheInputs`, por defecto `.claude/gw.local.json`).
- **`pre-push` (D44, D47):** no repite el check de un commit que solo añade la marca de revisión; si para por datos
  privados, dice qué commits no están subidos y da el `--amend` o el `rebase` solo sobre ellos. Distingue un hallazgo
  de `private-check` de un fallo del script o del cerrojo.
- **Gancho `Stop` (D41):** mientras corre un check o un push, avisa en una línea sin pedir subir.

### Actualizar un proyecto

- **`apply.py --update` (D45, D46, D51, D52):** conserva los pasos propios del CI del proyecto; lista los usos de
  nombres viejos (A8); no siembra la plantilla de la bitácora en el destino de una carpeta que mueve; conserva un
  script viejo solo si algo lo llama por su ruta instalada.
- **`settings.json` instalado (D6):** `worktree.baseRef: "head"`.

### Ganchos y guías

- **`pre-commit` (E25):** la regla QUOTED ya no toma por secreto una etiqueta citada en un `.md`.
- **`red-without-fix.sh` (E26):** no busca código de test en textos y datos (`nonTestExtensions`, configurable).
- **Guías (B17, E24, retro `0.5.1`):** en `gw-orchestrate-dealer`, un subagente que escribe en segundo plano va en un
  worktree, corre los tests de lo que toca y los ids del roadmap se commitean antes de repartir; un solo check
  completo tras fusionar la oleada. `patterns.md` y la plantilla de `REVIEW.md` piden una prueba con lo real de lo
  probado con un doble.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.1/CHANGELOG.md).

<a id="en"></a>

**EN**

Patch of `0.5` "Base": fixes from the `0.5.1` opening harvest, the (optional) closing harvest and the `0.5.0` retro.
New features from those harvests go to `0.6`.

### Check and pushes

- **`check.sh` (E20, E23):** fixed log at `.git/gw/check-<sha>.log`, an owned lock (stealing a stale one runs under a
  mutex and never deletes a live one) and a final `CHECK ok|FAILED` line naming the failed sections;
  `merge-branch.sh` uses it and records the green. The green cache includes the ignored files the check reads
  (`checkCacheInputs`, default `.claude/gw.local.json`).
- **`pre-push` (D44, D47):** does not rerun the check for a commit that only adds the review mark; when it stops on
  private data, it says which commits are not pushed and gives the `--amend` or `rebase` over them only. It tells a
  `private-check` finding from a script or lock failure.
- **`Stop` hook (D41):** while a check or a push runs, it warns in one line without asking to push.

### Updating a project

- **`apply.py --update` (D45, D46, D51, D52):** keeps the project's own CI steps; lists uses of old names (A8); does
  not seed the log template at the destination of a folder it moves; keeps an old script only if something runs it by
  its installed path.
- **Installed `settings.json` (D6):** `worktree.baseRef: "head"`.

### Hooks and guides

- **`pre-commit` (E25):** the QUOTED rule no longer takes a label quoted in a `.md` for a secret.
- **`red-without-fix.sh` (E26):** does not look for test code in text and data files (`nonTestExtensions`,
  configurable).
- **Guides (B17, E24, `0.5.1` retro):** in `gw-orchestrate-dealer`, a subagent that writes in the background works in
  a worktree and runs the tests of what it touches, and roadmap ids are committed before dealing; one full check after
  merging the wave. `patterns.md` and the `REVIEW.md` template ask for a real-thing test of what a double tests.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.1/CHANGELOG.md).
```
