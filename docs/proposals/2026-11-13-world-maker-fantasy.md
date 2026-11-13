# Harvest world-maker-fantasy — 2026-11-13

De `d8ef94ad` a `3a10a3fa` (`scripts/harvest.py`); sin skills ni scripts del flujo cambiados. Lo nuevo sale de 1
retro. Recogida de la `0.6.0` (H19).

## P1. `handoff.py closed` da la orden que lo arregla

- **Source:** `docs/records/retro-2026-11-11-tandas-117-118-a-main.md` punto 3 @ `07097351` (retro)
- **What changes:** el aviso «`<ID>` is closed in the plan; list it in the "Done" section» de `scripts/handoff.py`
  (`cmd_closed`) añade `fix: python3 <ruta>/handoff.py done '<ID>: <qué se hizo>'`.
- **Why it is general:** hoy manda a editar la bitácora a mano aunque la orden existe; es la regla de los mensajes de
  los scripts (`AGENTS.md`: «en inglés con la orden que arregla el fallo»).
- **Version bump:** patch
- **Status:** aprobada (2026-11-13) → D90
