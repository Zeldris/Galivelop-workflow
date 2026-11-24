# Harvest galivelop-image-generator — 2026-11-24

De `f025f40` a `7c2f412` (`scripts/harvest.py`). 17 commits; ningún skill ni script cambiado. Lo nuevo sale de
`docs/records/retro-2026-11-22-gw-0.8.2.md` y `docs/records/retro-2026-11-24-gw-0.9.0.md`.

## P1. `workflowClone` se busca también en la disposición de la nube

- **Source:** `docs/records/retro-2026-11-24-gw-0.9.0.md` P3 @ `20025ee` y `retro-2026-11-22-gw-0.8.2.md` P1 @ `78f9eb0`
  (script + skill); la repiten `private-project-3` P1 y `private-project-2` P5
- **What changes:** `config.py` ofrece una sola búsqueda del clon del flujo (`../<repo>`, `../<owner>/<repo>` y
  `/home/user/<owner>/<repo>`, sin distinguir mayúsculas; lista configurable) que usan `doctor.py`, `apply.py`,
  `review-scope.py` y `gw-update`, antes de avisar. Amplía D158.
- **Why it is general:** `add_repo` deja el clon en `/home/user/<owner>/<repo>` en minúsculas; cada proyecto en la
  nube recibe el aviso de `doctor.py` y busca el clon a mano (cuatro proyectos lo han contado).
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B48 (`0.9.1`)

## P2. `other-repo-read.py` no avisa al correr `apply.py` del clon

- **Source:** `retro-2026-11-24-gw-0.9.0.md` P2 @ `20025ee` (script); la repite `private-project-2` G2
- **What changes:** el aviso salta solo en lecturas (`cat`, `git diff`, `Read`) bajo `workflowClone`, y no cuando se
  corre `python3 <workflowClone>/scripts/apply.py`, que `gw-update` exige.
- **Why it is general:** ruido en el paso de actualización de todos los proyectos. Exentar solo `apply.py`, no todo
  script del clon: una lectura disfrazada de ejecución sigue avisando.
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B49 (`0.9.1`)

## P3. `review-scope.py` avisa de un árbol sin confirmar

- **Source:** `retro-2026-11-24-gw-0.9.0.md` P1 @ `20025ee` (script)
- **What changes:** con el árbol sucio imprime una línea («commit first or pass `--worktree`») y admite `--worktree`.
  Hoy solo mira commits y, antes de confirmar, lista solo la bitácora y el ledger: parece que no hay nada que revisar.
- **Why it is general:** cualquier proyecto que corra el alcance antes de confirmar.
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B54 (`0.9.1`)

## P4. `gw-update`, paso 1: rama nueva y ledger

- **Source:** `retro-2026-11-24-gw-0.9.0.md` P4 @ `20025ee` (skill); junto con `private-project-2` G1
- **What changes:** el paso 1 comprueba `git rev-list --count HEAD..origin/<protectedBranch>` y, si no es 0, para y
  propone `merge-main.py` o una rama nueva desde la protegida; y dice que la rama nueva más el merge de la anterior
  choca con el ledger sin confirmar (`merge-main.py` lo confirma antes, o se aparta).
- **Why it is general:** ocurre en cada ciclo de actualización.
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B51 (`0.9.1`)

## Joined to another proposal

- Retro 0.8.2 P2 (el `pre-push` ensucia el árbol con el ledger): con `2026-11-22-galivelop-image-generator.md` P1 y B2.

## Stays in the project

- Retro 0.8.2 P3 (rama base del `gw-0.8.2`, ya aplicada en su fila de actualización) y las medidas de gasto (76 % de
  arranque fijo, sin propuesta).
