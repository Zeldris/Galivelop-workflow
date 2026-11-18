# Harvest portal-galivelop — 2026-11-18

De `c926bcc9` a `5252aab1` (`scripts/harvest.py`). 117 commits; sin skills ni scripts del flujo cambiados (las copias
del flujo en el portal son de `0.7.0`/`b44cd14`). Lo nuevo sale de 3 retros
(`docs/records/retro-2026-11-16-gw-update-0.7.md` @ `192df67`, `retro-2026-11-17-auditorias.md` @ `d492dc1`,
`retro-2026-11-17-lector.md` @ `0ce4e7c`). Recogida de apertura de la `0.9` (2026-11-18).

Ninguna propuesta nueva: todo lo que el portal pide para el flujo ya está hecho o propuesto.

## Joined to another proposal

- Sesión abierta fuera del repo: `recover.py` solo lo avisa en stderr y el primer mensaje del agente no lo dice
  (retro `gw-update-0.7` @ `192df67`). Va con private-project-4 P3 (`2026-11-15-private-project-4.md`, `gw-selector`
  avisa; no aprobada el 2026-11-15): es el mismo hueco, y el portal añade un segundo caso en que se dijo a mano.

## Already here

- `apply.py --update --dry-run` con resumen corto y delegar su lectura a un subagente (retro `gw-update-0.7` @ `192df67`):
  `--dry-run --summary` es E52 (`2026-11-14-private-project-3.md` P3) y `skills/gw-update/SKILL.md` ya manda a un
  subagente de solo lectura el diff y el ensayo de más de ~200 líneas. El portal aún no tiene la `0.7`.
- El contador de «Pendiente» que `move-pending` pone al día y que el `commit-msg` no vigila (retro `auditorias` @
  `d492dc1`, arreglado a mano en el portal con `221c6c1`): B38 (`docs/roadmap.md`, hecho) cubre la cuenta del puntero
  sin vigilar en un commit que solo toca `pending.md`.
- `gw-orchestrate-dealer`: un encargo por arreglo cuando un lote trae más de tres (retro `auditorias` @ `d492dc1`):
  el paso «A batch of approved rows is dealt, not worked inline» de `skills/gw-orchestrate-dealer/SKILL.md` ya manda
  una fila por subagente (o dos pequeñas) y tiene la medida de contexto.
- `before-stop.py` bloquea con subagentes trabajando (retro `lector` @ `0ce4e7c`): D88 (`docs/roadmap.md`, hecho; `0.6`,
  `2026-11-11-world-maker-fantasy.md` P4) ya lo evita leyendo el transcript. El portal tiene el gancho de `b44cd14`,
  anterior a D88: se arregla con `gw-update`, no con cambios en el flujo.

## Stays in the project

- `check.py` no admite guiones en `r/u_…` de los canales de Reddit: es el `check.py` del portal, no del flujo.
- `gw-portal` (skill nacida en el proyecto: fichas, próximamente, muro, productos y guiones de lectura): depende de
  los repos de la cuenta y del stack web del portal; los enfoques al día (P2 de la retro `lector`) son de ella.
- Lector de la página (anclas estables, `LectorCarga`, audio, `guion.test.tsx`), `tools/qa/probar-lector.cjs`
  (Playwright), guiones en es/gl/en y auditorías: código y QA del portal.
