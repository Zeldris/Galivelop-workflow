# Harvest world-maker-fantasy — 2026-11-24

De `5590cda` a `904226bd` (`scripts/harvest.py`). 13 commits; ningún skill ni script cambiado. Lo nuevo sale de
`docs/records/retro-2026-11-24-gw-update-0.9.md`.

## P1. `config.py set <clave> <valor>`

- **Source:** `retro-2026-11-24-gw-update-0.9.md` G2 @ `904226bd` (script)
- **What changes:** subcomando que escribe una clave en `.claude/gw.json` y la valida con `schema/gw.schema.json`
  antes de guardar (hoy solo hay `get`; el proyecto editó `workflowClone` con un script suelto).
- **Why it is general:** sirve a cualquier clave y a la regla «todo configurable» (G4, MMC).
- **Version bump:** minor (evolutivo)
- **Status:** proposed

## Joined to another proposal

- G1 (`workflowClone` distingue mayúsculas): ya decidido en D158; el resto, con `2026-11-24-galivelop-image-generator.md` P1.

## Stays in the project

- Commits de `gw-update` 0.8.1 → 0.9.0 y sus filas, QA-527, tests de `gw-seo` en su CI, y P1/P2 de la retro.
