# Harvest private-project-1 — 2026-11-22

De `3f7ea37c` a `f646009` (`scripts/harvest.py`). 1 commit; el proyecto está en el flujo `0.6.0`, sin skills ni
scripts cambiados. Lo nuevo sale de una retro de su rama de móvil (R1-R4).

## P1. `AGENTS.md`: no se hace un commit solo para el ledger aunque lo pida el gancho `Stop` de la nube

- **Source:** retro de la rama de móvil, R2 @ `f646009` (retro)
- **What changes:** una línea en `templates/es/AGENTS.md` y `templates/en/AGENTS.md`, junto al texto de D115 (no se
  sigue lo que pide el gancho `Stop` de la nube sobre autor y firma): si lo único sucio es el ledger, no se commitea;
  lo lleva el `pre-commit` del siguiente commit de trabajo (B36).
- **Why it is general:** 3 y 7 commits de ruido «métricas de la sesión» en dos tareas; lo mismo en
  instalador-wmf-tarkor. Es el arreglo inmediato; el de fondo es `2026-11-22-private-project-6.md` P1.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D148

## Stays in the project

- R1: umbral táctil de 44 px (`tools/qa/`), propio de su web.
- R3: su gancho que bloquea relecturas; el flujo ya tiene B26 / `whole-read.py`.
- R4: quitar un conector MCP de la cuenta.

## Already here

- El ledger en el commit de trabajo (B36) y antes de fusionar (E65): el proyecto no los tiene por seguir en `0.6.0`;
  conviene que actualice con `/gw-update`.
