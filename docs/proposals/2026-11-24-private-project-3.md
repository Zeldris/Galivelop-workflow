# Harvest private-project-3 — 2026-11-24

De `d7d8def` a `aeca90d` (`scripts/harvest.py`). 10 commits; skills, scripts y `gw.json` iguales a los del flujo
(`0.8.2` instalado). Lo nuevo sale de `docs/records/retro-2026-11-22-gw-update-0-8-2.md`.

## P1. Clon del flujo en la disposición de `add_repo`

- **Source:** `retro-2026-11-22-gw-update-0-8-2.md` P3 @ `1580d1f` (script + skill)
- **What changes:** igual que `2026-11-24-galivelop-image-generator.md` P1: `doctor.py`, `review-scope.py` y
  `gw-update` prueban `/home/user/<owner>/<repo>` y `/home/user/<repo>` en minúsculas antes de avisar (observado:
  `/home/user/zeldris/galivelop-workflow`), con un ayudante común en `config.py` y lista configurable.
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B48 (`0.9.1`)

## Joined to another proposal

- Retro P2 (el ledger fuera del árbol): con `2026-11-22-galivelop-image-generator.md` P1; un caso más de la nube.

## Stays in the project

- Retro P4 (`instructionLines.warn` a 160 en su `gw.json`) y P1 (desconectar Claude Docs, lo hace la persona).

## Sin novedades

- `private-project-4`: nada desde `6cc80cc` (la recogida anterior). `private-project-1`: no se ha recogido en esta ronda
  (no se pudo añadir su repo en solo lectura); sigue en `f646009`.
