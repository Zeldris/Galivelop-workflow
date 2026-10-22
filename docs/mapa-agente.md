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
| Arranque, recuperación y diagnóstico | [`plan.md`](plan.md) §5.2; ganchos y ventana de compactación en `templates/claude/settings.json` (y `hooks/hooks.json` para el plugin) | `scripts/session-start.sh`, `recuperar.py`, `registro_sesion.py`, `doctor.py` |
| Bitácora por ramas | config `logRows`, `plan`, `taskId` | `scripts/bitacora.py`, `prepush-ramas.sh` |
| Aplicar y actualizar el flujo | [`es/aplicar.md`](es/aplicar.md), [`en/apply.md`](en/apply.md) | `scripts/aplicar.py` (`--init`, `--update`, `--check`) |
| Plantillas para proyectos | `templates/es`, `templates/en`, `templates/gw.json` | `tests/test_plantillas.py` |
| Skills | `skills/<nombre>/SKILL.md` (formato Agent Skills) | `tests/test_skills.py`; copia en `.claude/skills/` |
| Recogida de mejoras | `skills/gw-harvest/SKILL.md` | `scripts/recoger.py`, `docs/propuestas/` |
| Tests | `tests/test_*.py`, `skills/*/scripts/test_*.py` | `tests/comprobar.sh` |
| Problemas conocidos | [`es/problemas.md`](es/problemas.md), [`en/troubleshooting.md`](en/troubleshooting.md) | — |

La copia del flujo aplicada a este repo (`.claude/gw/`, `.claude/skills/`, `.githooks/`, `.claude/settings.json`) se
genera con `python3 scripts/aplicar.py .`; no se edita a mano (el check lo comprueba con `--check`).
