# Harvest private-project-6 — 2026-11-15

De `1c178d30` a `6e73f1ec` (`scripts/harvest.py`). 108 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 4 retros. Recogida de cierre de la `0.7` (usuario, 2026-11-15).

## P1. Los arreglos tras la fusión van a un subagente nuevo

- **Source:** `docs/records/retro-2026-11-15-sexta-tanda.md` P2 @ `8f7b999` (retro)
- **What changes:** `skills/gw-orchestrate-dealer/SKILL.md` manda devolver los arreglos al subagente original, pero
  `scripts/merge-branch.sh` borra su worktree al fusionar. El paso 3 dice que, tras la fusión, los arreglos van a un
  subagente nuevo con el archivo de hallazgos (la alternativa, `--keep-worktree`, sería minor).
- **Why it is general:** contradicción entre la skill y el script, en cualquier proyecto que reparta.
- **Version bump:** patch
- **Status:** aprobada (2026-11-15) → D111

## P2. El revisor recibe los leves ya apuntados

- **Source:** `docs/records/retro-2026-11-14-tercera-ida-a-main.md` W1 @ `2d2c91d` (retro)
- **What changes:** el encargo de la fase 1 (`AGENTS.md` y su plantilla, o `scripts/review-scope.py`, que imprimiría
  la ruta de `pendingFile`) pasa al revisor la lista de pendientes con «no informes de lo que ya está aquí».
- **Why it is general:** cualquier proyecto con `pendingFile` repite hallazgos en cada revisión.
- **Version bump:** patch
- **Status:** aprobada (2026-11-15) → D113

## P3. Un script lista los llamadores de lo que cambia una rama

- **Source:** `docs/records/retro-2026-11-15-quinta-tanda.md` P4 @ `6177066` (retro)
- **What changes:** un script nuevo (p. ej. `scripts/callers.py`, con su clave, `config.md` y tests) saca las
  funciones tocadas por el diff y sus usos fuera de la rama; el encargo del revisor de `gw-orchestrate-dealer`, que
  hoy pide un `grep` a mano, recibe su salida. Riesgo: ruido con nombres comunes.
- **Why it is general:** convierte en comprobación lo que hoy depende de la memoria del revisor.
- **Version bump:** minor
- **Status:** no aprobada (2026-11-15)

## Already here

- P2 de la cuarta tanda (los paralelos no corren la suite y esperan con `Monitor`): `skills/gw-orchestrate-dealer/SKILL.md`
  ya lo dice (esperas con `Monitor`; los paralelos, solo tests relacionados).
- W2 (el gancho de parada con el check en segundo plano): `scripts/before-stop.py` no bloquea mientras está el
  `check.lock`.

## Stays in the project

- Las tandas de imágenes, la marca y el generador.
