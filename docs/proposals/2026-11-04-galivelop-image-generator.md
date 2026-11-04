# Harvest galivelop-image-generator — 2026-11-04

De `e11f87a2` a `849b3012` (`scripts/harvest.py`). El proyecto sigue en la 0.4.3; sus copias viejas no son hallazgos.

## P1. Un subagente que escribe código en segundo plano trabaja siempre en un worktree

- **Source:** `docs/registros/retro-2026-11-04-f2-motor.md` @ `7e7c333` (retro)
- **What changes:** en `skills/gw-orchestrate-dealer/SKILL.md`, la regla de worktrees (hoy solo para arreglos en
  paralelo) cubre también a un único subagente que escribe mientras la sesión principal sigue: va en un worktree y
  vuelve con `merge-branch.sh`; nunca edita el árbol principal.
- **Why it is general:** el gancho `Stop` paró cinco veces la sesión principal por cambios ajenos sin commit (~105k
  tokens cada vuelta) y acabó en un `WIP` con `--no-verify`, rehecho después.
- **Version bump:** patch
- **Status:** aprobada (2026-11-04) → B17

## Stays in the project

- `gimg/doctor.py`: herramienta propia del motor de imágenes (falso positivo por el nombre).
- Plantilla de hoja de estilo (F2.12), `gimg sheet`, `gimg measure`, lecturas de Tarkor y `.claude/gw/opt-tokens.md`.

## Already here

- `.claude/gw/scripts/recuperar.py` cambiado: el presupuesto de compactaciones en `--state`, que la 0.5.0 trae en
  `scripts/recover.py` (B14).
