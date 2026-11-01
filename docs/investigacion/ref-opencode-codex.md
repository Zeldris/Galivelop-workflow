# Referencia: opencode y OpenAI Codex CLI (abrirles la puerta al flujo)

Fecha: 2026-11-01. Bloque F de `docs/diseno/README.md` (apoya A y E). Solo lectura: no se ha cambiado nada del flujo.

**Cómo se ha leído.** Los dominios de documentación (`opencode.ai`, `developers.openai.com`) no resolvían desde la sesión
(fuera de la lista de red permitida). Se ha leído el código y la documentación **que viven en los repos** (clon superficial
de `anomalyco/opencode` y `openai/codex`, `main`/`dev` a fecha de hoy): `packages/web/src/content/docs/*.mdx` de opencode y
los crates `codex-rs/*` de Codex (los `docs/*.md` de Codex solo enlazan a la web). Marca **[NC]** = no confirmado.

## 1. opencode

### Instrucciones
- Lee `AGENTS.md`; si no hay, cae a `CLAUDE.md` (compatibilidad Claude Code). Sube desde el directorio actual; gana el
  primer archivo hallado. Global: `~/.config/opencode/AGENTS.md`, o `~/.claude/CLAUDE.md` si no existe.
  Se desactiva con `OPENCODE_DISABLE_CLAUDE_CODE=1` (`..._PROMPT`, `..._SKILLS` para partes).
- Clave `instructions` en `opencode.json` (rutas, globs, URLs con 5 s de espera) que se suman a `AGENTS.md`.
- **No expande `@archivo` de `AGENTS.md`**: solo se puede pedir al modelo que lo lea (carga perezosa). Es decir, el
  `@AGENTS.md` de nuestro `CLAUDE.md` no se resuelve, pero como `AGENTS.md` tiene prioridad sobre `CLAUDE.md`, no hace falta.

### Skills y comandos
- Soporta `SKILL.md` con frontmatter Agent Skills: `name` (obligatorio, `^[a-z0-9]+(-[a-z0-9]+)*$`, igual al directorio),
  `description` (1-1024), `license`, `compatibility`, `metadata`; el resto se ignora. Se cargan bajo demanda con la
  herramienta `skill`.
- Busca en: `.opencode/skills/`, `~/.config/opencode/skills/`, **`.claude/skills/`**, `~/.claude/skills/`,
  `.agents/skills/`, `~/.agents/skills/` (sube hasta la raíz del worktree). Permisos por patrón (`permission.skill`).
  `OPENCODE_DISABLE_EXTERNAL_SKILLS` desactiva `.claude` y `.agents`.
- Comandos: `.opencode/commands/*.md` o `~/.config/opencode/commands/` (o clave `command`); frontmatter `description`,
  `agent`, `model`, `subtask`; plantilla con `$ARGUMENTS`, `$1..$n`, `` !`cmd` `` y `@archivo`. No son los comandos de
  Claude Code (`.claude/commands/`) **[NC]: no aparecen en los docs de comandos leídos**.

### Ganchos
- No hay ganchos por configuración de comandos: son **plugins JS/TS** (`.opencode/plugins/`, `~/.config/opencode/plugins/`
  o paquetes npm en `plugin`). Eventos: `session.created`, `session.idle`, `session.compacted`, `session.error`,
  `tool.execute.before` / `tool.execute.after`, `permission.asked`, `file.edited`, `shell.env`, `message.*`, `todo.updated`…
- Equivalencias: SessionStart ≈ `session.created`; PreToolUse ≈ `tool.execute.before` (se bloquea con `throw`, se puede
  mutar `output.args`); Stop ≈ `session.idle` (**es un evento, no puede vetar el cierre ni reinyectar un "sigue"** **[NC]**
  en los docs leídos; habría que comprobarlo en el SDK `client.session.prompt`). Un plugin puede ejecutar shell (`$`).
- Los plugins no ven ni leen `.claude/settings.json`.

### Subagentes, modelos, proveedores
- Agentes `primary` (build, plan) y `subagent` (general, explore) en `opencode.json` (`agent`) o markdown en
  `.opencode/agents/*.md` / `~/.config/opencode/agents/`. Campos: `description`, `mode`, `model` (`proveedor/modelo`),
  `temperature`, `steps`, `prompt`, `permission`, `disable`. Un subagente sin `model` usa el del agente que lo invoca.
  `permission.task` controla qué subagentes se pueden lanzar.
- `model`, `small_model` (títulos), `provider.<id>.options` (baseURL, timeouts), `variants` por modelo (esfuerzo de
  razonamiento), modelos locales (LM Studio, Ollama), `enabled_providers`/`disabled_providers`.

### Registros y gasto
- Datos en `~/.local/share/opencode/`: `opencode.db` (SQLite con proyectos, sesiones, mensajes), `log/opencode.log`,
  `snapshot/`. `opencode db path`, `opencode db "<SQL>" --format json`, `opencode export [id]` (JSON; `--sanitize`),
  `opencode stats [--days N --models --project]` (tokens y coste). Para `opt-tokens` basta SQL sobre la base de datos;
  el esquema exacto **[NC]** (no leído).

## 2. OpenAI Codex CLI

### Instrucciones
- Lee `AGENTS.md` desde la raíz del proyecto (marcador `.git` por defecto, `project_root_markers`) hasta el cwd,
  concatenando; `AGENTS.override.md` tiene prioridad local; `project_doc_fallback_filenames` permite añadir nombres como
  `CLAUDE.md` (solo nombres de archivo, no rutas); tope `project_doc_max_bytes`. Global en `~/.codex/` (`CODEX_HOME`).
  No expande includes `@`. Fuente: `codex-rs/core/src/agents_md.rs`.

### Skills y comandos
- `SKILL.md` con frontmatter `name`, `description`, `short-description` (`codex-rs/skills/src/parser.rs`). Raíces vistas
  en código: `$CODEX_HOME/skills`, `~/.agents/skills`, skills de sistema y de plugins. Las de proyecto (`.agents/skills/`,
  `.codex/skills/`) aparecen en tests y en la web, pero **la lectura de raíces de proyecto no se ha podido confirmar en
  el código** **[NC]**. **No lee `.claude/skills/`** (hay un crate de migración desde Claude Code, `external-agent-migration`,
  que importa `CLAUDE.md`, `.claude.json` y ganchos: indica que la ruta prevista es migrar, no compartir).
- Comandos de barra integrados; los prompts personalizados (`~/.codex/prompts/*.md`) están **[NC]** (la doc web no
  se pudo leer; en el código reciente no se vio) y las skills los van sustituyendo.

### Ganchos
- Existen y son casi un calco de los de Claude Code. Eventos (`protocol/src/hooks.rs`): `PreModelRequest`,
  `PostModelRequest`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`,
  `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop`, `Interrupt`.
- Config: `hooks.json` (`{"hooks": {...}}`) en la carpeta de config (`~/.codex/` o `.codex/` del proyecto) o tabla
  `[hooks]` de `config.toml`; grupos con `matcher` y manejadores `{"type":"command","command","timeout","statusMessage"}`
  (existe también un tipo MCP). Entrada JSON por stdin con `session_id`, `cwd`, `model`, `permission_mode`,
  `transcript_path`, `hook_event_name`, `source` (`startup|resume|clear|compact|fork`).
- Salida: `PreToolUse` admite `permissionDecision` allow/deny/ask, `permissionDecisionReason`, `updatedInput`,
  `additionalContext`; `Stop` admite `{"decision":"block","reason":...}` (el comentario del esquema dice "Claude requires
  reason…": copia deliberada del contrato de Claude). Hay `allow_managed_hooks_only` en `requirements.toml` (empresa) y
  una confianza ("trust") de ganchos por proyecto. Un `Stop` que bloquea es justo lo que usa `antes-de-parar.py`.

### Subagentes, modelos, proveedores
- Roles de agente: archivos `.toml` en `agents/` de la carpeta de config o tabla `[agents]`; campos `name`,
  `description`, `nickname_candidates` y cualquier clave de `config.toml` (p. ej. `model`), así que **cada rol puede fijar
  su modelo**. Reparto por la herramienta de lanzamiento de agentes; ganchos `SubagentStart/Stop`.
- `config.toml`: `model`, `model_provider`, `[model_providers.<id>]` (baseURL, claves), `model_reasoning_effort`,
  `[profiles.<n>]` (se elige con `--profile`), `--oss` para locales (LM Studio/Ollama). Sandbox y aprobaciones propios
  (`sandbox_mode`, `approval_policy`, `execpolicy`).

### Registros y gasto
- Sesiones en `~/.codex/sessions/AAAA/MM/DD/rollout-<fecha>-<uuid>.jsonl`; los eventos `token_count` llevan
  `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`, `total_tokens` (totales y por turno,
  `protocol.rs`). **Sin coste en dinero**: se calcula con tarifas externas. `codex exec --json` emite eventos en stdout.
  Forma exacta del `jsonl` en disco **[NC]** (no se abrió un archivo real).

## 3. Qué encaja, qué necesita adaptación, qué no

- **Encaja tal cual:** `AGENTS.md` como fuente de instrucciones (ambos); `SKILL.md` formato Agent Skills (opencode lo lee
  incluso de `.claude/skills/`; Codex de `~/.agents/skills`); `docs/traspaso.md`, `gw.json`, los scripts de Python y los
  ganchos de git (`.githooks/`, no dependen del agente).
- **Capa de adaptación:** (a) ganchos: para Codex, generar `hooks.json`/`[hooks]` a partir de la plantilla de
  `settings.json` (el contrato casi coincide; revisar nombres de campos y la matriz de `matcher`); para opencode, un
  plugin JS fino que invoque los mismos scripts y traduzca (`throw` / código de salida). (b) `CLAUDE.md` con `@AGENTS.md`:
  innecesario fuera de Claude Code, dejar solo `AGENTS.md`. (c) Lectura de logs para `opt-tokens`: un lector por formato
  (transcript de Claude Code, SQLite de opencode, rollout jsonl de Codex) detrás de una interfaz común de «uso por
  turno/agente/modelo». (d) Subagentes: `.claude/agents/*.md` → `.opencode/agents/*.md` (muy parecido) y roles `.toml` de
  Codex. (e) Ventana de compactación (`settings.json`): cada herramienta la configura aparte.
- **No encaja:** `PreToolUse` de Claude como bloqueo de permisos para el modo automático; el tope por sesión de
  subagentes (`tope-subagentes.py`) depende de campos de Claude; el `Stop` de opencode no veta **[NC]**; skills en
  Codex sin `.claude/skills/`; coste en dinero en Codex; disparo por descripción de skills (cada herramienta lo decide
  distinto).

## 4. Ideas que el flujo podría copiar
1. De opencode: `permission.skill` por patrón y por agente, y `steps` (tope de iteraciones por agente) como control de gasto.
2. De opencode: `opencode stats` y la base SQLite consultable: modelo para el MMC (bloque G) y para una interfaz de
   uso común; `export --sanitize` para compartir sesiones sin secretos.
3. De opencode: la clave `instructions` con globs en lugar de `@`; evita cadenas de includes.
4. De Codex: `AGENTS.override.md` (ajuste local sin tocar lo versionado), `project_doc_max_bytes` (tope duro del tamaño
   de instrucciones: comprobable por script) y `project_root_markers`.
5. De Codex: perfiles (`[profiles]`) y roles de agente con su propia configuración: encaja con los «perfiles» y
   «modelos por necesidad» del MMC (B4/B5/G).
6. De Codex: ganchos `PreModelRequest`/`PostModelRequest` y `SubagentStart/Stop` para medir gasto por agente en tiempo
   real, y confianza ("trust") de ganchos de proyecto, parecida a nuestra `guardia-config.py`.
7. Ambos: usar `.agents/skills/` como ubicación neutral de skills (la leen opencode y Codex; Claude Code, no: habría
   que enlazar `.claude/skills` → `.agents/skills` o copiar en `aplicar.py`).

## 5. Tabla: pieza del flujo → opencode → Codex

| Pieza del flujo | opencode | Codex |
|---|---|---|
| `AGENTS.md` | Sí (con `CLAUDE.md` de reserva) | Sí (`AGENTS.override.md`, reservas configurables, jerarquía raíz→cwd) |
| `CLAUDE.md` con `@AGENTS.md` | No expande `@`; innecesario | No expande `@`; innecesario |
| Skills `skills/<n>/SKILL.md` | Sí; lee `.claude/skills/` y `.agents/skills/` | Sí; lee `~/.agents/skills`, `$CODEX_HOME/skills`; `.claude/skills` no; proyecto [NC] |
| Comandos / `/skill` | `.opencode/commands/*.md` | Barra integrada; prompts personalizados [NC] |
| Gancho SessionStart (`session-start.sh`) | Plugin: `session.created` | `SessionStart` (`hooks.json`/`[hooks]`) |
| Gancho PreToolUse (`guardia-config.py`, `tope-subagentes.py`) | Plugin: `tool.execute.before` (`throw`) | `PreToolUse` con `permissionDecision` |
| Gancho Stop (`antes-de-parar.py`) | Plugin: `session.idle` (no veta [NC]) | `Stop` con `decision: block` |
| Ganchos de git (`.githooks/`) | Igual (independientes del agente) | Igual |
| `.claude/settings.json` (compactación, permisos) | `opencode.json` (`permission`, `agent`) | `config.toml` (`sandbox_mode`, `approval_policy`) |
| `.claude/gw.json` + `config.py` | Igual (propio del flujo) | Igual |
| Bitácora `docs/traspaso.md` | Igual | Igual |
| Subagentes (`orchestrate-dealer`, `selector`) | `.opencode/agents/*.md`, `model` por agente, `permission.task` | Roles `.toml` en `agents/`, `model` por rol |
| Modelo por agente / proveedores | `provider/modelo`, `small_model`, `variants` | `model_provider`, `[model_providers]`, `[profiles]`, esfuerzo |
| Registro de sesiones (`registro_sesion.py`, `recuperar.py`) | `opencode.db` (SQLite), `opencode export` | `~/.codex/sessions/**/rollout-*.jsonl` |
| Medida de gasto (`opt-tokens`) | `opencode stats`, SQL sobre la base | Eventos `token_count` del rollout; sin coste |
| Recuperación tras compactar | `session.compacted` (plugin) | `PostCompact` / `SessionStart source=compact` |

## Fuentes
- https://github.com/anomalyco/opencode (README; `packages/web/src/content/docs/`: `rules.mdx`, `skills.mdx`,
  `plugins.mdx`, `agents.mdx`, `commands.mdx`, `config.mdx`, `models.mdx`, `permissions.mdx`, `cli.mdx`,
  `troubleshooting.mdx`). Versión web equivalente: https://opencode.ai/docs/ (no accesible desde la sesión).
- https://github.com/openai/codex (README y `docs/`; código: `codex-rs/core/src/agents_md.rs`, `codex-rs/skills/src/parser.rs`,
  `codex-rs/hooks/schema/generated/*.json`, `codex-rs/hooks/src/engine/discovery.rs`, `codex-rs/protocol/src/hooks.rs`,
  `codex-rs/agent-roles/src/`, `codex-rs/config/src/config_toml.rs`, `codex-rs/protocol/src/protocol.rs`,
  `codex-rs/rollout/src/tests.rs`, `codex-rs/exec-server/src/discoverV2/capability_locations.rs`).
- Documentación web de Codex (no accesible): https://developers.openai.com/codex/guides/agents-md ,
  https://developers.openai.com/codex/skills , https://developers.openai.com/codex/config-reference
