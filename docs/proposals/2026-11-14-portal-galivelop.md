# Harvest portal-galivelop — 2026-11-14

De `f7ce4836` a `9b690870` (`scripts/harvest.py`). 25 commits; sin skills ni scripts del flujo cambiados ni retros
nuevas. Recogida de la `0.7` (H20).

## P1. `harvest.py` vuelve a listar ideas ya recogidas al archivar la bitácora

- **Source:** `docs/records/handoff-archive.md` @ `9b690870` (las 4 «ideas» del informe de esta recogida)
- **What changes:** `scripts/harvest.py` saca las secciones `## For Galivelop-workflow` y las líneas «Propuesta
  para el flujo» de las líneas añadidas en el rango, no del archivo entero que cambió; así, mover entradas viejas a
  `handoff-archive.md` no las vuelve a proponer.
- **Why it is general:** cada proyecto que archiva su bitácora repite en cada recogida ideas ya resueltas (aquí, las
  4: D45/D53 y P3-P4 de `2026-10-23-portal-galivelop.md`).
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D101

## Stays in the project

- Trabajo de marca y portadas, la retícula del papel y la actualización a `0.6.0` (`9d48d21`, `cc13697`).

## Sin novedades

- `private-project-1`: de `1f98db62` a `45e3209c`, 1 commit; su retro solo trae cambios del propio proyecto.
- `private-project-4`: primera recogida (proyecto nuevo, con el flujo `0.6.0`); 36 commits sin retros ni secciones
  `## For Galivelop-workflow` todavía.
