# Mapa para agentes

Dónde está cada contrato de este repo y qué lo implementa. Los encargos a subagentes apuntan aquí en vez de a varios
documentos. Si mueves una pieza, actualiza su fila en el mismo commit.

| Contrato | Dónde se define | Qué lo implementa / comprueba |
|---|---|---|
| Reglas para trabajar en este repo | [`AGENTS.md`](../AGENTS.md), [`CLAUDE.md`](../CLAUDE.md) | `tests/check.sh` (check), `.githooks/` |
| Decisiones y fases | [`plan.md`](plan.md) §0 y §9 | [`handoff.md`](handoff.md) (estado) |
| Config del proyecto (`.claude/gw.json`) | [`schema/gw.schema.json`](../schema/gw.schema.json), [`es/config.md`](es/config.md) | `scripts/config.py` (único lector) |
| Código frente a contenido | `content` del config | `scripts/is-code.sh` |
| Subida y revisión antes de la rama protegida | [`plan.md`](plan.md) §5.3, `AGENTS.md` § ramas | `templates/githooks/pre-push`, `scripts/reviewed.sh`, `scripts/review-before-main.sh`, `scripts/merge-branch.sh` (fusión con check y tests relacionados), `scripts/check.sh` (pasa el `check` y apunta el verde) y `scripts/check-green.sh` (la caché que lee el `pre-push`; [`es/config.md`](es/config.md) § Notas; tests en `tests/test_hooks.py`, clases `CheckCache`, `CheckRunner` y `CheckVerde`) |
| CI en local cuando GitHub no lo arranca | cabecera de `scripts/ci-local.py`; config `ciLocalLog` y `ciLocalWorkflows` | `scripts/ci-local.py` (con `--record`, la línea que acepta `review-before-main.sh`, `ci_local_green`; tests en `tests/test_ci_local.py` y `tests/test_review_before_main.py`) |
| Secretos y rutas protegidas | Patrones en la cabecera de `templates/githooks/pre-commit`; rutas en la clave `protectedPaths` | `templates/githooks/pre-commit` (tests en `tests/test_hooks.py`) |
| Bitácora en el commit | `log` y `logRows` del config; cabecera de `templates/githooks/commit-msg` | `templates/githooks/commit-msg` (corre `handoff.py check` sobre la bitácora preparada; tests en `tests/test_hooks.py`, clase `CommitMsg`) |
| Sin firmas del agente en los commits | config `agentSignatures` ([`schema/gw.schema.json`](../schema/gw.schema.json), [`es/config.md`](es/config.md)); bandera `apply.py --init --agent-signatures`; cabecera de `templates/githooks/commit-msg` | `templates/githooks/commit-msg` (con `false` rechaza `Co-Authored-By` de un modelo Claude o con `noreply@anthropic.com`, `Claude-Session` y las líneas que empiezan por «Generated with Claude Code» o un enlace `claude.ai/code/session`; tests en `tests/test_hooks.py`, clase `CommitMsgSignatures`, y `tests/test_templates.py`) |
| Arranque, recuperación y diagnóstico | [`plan.md`](plan.md) §5.2; ganchos y ventana de compactación en `templates/claude/settings.json` (y `hooks/hooks.json` para el plugin) | `scripts/session-start.sh`, `recover.py`, `session_log.py`, `doctor.py` |
| Cierre de turno: nada sin subir ni sin bitácora (gancho `Stop`) | cabecera de `scripts/before-stop.py`; `Stop` en `templates/claude/settings.json` y `hooks/hooks.json` | `scripts/before-stop.py` (tests en `tests/test_before_stop.py`); `doctor.py` y `apply.py` avisan de un `Stop` duplicado |
| Configuración del flujo protegida (gancho `PreToolUse` que pide permiso) | cabecera de `scripts/config-guard.py`; `PreToolUse` en `templates/claude/settings.json` y `hooks/hooks.json` | `scripts/config-guard.py` (tests en `tests/test_config_guard.py`); `doctor.py` y `apply.py` avisan de un gancho viejo duplicado |
| Tope de subagentes por sesión (gancho `PreToolUse` que pide permiso) | cabecera de `scripts/subagent-cap.py`; config `subagentCap`; `PreToolUse` en `templates/claude/settings.json` y `hooks/hooks.json` | `scripts/subagent-cap.py` (tests en `tests/test_subagent_cap.py`); `doctor.py` y `apply.py` avisan de un gancho viejo duplicado |
| Bitácora por ramas | config `logRows`, `plan`, `taskId` | `scripts/handoff.py`, `prepush-branches.sh`; tareas cerradas frente a «Hecho» también en `templates/githooks/pre-commit` (`handoff.py closed --staged`); id de tarea dado de alta en dos ramas: `handoff.py clash` (`prepush-branches.sh`, y `clash --merging` en el `pre-commit`) |
| Bitácora corta (celdas ≤ 800, «Hecho» ≤ 5 elementos) | `log` del config; sin `logRows` también | `scripts/handoff.py` (`check --strict`, `done`); `tests/check.sh` la pasa sobre la bitácora de este repo; tests en `tests/test_utils.py` |
| Mapa para agentes: rutas que cita | [`agent-map.md`](agent-map.md) (este archivo); config `agentMap` (`path`, `prefixes`, `roots`) en [`schema/gw.schema.json`](../schema/gw.schema.json) y [`es/config.md`](es/config.md) | `scripts/agent-map.py` (en el `check` de las plantillas y de este repo; tests en `tests/test_agent_map.py`) |
| Aplicar y actualizar el flujo | [`es/apply.md`](es/apply.md), [`en/apply.md`](en/apply.md) | `scripts/apply.py` (`--init`, `--update`, `--check`, `--no-personal-notes`) |
| Notas personales (de `~/.claude/gw/notas/` o `GW_PERSONAL_NOTES` a `.claude/gw/` de cada proyecto, nunca al repo del flujo) | [`es/config.md`](es/config.md) § Notas personales, [`en/config.md`](en/config.md) | `scripts/apply.py` (tests en `tests/test_apply.py`, clase `NotasPersonales`) |
| Plantillas para proyectos | `templates/es`, `templates/en`, `templates/gw.json` | `tests/test_templates.py` |
| Skills | `skills/<nombre>/SKILL.md` (formato Agent Skills); consultas de disparo en `skills/<nombre>/evals/triggers.json` (a mano) | `tests/test_skills.py`; copia en `.claude/skills/` |
| Contenido para redes (`gw-media-content`, `gw-media-content-now`) | `skills/gw-media-content/SKILL.md`, `skills/gw-media-content-now/SKILL.md`; límites por red en `reglas.json` (`P` verificado, `S` por fuente, `NV` sin verificar), tipos de post en `catalogo.md`; investigación en `docs/research/social-media.md`; nota del proyecto (`gw-media-content.md`, junto a las demás notas de `.claude/gw/` del proyecto que lo use) | `skills/gw-media-content/scripts/` (`cifras.py`, `comprobar.py`, `render.mjs` y sus `test_*.py`; el render real necesita Playwright e ImageMagick y no lo cubre el CI) |
| Recogida de mejoras (una por versión) | `skills/gw-harvest/SKILL.md`, `AGENTS.md` | `scripts/harvest.py`, `docs/proposals/`; `scripts/version.py --release` la exige |
| Tests | `tests/test_*.py`, `skills/*/scripts/test_*.py` | `tests/check.sh` |
| Problemas conocidos | [`es/troubleshooting.md`](es/troubleshooting.md), [`en/troubleshooting.md`](en/troubleshooting.md) | — |

La copia del flujo aplicada a este repo (`.claude/gw/`, `.claude/skills/`, `.githooks/`, `.claude/settings.json`) se
genera con `python3 scripts/apply.py .`; no se edita a mano (el check lo comprueba con `--check`).

**Qué no leer** salvo que el encargo lo pida: `docs/research/` y `docs/proposals/` (notas y recogidas, no
contratos), `docs/records/` (historial) y `CHANGELOG*` (lo lleva la sesión principal).
