# Harvest galivelop-image-generator — 2026-11-11

De `71a69a34` a `db9c3645` (`scripts/harvest.py`). 129 commits de marca, portal, motor y worker; ninguno toca skills,
scripts ni `.claude/` del flujo. Lo nuevo sale de 3 retros. Recogida de cierre de la `0.6` (H18).

## P1. `backport.sh` para sacar parches desde la rama protegida

- **Source:** `docs/records/retro-2026-11-06-fix-0.4.1.md` P3 @ `6e00b0d` (retro)
- **What changes:** un script nuevo (`scripts/backport.sh <sha>...`) que aplica los commits con cherry-pick en orden
  topológico, para en un conflicto y comprueba con `git cherry`; citado en la guía de parches (es/en) y en
  `docs/agent-map.md`.
- **Why it is general:** «solo la última menor recibe parches» (plan §7) obliga a todo proyecto a sacar arreglos así;
  el bucle a mano falló por el orden.
- **Version bump:** minor
- **Status:** proposed

## P2. El encargo de `gw-orchestrate-dealer` dice quién sube

- **Source:** `docs/records/retro-2026-11-11-marca-r9.md` W2 @ `b46f975` (retro)
- **What changes:** la plantilla del encargo dice «commit and push each stable point» y la regla de los worktrees,
  «does not touch the log or push». Una línea propia: en la rama de trabajo sube el subagente; en un worktree, no; y
  la principal mira `git status -sb` al volver.
- **Why it is general:** la contradicción está en la skill; en el proyecto dejó un commit sin subir con la principal
  parada.
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- Bitácora, marca, logo, texturas y worker: contenido propio.

## Already here

- `docs/records/retro-2026-11-11-marca-r9.md` W1 (el `Stop` no ve un push en marcha): `before-stop.py` ya lee el
  marcador `gw-push-in-progress.<pid>` del `pre-push` (D41); el proyecto tiene una copia anterior.
- `docs/records/retro-2026-11-11-relevo-portal-marca.md` (worktree por defecto para el subagente que escribe):
  recogida el 2026-11-04 (P1) y ya en la skill; la copia del proyecto es anterior.
