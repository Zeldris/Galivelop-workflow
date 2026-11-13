# Harvest instalador-wmf-tarkor — 2026-11-13

De `84c5c1b2` a `bf7eb5fd` (`scripts/harvest.py`); sin skills ni scripts del flujo cambiados. Lo nuevo sale de 3
retros. Recogida de la `0.6.0` (H19).

## P1. `red-without-fix.sh` con el test en el mismo archivo que el arreglo

- **Source:** `docs/records/retro-2026-11-11-ins45.md` @ `2635e765` y `docs/records/retro-2026-11-12-ins-59.md` @
  `db30ecfb` (retro, dos veces)
- **What changes:** `scripts/red-without-fix.sh` acepta revertir solo el arreglo dentro del archivo: `--patch
  <arreglo.diff>` (lo aplica al revés, corre el test y lo vuelve a aplicar) o `--lines A-B`.
- **Why it is general:** los tests en línea (`#[cfg(test)] mod tests` de Rust, doctests, `if __name__` con asserts)
  son lo normal en varios lenguajes; hoy el script se niega y el rojo se comprueba a mano.
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → E48

## P2. `merge-branch.sh` y el `Siguiente:` de `commitNext`

- **Source:** `docs/records/retro-2026-11-11-ins45.md` @ `2635e765` (retro)
- **What changes:** los ejemplos de `merge-branch.sh` en la plantilla de `AGENTS.md` y en
  `skills/gw-orchestrate-dealer/SKILL.md` llevan el trailer `Siguiente:`, o el script acepta `--next "<paso>"`.
- **Why it is general:** con `commitNext: true` (el defecto desde D59) el ejemplo tal cual falla con salida 2.
- **Version bump:** patch
- **Status:** aprobada (2026-11-13) → D91

## P3. `handoff.py add-pending` y `add-decision`

- **Source:** `docs/records/retro-2026-11-11-ins45.md` @ `2635e765` (retro)
- **What changes:** dos subórdenes que añaden una línea a «Pendiente» o a las decisiones de la bitácora sin leerla.
- **Why it is general:** en esa tarea la bitácora se leyó 40 veces (~397k tokens arrastrados) solo para añadir líneas.
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → D95

## Stays in the project

- `docs/records/retro-2026-11-11-ins15.md`: sus dos propuestas dependen de los documentos del proyecto.
