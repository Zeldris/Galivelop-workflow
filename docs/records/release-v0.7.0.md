# Release de GitHub `v0.7.0` (textos)

- **Etiqueta:** `v0.7.0`, sobre `c1e75c8` (subida a `main` el 2026-11-15).
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** a mano por el usuario en local (elegido por él): `gh release create v0.7.0 --target c1e75c8 --title "Galivelop-workflow v0.7.0" --notes-file <cuerpo>`, con el cuerpo de abajo.

```text
Galivelop-workflow v0.7.0
```

````markdown
## Galivelop-workflow v0.7.0 — 2026-11-15

**ES** · [English below](#en)

Versión «Preguntar» publicada con lo hecho; lo pendiente de la `0.7` pasa a la `0.8`.

### Autoría y CI

- El `pre-commit` rechaza un autor o committer de `authorDeny`; el `pre-push` y el CI comprueban cada commit nuevo.
- El check valida el YAML de `.github/workflows/*.yml` (`ciYamlCheck`); `apply.py --update` lo añade a los
  proyectos ya instalados.

### Instalar y actualizar

- `apply.py --dry-run --summary`: el ensayo muestra renombrados, actualizaciones de plantilla y el diff de `REVIEW` y
  `GLOSSARY` entre versiones.
- Un gancho `PreToolUse` avisa, sin bloquear, al editar una copia generada del flujo y nombra su fuente.

### Subagentes y tokens

- El dealer lanza cada trozo con `gw-worker` y cada revisión con el nuevo `gw-reviewer`, con el `model` y el
  `effort` de su peldaño (arrancan con ~13-20k en vez de ~65-68k); `general-purpose` queda para lo que necesita
  skills, web o MCP. `subagent-cap.py` lo recuerda.
- El libro de tokens no lleva commits propios (`commitLedger`); `measure.py` no cuenta como archivos los argumentos
  de `git config`.

### Tests y retro

- Un único factor `GW_TEST_TIMEOUT_SCALE` para las esperas de los tests; `red-without-fix.sh` revierte solo el
  arreglo dentro del archivo del test.
- La `retro` propone una tarea de barrido con los leves pendientes de un mismo script.
- `version.py --release` cuenta la recogida que un parche se trajo de la rama de la menor.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update`, y luego `python3 .claude/gw/scripts/doctor.py`. Claves nuevas
en `.claude/gw.json`, con su valor por defecto: `authorDeny`, `ciYamlCheck` y `metrics.commitLedger`.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.7.0/CHANGELOG.md).

<a id="en"></a>

**EN**

«Preguntar» release shipped with what was done; what was pending in `0.7` moves to `0.8`.

### Authorship and CI

- The `pre-commit` rejects an author or committer in `authorDeny`; the `pre-push` and CI check every new commit.
- The check validates the YAML of `.github/workflows/*.yml` (`ciYamlCheck`); `apply.py --update` adds it to
  already installed projects.

### Install and update

- `apply.py --dry-run --summary`: the dry run shows renames, template updates and the `REVIEW` and `GLOSSARY` diff
  between versions.
- A `PreToolUse` hook warns, without blocking, when editing a generated copy of the workflow, naming its source.

### Subagents and tokens

- The dealer launches each chunk with `gw-worker` and each review with the new `gw-reviewer`, with its rung's
  `model` and `effort` (they start at ~13-20k instead of ~65-68k); `general-purpose` stays for what needs skills,
  web or MCP. `subagent-cap.py` reminds it.
- The token ledger gets no commits of its own (`commitLedger`); `measure.py` no longer counts `git config`
  arguments as files.

### Tests and retro

- A single `GW_TEST_TIMEOUT_SCALE` factor for test waits; `red-without-fix.sh` reverts only the fix inside the
  test file.
- The `retro` proposes a sweep task with the open minors of one script.
- `version.py --release` counts the harvest a patch brought from the minor's branch.

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. New keys in
`.claude/gw.json`, with their defaults: `authorDeny`, `ciYamlCheck` and `metrics.commitLedger`.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.7.0/CHANGELOG.md).
````
