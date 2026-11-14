# Harvest private-project-3 — 2026-11-14

De `5f67bd4a` a `d7d50956` (`scripts/harvest.py`). 12 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro (`docs/records/retro-2026-11-14-gw-update.md`, R1-R6), de una actualización `0.3.0` → `0.6.0`.
Recogida de la `0.7` (H20).

## P1. `gw-update`: tres arreglos de la skill

- **Source:** `docs/records/retro-2026-11-14-gw-update.md` R1, R5 y R6 @ `d7d50956` (retro; R6, `.githooks/pre-commit`
  @ `bd6d8e0`)
- **What changes:** en `skills/gw-update/SKILL.md`: (R1) se sigue la skill del flujo en la etiqueta de destino, no
  la copia del proyecto, que es de la versión vieja; (R5) el PR se abre tras las tres fases de `AGENTS.md`, no justo
  tras el commit; (R6) el CI del PR corre los ganchos de la rama base: si el `pre-commit` viejo rechaza texto del
  nuevo, se marca con `gw-allow-secret` y se dice en el PR.
- **Why it is general:** cualquier proyecto que se actualice desde una versión vieja choca con las tres.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D99

## P2. `doctorTestDirsIgnore` deja fuera las skills copiadas del flujo

- **Source:** `docs/records/retro-2026-11-14-gw-update.md` R4 @ `d7d50956` (retro)
- **What changes:** el defecto de `doctorTestDirsIgnore` (`schema/gw.schema.json`, `templates/gw.json`) incluye
  `.claude/skills` (este repo ya lo tiene en su `gw.json`); `docs/es/config.md` y `docs/en/config.md`.
- **Why it is general:** cada actualización copia skills con tests que se prueban en el flujo; `doctor.py` avisa de
  ellos en cada proyecto.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D102

## P3. `apply.py --summary` y renombres en el `--dry-run`

- **Source:** `docs/records/retro-2026-11-14-gw-update.md` R2 y R3 @ `d7d50956` (retro)
- **What changes:** `scripts/apply.py --dry-run --summary`: recuentos por acción, solo lo que pide decisión y los
  avisos de nombres viejos sin repetir (el dry-run dio 314 líneas, 87 `create`). Las actualizaciones de plantilla de
  la bitácora y de `.claude/gw/gw-*.md` salen ya en el dry-run (hoy, solo en `--check` tras aplicar), con el mapa de
  nombres viejos aplicado; el diff de `REVIEW.md` y `GLOSSARY.md` pasa a ser plantilla vX → vY. Paso 3 de
  `skills/gw-update/SKILL.md` y docs.
- **Why it is general:** cualquier salto de varias versiones da un dry-run ilegible.
- **Version bump:** minor
- **Status:** aprobada (2026-11-14) → E52

## Stays in the project

- Commits de autoría, métricas, «Revisado:» y bitácora; la actualización misma (`d7d50956`, `d7d993d`, `768b271`).
