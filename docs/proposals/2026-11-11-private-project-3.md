# Harvest private-project-3 — 2026-11-11

De `195bb867` a `5f67bd4a` (`scripts/harvest.py`). 16 commits: la fase F1 (núcleo), con módulos copiados de otro
proyecto; sin cambios en `.claude/` ni en scripts del flujo. Lo nuevo sale de 1 retro. Recogida de cierre de la `0.6`
(H18).

## P1. Tipo de subagente ligero para los encargos del dealer

- **Source:** `docs/registros/retro-2026-11-11-f1.md` R3 @ `27c589e` (retro)
- **What changes:** la plantilla del encargo de `skills/gw-orchestrate-dealer/SKILL.md` nombra un `subagent_type`
  definido en `.claude/agents/<tipo>.md` con solo las herramientas del encargo (y `model:`/`effort:`), y repite que
  otro repositorio se lee y no se modifica; `gw-init` crea ese tipo (p. ej. `gw-worker`). `subagent-cap.py` y
  `agentFields` ya entienden esas definiciones.
- **Why it is general:** con `general-purpose`, cada subagente arranca con ~68k (herramientas MCP y skills); medido
  en 5 subagentes y 88 llamadas. Pasa en cualquier proyecto con muchas herramientas MCP.
- **Version bump:** minor
- **Status:** aprobada (2026-11-11) → B28
