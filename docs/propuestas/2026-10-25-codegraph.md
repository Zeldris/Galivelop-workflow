# Investigación: colbymchenry/codegraph — 2026-10-25

Revisión de [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) @ `69af19a` (v1.6.2 + Unreleased,
MIT), pedida por el usuario (2026-10-23) para buscar mejoras para el flujo. No es una recogida (`gw-harvest`): no
cuenta para `version.py --release`. Leído en un clon de solo lectura; nada se ha ejecutado ni instalado. Lo marcado
**[código]** se ha comprobado leyendo su código; **[README]** sale solo de su documentación.

## Qué es

- Un grafo local del código: símbolos y aristas (llamadas, imports, referencias) sacados con tree-sitter, guardado en
  SQLite con FTS5 en `.codegraph/` del proyecto (`src/db/schema.sql`) **[código]**. ~20 lenguajes, TS/JS, Rust y
  Python entre ellos **[README]**.
- Se ofrece a Claude Code como servidor MCP con una sola herramienta por defecto, `codegraph_explore`, que devuelve
  en una llamada el código de los símbolos que importan y los caminos entre ellos; también como CLI
  (`callers`, `impact`, `affected`…) **[código]**.
- El índice se mantiene con un vigilante de archivos o, si no hay, con ganchos de git `post-commit`/`post-merge`
  (`src/sync/git-hooks.ts`), y cada respuesta avisa si hay archivos cambiados desde la última sincronización
  (`src/mcp/answer-freshness.ts`) **[código]**.
- Un gancho `UserPromptSubmit` (`codegraph prompt-hook`, `src/bin/codegraph.ts:1486`) mira el prompt y, si es una
  pregunta de estructura, inyecta ya la respuesta de `explore` para que el agente no se ponga a hacer grep. Nunca
  rompe el prompt: todo fallo sale con 0 y sin salida, y se apaga con `CODEGRAPH_NO_PROMPT_HOOK=1` **[código]**.

## Lo que dicen sus cifras

- En 7 repos, una pregunta de arquitectura por repo, `claude -p` con y sin la herramienta, mediana de 4: 88 % menos
  llamadas, 62 % menos tokens procesados, 44 % menos coste (13 % en Django, nada en Gin) (`README.md:200-231`)
  **[README]**; los scripts están en `scripts/agent-eval/` **[código, no ejecutado]**.
- Ellos mismos dicen que deja **~80 % más contexto residente** al final de la sesión (VS Code: 67k frente a 18k;
  `docs/benchmarks/residual-context-occupancy.md`) **[README]**. Nuestro `opt-tokens/medir.py` ya pesa justo eso (un
  resultado pesa lo que ocupa por cada llamada hasta la siguiente compactación), así que con nuestra métrica el
  ahorro sería menor que el suyo.
- Solo miden preguntas de «cómo funciona X»; nada de edición con bitácora, revisión ni relevos.

## Pegas para adoptarlo tal cual

- **Nube:** cada contenedor tendría que bajar ~50 MB (`install.sh`) y reindexar; `.codegraph/` no sobrevive.
- **`install.sh`** es `curl | sh` sin comprobar suma ni firma **[código]**; `codegraph install` reescribe el
  `settings.json` y el MCP de cada agente, que en nuestros proyectos gestiona `aplicar.py`.
- **Telemetría activada por defecto** (anónima, sin código ni rutas; `TELEMETRY.md`); se apaga con `DO_NOT_TRACK=1`.
- **Madurez media:** una versión al mes, 350 líneas de arreglos de resolución en «Unreleased», fallos del daemon en el
  CHANGELOG, y sin CI de tests en el repo (solo `deploy-site.yml` y `release.yml`) **[código]**.
- No entiende lo que más nos cuesta leer: bitácora, roadmaps y documentos de diseño.

## P1. Gancho opcional que inyecta la fila del mapa para agentes

- **Source:** `codegraph prompt-hook` (`src/bin/codegraph.ts:1486-1560`).
- **What changes:** un gancho `UserPromptSubmit` del flujo, apagado por defecto (clave en `.claude/gw.json`): si el
  prompt nombra un sistema de `docs/mapa-agente.md` (por la primera columna de la fila o unas palabras clave
  declaradas en ella), imprime esa fila (entradas, tests, qué no leer). Falla en silencio y con 0 (es contexto
  añadido, no una barrera), con interruptor por variable de entorno; tests de acierto, de prompt sin sistema y de
  mapa ausente.
- **Why it is general:** WMF y VeriNews ya piden «antes de buscar código de un sistema, abre el mapa»; es una regla
  que el agente se salta, y «lo comprobable lo hace un script». Es la idea de codegraph sin su índice: el mapa ya lo
  escribe y lo comprueba cada proyecto.
- **Riesgo:** inyectar en prompts que no lo necesitan gasta tokens. Se mide con `opt-tokens` en una ronda real de WMF
  antes de encenderlo por defecto.
- **Version bump:** minor
- **Status:** sin decidir

## P2. Comprobador genérico del mapa para agentes

- **Source:** el aviso de obsolescencia de codegraph (`src/mcp/answer-freshness.ts`); el comprobador ya existe en WMF
  (`tools/qa/mapa-agente.py`, `QA-108`).
- **What changes:** llevar al flujo un `scripts/mapa-agente.py` que compruebe que cada ruta (y `ruta#nombre`) del mapa
  existe, con los prefijos de rutas en el config, y añadirlo al `check` de las plantillas. WMF dejaría el suyo.
- **Why it is general:** un mapa que apunta a lo que ya no existe es peor que no tenerlo (el agente se fía de él), y
  todos los proyectos tienen mapa; hoy solo WMF lo comprueba.
- **Version bump:** minor
- **Status:** sin decidir

## P3. «Anti-patrones» y «Límites» en el mapa y en `writing-for-agents`

- **Source:** `src/mcp/server-instructions.ts` (cabecera «Keep it tight; the agent reads this every session»,
  secciones «How to query», «Anti-patterns» y «Limitations», y una versión corta cuando no hay índice).
- **What changes:** la skill `writing-for-agents` recomienda, para documentos que el agente lee en cada sesión, una
  sección corta de anti-patrones (qué no hacer, en una línea cada uno) y otra de límites honestos; la plantilla del
  mapa para agentes gana una columna o nota «qué no leer» donde no la tenga.
- **Why it is general:** dice al agente lo que no debe hacer en el sitio donde lo va a leer, sin alargar `AGENTS.md`.
- **Version bump:** patch
- **Status:** sin decidir

## P4. Probar codegraph en un proyecto, como experimento medido

- **Source:** todo lo de arriba.
- **What changes:** nada en el flujo. Si el usuario quiere, una prueba en una rama de WMF (backend TS): versión
  fijada, `DO_NOT_TRACK=1`, sin el gancho de prompt, unas cuantas tareas reales con y sin la herramienta, medidas con
  `opt-tokens` (que cuenta el contexto residente). Se decide con los números; si sale bien, se vería cómo
  instalarla en la nube (`setup script` del entorno) y la propuesta pasaría a la recogida de su versión.
- **Why:** sus cifras no cubren nuestro patrón de trabajo y su propio README admite el coste en ventana.
- **Version bump:** ninguna
- **Status:** sin decidir (recomendación: aplazar hasta tener P1 medida; P1 cubre la parte barata del mismo hueco)

## Descartado

- **Gancho `PreToolUse` que deniega `Read` de código** (`scripts/agent-eval/block-read-hook.sh`): es su experimento,
  no su producto; bloquear lecturas empeora el resultado («calidad primero»).
- **`codegraph affected`** (tests afectados por los archivos cambiados): ya lo tenemos con `relatedTests` y
  `tests-relacionados.sh`.
- **Su `CLAUDE.md` = `@AGENTS.md` + unas líneas**: ya lo hacemos así.
