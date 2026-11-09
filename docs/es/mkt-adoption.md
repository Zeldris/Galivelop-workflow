# Galivelop-workflow para tu equipo

[English](../en/mkt-adoption.md)

Un flujo de trabajo para programar con agentes de IA (primero Claude Code), sacado de proyectos reales: **skills,
ganchos, scripts y plantillas** que se instalan en tu repositorio y hacen cumplir las reglas en vez de confiar en que
el agente las recuerde.

## Qué resuelve

- **Las sesiones se acaban** (tokens, contenedor, cambio de cuenta): la bitácora `docs/handoff.md` y el trailer
  `Siguiente:` de cada commit dejan a la siguiente sesión seguir sin preguntar; `recover.py` recupera el estado tras
  un `/clear` o una compactación.
- **Lo que el agente da por bueno no siempre lo está:** el `pre-push` corre tu check sobre el commit exacto que se
  sube, y la rama protegida exige una marca de revisión atada a ese commit (`reviewed.sh`).
- **El gasto de tokens crece sin medirse:** `gw-selector` elige skill y modelo por tarea, `gw-orchestrate-dealer`
  reparte el trabajo a subagentes de contexto limpio y `gw-opt-tokens` mide dónde se fue el gasto.

## Qué se instala

| Pieza | Qué hace |
|---|---|
| Ganchos de git | `pre-commit` (secretos), `commit-msg` (formato, `Refs:`, `Siguiente:`, sin firmas del agente), `pre-push` (check, datos privados, marca de revisión, bitácora) |
| Ganchos de Claude Code | Estado al empezar, no acabar sin subir, revisión antes de un PR, tope de subagentes, guardia de la configuración |
| Skills | 26, en formato abierto Agent Skills: 11 propias (`gw-*`) y 15 de Matt Pocock |
| Scripts | Deterministas, en Python 3.8+ y bash 3.2: `apply.py`, `doctor.py`, `check.sh`, `handoff.py`, `version.py`… |
| Configuración | Un solo archivo, `.claude/gw.json`: idioma, check, rama protegida, qué es contenido y qué es código |

Todo queda **dentro de tu repositorio** (`.claude/gw/`, `.claude/skills/`, `.githooks/`), así que funciona también en
sesiones en la nube que no cargan plugins.

## Cómo se aplica

1. Requisitos: `git`, `bash` y `python3` 3.8 o superior (en Windows, Git Bash o WSL).
2. En Claude Code, `/gw-init`: el agente decide contigo lo que exige criterio y `apply.py` copia y configura.
3. `/gw-doctor` comprueba que queda bien montado y da la orden que arregla cada fallo.
4. `/gw-update` lleva el proyecto a cada versión nueva y enseña los cambios antes de aplicarlos.

## Por qué fiarse

- Las reglas comprobables las comprueba un script; los ganchos **fallan cerrados** si les falta un dato.
- El propio repo pasa más de mil pruebas automáticas en Linux y macOS y se trabaja con su propio flujo.
- Las mejoras de tu proyecto vuelven al flujo con `gw-harvest`, siempre como propuesta y con tu confirmación.

Código, documentación y versiones: [github.com/Zeldris/Galivelop-workflow](https://github.com/Zeldris/Galivelop-workflow).
