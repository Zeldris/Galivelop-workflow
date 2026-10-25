# Mapa para agentes

Dónde está cada contrato de este repo y qué lo implementa. Los encargos a subagentes apuntan aquí en vez de a varios
documentos. Si mueves una pieza, actualiza su fila en el mismo commit.

| Contrato | Dónde se define | Qué lo implementa / comprueba |
|---|---|---|
| Reglas para trabajar en este repo | [`AGENTS.md`](../AGENTS.md), [`CLAUDE.md`](../CLAUDE.md) | `tests/comprobar.sh` (check), `.githooks/` |
| Decisiones y fases | [`plan.md`](plan.md) §0 y §9 | [`traspaso.md`](traspaso.md) (estado) |
| Config del proyecto (`.claude/gw.json`) | [`schema/gw.schema.json`](../schema/gw.schema.json), [`es/config.md`](es/config.md) | `scripts/config.py` (único lector) |
| Código frente a contenido | `content` del config | `scripts/es-codigo.sh` |
| Subida y revisión antes de la rama protegida | [`plan.md`](plan.md) §5.3, `AGENTS.md` § ramas | `templates/githooks/pre-push`, `scripts/revisado.sh`, `scripts/revision-antes-de-main.sh`, `scripts/fusionar.sh` (fusión con check) |
| Secretos y rutas protegidas | Patrones en la cabecera de `templates/githooks/pre-commit`; rutas en la clave `protectedPaths` | `templates/githooks/pre-commit` (tests en `tests/test_ganchos.py`) |
| Bitácora en el commit | `log` y `logRows` del config; cabecera de `templates/githooks/commit-msg` | `templates/githooks/commit-msg` (corre `bitacora.py check` sobre la bitácora preparada; tests en `tests/test_ganchos.py`) |
| Arranque, recuperación y diagnóstico | [`plan.md`](plan.md) §5.2; ganchos y ventana de compactación en `templates/claude/settings.json` (y `hooks/hooks.json` para el plugin) | `scripts/session-start.sh`, `recuperar.py`, `registro_sesion.py`, `doctor.py` |
| Cierre de turno: nada sin subir ni sin bitácora (gancho `Stop`) | cabecera de `scripts/antes-de-parar.py`; `Stop` en `templates/claude/settings.json` y `hooks/hooks.json` | `scripts/antes-de-parar.py` (tests en `tests/test_parar.py`); `doctor.py` y `aplicar.py` avisan de un `Stop` duplicado |
| Configuración del flujo protegida (gancho `PreToolUse` que pide permiso) | cabecera de `scripts/guardia-config.py`; `PreToolUse` en `templates/claude/settings.json` y `hooks/hooks.json` | `scripts/guardia-config.py` (tests en `tests/test_guardia.py`); `doctor.py` y `aplicar.py` avisan de un gancho viejo duplicado |
| Bitácora por ramas | config `logRows`, `plan`, `taskId` | `scripts/bitacora.py`, `prepush-ramas.sh` |
| Aplicar y actualizar el flujo | [`es/aplicar.md`](es/aplicar.md), [`en/apply.md`](en/apply.md) | `scripts/aplicar.py` (`--init`, `--update`, `--check`) |
| Plantillas para proyectos | `templates/es`, `templates/en`, `templates/gw.json` | `tests/test_plantillas.py` |
| Skills | `skills/<nombre>/SKILL.md` (formato Agent Skills) | `tests/test_skills.py`; copia en `.claude/skills/` |
| Contenido para redes (`gw-media-content`, `gw-media-content-now`) | `skills/gw-media-content/SKILL.md`, `skills/gw-media-content-now/SKILL.md`; límites por red en `reglas.json` (`P` verificado, `S` por fuente, `NV` sin verificar), tipos de post en `catalogo.md`; investigación en `docs/investigacion/redes-sociales.md`; nota del proyecto `.claude/gw/gw-media-content.md` | `skills/gw-media-content/scripts/` (`cifras.py`, `comprobar.py`, `render.mjs` y sus `test_*.py`; el render real necesita Playwright e ImageMagick y no lo cubre el CI) |
| Recogida de mejoras (una por versión) | `skills/gw-harvest/SKILL.md`, `AGENTS.md` | `scripts/recoger.py`, `docs/propuestas/`; `scripts/version.py --release` la exige |
| Tests | `tests/test_*.py`, `skills/*/scripts/test_*.py` | `tests/comprobar.sh` |
| Problemas conocidos | [`es/problemas.md`](es/problemas.md), [`en/troubleshooting.md`](en/troubleshooting.md) | — |

La copia del flujo aplicada a este repo (`.claude/gw/`, `.claude/skills/`, `.githooks/`, `.claude/settings.json`) se
genera con `python3 scripts/aplicar.py .`; no se edita a mano (el check lo comprueba con `--check`).
