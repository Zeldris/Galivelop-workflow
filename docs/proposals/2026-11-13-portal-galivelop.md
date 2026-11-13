# Harvest portal-galivelop — 2026-11-13

De `48827b11` a `f7ce4836` (`scripts/harvest.py`). 56 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro. Recogida de la `0.6.0` (H19).

## P1. El dealer devuelve el texto literal al aplicar un documento de otro repo

- **Source:** `docs/records/retro-2026-11-12-hoja-generador.md` P3 @ `744e5081` (retro)
- **What changes:** en `skills/gw-orchestrate-dealer/SKILL.md`, cuando la tarea es aplicar un documento de otro repo,
  el subagente que lo lee devuelve cada punto con su texto literal y su ruta, no un resumen.
- **Why it is general:** con un resumen, la sesión principal vuelve a leer el documento para aplicarlo: se paga dos
  veces.
- **Version bump:** patch
- **Status:** aprobada (2026-11-13) → D93

## Sin novedades

- `private-project-1`: de `1f98db62` a `1f98db62`, sin commits en la rama por defecto.
- `private-project-3`: de `5f67bd4a` a `5f67bd4a`, sin commits.
