# Patrones opcionales

> [English](../en/patterns.md)

Formas de trabajar que el flujo permite pero no impone. Ninguna es necesaria para aplicarlo ([aplicar](aplicar.md)); se
adoptan cuando el proyecto las pide. Todas se apoyan en lo mismo: lo que no está subido no existe, la bitácora dice por
dónde se iba y un script, no una opinión, decide si algo puede subir.

## Tarea semanal programada

Una sesión que arranca sola cada semana (una «tarea programada» de Claude Code) para un trabajo repetible: poner al
día dependencias, revisar enlaces rotos, pasar `scout-updates`, limpiar la bitácora. El flujo **no incluye** el
encargo concreto: cada proyecto escribe el suyo.

Cómo se plantea, en genérico:

1. **Cada disparo, una sesión nueva** con el encargo completo (no puede suponer una conversación anterior): qué
   hacer, en qué rama, qué comprobar y cuándo parar.
2. **Empieza como cualquier sesión**: lee la bitácora, `git fetch`, trae la rama protegida y corre
   `python3 .claude/gw/scripts/doctor.py` y el `check`. Si algo está en rojo antes de tocar nada, lo apunta en la
   bitácora y para.
3. **Trabaja en su rama** (`claude/semanal-<fecha>`), con commits y push como siempre, y la bitácora al día.
4. **A la rama protegida, según la configuración** ([config](config.md)):
   - `pushToProtected: pr`: abre un pull request; el gancho de PR y el CI hacen de guardia y la persona decide.
   - `direct`: puede subir a la rama protegida **solo si la marca de revisión cubre el código** (el `pre-push` lo exige
     y falla cerrado). Si la tarea cambia código sin revisión, no sube: deja la rama con su bitácora para que una
     persona la revise. Un cambio solo de `content` no necesita marca.
5. **Termina con un informe corto** en la bitácora: qué hizo, qué dejó pendiente y el siguiente paso.

Autorización: una tarea que sube a la rama protegida sin nadie delante merece escribirse como regla en `AGENTS.md`,
para que quede dicho quién lo permitió.

## Dos cuentas que se relevan

Dos cuentas (o dos personas, o una sesión local y otra en la nube) trabajan el mismo proyecto por turnos y a veces a
la vez.

- **Cada sesión, su propia rama.** Dos sesiones a la vez nunca suben a la misma. Si la rama de la bitácora ya la usa
  otra, crea `claude/<tema>` desde ella y apunta su fila en la bitácora.
- **Bitácora de filas** (`"logRows": true`): cada rama escribe solo en su fila «Tarea en curso · `<rama>`», de como
  mucho 600 caracteres. El `pre-push` rechaza tocar la fila de otra rama o una compartida; para una compartida
  (p. ej. añadir tu rama a «Ramas de trabajo»), `BITACORA_COMPARTIDA=1 git push`.
- **Merge, nunca rebase**, al empezar cada tarea (`git fetch origin <protegida>` y `git merge origin/<protegida>`):
  las ramas están subidas. Lo suyo vuelve a la rama principal por `git merge` antes del PR.
- **Al empezar**, la sesión nueva lee la bitácora y comprueba que el último commit coincide con lo que dice; no
  pregunta por dónde iba. Tras un `/clear` o una compactación, `recuperar.py --estado` se lo recuerda.
- Al cerrar la rama, `bitacora.py close-row <rama>` deja su fila como «fusionada, rama terminada» para que la rama
  protegida no herede un «Siguiente» viejo.

## Sesión local que no puede crear PRs

Hay entornos (un portátil sin `gh`, una consola) donde la sesión puede trabajar y subir ramas, pero no crear el PR. Se
reparte así:

1. La sesión local termina el trabajo y pasa la revisión (`/code-review`, y si hay `retro`, también). Después escribe
   la descripción del PR con la skill `pr` en `docs/registros/pr/<rama>.md`.
2. En su fila de la bitácora deja **«PR listo»** con el título, y lo sube **todo en el último commit** de la rama.
3. Una **sesión en la nube** (con herramienta de GitHub) comprueba que nada va detrás de ese commit (`git log
   <commit>..origin/<rama>` vacío), corre `bash .claude/gw/scripts/revisado.sh` para dejar la marca del mismo commit,
   crea el PR con esa descripción y sigue con el CI y, cuando la persona lo confirme, la fusión.

El gancho de PR bloquea crear o fusionar sin la marca del mismo commit, de modo que un descuido (algo subido después
de «PR listo») sale como bloqueo y no como código sin revisar.

## Recoger mejoras de vuelta

El flujo aprende de los proyectos que lo usan. Hay dos mitades:

- **Empuja el proyecto.** Una `retro` que descubre una mejora **general** (de una skill, un script, una plantilla, una
  regla de `AGENTS.md`) no parchea la copia local, que la próxima actualización pisaría: la propone al flujo, como
  incidencia o PR en este repo, o la deja en el archivo de la retro bajo un encabezado
  `## Para Galivelop-workflow` (o `## For Galivelop-workflow`).
- **Tira el flujo.** Desde este repo, la skill `gw-harvest` recorre los proyectos conectados que tengan
  `.claude/gw.json`. La parte mecánica la hace `python3 scripts/recoger.py <proyecto>...` (copias del flujo editadas,
  skills nuevas, secciones de retros, commits desde la última recogida); el agente solo decide qué es general y escribe
  `docs/propuestas/AAAA-MM-DD-<repo>.md`. **Nunca aplica nada sin confirmación**: lo aprobado entra como un cambio
  normal con entrada en el CHANGELOG y nueva versión ([contribuir](contribuir.md)).

Los proyectos se leen, no se modifican, desde la sesión que recoge.
