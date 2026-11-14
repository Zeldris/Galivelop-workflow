# Harvest instalador-wmf-tarkor — 2026-11-14

De `bf7eb5fd` a `9fce3d18` (`scripts/harvest.py`). 26 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro (`docs/records/retro-2026-11-14-ins-47-flu-9.md`, P2 y P3). Recogida de la `0.7` (H20).

## P1. El check valida los YAML de `.github/workflows/`

- **Source:** `docs/records/retro-2026-11-14-ins-47-flu-9.md` P2 @ `27d57a3` (retro; un nombre de paso sin comillas
  en `app.yml` dejó el flujo sin arrancar y sin rojo)
- **What changes:** `tests/check.sh` y la plantilla de check de los proyectos parsean cada
  `.github/workflows/*.yml` con el lector de `scripts/ci-local.py`; clave en `.claude/gw.json` para apagarlo.
- **Why it is general:** un workflow con YAML inválido no corre, así que ningún CI da rojo.
- **Version bump:** minor
- **Status:** aprobada (2026-11-14) → E51

## P2. En CI, el script de instalación del entorno falla en su paso

- **Source:** `docs/records/retro-2026-11-14-ins-47-flu-9.md` P2 @ `0a545ad`, `aa77905` (retro)
- **What changes:** regla de criterio en la guía de entorno: en CI, el script de instalación falla en su propio paso
  con el final de su log, no en el siguiente.
- **Why it is general:** cualquier proyecto con instalación en CI pierde tiempo buscando el fallo dos pasos después.
- **Version bump:** minor
- **Status:** aprobada (2026-11-14) → E53

## Already here

- P3 (`test_measure.py` no encuentra `config.py` en un proyecto): el `skills/gw-opt-ai/scripts/test_measure.py`
  actual ya lo busca en `.claude/gw/` (E18, A13).

## Stays in the project

- INS-47 (licencias de terceros) y commits de bitácora, métricas y autoría.
