# Harvest private-project-1 — 2026-11-05

De `a048746e` a `aefe95ab` (`scripts/harvest.py`), recogida de inicio de la `0.6`. 1 commit, sin tocar las copias del
flujo (`.claude/gw/` sigue en la `0.5.0`).

## P1. El check ve lo que el `pre-push` rechaza en la bitácora

- **Source:** `docs/records/retro-2026-11-05-ar-23-imagen.md` @ `aefe95a` (retro, R3)
- **What changes:** `scripts/check.sh` solo corre las órdenes de `check`, y ninguna de la plantilla mira la
  bitácora; la fecha de «Actualizado» y los ids que chocan con `main` solo salen en `prepush-branches.sh`. Un
  subcomando (`handoff.py preflight`) que corra sin subir `check --date <hoy>` y `clash HEAD
  refs/remotes/origin/<protectedBranch>`, en el `check` de `templates/gw.json` y en `tests/check.sh`.
- **Why it is general:** en todo proyecto con `logRows: true`, un check en verde no basta para subir: cuesta un viaje
  de push de más.
- **Version bump:** minor
- **Status:** proposed

## P2. Las plantillas de `AGENTS.md` nombran `handoff.py set-row`

- **Source:** `docs/records/retro-2026-11-05-ar-23-imagen.md` @ `aefe95a` (retro, R2)
- **What changes:** una línea en `templates/*/AGENTS.md`: la fila propia de la bitácora, con `handoff.py set-row`; al
  cerrar, `close-row` (hoy solo lo dice `docs/es/patterns.md`).
- **Why it is general:** el agente reescribió la fila tres veces con heredocs de Python (~33k tokens) porque no
  encontró la orden.
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- R1 (un hueco de su propio mapa para agentes) y R4 (la revisión con otro modelo, ya decidida sin cambio).
