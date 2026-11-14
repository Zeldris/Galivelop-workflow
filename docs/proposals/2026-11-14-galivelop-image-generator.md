# Harvest galivelop-image-generator — 2026-11-14

De `529468bc` a `1c178d30` (`scripts/harvest.py`). 41 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 2 retros (`docs/records/retro-2026-11-13-leves-y-negative.md`, `docs/records/retro-2026-11-14-segunda-ida-a-main.md`).
Recogida de la `0.7` (H20).

## P1. `red-without-fix.sh` sin `git stash`

- **Source:** `docs/records/retro-2026-11-13-leves-y-negative.md` W1 @ `1c178d30` (retro; segunda vez)
- **What changes:** `scripts/red-without-fix.sh` (l. 160-168) aparta el arreglo en una copia temporal propia en vez
  de `git stash`; se hace junto a E48, que toca el mismo script.
- **Why it is general:** el stash es común a todos los worktrees: con subagentes en paralelo uno puede recoger el
  stash del otro. Pasó dos veces, sin pérdida.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D98

## P2. Rechazar el autor o committer del agente

- **Source:** `docs/records/retro-2026-11-13-leves-y-negative.md` W4 @ `1c178d30` (retro; el proyecto lo hizo en su
  gancho, `796a290`)
- **What changes:** es E41 (pendiente); ver private-project-2 P2.
- **Why it is general:** ningún gancho del flujo comprueba el autor.
- **Version bump:** minor (la de E41)
- **Status:** aprobada (2026-11-14) → E41

## P3. El encargo del dealer dice dónde viven los tests de lo que se toca

- **Source:** `docs/records/retro-2026-11-14-segunda-ida-a-main.md` W2 @ `1c178d30` (retro)
- **What changes:** la plantilla de encargo de `skills/gw-orchestrate-dealer/SKILL.md` nombra dónde viven los tests
  de cada capa tocada (aquí, `tests/test_ui_browser.py` para la interfaz, que el subagente no encontró).
- **Why it is general:** cualquier proyecto con tests por capas.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D103

## Already here

- W2 (check de «Al empezar» filtrado): `scripts/check.sh --quiet` y `checkTailLines`.
- W3 (tope de llamadas en el encargo): `skills/gw-orchestrate-dealer/SKILL.md` y `subagentCap*`.
- W1 de la segunda retro (no cerrar el turno con un subagente escribiendo): `skills/gw-orchestrate-dealer/SKILL.md`.
