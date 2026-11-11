# Harvest instalador-wmf-tarkor — 2026-11-11

De `a73f8812` a `84c5c1b2` (`scripts/harvest.py`). 51 commits: bitácora, licencia MIT, FLU-7 y FLU-8 (actualización
a la `0.5.1`). Las copias del flujo son iguales a la `0.5.1`. Lo nuevo sale de 2 retros. Recogida de cierre de la
`0.6` (H18).

## P1. `gw-update` termina con el PR a la rama protegida

- **Source:** `docs/records/retro-2026-11-05-licencia-mit.md` P1 @ `b2e9537` (retro)
- **What changes:** último paso de `skills/gw-update/SKILL.md`: abrir el PR de la rama de actualización a la
  protegida antes de otra tarea.
- **Why it is general:** sin él, la actualización se queda en una rama y la siguiente tarea parte del flujo viejo.
- **Version bump:** patch
- **Status:** proposed

## P2. Lo copiado tal cual del flujo, fuera de la revisión (`vendored`)

- **Source:** `docs/records/retro-2026-11-05-licencia-mit.md` P2 @ `b2e9537` y `docs/records/retro-2026-11-11-flu8.md` P1 @ `317b0b1` (retro)
- **What changes:** `gw-update`/`apply.py` marcan lo copiado sin cambios y la fase 1 de `AGENTS.md` lo deja fuera
  del `/code-review`. Vecino de D53 (`ownedFiles`) y B19 (que ya excluye las copias idénticas en la rama de
  actualización); falta que sea regla general de la fase 1.
- **Why it is general:** cada actualización mete cientos de líneas ya revisadas aquí en la revisión del proyecto.
- **Version bump:** minor
- **Status:** proposed

## P3. `doctor.py` avisa de tests que el check no corre

- **Source:** `docs/records/retro-2026-11-05-licencia-mit.md` P3 @ `b2e9537` (retro)
- **What changes:** aviso inverso de `check_skill_tests`: carpetas con `test_*.py` que ningún comando del check
  cubre; carpetas excluidas configurables.
- **Why it is general:** un test que no corre da un verde falso en cualquier proyecto.
- **Version bump:** minor
- **Status:** proposed

## P4. `gw-update` añade a `staleRefs` lo que renombra su migración

- **Source:** `docs/records/retro-2026-11-05-licencia-mit.md` P4 @ `b2e9537` (retro)
- **What changes:** al renombrar rutas o nombres (A8), `apply.py --update` añade los nombres viejos al `staleRefs`
  del proyecto.
- **Why it is general:** sin eso, las referencias viejas vuelven sin aviso tras cada migración.
- **Version bump:** minor
- **Status:** proposed

## P5. `check.yml` con directorios de Node y Rust configurables y caché de Rust

- **Source:** `docs/records/retro-2026-11-05-licencia-mit.md` P5 @ `b2e9537` (retro)
- **What changes:** `templates/github/check.yml` lee los directorios de Node y Rust de `.claude/gw.json` y usa
  `Swatinem/rust-cache`. Lo de correr o no en `main` ya lo cubre D54 (`ciOnPush`); cercano a D63.
- **Why it is general:** cualquier proyecto con la app en una subcarpeta tiene que parchear el CI a mano.
- **Version bump:** minor
- **Status:** proposed

## Stays in the project

- `review-before-main.sh` no reconoce el formato viejo `· en verde` de `ci-local.md`: formato propio anterior,
  migrable a mano.
- Los 14 hallazgos de la revisión de la `0.5.1` que cita la bitácora del proyecto: no se leyeron en esta recogida.

## Already here

- El comentario de `PATHCODE` como secreto en el `pre-commit`: la `0.5.0` ya descarta el par ruta-código.
- `docs/records/retro-2026-11-11-flu8.md` P3 (`handoff.py set-row` en la plantilla de `AGENTS.md`): D60 y D23.
