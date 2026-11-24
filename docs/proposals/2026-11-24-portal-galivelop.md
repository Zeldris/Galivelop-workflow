# Harvest portal-galivelop — 2026-11-24

De `7973aa5` a `e2c9b9b` (`scripts/harvest.py`). 38 commits; ningún skill ni script del flujo cambiado. Lo nuevo sale de
`docs/records/retro-2026-11-22-galivelopcode.md` y `retro-2026-11-24-productos.md`.

## P1. `private-check.py` también en el `pre-commit`

- **Source:** `retro-2026-11-22-galivelopcode.md` P1 @ `96f01ed` (gancho)
- **What changes:** `.githooks/pre-commit` corre `private-check.py` sobre lo preparado (hoy solo rechaza
  `gw.local.json`; la comprobación está en el `pre-push`), con clave de configuración para apagarla y test.
- **Why it is general:** un subagente escribió un correo real en un test; el `pre-push` lo cazó tarde y arreglarlo
  obligó a reescribir dos commits.
- **Version bump:** minor (evolutivo)
- **Status:** proposed

## P2. `handoff.py show <sección>`

- **Source:** `retro-2026-11-22-galivelopcode.md` P2 @ `96f01ed` (script)
- **What changes:** lee una fila o sección de la bitácora sin `sed` a mano.
- **Why it is general:** la bitácora se releyó entera 24 veces (1,34 M tokens). Mirar antes `recover.py --state`.
- **Version bump:** minor (evolutivo)
- **Status:** proposed

## P3. Regla de `REVIEW.md`: sin guardas temporales en los tests

- **Source:** `retro-2026-11-24-productos.md` P4 @ `d03f7e0` (plantilla)
- **What changes:** en `templates/{es,en}/REVIEW.md` (sección Tests), marcada «(criterio)»: un test no depende de
  que exista lo que comprueba (`if (existsSync(...))`); si falta, se marca pendiente.
- **Why it is general:** un subagente apagó una comprobación en silencio.
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- Skill `gw-portal`; retro P3-P5 de `galivelopcode`; P1-P3, P5 y P6 de `productos`.
