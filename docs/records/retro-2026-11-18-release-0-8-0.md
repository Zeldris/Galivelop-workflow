# Retro del sello de la `0.8.0` (2026-11-18)

**Estado:** decidida por el usuario (2026-11-18): P1, P2 y P3 aprobadas y aplicadas (B44, B45, B46); P5 aprobada
y aplazada a la `0.10` como B43; P4 rechazada: en la nube no hay conectores que desactivar (los tres servidores
MCP los pone el entorno).

Sesión del sello: CHANGELOG, versión, README y roadmap por dos `gw-worker` (Sonnet) en paralelo; la sesión principal
revisó, hizo el commit `9ab4f9d` y corrió el check completo. Incluye el paso de `/gw-opt-tokens`.

## Gasto (`measure.py --hours 0`)

- Sesión principal: 36 llamadas, contexto medio 123k, suelo 86k y techo 150k, 0 compactaciones (presupuesto 2),
  4,4M de entrada. Subagentes: 2 `gw-worker` (27 llamadas, arranque ~15k, 1,05M).
- Del arranque de 86k, ~78k son el resto del sistema (prompt, herramientas y servidores MCP: Claude Docs, GitHub y
  el remoto). Es la T1 aplazada en la retro de la `0.7.1`: sigue siendo el mayor coste fijo.
- Lecturas que sobraron: la cabecera de `docs/agent-map.md` (4k, arrastrada 112k) para escribir encargos que ya
  bastaba con apuntar al mapa.

## Propuestas

Ordenadas por gravedad. Todas son generales: van al flujo (este repo).

1. **P1. `scope-guard` no cuenta copias generadas ni cabeceras de versión** (comprobación automática). El registro
   de desviaciones tiene 226 entradas del sello (cabeceras `v0.8.0`) y 129 de D7 (copias que `apply.py` escribe en
   `.claude/` y `.agents/skills`), todas «fuera de alcance» de la tarea marcada. Ese ruido tapa las desviaciones de
   verdad para la retro. Propuesta: `scope-guard.py` salta los archivos que `apply.py --vendored` da por copia del
   flujo y los cambios que solo tocan la línea `galivelop-workflow vX.Y.Z`/`version:`; un commit con `chore(H…)` de
   sello no exige ficha. Riesgo: ninguno si el filtro es exacto (test con un cambio real en un archivo copiado).
2. **P2. `review-scope.py --trivial` no cuenta las cabeceras de versión** (comprobación automática). Desde la última
   revisión solo cambiaron dos líneas de `gw-selector`, pero salió «113 code files, 229 lines» por las cabeceras del
   sello. Propuesta: descontar las líneas que solo cambian la versión estampada. Riesgo: ninguno con su test.
3. **P3. Tarea en curso caducada** (información). `task.py current` seguía en B9 al empezar el sello; nadie la
   cambia al cerrar una tarea. Propuesta: `close-row <id>` borra la marca si es esa tarea, y `recover.py --state`
   dice la tarea en curso. Riesgo: ninguno.
4. **P4. T1 de nuevo: conectores sin uso** (gasto, ~78k por llamada en arranque). Decisión del usuario en los ajustes
   de la nube; sin cambio en el repo. Riesgo: perder un conector que una tarea pida (se vuelve a activar).
5. **P5. Barrido para la `0.10`**: `trace.py` reúne 6 leves abiertos de `pending.md` (revisión D14 n.º 2 y C11-trace
   n.º 3-7). Propuesta: una tarea B nueva de la `0.10` que los cierre todos. Riesgo: ninguno.

## Lo que fue bien

- Dos subagentes en paralelo con archivos disjuntos: sin choques y la sesión principal sin leer el log entero.
- `version.py 0.8.0` + `apply.py .` dejaron las copias al día de una vez; los tests de versión, en verde.
