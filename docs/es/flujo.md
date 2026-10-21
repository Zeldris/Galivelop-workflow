# El flujo, en una página

> [English](../en/workflow.md)

Resumen para personas. El detalle irá creciendo en esta carpeta según se construya el flujo (plan §9).

## La idea

Una sesión con un agente puede acabarse en cualquier momento. El flujo está pensado para que la siguiente sesión,
de la misma cuenta o de otra, siga **sin perder nada y sin preguntar por dónde iba**, y para que nada sin revisar
llegue a la rama protegida.

## Las piezas

| Pieza | Para qué |
|---|---|
| `AGENTS.md` | Reglas del flujo para cualquier agente: al empezar, relevos, commits, ramas |
| `CLAUDE.md` | `@AGENTS.md` + lo propio de Claude Code |
| Bitácora (`docs/traspaso.md`) | Estado actual, siguiente paso, hecho y pendiente; se actualiza en el mismo commit que el trabajo |
| Skills | Cómo elegir modelo y skill, orquestar subagentes, revisar, hacer retros |
| Ganchos | Recuperar el estado tras `/clear`, no subir código sin revisión ni con el check en rojo |
| `.claude/gw.json` | Lo que cambia de un proyecto a otro (idioma, bitácora, check, rama protegida…) |

## De dónde sale

De los proyectos del taller Galivelop y, antes, del trabajo de **Matt Pocock**
([mattpocock/skills](https://github.com/mattpocock/skills)), de quien aprendimos esta forma de trabajar con agentes.
Sus skills incluidas aquí llevan su mención y su licencia ([créditos](../../CREDITS.md)).

## Las reglas que más importan

1. **Lo que no está subido no existe:** commit + push en cada punto estable.
2. **La bitácora va en el mismo commit** que el trabajo que describe.
3. **Último renglón del commit:** `Siguiente: <paso concreto>`.
4. **A la rama protegida, solo con confirmación** y con revisión del diff.
5. **Lo comprobable lo comprueba un script**, no la opinión de un agente.
