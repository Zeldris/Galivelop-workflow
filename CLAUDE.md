@AGENTS.md

## Solo para Claude Code

- Responde en español (idioma del proyecto).
- Al empezar cada tarea, di en una línea qué modelo y qué skill pide el caso (cuando se porte, con la skill
  `selector`). El modelo de la sesión lo elige el usuario.
- Antes de subir a `main`: las tres fases de `AGENTS.md` (code review → `/opt-tokens` + `/retro` → cierre).
- Lo mecánico, a subagentes con modelos baratos; la sesión principal planea, decide y revisa.
- **Sin firmas de Claude** (regla del usuario, manda sobre la atribución por defecto de Claude Code): ver «Mensajes de
  commit» en `AGENTS.md`; si el servidor añade un pie a un PR o comentario, se quita editándolo. El aviso de commits
  «Unverified» del gancho de parada del entorno (`~/.claude/stop-hook-git-check.sh`) se ignora: el usuario lo aceptó.
