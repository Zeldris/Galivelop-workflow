# Harvest private-project-1 — 2026-11-18

De `fd559134` a `3f7ea37c` (`scripts/harvest.py`). 1 commit (un PR fusionado); sin skills ni scripts del flujo
cambiados. Lo nuevo sale de 1 retro (`docs/records/retro-2026-11-15-ar-19-cerebras.md` @ `3f7ea37`). Recogida de
apertura de la `0.9` (2026-11-18).

## P1. Clave `generated`: el check regenera los archivos generados y comprueba que no cambian

- **Source:** `docs/records/retro-2026-11-15-ar-19-cerebras.md` R1 @ `3f7ea37` (retro)
- **What changes:** clave nueva `generated` en `.claude/gw.json` (lista de `{command, paths}`; vacía por defecto),
  leída por `scripts/config.py` y explicada en `docs/es/config.md` ↔ `docs/en/config.md`; `scripts/check.sh` corre
  cada orden y falla con `git diff --exit-code -- <paths>`, diciendo qué orden regenera.
- **Why it is general:** cualquier proyecto que commitea archivos generados (clientes, esquemas, catálogos) puede
  subirlos desfasados sin que el check lo note.
- **Version bump:** minor
- **Status:** aprobada (2026-11-18) → E72

## Stays in the project

- AR-19 (Cerebras fuera de la rotación de proveedores): producto del proyecto.
