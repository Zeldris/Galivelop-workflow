# Referencias: JetBrains thinkrail, garrytan/gstack y affaan-m/ECC

Fecha: 2026-11-01. Bloque F de `docs/diseno/README.md`. Solo se leyó la página principal de cada repo (WebFetch,
resumida por un modelo pequeño); no se abrieron sus subcarpetas ni docs enlazados. Lo no confirmado va marcado
**[sin confirmar]**.

## 1. JetBrains thinkrail

- **Qué es:** IDE agéntico de escritorio y navegador (Apache-2.0) construido sobre el agente `pi`. Resuelve que los
  agentes en un único checkout chocan, pierden contexto entre sesiones y dan poca visibilidad: aísla el trabajo en
  git worktrees y guarda el conocimiento del proyecto en especificaciones vivas (`SPEC.md`).
- **Estado:** 6,9k estrellas, 389 forks, 648 commits en `main`, 215 issues y 108 PR abiertos. Releases y fecha de la
  última actividad: **[sin confirmar]** (no salen en la página).
- **Piezas:** `apps/` (cli, desktop con Electrobun, web React), `packages/` (server, shared, contracts),
  `pi-extensions/`, `thinkrail-extensions/`, `.pi/prompts/`, `e2e/`, `.changeset/`, `.husky/`, `design-audit/`,
  `biome-plugins/`; docs `architecture.md`, `goal-and-requirements.md`, `AGENTS.md`. Skills portables (Agent Skills),
  workflows incluidos (montar proyecto, brainstorming de diseño, enviar PR), herramientas `spec_*` para leer, buscar
  y mantener los `SPEC.md`, MCP por `mcp.json`, subagentes. Ganchos propios: **[sin confirmar]**.
- **Instalación y actualización:** instaladores de escritorio y CLI (`install.sh`/`install.ps1`); canales stable y
  nightly, versión fijable; autoactualización desde Ajustes y `thinkrail update`.
- **Modelos:** un modelo por chat; JetBrains AI o cualquier proveedor vía `pi`, y servidores compatibles con OpenAI.
  Sin tabla de modelo por tarea (**[sin confirmar]**).
- **Tokens:** lectura en vivo de tokens y coste en cada chat. Informes por periodo: **[sin confirmar]**.
- **Memoria/traspaso:** grafo de `SPEC.md` junto al código (la intención sobrevive a las sesiones), planes
  compartidos y commit por paso.
- **Preguntas antes de implementar:** no hay mecanismo explícito visible.
- **Revisión:** comentarios anclados en archivos y diffs que se envían al chat; estado del workspace frente a
  `origin` y al PR; CI y decisiones de revisión visibles.
- **Versionado:** `.changeset/`, canales y fijado de versión.
- **Configuración/perfiles:** lee `~/.pi/agent`; perfiles alternos con `PI_CODING_AGENT_DIR` o Ajustes; estado en
  `~/.thinkrail`; analítica desactivable.
- **Mejor que el flujo:** interfaz visual (diff, terminal, árbol de worktrees, coste en vivo), specs vivos
  consultables por herramienta, perfiles alternables, canales stable/nightly con autoactualización.
- **Mejor en el flujo:** reglas deterministas en ganchos (marca de revisión, bitácora en el commit, sin firmas),
  traspaso por relevos entre sesiones, retro y `opt-tokens`, cierre por fases antes de `main`.
- **Ideas:** (a) panel con coste vivo por chat/agente -> G, B1; (b) perfiles alternables por entorno -> G;
  (c) `SPEC.md` por carpeta como memoria de intención, enlazada a la bitácora -> D (trazabilidad); (d) comentarios
  de revisión anclados que se pasan al agente como contexto -> D; (e) worktree por tarea como unidad de aislamiento
  -> D (worktrees); (f) canales stable/nightly -> A.

## 2. garrytan/gstack

- **Qué es:** conjunto de skills Markdown (MIT) que convierte Claude Code (y otros agentes) en un equipo virtual con
  roles por fase del sprint, «roles en vez de un prompt en blanco». Lo publica Garry Tan (YC) como su configuración
  diaria.
- **Estado:** 138,6k estrellas, 20,5k forks, 792 commits, 81 issues y 90 PR abiertos. La descripción dice «23
  herramientas», pero la página lista bastantes más (cuenta exacta: **[sin confirmar]**). Releases vacías en la
  captura; fecha de última actividad **[sin confirmar]**.
- **Piezas (por grupo):**
  - Planificación y revisión: `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`,
    `/plan-devex-review`, `/autoplan`, `/review`, `/test-audit`, `/cso` (seguridad), `/investigate`, `/verify`.
  - Diseño: `/design-consultation`, `/design-shotgun`, `/design-html`, `/design-motion`, `/design-review`.
  - Construir y publicar: `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/spec`, `/eval-plan`.
  - QA y navegador: `/qa`, `/qa-only`, `/browse`, `/scrape`, `/pair-agent`.
  - Docs: `/document-release`, `/document-generate`, `/diagram`, `/write-skill`.
  - Seguridad: `/careful`, `/freeze`, `/guard`, `/unfreeze`.
  - Equipo: `/captain`, `/retro`; iOS (`/ios-*`); segundas opiniones `/codex`, `/claude-code`; `/learn`,
    `/gstack-upgrade`, `gstack-doctor`.
- **Instalación y actualización:** clonar en `~/.claude/skills/gstack` y `./setup` (necesita Bun >= 1.4.2); otros
  agentes con `--host`. Modo equipo (`./setup --team`) comprueba actualizaciones al inicio (máx. cada hora);
  `/gstack-upgrade` a mano.
- **Modelos:** sin selector general; el navegador enruta Sonnet para acciones y Opus para análisis; Codex como
  segunda opinión.
- **Tokens:** poco tratado; CLI `gstack-context-bill` y `/eval-plan` con ejecución de prueba a 0 $ (detalles
  **[sin confirmar]**).
- **Memoria/traspaso:** `/learn` (patrones y preferencias persistentes), GBrain (base de conocimiento), `/spec`
  archivado; `/context-save` y `/context-restore` aparecen en el árbol pero no se describen **[sin confirmar]**.
- **Preguntas antes de implementar:** `/office-hours` interroga y reta el planteamiento y escribe un diseño que leen
  las demás; la revisión de diseño pregunta una cosa por decisión; `/autoplan` solo te pasa las decisiones de gusto.
- **Revisión:** `/review` (arregla lo obvio), cuatro revisiones de plan (CEO, ingeniería, diseño, DX), `/cso`, `/qa`
  en navegador real.
- **Versionado:** canal `stable` con releases etiquetadas lunes y jueves, mínimo 72 h entre ellas; canal `main`
  opcional; `CHANGELOG.md`.
- **Configuración:** `gstack-config set` (`update_check`, `codex_reviews`, `update_channel`), telemetría apagada por
  defecto, `gstack-doctor`; perfiles con nombre: no se ven.
- **Mejor que el flujo:** roles claros por fase (producto, diseño, DX, release, seguridad), preguntas guiadas antes
  de planificar, QA en navegador real, segunda opinión de otro modelo, cadencia de releases definida, `/freeze` y
  `/careful` como modos restrictivos.
- **Mejor en el flujo:** control determinista (ganchos y check en vez de solo skills), traspaso entre sesiones sin
  perder estado, mediciones de tokens, marca de revisión obligatoria antes de `main`.
- **Ideas:** (a) `/freeze`/`/careful` como modelo del modo restrictivo -> C; (b) `/office-hours` + `/autoplan`: skill
  de preguntas previas que solo escala lo que exige criterio -> C; (c) roles como skills que consumen el mismo
  documento de diseño -> G (roles DEV/QA/ADMIN) y D; (d) canal stable con cadencia mínima entre releases y
  `doctor` -> A, D; (e) segunda opinión de otro modelo en la revisión -> B5/B6; (f) `/eval-plan` con ejecución de
  prueba a coste 0 -> B; (g) `context-bill`: factura de contexto por skill -> B1.

## 3. affaan-m/ECC

- **Qué es:** «agent harness» (MIT) de skills, agentes, comandos, ganchos, reglas y memoria para Claude Code, con
  plugins nativos para Codex y Qoder y adaptadores parciales (Cursor, OpenCode, Gemini, Copilot…). Aporta un proceso
  repetible: planificar antes, test primero, revisar con contexto limpio, verificar, guardar aprendizajes. Lema:
  «Optimiza la ventana de contexto. Persiste todo lo demás».
- **Estado:** ~294,7k estrellas, ~43,6k forks, 4.321 commits, versión 2.2.3 (2026-10-01). Número de releases y última
  actividad **[sin confirmar]**.
- **Piezas:** 71 agentes, 314 skills (superficie principal), 98 atajos de comandos (compatibilidad; los retirados
  en `legacy-command-shims/`), ganchos, reglas opcionales (`common/` + paquetes por lenguaje), AgentShield (escaneo
  de prompts, ganchos, MCP y permisos).
- **Instalación y actualización:** `npx ecc-universal@2.2.3 setup` o `/plugin marketplace add` + `/plugin install
  ecc@ecc`; no apilar métodos; volver a correr la guía actualiza y cambia ámbito o perfil de ganchos.
- **Modelos:** agnóstico del proveedor (`ANTHROPIC_BASE_URL`, modelos autoalojados). Sin tabla por tarea
  **[sin confirmar]** (leído solo el 70 % de la página).
- **Tokens:** las reglas siempre cargan, por eso se recomienda `common` + un lenguaje; perfiles `minimal`;
  `ECC_SESSION_START_MAX_CHARS` y `ECC_SESSION_START_CONTEXT=off` limitan el contexto de arranque.
- **Memoria/traspaso:** Memory Vault en Markdown `ecc.memory.v1` (`.ecc/memory/` y `~/.ecc/memory/`), comandos
  `ecc memory` (búsqueda, traspasos entre harness, doctor); lo recordado se trata como contexto sin revisar, no como
  política.
- **Preguntas antes de implementar:** `/ecc:plan` produce un plan editable antes de implementar; paso explícito de
  preguntas: no visible.
- **Revisión:** `/code-review` con agente de contexto limpio; TDD con puerta RED, GREEN, REFACTOR y verificación.
- **Versionado:** paquete npm `ecc-universal` por etiqueta de versión, `CHANGELOG.md`.
- **Configuración/perfiles:** perfiles de instalación `minimal`/`core`/`full`, `--no-hooks`/`--enable-hooks`,
  `ECC_HOOK_PROFILE` (por defecto `standard`), `ECC_DISABLED_HOOKS`, `ECC_DISABLED_MCPS`, `ECC_AGENT_DATA_HOME`;
  madurez desigual por harness.
- **Mejor que el flujo:** perfiles de instalación y de ganchos configurables por variable, memoria portable con
  búsqueda y doctor, multi-harness (abre la puerta a Codex, OpenCode…), escaneo de seguridad de la configuración,
  límite del contexto de arranque, distribución por npm y marketplace.
- **Mejor en el flujo:** pocas piezas, con ganchos que fallan cerrados y tests por cambio (ECC mide por volumen: 314
  skills y 71 agentes pesan en contexto); marca de revisión; bitácora ligada al commit; medición de tokens.
- **Ideas:** (a) perfiles `minimal/core/full` y `ECC_HOOK_PROFILE` -> G (perfiles) y A; (b) `ECC_DISABLED_HOOKS`
  como interruptores por gancho -> C, G; (c) tope de caracteres del contexto de arranque -> B (gasto); (d) memoria
  «sin revisar» frente a política -> D (trazabilidad, qué se fía); (e) escáner de la configuración (AgentShield)
  -> E; (f) `memory doctor` y búsqueda -> D; (g) publicar también por npm/marketplace -> A.

## 4. Tabla comparativa

| Aspecto | Flujo Galivelop | thinkrail | gstack | ECC |
|---|---|---|---|---|
| Tipo | skills + ganchos + scripts | IDE sobre `pi` | skills por rol | harness de skills/agentes/ganchos |
| Adopción | repo propio | 6,9k estrellas | 138,6k | ~294,7k |
| Piezas | pocas, deterministas | app, specs, extensiones | muchas skills (>23) | 314 skills, 71 agentes |
| Instalación | `aplicar.py` / plugin | instalador, CLI | clon + `./setup` | npx, plugin marketplace |
| Actualización | `aplicar.py --update` | autoactualiza, canales | `/gstack-upgrade`, canal stable | reejecutar guía |
| Modelo por tarea | `selector` (criterio); tabla en B5 | por chat | casi nada | casi nada (sin confirmar) |
| Gasto de tokens | `opt-tokens`, informes (en diseño) | coste en vivo | `context-bill` | límites de contexto |
| Traspaso | bitácora + ganchos | `SPEC.md` + planes | `/learn`, GBrain | Memory Vault |
| Preguntas previas | bloque C (en diseño) | no visible | `/office-hours` | `/ecc:plan` |
| Revisión | `/code-review` + marca obligatoria | comentarios anclados | `/review`, 4 planes | `/code-review`, TDD |
| Releases | etiqueta manual, recogida | changesets, canales | stable L/J, 72 h | npm por etiqueta |
| Perfiles | ninguno (bloque G) | `PI_CODING_AGENT_DIR` | `gstack-config` | minimal/core/full |

## 5. Ideas priorizadas por bloque de diseño

- **A:** canal stable con cadencia mínima (gstack); distribución por npm/marketplace (ECC); `doctor` (ya existe).
- **B:** coste en vivo por chat (thinkrail) para B1; `context-bill` por skill (gstack); tope del contexto de
  arranque (ECC); `/eval-plan` a coste 0; segunda opinión de otro modelo para B5/B6.
- **C:** `/freeze`/`/careful` y `/office-hours`+`/autoplan` (gstack); interruptores por gancho (ECC).
- **D:** worktree por tarea y comentarios anclados (thinkrail); `SPEC.md` por carpeta enlazado a la bitácora;
  memoria «no es política» (ECC).
- **E:** escáner de configuración tipo AgentShield (ECC).
- **G:** perfiles alternables (thinkrail), `minimal/core/full` (ECC), roles como skills (gstack), panel de coste.

## Fuentes

- https://github.com/JetBrains/thinkrail
- https://github.com/garrytan/gstack
- https://github.com/affaan-m/ECC (leído hasta el carácter 100.000 de 139.157)

Limitación: los datos salen de la página principal de GitHub resumida por un modelo pequeño; las cifras
(estrellas, commits) son las de esa captura y conviene reverificarlas.
