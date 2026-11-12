# Release de GitHub `v0.5.2` (textos)

- **Etiqueta:** `v0.5.2`, sobre `2e55d66` (la crea el agente con `gh release create`, a petición del usuario).
- **Título:** `Galivelop-workflow v0.5.2`
- **Cuerpo:** lo que va entre las dos rayas de abajo. La entrada completa está en el CHANGELOG.

---

## Galivelop-workflow v0.5.2 — 2026-11-12

**ES** · [English below](#en)

Parche de la `0.5` «Base»: arreglos de las recogidas de la `0.6` (H16 y H18) y de la revisión `0.5.1` del
instalador. No trae evolutivos: esos van a la `0.6` (reparto en `docs/roadmap.md`).

### Contexto de arranque y bitácora

- **`context_guard.py` (B21, D65):** tras un `/clear` o una compactación compara el uso del primer turno con el punto
  de corte, y el `SessionStart` avisa o da la alarma (bucle de compactaciones) con el desglose del culpable.
- **Tamaño de la bitácora (D65):** tope `logSize` y `handoff.py archive`, que mueve lo pendiente de versiones
  publicadas a `logArchive`.
- **`handoff.py` (D58, D71):** `close-row` avisa y sale con 1 con `logRows` apagado y toma la rama como `set-row`.

### Comprobaciones y CI

- **`check.sh` y su candado (D76, E39, E40):** el mismo pid actualiza el candado, un `.steal` sin pid no bloquea y
  `before-stop.py` compara el sha completo; sin `--quiet` conserva TTY y colores (también en macOS); guarda los
  últimos `checkLogKeep` registros.
- **`merge-branch.sh` (D77):** valida `check` y `checkWrapper` antes de fusionar.
- **`version.py` (D66, D69):** tipo `hotfix` (cuenta como parche); `--release` exige que los archivos de
  `releaseDocs` nombren la versión.

### Ganchos

- **`pre-push` (D78):** vuelve a mirar la caché de verdes tras esperar el candado.
- **Gancho `Stop` (D88):** no pide subir mientras hay subagentes en segundo plano (`stopTranscriptBytes`,
  `stopSubagentMaxAge`).
- **`pre-commit` (E38):** caza un secreto de una palabra entre comillas en un `.md`; **`private-check.py` (D79)** da
  un arreglo sin `rebase -i` sobre una etiqueta ni `git add -A`.

### Medir y recoger

- **`measure.py` (B20, B22, D70):** mide el registro de un subagente, muestra el `action` de las llamadas a Artifact
  y `--since` elige la sesión correcta.
- **`harvest.py` (D57):** sigue los renombrados y marca «… (truncated)» la idea recortada a 2000 caracteres.
  **`related-tests.sh` (D74)** da el número de archivos y un temporal con la orden.

### Plantillas, guías y skills

- **Plantillas (D58, D59, D60):** `commitNext: true` por defecto; `AGENTS.md` nombra `handoff.py set-row` y
  `close-row`; la bitácora solo explica `logRows` si está encendido (bloques `<!-- if key -->` de `apply.py`).
- **Guías (D64, D72, D73, D75, B23, B24, B25):** `gw-selector` separa el modelo de la sesión y el de los subagentes;
  el encargo del dealer dice quién sube y qué hacer con el commit; `gw-update` abre el PR; cierre de ronda de
  pruebas; `prototype` publica desde un subagente; la fase 1 se revisa tras `/clear` o en un subagente limpio;
  `gw-scout-updates` con 2 subagentes.
- **`REVIEW.md` (retro `0.5.2`):** pide redirigir la entrada de un comando dentro de un `while read` y probarlo con
  dos elementos.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update` (o `python3 <flujo>/scripts/apply.py <proyecto>`), y luego
`python3 .claude/gw/scripts/doctor.py`. Las claves nuevas del config (`logSize`, `logArchive`, `checkLogKeep`,
`stopTranscriptBytes`, `stopSubagentMaxAge`, `releaseDocs`) son opcionales.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.2/CHANGELOG.md).

<a id="en"></a>

**EN**

Patch of `0.5` "Base": fixes from the `0.6` harvests (H16 and H18) and from the installer's `0.5.1` review. No new
features: those go to `0.6` (split in `docs/roadmap.en.md`).

### Start-up context and log

- **`context_guard.py` (B21, D65):** after a `/clear` or a compaction it compares the first turn's usage with the
  compaction cut-off, and `SessionStart` warns or raises the alarm (compaction loop) with the culprit breakdown.
- **Log size (D65):** a `logSize` cap and `handoff.py archive`, which moves pending items of published versions to
  `logArchive`.
- **`handoff.py` (D58, D71):** `close-row` warns and exits 1 with `logRows` off and takes the branch like `set-row`.

### Checks and CI

- **`check.sh` and its lock (D76, E39, E40):** the same pid updates the lock, a `.steal` without pid does not block
  and `before-stop.py` compares the full sha; without `--quiet` it keeps TTY and colours (on macOS too); it keeps the
  last `checkLogKeep` logs.
- **`merge-branch.sh` (D77):** validates `check` and `checkWrapper` before merging.
- **`version.py` (D66, D69):** `hotfix` type (counts as a patch); `--release` requires the `releaseDocs` files to
  name the version.

### Hooks

- **`pre-push` (D78):** looks at the green cache again after waiting for the lock.
- **`Stop` hook (D88):** does not ask to push while background subagents run (`stopTranscriptBytes`,
  `stopSubagentMaxAge`).
- **`pre-commit` (E38):** catches a one-word quoted secret in a `.md`; **`private-check.py` (D79)** gives a fix
  without `rebase -i` onto a tag or `git add -A`.

### Measuring and harvesting

- **`measure.py` (B20, B22, D70):** measures a subagent's log, shows the `action` of Artifact calls and `--since`
  picks the right session.
- **`harvest.py` (D57):** follows renames and marks an idea cut at 2000 characters with "… (truncated)".
  **`related-tests.sh` (D74)** gives the file count and a temp file with the command.

### Templates, guides and skills

- **Templates (D58, D59, D60):** `commitNext: true` by default; `AGENTS.md` names `handoff.py set-row` and
  `close-row`; the log only explains `logRows` when it is on (`apply.py`'s `<!-- if key -->` blocks).
- **Guides (D64, D72, D73, D75, B23, B24, B25):** `gw-selector` keeps the session's model and the subagents' apart;
  the dealer brief says who pushes and what to do with the commit; `gw-update` opens the PR; closing step of a test
  round; `prototype` publishes from a subagent; phase 1 is reviewed after `/clear` or in a clean subagent;
  `gw-scout-updates` with 2 subagents.
- **`REVIEW.md` (`0.5.2` retro):** asks to redirect the input of a command inside a `while read` loop and to test it
  with two items.

### Updating a project

From a session in the project, the `gw-update` skill (or `python3 <workflow>/scripts/apply.py <project>`), then
`python3 .claude/gw/scripts/doctor.py`. The new config keys (`logSize`, `logArchive`, `checkLogKeep`,
`stopTranscriptBytes`, `stopSubagentMaxAge`, `releaseDocs`) are optional.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.2/CHANGELOG.md).

---
