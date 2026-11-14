# Harvest private-project-2 — 2026-11-14

De `70b0396a` a `d7e9e7ad` (`scripts/harvest.py`). 27 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro (`docs/records/retro-2026-11-14-f1-instalacion.md`); las otras dos ya se recogieron el 2026-10-27.
Recogida de la `0.7` (H20).

## P1. `changeSize.block` no ve un `Findings:` en párrafo propio

- **Source:** `docs/records/retro-2026-11-14-f1-instalacion.md` R3 @ `f91cd5c` (retro)
- **What changes:** el mismo fallo que world-maker-fantasy P1, visto desde el lector: `scripts/change-size.py`
  (`block()`) lee `%(trailers:key=Findings)`. Se arregla con el rechazo en el `commit-msg` de esa propuesta; no hace
  falta cambiar el lector.
- **Why it is general:** salta «review overdue» con todos los bloques revisados.
- **Version bump:** patch
- **Status:** aprobada (2026-11-14) → D97

## P2. Más evidencia para E41: autor o committer del agente

- **Source:** `docs/records/retro-2026-11-14-f1-instalacion.md` R1 @ `c988357` (retro; 17 commits reescritos con
  force-push)
- **What changes:** E41 (pendiente, `authorDeny` en el `pre-commit`) mira también el committer, y `doctor.py` avisa
  si `git config user.email` es del agente con `agentSignatures: false`. Lo mismo trae galivelop-image-generator P2.
- **Why it is general:** dos proyectos más tuvieron que reescribir historial por ello; E41 sube de prioridad.
- **Version bump:** minor (la de E41)
- **Status:** aprobada (2026-11-14) → E41

## Stays in the project

- R2 (`GIT_AUTHOR_*` y `GIT_COMMITTER_*` en el entorno de la nube): ajuste personal del entorno.
- T1 (`/clear` tras cada paso) y T2 (conectores MCP del arranque): ya cubiertos por `AGENTS.md` y `gw-opt-tokens`.

## Already here

- T3 (`gw-update` reparte los diffs a un subagente): B19.
- `gw-allow-secret` por un comentario de ejemplo en el `pre-commit` de la base: la plantilla actual ya lo trae
  (ver private-project-3 P1 para el CI del PR de actualización).
