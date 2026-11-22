# Harvest galivelop-image-generator — 2026-11-22

De `61ce5096` a `f025f40` (`scripts/harvest.py`). Sin skills ni scripts del flujo cambiados (copias de `da1a462`,
`0.8.1`); lo nuevo sale de `docs/records/retro-2026-11-19-gw-0.8.1.md`. Recogida de cierre de la `0.9` y del parche
`0.8.2` (2026-11-22).

## P1. El ledger de métricas no ensucia el árbol entre turnos

- **Source:** `docs/records/retro-2026-11-19-gw-0.8.1.md` P1 @ `bd4284b` (retro; retoma la P2 de
  `retro-2026-11-16-barrido-b.md`)
- **What changes:** `metrics.py record` escribe en un archivo ignorado (p. ej. `ledger.spool.jsonl` o
  `<git common dir>/gw/`) y `metrics.py stage-ledger` (B36) lo vuelca a `docs/metrics/ledger.jsonl` en el `pre-commit`
  del siguiente commit de trabajo. Hay que diseñarlo junto con B2 de `pending.md` (el ledger de la última parada se
  pierde si muere el contenedor).
- **Why it is general:** B36 quitó los commits propios del ledger, pero el árbol sigue sucio tras cada turno y el
  gancho `Stop` del entorno de la nube (que no es nuestro) pide subir cada vez: 4 turnos de más aquí (~1,1M de caché),
  5 en private-project-3 (~0,5M), commits solo de ledger en private-project-1 (3 y 7) e instalador-wmf-tarkor (una
  docena en un PR, con el CI siempre en cola). Lo traen cuatro proyectos.
- **Version bump:** minor
- **Status:** aprobada (2026-11-22) → E79

## P2. `apply.py --dry-run --summary` resume los avisos de nombres viejos

- **Source:** `docs/records/retro-2026-11-19-gw-0.8.1.md` P2 @ `bd4284b` (retro)
- **What changes:** con `--summary`, `plan_legacy_names` da un recuento por nombre viejo y la orden
  `git grep -n -F '<nombre>'`, no una línea por aviso.
- **Why it is general:** ~50 líneas (2,9k tokens, arrastrados con 118k de contexto), el resultado más pesado de la
  sesión; contradice el propósito de `--summary` (E52).
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D161

## P3. El aviso de nombres viejos no salta en citas de otros repos

- **Source:** `docs/records/retro-2026-11-19-gw-0.8.1.md` P4 @ `bd4284b` (retro)
- **What changes:** como mínimo, el aviso sugiere `legacyNamesSkip` para el archivo; mejor, `plan_legacy_names` no
  avisa en una línea que cita una ruta de otro repo junto a un commit.
- **Why it is general:** renombrar esas citas las rompería; el proyecto acabó con `legacyNames: false`, que apaga
  también los avisos buenos.
- **Version bump:** patch (el texto del aviso); minor (detectar las citas)
- **Status:** aprobada (2026-11-22) → D165, E83

## Stays in the project

- P5: un worktree de agente con la rama ya fusionada y cambios sin guardar; lo decide la persona.

## Already here

- P3 de la retro (`measure.py` sin `--session` mide una sesión vieja): `pending.md`, para la `0.8.2` (era «D142», id
  que choca con el D142 del roadmap; pasa a D144).
