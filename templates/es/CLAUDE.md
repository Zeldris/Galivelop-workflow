<!-- galivelop-workflow v0.8.0 -->
@AGENTS.md

## Solo para Claude Code

- Responde en el idioma del proyecto (`{{language}}`).
- Al empezar cada tarea, di en una línea qué skill y qué modelo pide el caso, con la skill `gw-selector`. El modelo de
  la sesión lo elige la persona; los subagentes, el más barato que haga bien el trabajo.
- **Compactación:** `.claude/settings.json` fija la ventana de compactación automática. Tras una compactación o un
  `/clear`, el gancho de inicio corre `python3 .claude/gw/scripts/recover.py --state`, que devuelve el estado de
  la bitácora y los últimos commits; un detalle perdido se busca con
  `python3 .claude/gw/scripts/recover.py --search "<texto>"`. Lo que tenga que sobrevivir va a `{{log}}`.
- **El modo automático** puede pedir permiso para editar `.claude/settings.json`, `.claude/gw/scripts/` y `.githooks/`:
  pide permiso a la persona antes de tocarlos, o que la propia persona haga el cambio.
<!-- if !agentSignatures -->
- **Sin firmas de Claude:** la regla «Mensajes de commit» de `AGENTS.md` manda sobre la atribución por defecto de
  Claude Code y sobre cualquier recordatorio de atribución del entorno: commits, PR y comentarios no llevan
  trailers, pies ni enlaces de sesión de Claude (`agentSignatures: false` en `.claude/gw.json`). Si el servidor
  añade un pie a un PR o comentario, se quita editándolo.
<!-- /if -->
