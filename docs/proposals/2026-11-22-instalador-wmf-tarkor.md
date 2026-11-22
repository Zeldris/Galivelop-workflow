# Harvest instalador-wmf-tarkor — 2026-11-22

De `f60399b3` a `50535c7` (`scripts/harvest.py`). Skills y scripts iguales a `da1a462` (`0.8.1`). Lo nuevo sale de
`docs/records/retro-2026-11-18-flu-12.md` y `docs/records/retro-2026-11-19-flu-14.md`.

## P1. `test_measure.py` funciona con el flujo instalado

- **Source:** `docs/records/retro-2026-11-19-flu-14.md` @ `641140f` (retro; también world-maker-fantasy, que lleva el
  parche local en `.claude/skills/gw-opt-tokens/scripts/test_measure.py` @ `ce2a060d`)
- **What changes:** los tests copian `scripts/config.py` y `schema/gw.schema.json` con una ruta que solo existe en el
  repo del flujo; buscan primero ahí y luego en `.claude/gw/<ruta>`. Cuatro sitios, incluido el `copytree` del test de
  E76.
- **Why it is general:** `FileNotFoundError` en cualquier proyecto (5 tests en rojo en el CI); cada `/gw-update` borra
  el parche local.
- **Version bump:** patch
- **Status:** pendiente

## P2. `doctor.py` comprueba que exista la carpeta de `workflowClone`

- **Source:** `docs/records/retro-2026-11-19-flu-14.md` @ `641140f` (retro)
- **What changes:** `doctor.py` avisa si la ruta de `workflowClone` no existe (y, si existe con otras mayúsculas, la
  nombra).
- **Why it is general:** con `"../galivelop-workflow"` y el clon en `Galivelop-workflow`, `review-scope.py` (D132) y
  `scope-guard.py` (B44) no encuentran lo vendored y nada lo dice.
- **Version bump:** patch
- **Status:** pendiente

## P3. `paths-ignore` del ledger en la plantilla del CI

- **Source:** `docs/records/retro-2026-11-18-flu-12.md` @ `9c8f6f6` (retro)
- **What changes:** `templates/github/check.yml` ignora en `push` los cambios que solo tocan el directorio de
  métricas.
- **Why it is general:** una docena de commits solo de métricas en un PR dejó el CI siempre en cola.
- **Version bump:** patch
- **Status:** pendiente

## Joined to another proposal

- La línea de `AGENTS.md` sobre el gancho `Stop` y el ledger: con `2026-11-22-private-project-1.md` P1; el ledger fuera
  del árbol, con `2026-11-22-galivelop-image-generator.md` P1.

## Stays in the project

- FLU-13 (`paths-ignore` en su `app.yml`), FLU-9 y FLU-12: filas de su plan.

## Already here

- `whole-read.py` repetido: D128. `pendingFile` en la plantilla: D129/D104. Ensayo largo de `gw-update`: E52.
- `measure.py` y la sesión en curso: `pending.md`, D144 (antes «D142»); su idea de usar el `transcript_path` del gancho
  sirve para el arreglo.
