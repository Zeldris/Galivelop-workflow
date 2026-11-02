# Release de GitHub `v0.4.2` (textos)

- **Etiqueta:** `v0.4.2`, sobre `8a6f367` (la publica a mano el usuario).
- **Título:** `Galivelop-workflow v0.4.2`
- **Cuerpo:** lo que va entre las dos rayas de abajo. La entrada completa está en el CHANGELOG.

---

## Galivelop-workflow v0.4.2 — 2026-10-27

**ES** · [English below](#en)

Parche de correcciones de la segunda recogida del 2026-10-26. La `0.4` solo recibe correcciones; los evolutivos de
esa recogida van a la `1.0.0`.

### Bitácora

- `bitacora.py` ya no sugiere `git commit --amend`. Al hacer commit, dice que se añada el log y se repita el commit;
  al subir, que se haga un commit nuevo con el arreglo.
- Para que ese commit nuevo desbloquee la subida, `prepush-ramas.sh` comprueba el log como queda en la punta que se
  sube, no el de cada commit intermedio.

### Secretos (`pre-commit`)

- Ve las claves con el nombre `api.key` (con punto, como `openai.api.key` en un `.properties`) y las pegadas a un
  proveedor de IA (`openaikey`, `OPENAI_KEY`, `anthropic-key`…).
- A propósito no casa un sufijo `*key` genérico (`primary_key`, `sort_key`, `cache_key`).

### `fusionar.sh`

- Tras el check en verde, corre los tests relacionados (`relatedTests`) de los archivos que trae la fusión, como el
  `pre-push`. Si fallan, la fusión ya está hecha y dice cómo repetirlos y cómo deshacerla.
- Con `relatedTests` configurado y sin `tests-relacionados.sh` instalado, falla en vez de saltárselos.

### `mapa-agente.py`

- Reconoce los métodos con tipo de retorno de Java y otros lenguajes tipados (`.java`, `.kt`, `.cs`, `.kts`,
  `.scala`, `.groovy`), con modificadores, genéricos, anotaciones y `throws`.
- Las palabras de control (`if`, `for`, `while`…) no cuentan como método.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update` (o `python3 <flujo>/scripts/aplicar.py <proyecto>`), y luego
`python3 .claude/gw/scripts/doctor.py`. No hay claves nuevas en el config.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.2/CHANGELOG.md).

<a id="en"></a>

**EN**

Bug-fix patch from the second 2026-10-26 harvest. `0.4` only gets fixes; the new features from that harvest go to
`1.0.0`.

### Hand-off log

- `bitacora.py` no longer suggests `git commit --amend`. At commit time it says to stage the log and run the commit
  again; at push time, to make a new commit with the fix.
- So that this new commit unblocks the push, `prepush-ramas.sh` checks the log as the pushed tip has it, not each
  intermediate commit's.

### Secrets (`pre-commit`)

- It sees keys named `api.key` (with a dot, like `openai.api.key` in a `.properties` file) and keys glued to an LLM
  provider (`openaikey`, `OPENAI_KEY`, `anthropic-key`…).
- On purpose it does not match a bare `*key` suffix (`primary_key`, `sort_key`, `cache_key`).

### `fusionar.sh`

- After a green check, it runs the related tests (`relatedTests`) of the files the merge brings, like the
  `pre-push`. If they fail, the merge is already done and it says how to rerun them and how to undo it.
- With `relatedTests` set and `tests-relacionados.sh` not installed, it fails instead of skipping them.

### `mapa-agente.py`

- It recognises methods with a return type in Java and other typed languages (`.java`, `.kt`, `.cs`, `.kts`,
  `.scala`, `.groovy`), with modifiers, generics, annotations and `throws`.
- Control keywords (`if`, `for`, `while`…) do not count as methods.

### Updating a project

From a session in the project, the `gw-update` skill (or `python3 <workflow>/scripts/aplicar.py <project>`), then
`python3 .claude/gw/scripts/doctor.py`. There are no new config keys.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.2/CHANGELOG.md).

---
