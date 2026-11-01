# Referencias: GitHub agentic workflows, OpenHands y palancas de Claude Code

Fecha: 2026-11-01. Investigación de solo lectura para la sesión de diseño de la `1.0.0` (bloques B, D, G; ver
`docs/diseno/README.md`, sección F). Lo no confirmado va marcado con **[NO CONFIRMADO]**.

Límites de esta pasada: `github.blog`, `github.github.io/gh-aw`, `docs.all-hands.dev` y `docs.openhands.dev` no
resuelven desde el entorno en nube (fuera de los dominios permitidos). Para gh-aw se usó el README de
`github/gh-aw` y un resumen de búsqueda (fuentes secundarias); para OpenHands, los `AGENTS.md`/README/código del
repo. Si se quiere la fuente primaria de gh-aw, hay que permitir esos dominios y repetir.

## 1. GitHub Agentic Workflows (`gh aw`)

### Qué son (confirmado en el README de github/gh-aw)

- Automatización del repo escrita en **Markdown** que el CLI `gh aw` compila a un workflow normal de Actions
  (`.lock.yml`). Se instala con `gh extension install github/gh-aw`; `gh aw compile` valida el `.md` y genera el
  `.lock.yml`. El propio proyecto dice que complementa al CI/CD, no lo sustituye.
- Archivo en dos partes: frontmatter YAML (disparadores, permisos, herramientas, motor de IA) y cuerpo en lenguaje
  natural con la tarea del agente.
- Motores: GitHub Copilot, Claude Code, OpenAI Codex, Gemini y Pi.
- Usos típicos: triaje de issues, revisión de PR, investigar fallos de CI, mantener la documentación, informes del repo.
- Seguridad: el job del agente es de **solo lectura y en sandbox** por defecto; las escrituras en GitHub
  (comentar, abrir issue/PR…) pasan por **safe-outputs**: se guardan en búfer, se validan y se aplican en jobs
  aparte con permisos mínimos. El autor puede relajar los controles, así que hay que revisar permisos, herramientas,
  red y archivos generados. El README avisa de que las versiones `>= 0.83.3, < 0.85.4` se retiraron por una
  vulnerabilidad.
- Estado: technical preview desde 2026-02-13 (changelog de GitHub, vía búsqueda). Un artículo de terceros da v0.91.5
  a 2026-10-07 **[fuente secundaria]**.

### Coste (secundario, **[NO CONFIRMADO] en fuente primaria**)

- Corre **dentro de Actions**: gasta minutos de Actions además del motor. Un artículo de terceros cuenta ~2 premium
  requests de Copilot por ejecución (una del agente y otra de la detección de amenazas de los safe-outputs).
- Sin precio final ni fecha de GA según esas fuentes. Otro artículo cita un ataque demostrado con contenido
  malicioso en issues (inyección de prompt): relevante para cualquier flujo que lea texto de terceros.

### Ideas para el flujo

| Idea | Bloque | Nota |
|---|---|---|
| Patrón **safe-outputs**: el agente solo propone; un paso aparte y con permisos mínimos aplica. Copiarlo como regla de diseño (el agente nunca tiene el token con escritura) | D, G | Encaja con el gancho `pre-push` y `revisado.sh` |
| `staged: true` / modo simulacro: ver qué crearía sin escribir | D | Útil para `release` y recogidas (`gw-harvest`) |
| Fuente en Markdown + artefacto compilado + check de que no divergen | D, E | El flujo ya hace pares ES/EN; mismo patrón de comprobación |
| Tareas en Actions por evento (triaje, informe diario de gasto, notas de release) | B2, D | **Choca con la falta de cuota de Actions del usuario**: no depender de ello |
| Alternativa sin cuota: ejecutar la misma definición en local o en sesión en nube (`scripts/ci-local.py` ya existe) y que el CI sea opcional | D | Un único Markdown de tarea, dos ejecutores (Actions o local) |
| Roles/entornos: los permisos del frontmatter como modelo de «qué puede hacer cada rol/entorno» | D (roles), G | Permisos declarativos por tarea, no por conversación |
| Aviso de inyección de prompt al leer issues/PR ajenos: tratar como datos | D | Ya es regla del flujo para contenido de terceros |

Fuentes:
- https://github.com/github/gh-aw
- https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/ (solo como resultado de búsqueda; no se pudo abrir)
- https://github.github.io/gh-aw/ (no se pudo abrir)
- https://startdebugging.net/2026/10/what-is-github-agentic-workflows-and-how-does-it-differ-from-github-actions/ (secundaria)
- https://jorijn.com/en/blog/github-actions-agentic-workflows-natural-language-cicd/ (secundaria)

## 2. OpenHands

### Arquitectura (confirmado en el README y `AGENTS.md` de `OpenHands/OpenHands`)

- El repo `OpenHands/OpenHands` es ahora **Agent Canvas**: «centro de control autoalojado para agentes de código y
  automatizaciones». Frontend React/TypeScript. Corre en `localhost:8000` (o `/canvas` en la imagen Docker).
- Reparto en cuatro repos con dependencia en una dirección: `software-agent-sdk` (SDK Python + Agent Server con API
  REST/WebSocket) → cliente TypeScript → Canvas. `OpenHands/extensions` guarda skills, automatizaciones y plugins
  públicos; `OpenHands/automation` programa disparadores (cron, webhooks), historial de ejecuciones y despacho.
- Canvas se conecta a **varios Agent Servers** (portátil, VM, Cloud) y alterna entre ellos; puede ejecutar el agente
  propio u otros (Claude Code, Codex, Gemini CLI, OpenCode…) por ACP. Integraciones con Slack, GitHub, Linear.
- Local solo en loopback; al exponerlo exige API key.

### Skills / microagentes

- Confirmado: skills de contribución en `.agents/skills/` del repo, cada una con `SKILL.md` y una tabla en
  `AGENTS.md` («invoca toda skill aplicable antes de tocar esa zona»); skills públicas reutilizables vienen del paquete
  `@openhands/extensions`. Es el mismo patrón que Claude Code y que este flujo.
- **[NO CONFIRMADO]** el mecanismo de «microagentes» por palabra clave o por repo (la documentación no se pudo abrir).

### Modelo y coste

- Modelo: «trae tu propio modelo / cualquier LLM», con ajustes de LLM y **perfiles de LLM** (README de Canvas; el
  detalle de los perfiles **[NO CONFIRMADO]**). El SDK construye `LLM(model=..., api_key=...)` por agente.
- Coste: el SDK lleva una clase `Metrics` (archivo `openhands-sdk/openhands/sdk/llm/utils/metrics.py`) con
  `accumulated_cost`, `accumulated_token_usage`, lista de `costs`, `token_usages` y `response_latencies`, y un
  `MetricsSnapshot` copiable. Es decir: el coste se **acumula en el objeto de la conversación** y se puede
  instantanear; no se calcula al informar.
- **[NO CONFIRMADO]** cómo se muestra el coste en la interfaz.

### Ideas para el flujo

| Idea | Bloque |
|---|---|
| Esquema de métricas: `accumulated_cost` + tokens por tipo + latencias, con snapshot; guardar el acumulado y servirlo sin recalcular | B1 |
| Separar **fuente de datos** (servidor/API) de la **interfaz** (Canvas) con un cliente tipado: el MMC como UI sobre archivos/API del flujo, no sobre lógica propia | G |
| Varios «backends» seleccionables (local, VM, nube) ↔ varios perfiles/proyectos en el MMC (perfil global y privado) | G |
| Perfiles de LLM con nombre ↔ perfiles guardados del MMC y tabla de modelos por necesidad | B5, G |
| Repo de extensiones separado y versionado ↔ skills `gw-` públicas | A |
| Tabla «skill ↔ cuándo cargarla» en `AGENTS.md` (ya lo hace el mapa de agente) | E |
| Compatibilidad mínima declarada entre UI y servidor (`compatibility.minimumAgentServer`) ↔ versión mínima del flujo que exige el MMC | A, G |
| Automatizaciones con disparador programado y webhook con historial de ejecuciones | B2, G |
| Regla en su `AGENTS.md`: la sección «HUMAN:» del PR no la toca un agente | D |

Fuentes:
- https://github.com/OpenHands/OpenHands (README, `AGENTS.md`)
- https://github.com/OpenHands/software-agent-sdk (README, `metrics.py`)
- https://github.com/OpenHands/extensions, https://github.com/OpenHands/automation (solo por las referencias de `AGENTS.md`)
- https://docs.openhands.dev/ (no se pudo abrir)

## 3. Palancas de Claude Code para subagentes, modelo, esfuerzo y gasto

Todo confirmado en la documentación oficial salvo lo marcado.

### Existen

- `CLAUDE_CODE_SUBAGENT_MODEL`: modelo por defecto de subagentes, teammates de agent teams y agentes de workflows
  sin modelo asignado de otro modo. Acepta alias (`haiku`) o nombre completo; `inherit` equivale a no definirla.
  **Desde v2.1.251 ya no gana a nada**: orden de resolución = (1) parámetro `model` de la invocación, (2) `model` del
  frontmatter del subagente (`inherit` = el de la conversación), (3) `CLAUDE_CODE_SUBAGENT_MODEL`, (4) modelo de la
  conversación. No cambia los modelos de los subagentes integrados Explore y Plan por sí sola.
- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+): fuerza un solo modelo a todos los subagentes, teammates y agentes
  de workflow. Para el patrón «scouts»/ahorro hay que ponerla **junto a** la anterior:
  `{"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "haiku", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}}`.
- Frontmatter de subagente: `model` (`sonnet|opus|haiku|fable`, id completo o `inherit`) y `effort`
  (`low|medium|high|xhigh|max`, según modelo). El `effort` del subagente pisa el de la sesión, **no** a
  `CLAUDE_CODE_EFFORT_LEVEL`. Desde v2.1.292 Claude puede pasar `effort` por invocación (pisa al frontmatter y
  persiste al reanudar). También `maxTurns`, `autoCompactWindow` (100k-1M, v2.1.296+), `omitClaudeMd` (v2.1.271+),
  `isolation: worktree`, `background`, `memory`, `skills`, `tools`/`disallowedTools`.
- Esfuerzo: `CLAUDE_CODE_EFFORT_LEVEL` (gana a todo; `auto`/`unset` = no enviar nivel), `--effort`, `/effort` (sin
  argumento abre selector; `/effort auto` limpia; `s` aplica solo a la sesión), ajustes `effortLevel` y
  `modelSettings`, tope `maxEffortLevel`. Por defecto `high`, salvo Opus 5.5, Sonnet 5.5 y Haiku 5.5 en `medium`.
  Orden: variable de entorno > selección en sesión > `--effort` > ajustes > defecto del modelo.
- Otras: `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU,FABLE}_MODEL` (a qué resuelve cada alias; `HAIKU` también para tareas
  de fondo), `ANTHROPIC_MODEL`, ajuste `model`, alias `opusplan` (Opus en plan, Sonnet al ejecutar),
  `availableModels` (lista blanca; un subagente bloqueado cae a un modelo de reserva), `MAX_THINKING_TOKENS` (solo
  modelos con presupuesto fijo; Opus/Sonnet/Haiku 5.5 y Fable no admiten apagar el pensamiento),
  `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` (`5m`|`1h`; la escritura de caché de 1 h cuesta más),
  `--max-budget-usd`, ajuste `modelPricing` (tarifas contratadas, solo en ajustes gestionados).

### No existe en la documentación

- **`CLAUDE_CODE_SUBAGENT_EFFORT` no figura** en la página de variables de entorno ni en la de subagentes (búsqueda
  de la cadena en ambas: 0 resultados, 2026-11-01). Los tuits del usuario pueden referirse a una versión posterior,
  a una función sin documentar o a un error. **Para B7 no se puede basar nada en ella.** Equivalente documentado:
  `effort` en el frontmatter del subagente (y el parámetro por invocación), y, para forzar a todos,
  `CLAUDE_CODE_EFFORT_LEVEL` (pero afecta también a la sesión principal).

### Medición del gasto (para B1)

- `/usage` (en la doc actual el bloque «Session»; `/cost` es el nombre antiguo, **[NO CONFIRMADO]** si sigue como
  alias): coste local a precio de lista, **desglose por modelo** (`Usage by model`), líneas cambiadas, duración, y
  línea `Prompt cache (main)`. Se reinicia con `/clear` (desde v2.1.211). En suscripciones muestra además
  atribución a skills, subagentes, plugins y servidores MCP (24 h o 7 días), y recomendaciones (`f` aplica las de
  `/effort`). Es estimación, no factura.
- **Statusline**: el script recibe JSON por stdin con `cost.total_cost_usd`, `cost.total_duration_ms`,
  `cost.total_api_duration_ms`, `effort.level`, `rate_limits.five_hour|seven_day.{used_percentage,resets_at}`
  (solo suscripciones), `prompt_cache`, `agent`, modelo y contexto. Es el punto de enganche más barato para un
  **escuchador** que vuelque el acumulado por sesión a un archivo en cada refresco. Límite: da el total de la
  sesión, no el desglose por modelo (eso solo está en `/usage` y en OpenTelemetry).
- **OpenTelemetry** (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER=otlp|prometheus|console|none`,
  `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_METRIC_EXPORT_INTERVAL`, por defecto 60000 ms, temporalidad `delta`): métricas
  `claude_code.cost.usage` (USD) y `claude_code.token.usage` (`type`: input/output/cacheRead/cacheCreation), tras cada
  petición, con atributos `model`, `query_source` (`main|subagent|auxiliary`), `effort`, `speed`, `agent.name`
  (nombres propios aparecen como `custom`), `skill.name`, `plugin.name`, `mcp_server.name`. Es **la única fuente
  documentada de coste por modelo y por tipo de agente casi en tiempo real**. Con `console` o un colector local
  mínimo (OTLP a un archivo/SQLite) sirve para B1 sin servicios externos. `agent_id` solo va en eventos/spans.
- `ccusage` (paquete de terceros que lee los JSONL de `~/.claude/projects/`): **[NO CONFIRMADO]** en esta pasada,
  no está en la documentación oficial y no se abrió su repo. Debe evaluarse aparte (licencia, si desglosa
  subagentes, si calcula con tarifas vigentes).
- Para quien use la API por Console: panel y Claude Code Analytics API (por usuario); en Teams/Enterprise, informe
  de gasto (CSV) y Enterprise Analytics API.

### Ideas para el flujo

| Idea | Bloque |
|---|---|
| B1 en dos capas: (a) hook de statusline que escribe `cost.total_cost_usd` + `effort.level` por sesión (sin dependencias); (b) colector OTLP/`console` local para el desglose por `model` y `query_source` | B1 |
| Guardar las cifras como delta por modelo/día en `docs/mediciones/` y servirlas sin recalcular; recordar que `/usage` se reinicia con `/clear`, así que el escuchador debe acumular él | B1, B2 |
| Atributos `effort` y `query_source` ya vienen etiquetados: la tabla determinista B5 puede salir de coste real por (modelo, esfuerzo, tipo de agente) | B5 |
| `CLAUDE_CODE_SUBAGENT_MODEL=haiku` + `_FORCE=1` solo en perfiles «modo restringido»; sin FORCE, el frontmatter de cada agente manda (más fino) | B6, B7 |
| Poner `model` y `effort` en el frontmatter de los subagentes del flujo (scouts: `haiku` + `low`, `omitClaudeMd`, `maxTurns`) en vez de depender de una variable | B7 |
| Cuidado: el orden cambió en v2.1.251; un doc o tuit anterior que diga «la variable manda sobre todo» ya no es cierto sin `_FORCE` | B7 |
| `CLAUDE_CODE_EFFORT_LEVEL` gana a todo, incluido el `effort` de skills y subagentes: no fijarla globalmente si se quiere que `selector` recomiende por tarea | B6 |
| `doctor.py` puede comprobar `CLAUDE_CODE_SUBAGENT_MODEL(_FORCE)`, `CLAUDE_CODE_EFFORT_LEVEL`, `availableModels` y versión mínima de Claude Code | B7 |
| Sesión en nube: el coste de `/usage` es a precio de lista; si hay `modelPricing`, el informe debe decirlo | B1 |

Fuentes:
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/sub-agents (secciones «Choose a model», «Choose an effort level», «Run every subagent on one model»)
- https://code.claude.com/docs/en/env-vars
- https://code.claude.com/docs/en/costs
- https://code.claude.com/docs/en/statusline
- https://code.claude.com/docs/en/monitoring-usage

## Pendiente de confirmar

1. Fuente primaria de gh-aw (blog y `github.github.io/gh-aw`): coste real, red/firewall, límites. Requiere permitir los dominios.
2. Documentación de OpenHands: microagentes, perfiles de LLM, coste en la interfaz.
3. `CLAUDE_CODE_SUBAGENT_EFFORT`: pedir al usuario la captura del tuit y la versión de Claude Code; probar en local con `claude --version` y un subagente.
4. `ccusage`: licencia y alcance.
5. Si `/cost` sigue existiendo como alias de `/usage`.
