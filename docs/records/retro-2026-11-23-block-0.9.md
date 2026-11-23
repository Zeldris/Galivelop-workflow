# Retro: bloque `0.9` (2026-11-23)

**Estado:** pendiente de la decisión del usuario (nada aplicado todavía).

Fuentes: `measure.py` de esta sesión (22 llamadas, contexto medio 103k, 84 % arranque fijo), `pending.md`, el registro de
desviaciones (`task.py deviations`) y la sesión de los cierres D171-D175. Todas las propuestas son **generales** (este repo
es el flujo, así que se aplican aquí mismo).

## Propuestas, de más a menos grave

### R1. El fallo de `/clear` al cerrar tareas (Navegación / check automático)

Ya anotado en `pending.md` («Para la retro de la `0.9`»). Se cerraron D171-D174 seguidas sin pedir `/clear`; el aviso de
`commit-msg` (D108) solo salta al cerrar una sección del roadmap o cambiar «Fase en curso», no al cerrar una tarea suelta.
Propuesta: el `commit-msg` avisa también cuando el commit deja `hecho` una fila de tarea (`Refs:` de una fila que pasa de
abierta a hecha) y la sesión pasó su presupuesto de compactaciones **o** `clearAfterTask`; clave nueva en `.claude/gw.json`
(`clearOnTaskClose`, por defecto `true`) y fila en `docs/es/config.md`. **Riesgo de calidad:** ninguno (solo avisa); coste: un
aviso más por tarea, que es lo que manda `AGENTS.md`. Alternativa: bajar `contextGuard.clearAfterTask`, que no resuelve el
caso de un contexto pequeño por subagentes.

### R2. Entradas de `pending.md` ya hechas (Comprobación automática; ahorro medido)

Hoy P1 y P4 figuraban abiertas, pero ya estaban hechas (E84, E86): ~15 llamadas y ~100k de contexto arrastrado para
descubrirlo. Propuesta: `handoff.py check` avisa de una entrada abierta que cita un id del roadmap en estado cerrado
(`E84`, `D173`…), y la regla de `AGENTS.md` pide citar el id al apuntar un pendiente. **Riesgo:** falsos avisos si la
entrada cita un id solo como referencia; se salvan con un id «Related:» al principio. Coste: ~40 líneas y 3 tests.

### R3. Barrido de leves (el cierre de bloque lo pide la skill)

70 entradas abiertas de `0.10`. El script con más leves abiertos es **`trace.py`** (7 menciones; le siguen `tests-for.py`,
`task.py`, `scope-guard.py` y `apply.py`, 3 cada uno; `apply.py` ya tiene P6). Propuesta: tarea `D176`, para la `0.10`, que
limpie los leves de `trace.py` (lista en `pending.md`, `grep -n 'trace.py' docs/records/pending.md`); tú eliges cuáles entran.
**Riesgo:** ninguno.

### R4. Coste fijo de la sesión (Economía de herramientas)

El 84 % del gasto de esta sesión es arranque fijo (~87k por llamada: sistema, ~120 herramientas diferidas, MCP). No lo
reduce el repo; solo desactivar conectores o servidores MCP que este flujo no usa (`/context`). Sin propuesta de código.
Lectura menor: `cat scripts/push.sh` entero (3,8k) cuando bastaba el `grep` de `--wip`; sin regla nueva.

### R5. Skills y desviaciones

`gw-selector`, `gw-orchestrate-dealer` y `gw-reviewer` funcionaron (revisión de 4 llamadas, ~29k de contexto medio). Las
desviaciones de E86 (cinco archivos fuera de su ficha) vienen de los arreglos de revisión commiteados con el id cerrado;
D172 ya usa id propio. Sin acción.

## Fase 1 (código)

`/code-review` del tramo `ca88948..HEAD` (gw-reviewer): 0 importantes, 1 leve (`whole-read.py`, glob antes de contar
operandos) anotado en `pending.md` como `0.10`.
