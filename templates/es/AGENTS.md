<!-- galivelop-workflow v0.4.0 -->
# {{project}} — instrucciones para agentes

Este proyecto se trabaja por relevos: una sesión puede acabarse en cualquier momento (tokens, contenedor, cambio de
cuenta) y la siguiente tiene que seguir **sin perder nada y sin preguntar por dónde iba**. Todo lo de este archivo
existe para eso. El flujo es Galivelop-workflow v{{version}}; sus scripts están en `.claude/gw/scripts/`, sus skills
en `.claude/skills/` y su configuración en `.claude/gw.json` (solo la lee `.claude/gw/scripts/config.py`).

## Al empezar cualquier sesión

1. Lee la bitácora, `{{log}}`: rama, tarea en curso, qué falta y siguiente paso.
2. `git fetch origin <rama>` y comprueba que el último commit coincide con lo que dice la bitácora.
3. Comprueba que el check está en verde antes de tocar nada: {{check}}.
4. Sigue por el **siguiente paso** de la bitácora, salvo que la persona pida otra cosa.
5. Al empezar cada tarea, trae la rama protegida: `git fetch origin {{protectedBranch}}` y, si trae commits,
   `git merge origin/{{protectedBranch}}` (merge, nunca rebase: las ramas están subidas). Si el conflicto toca la
   misma lógica por los dos lados, se para y se consulta a la persona.
6. **La sesión se abre con el repo como carpeta de trabajo.** Abierta en otra (una que contiene varios repos, la
   carpeta personal), no carga `.claude/settings.json`: ni el tope de compactación, ni el gancho de inicio, ni el que
   vigila la subida a la rama protegida. Si pasa, dilo a la persona para que la reabra desde el repo; mientras tanto,
   `git config core.hooksPath .githooks` antes del primer commit y, antes de subir a `{{protectedBranch}}` o de crear
   o fusionar un pull request, comprueba a mano lo que comprobaría ese gancho: la marca de revisión del mismo commit y
   el CI en verde.

## Relevos: commit y push constantes

Cada sesión puede correr en un contenedor temporal: **lo que no está subido no existe** para la siguiente.

- Commit + push en cada punto estable (check en verde). **Nunca más de 30-45 minutos de trabajo sin subir.** Las
  tareas grandes se parten en pasos pequeños con su propio commit.
- **La bitácora se actualiza en el mismo commit** que el trabajo que describe, no al final de la sesión.
- **El estado vive en los archivos, no en la conversación**: el plan dice qué está implementado y la bitácora qué se
  está haciendo. Una tarea a medias dice qué está hecho y qué falta.
- Si hay que parar con algo a medias o en rojo: commit igualmente con `WIP:` al principio del mensaje y, en la
  bitácora, qué falla y por qué. Nunca dejar trabajo solo en local.
- Push a la rama de trabajo (`git push -u origin <rama>`); si falla por red, reintentar con espera 2, 4, 8 y 16 s.
- **Tras una llamada interrumpida o rechazada, `git status` y `git diff` antes de repetirla**: el cambio puede
  haberse guardado, o incluso subido, y repetirlo lo duplica.
- Si la persona dice que se para, se para: se sube lo que haya, se deja la bitácora al día y no se sigue con nada más.
- **Al cerrar cada tarea o PR** (y cada fase), con todo subido y la bitácora al día, se pide a la persona un `/clear` en
  una línea, con el porqué: el contexto largo es casi todo el gasto, y la bitácora basta para retomar.
- **Al cerrar cada bloque o fase, mira el CI de la última subida.** Un CI que no arranca (sin cuota, sin runners)
  cuenta como rojo: se dice a la persona y no se da nada por comprobado en el CI. Entonces vale el check pasado en
  local sobre el mismo commit (el de `.githooks/pre-push`) **solo si la persona lo confirma**, y se dice y se apunta en
  la bitácora como «comprobado solo en local». Un CI que arrancó y falló nunca se sustituye así.

## Comprobar

- **El check del proyecto:** {{check}}. `.githooks/pre-push` lo corre sobre el commit que se sube, y el CI
  (`.github/workflows/comprobar.yml`) en cada push fuera de `{{protectedBranch}}` y en cada pull request.
- **Lo comprobable lo hace un script**, no un agente: las skills y guías solo deciden lo que exige criterio. Si una
  regla se sigue rompiendo, se convierte en una comprobación.
- **Lo que depende de una máquina concreta no se da por probado con tests** (otro sistema operativo, un dispositivo,
  el equipo de la persona): se apunta como pendiente en el plan, con quién lo comprueba y dónde.
- Un test nuevo tiene que fallar sin su arreglo: `bash .claude/gw/scripts/rojo-sin-arreglo.sh "<orden del test>"
  <archivo-del-arreglo>...`.
- Un test que espera un fallo comprueba **el motivo** (el mensaje o la causa), no solo el código de salida: si no,
  pasa también cuando falla por otra razón.
- `python3 .claude/gw/scripts/doctor.py` dice si el flujo está bien montado, con la orden que arregla cada problema.

## Mensajes de commit

- Primera línea: qué cambia, en el idioma del proyecto, con los identificadores de las tareas tocadas.
- Cuerpo: qué se hizo, qué queda de esa tarea si no está cerrada, y estado del check.
- **Última línea: `Siguiente: <próximo paso concreto>`**, en el mismo bloque final que las líneas de atribución.

## Ramas y `{{protectedBranch}}`

- Se trabaja en la rama que indique la bitácora (o la que asigne la sesión, que se apunta en la bitácora nada más
  empezar).
- **Cada sesión, su propia rama**: dos sesiones a la vez nunca suben a la misma rama. Si la rama de la bitácora ya la
  usa otra sesión, crea `claude/<tema>` desde ella y escribe solo en tu parte de la bitácora. Lo tuyo vuelve por
  `git merge` antes de ir a `{{protectedBranch}}`.
- Merge, nunca rebase: las ramas están subidas.
- **A `{{protectedBranch}}` solo con confirmación de la persona**, y se apunta en la bitácora. Según `pushToProtected`
  de `.claude/gw.json`, se sube directo (`direct`: `.githooks/pre-push` pide la marca de revisión) o por pull request
  (`pr`: un gancho de Claude Code pide la marca antes de crearlo o fusionarlo; un push directo la sigue pidiendo).
- **Se fusiona solo con el CI en verde**, también cuando la persona dice «fusiona directamente»: eso quita esperar a
  más revisiones, nunca el CI ni la retro presentada a la persona. Si el CI no arranca, vale el check en local de
  «Relevos» con la confirmación de la persona: se sube directo (el `pre-push` corre el check) o fusiona ella; el
  gancho no deja al agente fusionar un pull request sin CI.
- La rama de un subagente vuelve con `bash .claude/gw/scripts/fusionar.sh <rama> "<mensaje>"`, que corre el check y
  limpia su worktree.

## Antes de ir a `{{protectedBranch}}`: tres fases

Nunca sobre trabajo ya fusionado.

1. **Código:** `git fetch origin {{protectedBranch}}` y revisión del diff contra `origin/{{protectedBranch}}` con
   todos los hallazgos (en Claude Code, `/code-review --max-findings all`), con el criterio de `REVIEW.md`. Arreglos
   con commit y subidos: lo grave o medio y lo que el propio arreglo rompe; lo leve se apunta como pendiente en la
   bitácora y no vuelve a revisarse en ese PR. Solo el código necesita revisión: lo que casa con `content` de `.claude/gw.json` es
   contenido.
2. **Entorno:** la skill `opt-tokens` y luego `retro` (más `opt-ai` si hubo medidas con un modelo de IA local). Sus
   propuestas se **presentan a la persona**; lo que confirme se aplica en la rama. Una retro escrita sin presentarla no
   vale.
3. **Cierre:** si la fase 2 trajo código, revisión solo de esos commits y sus arreglos; luego
   `bash .claude/gw/scripts/revisado.sh` (escribe la marca de revisión, `{{reviewMark}}`, y hace su commit) y
   `git push`; para un pull request, su descripción con la skill `pr`. Solo entonces se sube a `{{protectedBranch}}`
   o se crea el pull request. Sin la marca del mismo commit, los ganchos lo rechazan.

## Subagentes

**Reparto a subagentes autorizado:** el trabajo de más de un paso se reparte a subagentes de contexto limpio con la
skill `orchestrate-dealer` (y los modelos que elija la skill `selector`) sin preguntar cada vez; la sesión principal
planea, decide y revisa. Esta línea es la autorización que piden las instrucciones del propio agente.

- Cada subagente recibe un encargo: objetivo, rutas, restricciones, el check que debe pasar y qué tiene que devolver.
- Otros repositorios se leen con un subagente que devuelve un resumen con rutas; desde aquí nunca se modifican.

## Reglas del proyecto

<!-- Las rellena el proyecto: stack, cómo se arranca, lo que nunca se hace, reglas del dominio, dónde está cada cosa.
     Breve; una regla comprobable se convierte en un script. -->

- Instalar: {{install}}.
- _(por rellenar)_
