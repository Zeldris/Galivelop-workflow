# Release de GitHub `v0.5.2` (textos)

- **Etiqueta:** `v0.5.2`, sobre `2e55d66` (se sube desde una sesión local, que dispara `release.yml`, o la crea el usuario a mano).
- **Título:** el del bloque de abajo.
- **Cuerpo:** el del segundo bloque. La entrada completa está en el CHANGELOG.

## Título

```text
Galivelop-workflow v0.5.2
```

## Cuerpo

```markdown
## Galivelop-workflow v0.5.2 — 2026-11-12

**ES** · [English below](#en)

Parche de la `0.5` «Base»: los arreglos de las recogidas de la `0.6` (H16 y H18) y de la revisión `0.5.1` del
instalador, separados de la rama de la `0.6`. Lo evolutivo sale en la `0.6`.

### Check y subidas

- **`check.sh` (D76, E39, E40):** sin `--quiet` el comando conserva la terminal (colores, barras de progreso) y corre
  toda la lista de `check`; el candado lo actualiza el mismo pid, un `.steal` sin pid no bloquea y se guardan los
  últimos `checkLogKeep` registros.
- **`pre-push` (D78):** vuelve a mirar la caché de verdes tras esperar el candado.
- **`merge-branch.sh` (D77):** valida `check` y `checkWrapper` antes de fusionar.
- **Gancho `Stop` (D88):** no pide subir mientras hay subagentes en segundo plano (`stopTranscriptBytes`,
  `stopSubagentMaxAge`); `before-stop.py` compara el sha completo.

### Contexto y bitácora

- **Arranque (B21, D65):** tras un `/clear` o una compactación, `context_guard.py` compara el primer turno con el punto
  de corte y el `SessionStart` avisa o da la alarma (bucle de compactaciones) con el desglose del culpable. Tope de
  tamaño de la bitácora (`logSize`) y `handoff.py archive` (`logArchive`).
- **`handoff.py` (D58, D71):** `close-row` avisa con `logRows` apagado y toma la rama como `set-row`.
- **`measure.py` (B20, B22, D70):** mide el registro de un subagente, muestra el `action` de Artifact y `--since` elige
  la sesión correcta.

### Versiones, recogidas y guardas

- **`version.py` (D66, D69):** tipo `hotfix` (cuenta como parche) y `--release` exige que `releaseDocs` nombren la
  versión.
- **`harvest.py` (D57):** sigue los renombrados y marca la idea recortada.
- **`private-check.py` (D79)** da un arreglo sin `rebase -i` sobre una etiqueta; **`pre-commit` (E38)** caza un secreto
  de una palabra entre comillas en un `.md`.
- **Plantillas y guías (D59, D60, D64, D72-D75, B23-B25):** `commitNext: true` por defecto; la fase 1 se revisa tras
  `/clear` o en un subagente limpio; `REVIEW.md` pide redirigir la entrada de un comando dentro de un `while read`.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.2/CHANGELOG.md).

<a id="en"></a>

**EN**

Patch of `0.5` "Base": the fixes from the `0.6` harvests (H16 and H18) and from the installer's `0.5.1` review, split
off the `0.6` branch. New features ship in `0.6`.

### Check and pushes

- **`check.sh` (D76, E39, E40):** without `--quiet` the command keeps the terminal (colours, progress bars) and the
  whole `check` list runs; the same pid updates the lock, a `.steal` without pid does not block, and the last
  `checkLogKeep` logs are kept.
- **`pre-push` (D78):** looks at the green cache again after waiting for the lock.
- **`merge-branch.sh` (D77):** validates `check` and `checkWrapper` before merging.
- **`Stop` hook (D88):** does not ask to push while background subagents run (`stopTranscriptBytes`,
  `stopSubagentMaxAge`); `before-stop.py` compares the full sha.

### Context and log

- **Start-up (B21, D65):** after a `/clear` or a compaction, `context_guard.py` compares the first turn with the
  cut-off and `SessionStart` warns or raises the alarm (compaction loop) with the culprit breakdown. A log size cap
  (`logSize`) and `handoff.py archive` (`logArchive`).
- **`handoff.py` (D58, D71):** `close-row` warns with `logRows` off and takes the branch like `set-row`.
- **`measure.py` (B20, B22, D70):** measures a subagent's log, shows Artifact's `action` and `--since` picks the right
  session.

### Versions, harvests and guards

- **`version.py` (D66, D69):** `hotfix` type (counts as a patch) and `--release` requires `releaseDocs` to name the
  version.
- **`harvest.py` (D57):** follows renames and marks a cut idea.
- **`private-check.py` (D79)** gives a fix without `rebase -i` onto a tag; **`pre-commit` (E38)** catches a one-word
  quoted secret in a `.md`.
- **Templates and guides (D59, D60, D64, D72-D75, B23-B25):** `commitNext: true` by default; phase 1 is reviewed after
  `/clear` or in a clean subagent; `REVIEW.md` asks to redirect the input of a command inside a `while read` loop.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.5.2/CHANGELOG.md).
```
