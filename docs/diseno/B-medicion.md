# B. Medición de gasto y modelos

**Estado:** preguntas abiertas (2026-11-01). Nada se implementa hasta cerrar el bloque. B1 y B2 van en la `1.0.0`
(A-5); el resto, en menores `1.x` (bloque H).

Fuentes: [`README.md`](README.md) (bloque B y el apéndice con el mapa de modelos),
[`ref-agentic-openhands-palancas.md`](../investigacion/ref-agentic-openhands-palancas.md) §3 y `medir.py` de
`opt-tokens`, que ya lee los registros de sesión con su desglose por modelo y por subagente.

## Preguntas (se responden por número)

Cada punto lleva la recomendación del agente (**Rec.**).

1. **De dónde sale el dato (B1):** hay dos opciones.
   - (a) Los registros de sesión de Claude Code, que ya lee `medir.py`. Un gancho de fin de turno (`Stop`) apunta los
     tokens nuevos. No hace falta un servicio en marcha.
   - (b) OpenTelemetry: es la fuente oficial, con un desglose por modelo y por subagente, pero necesita un colector
     siempre en marcha. `/usage` no sirve: se pone a cero con `/clear`.

   **Rec.:** (a) en la `1.0.0` y (b) como opción en una `1.x`. La segunda sirve de comprobación cruzada.
2. **Dónde se guarda:** en la nube, el contenedor se borra y lo que quede fuera del repo se pierde. Opciones:
   - (a) un registro en el repo (`docs/metrics/ledger.jsonl`, en inglés según A-4) que se sube con el resto del trabajo;
   - (b) fuera del repo (`~/.claude`), que se pierde en la nube.

   **Rec.:** (a). El repo es público (A-1), así que se verían el gasto y las horas de trabajo, pero no el contenido.
   ¿Te parece bien que eso sea público?
3. **Qué se guarda:** **Rec.:** tokens, no euros. Por modelo y tipo (entrada, lectura de caché, escritura de caché,
   salida), con la fecha, la rama, el id de tarea (`Refs:`, de D-12) y el subagente. El coste en dinero se calcula al
   hacer el informe, con una tabla de precios con fecha en la config. Los precios cambian, y con una suscripción no se
   paga por token.
4. **Informes (B2):** **Rec.:**
   - Un script los genera (`metrics.py report --period day|week|month|quarter`) y los deja en `docs/metrics/` (en
     inglés: `daily/`, `weekly/`, `monthly/`, `quarterly/`). El de un día sin actividad no se escribe.
   - Una sola skill, `gw-metrics`, interpreta los informes; las cifras las hace el script, no el agente.

   Así no hay cuatro skills.
5. **Comparaciones (B3):** **Rec.:** el mismo script y la misma skill. `metrics.py compare` compara un periodo con el
   anterior (hoy frente a ayer, esta semana frente a la pasada), y también dos periodos que elijas tú (dos días, dos
   semanas, dos meses).
6. **Aviso cuando un modelo gasta de más (B4):** **Rec.:**
   - Se avisa cuando el gasto diario de un modelo pasa de 1,5 veces su media de las últimas 4 semanas, y solo si hay al
     menos 7 días de datos.
   - El aviso lo da el gancho de inicio de sesión.
   - El umbral y la ventana van en la config.
7. **Desactivar un modelo (B4):** **Rec.:** una lista `models.disabled` en `gw.json`, que se cambia con la skill o el
   script.
   - `selector` y `orchestrate-dealer` la respetan.
   - Un gancho rechaza lanzar un subagente con un modelo desactivado y dice cómo reactivarlo.
8. **La tabla determinista (B5):** necesita medir el resultado, no solo el gasto. **Rec.:**
   - Como resultado cuenta lo que ya es comprobable: los hallazgos del code review por tarea, los reintentos, el check
     en rojo y el trabajo rehecho.
   - Mientras no haya 4 semanas de datos, vale tu mapa inicial (apéndice del README).
   - Luego un script propone la tabla y tú la confirmas.

   ¿Qué más cuenta para ti como «buen resultado»?
9. **Modelos de fuera de Anthropic** (GPT, Gemini, DeepSeek… del mapa): Claude Code solo lanza modelos de Claude.
   **Rec.:** la tabla los admite como dato, pero solo se usan desde opencode u otra herramienta (D-7). El gasto de
   opencode y Codex (SQLite y JSONL) se lee en una `1.x`.
10. **El `selector` recomienda el modelo y el esfuerzo de la sesión principal (B6):** **Rec.:** sí, solo recomienda; el
    modelo lo eliges tú. El «modo restringido de tokens» se diseña en el bloque C, junto con el modo restrictivo: un
    solo interruptor de modos, no dos.
11. **Palancas de Claude Code (B7):** `CLAUDE_CODE_SUBAGENT_EFFORT` no está documentada. Fijar `CLAUDE_CODE_EFFORT_LEVEL`
    gana a todo y anula lo que el `selector` recomiende por tarea. `CLAUDE_CODE_SUBAGENT_MODEL` solo manda sobre todos
    los subagentes con `_FORCE=1`. **Rec.:**
    - El flujo fija el `model` y el `effort` en cada agente y en cada encargo, no con variables globales.
    - `SUBAGENT_MODEL` con `_FORCE` solo en el modo restringido.
    - Los precios de B7 se comprueban en la doc oficial al implementar.
12. **Patrón «scouts» (B7):** muchos subagentes baratos leen y resumen; el grande solo ve lo que señalan, y cada
    afirmación se comprueba contra la fuente. **Rec.:** va como mejora de `orchestrate-dealer` en una `1.x`, y medido con
    B1 antes y después.
13. **Ahorro medido (B8):** comparar «con el flujo» y «sin él» necesita una base que no existe. **Rec.:**
    - Se publica la tendencia dentro del flujo: tokens por tarea, versión a versión.
    - Una sola vez, una prueba A/B con un juego pequeño de tareas fijas, hechas con el flujo y sin él.
