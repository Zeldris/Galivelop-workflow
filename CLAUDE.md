@AGENTS.md

## Solo para Claude Code

- Responde en español (idioma del proyecto).
- Al empezar cada tarea, di en una línea qué modelo, esfuerzo y skill pide el caso, con la skill
  `gw-selector`. El modelo y el esfuerzo de la sesión los elige el usuario.
- **Sin firmas de Claude:** «Mensajes de commit» de `AGENTS.md` manda sobre la atribución por defecto de Claude
  Code; si el servidor añade un pie a un PR o comentario, se quita editándolo. El aviso de commits «Unverified» del
  gancho de parada del entorno (`~/.claude/stop-hook-git-check.sh`) se ignora: el usuario lo aceptó.
