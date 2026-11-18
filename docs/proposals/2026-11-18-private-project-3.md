# Harvest private-project-3 — 2026-11-18

De `d7d50956` a `12badcbd` (`scripts/harvest.py`). 116 commits; sin skills del flujo cambiados y un script
coincidente por nombre (`gvoice/models.py`, ver «Stays in the project»). Lo nuevo sale de 7 retros
(`docs/records/retro-2026-11-15-f5-1.md` a `retro-2026-11-18-gw-update-0-8-0.md`). Recogida de apertura de la `0.9`
(2026-11-18).

## P1. Aviso de `/clear` al cerrar una tarea con el contexto alto, antes de «Siguiente»

- **Source:** `docs/records/retro-2026-11-16-pr-f5.md` P1 @ `c9fbde8` (retro)
- **What changes:** `scripts/recover.py --state` (y el gancho `Stop`, `scripts/before-stop.py`) avisan al cerrar una
  tarea con el contexto por encima de un umbral (clave nueva en `.claude/gw.json`, `docs/es/config.md`), y
  `AGENTS.md` dice que un «Siguiente» tras un cierre se contesta con la petición de `/clear`. D108 y D122 cubren solo
  el commit de cierre de fase y el culpable del arranque; no el «Siguiente» de cada tarea.
- **Why it is general:** la regla de `/clear` al cerrar tarea no se cumple con solo texto; encadenar tareas costó
  ~15-20M de tokens en un tramo (454 llamadas a 117k de media).
- **Version bump:** minor
- **Status:** aprobada (2026-11-18) → E66

## P2. `measure.py` separa el arranque del entorno de la nube del coste del proyecto

- **Source:** `docs/records/retro-2026-11-16-pr-f5.md` (Para Galivelop-workflow) @ `c9fbde8` (script)
- **What changes:** `skills/gw-opt-tokens/scripts/measure.py` muestra aparte el arranque fijo (sistema, herramientas y
  MCP, ~85k) y deja el resto como coste del proyecto.
- **Why it is general:** el arranque fijo tapa lo que sí se puede recortar en cualquier proyecto en la nube.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → E76

## P3. Aviso mecánico al leer otro repositorio desde la sesión principal

- **Source:** `docs/records/retro-2026-11-17-v0-2-0.md` P2 @ `051171f` (retro)
- **What changes:** un gancho `PreToolUse` (`Read`/`Bash`, plantilla `templates/claude/settings.json`) avisa, sin
  bloquear, cuando la sesión principal lee rutas de un repositorio hermano; clave para apagarlo. Hoy `config-guard.py`
  solo vigila escrituras.
- **Why it is general:** «otro repo, con subagente» falló dos veces solo con texto (~380k arrastrados).
- **Version bump:** minor
- **Status:** aprobada (2026-11-18) → E74

## P4. Prefijo propio para las skills del proyecto

- **Source:** `docs/records/retro-2026-11-18-gw-update-0-8-0.md` @ `00cc4e8` (retro; pedido por la persona el
  2026-11-18)
- **What changes:** clave nueva `projectSkillPrefix` en `.claude/gw.json` (`scripts/config.py`, `docs/es/config.md` ↔
  `docs/en/config.md`), que `gw-init` pregunta y escribe; `scripts/doctor.py` avisa de una skill del proyecto (no
  del flujo) que no lo lleva. Las del flujo siguen con `gw-`.
- **Why it is general:** cualquier proyecto con skills propias necesita distinguirlas de las del flujo (aquí
  `gvg-`), y hoy no hay dónde decirlo ni quién lo compruebe.
- **Version bump:** minor
- **Status:** aprobada (2026-11-18) → E73

## Joined to another proposal

- La fusión de `settings.json` sustituye la entrada de un gancho cuyo matcher cambió, con su test, y el `FAIL` de
  `doctor.py` con el mismo script dos veces en un evento (retro `gw-update-0-8-0` @ `00cc4e8`):
  instalador-wmf-tarkor P1 (`2026-11-18-instalador-wmf-tarkor.md`).

## Stays in the project

- `gvoice/models.py`: choque de nombre con `scripts/models.py` del flujo; es el catálogo de motores y descargas del
  proyecto (D18), no una copia.
- F5.x (barridos de la interfaz, B1/B2 de `effects.py` y `api.js`), versionado `releases.py`, arnés de Chrome: producto.
- Conectores MCP sin usar (P4 del retro 0.2.0): lo hace la persona con `/mcp`.

## Already here

- `Findings:`/`Retries:` fuera del último bloque de trailers (retro F5.1): D97; lo propone también
  instalador-wmf-tarkor de hoy (`2026-11-18-instalador-wmf-tarkor.md`).
- `pre-push` que deja `docs/metrics/ledger.jsonl` modificado y el `Stop` lo cuenta (retro F5.9 P4): `before-stop.py`
  ignora `metrics.ledger` y B36 (`metrics.py stage-ledger`, ver `2026-11-15-private-project-1.md`).
- Revisión de un diff pequeño sin `/code-review` anidado (P1 del retro F5.9): la persona la rechazó (coste
  conocido); no se recoge.
