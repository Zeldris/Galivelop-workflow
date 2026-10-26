# Harvest world-maker-fantasy — 2026-10-26 (ventana de la 0.4.1)

De `b36cc5e0` a `948ea734` (`scripts/recoger.py`, 61 commits; `main` del proyecto). Las ideas salen de las retros
`docs/registros/retro-2026-10-25-lore-enciclopedia.md` y `docs/registros/retro-2026-10-25-plan-imagenes.md`, y de
QA-250. Según el plan §7, la `0.4` solo recibe correcciones: lo evolutivo va marcado «para la 1.0.0» y se apunta en
la rama `version/1.0.0`.

## P1. `config.py` y los scripts de shell buscan la raíz bien dentro de un worktree

- **Source:** `docs/registros/retro-2026-10-25-plan-imagenes.md:46-48` @ `8d4912e8` (script)
- **What changes:** `scripts/config.py` (`git_toplevel`, líneas 40-46, y `find_root`, 94-108) no cae en
  `CLAUDE_PROJECT_DIR` (línea 103) ni lee la config de la copia principal cuando el script corre en un worktree sin
  `--root`; los `.sh` que hacen `git -C "$here" rev-parse` quitan `GIT_DIR`/`GIT_WORK_TREE` antes, como ya hacen los
  ganchos. Un test con un worktree de verdad.
- **Why it is general:** reproducido en un repo de prueba: dentro de un worktree, el check y `bitacora.py` leen la
  config y la bitácora de la copia principal. Rompe la regla de §4.3 («raíz desde la ruta del script o
  `git rev-parse --show-toplevel`, nunca desde `$CLAUDE_PROJECT_DIR`»).
- **Version bump:** patch (corrección)
- **Status:** aprobada (2026-10-26)

## P2. Ids de tarea que chocan entre ramas paralelas — para la 1.0.0

- **Source:** `docs/registros/retro-2026-10-25-lore-enciclopedia.md` @ `84378f3d` (retro)
- **What changes:** que `bitacora.py` (o un script nuevo) detecte, al traer `main`, un id de tarea (`taskId`, hoy solo
  un regex en `bitacora.py:89`) dado de alta a la vez en dos ramas; unas 60-100 líneas.
- **Why it is general:** dos sesiones en paralelo cogieron el mismo número siguiente; cualquier proyecto con ramas por
  sesión lo puede repetir.
- **Version bump:** minor → **para la 1.0.0** (evolutivo)
- **Status:** aprobada (2026-10-26)

## P3. `recuperar.py --estado` enseña los otros worktrees — para la 1.0.0

- **Source:** QA-250 en el proyecto @ `948ea734` (script; `tools/qa/tests/test_recuperar.py`)
- **What changes:** `other_worktrees(root)` con `git worktree list --porcelain` y, por cada worktree, su rama y su
  fila de la bitácora; unas 15-20 líneas, test y CHANGELOG.
- **Why it is general:** tras una compactación, la sesión no sabe que tiene subagentes trabajando en worktrees.
- **Version bump:** minor → **para la 1.0.0** (evolutivo)
- **Status:** aprobada (2026-10-26)

## Ya está aquí

- `revisado.sh` con un `commit-msg` que pide «Siguiente:»: `revisado.sh --footer` desde la 0.3.0 (duplicado de
  `2026-10-25-world-maker-fantasy.md`).
- Ganchos en worktrees: ya hacen `unset GIT_DIR` (P2 de `2026-10-23-world-maker-fantasy.md`); lo que falta es la P1.

## Se queda en el proyecto

- `tools/qa/mapa-agente.py`: el flujo ya trae la versión general (`scripts/mapa-agente.py`).
