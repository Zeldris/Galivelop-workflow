# Harvest labs-log-detective — 2026-10-25 (primera recogida)

Hasta `bc501f91` (`scripts/recoger.py`, primera vez). El proyecto llevaba una copia a mano del flujo y en `a6a513c`
(QA-12) instaló Galivelop-workflow `0.3.0`; sus scripts y skills del flujo son iguales a los de la `0.3.0`. Las ideas
salen de tres skills nacidas en el proyecto, de la retro `docs/registros/retro-2026-10-19-primer-pr.md`, de los
commits anteriores a la instalación y de cómo fue esta.

## Fallos (patch)

## P1. `doctor.py` da por ignorado un archivo que una negación des-ignora

- **Source:** instalación @ `a6a513c` (QA-12; el proyecto simplificó su `.gitignore` para esquivarlo y dejó escrito
  que el arreglo de fondo es del flujo)
- **What changes:** en `scripts/doctor.py` (`ignored_paths`), `git check-ignore -v` sale con 0 también cuando la regla
  que casa es una negación (`!.claude/gw.json`); hay que descartar las reglas cuyo patrón empieza por `!`. Con su
  caso en `tests/test_doctor.py`.
- **Why it is general:** reproducido aquí con `.claude/*` + `!.claude/gw.json`: `rc=0` y la regla
  `.gitignore:2:!.claude/gw.json`. El doctor da un FAIL falso justo a quien sigue su propio consejo («add to
  .gitignore: !<ruta>»).
- **Version bump:** patch
- **Status:** aprobada (2026-10-25)

## Skills nuevas (minor)

## P2. Skill `wait-what`

- **Source:** `.claude/skills/wait-what/SKILL.md` @ `bc501f91` (port de `mattpocock/skills`, MIT; copia sin
  `metadata`)
- **What changes:** skill nueva de diez líneas, solo a mano (`disable-model-invocation`): «no entendí tu último
  mensaje; vuelve a explicarlo con contexto, en lenguaje simple y con los términos de `GLOSSARY.md`». Se porta con
  `metadata.source: "mattpocock/skills@<sha>"` como `grilling`, en el idioma del proyecto en vez de fijar ASD-STE100
  (inglés), y lo del proyecto va a `.claude/gw/wait-what.md`.
- **Why it is general:** cualquier usuario se encuentra con una respuesta que no entiende; hoy la única salida es
  pedirlo a mano cada vez. Se apoya en `domain-modeling`, que el flujo ya trae.
- **Version bump:** minor
- **Status:** aprobada (2026-10-25)

## P3. Skills `to-spec` y `wayfinder`, con un destino Markdown local por defecto

- **Source:** `.claude/skills/to-spec/SKILL.md` y `.claude/skills/wayfinder/SKILL.md` @ `bc501f91` (ports de
  `mattpocock/skills`); notas del proyecto en `.claude/gw/` que las bajan a Markdown (`docs/producto/mapa-diseno.md`,
  tareas del roadmap)
- **What changes:** `to-spec` convierte la conversación en una especificación sin entrevista; `wayfinder` planifica
  trabajo de varias sesiones como un mapa de tickets de decisión (research, prototype, grilling, task) que se
  resuelven de uno en uno, reutilizando skills del flujo. Las dos dependen de un tracker y de
  `/setup-matt-pocock-skills`, que el flujo no tiene: portarlas exige decidir antes un destino por defecto (archivos
  Markdown en el repo, con el tracker como opción en `.claude/gw/<skill>.md`), que es lo que hizo el proyecto.
- **Why it is general:** el flujo cubre bien una tarea por sesión, pero no tiene pieza para «una idea grande con
  niebla» que no cabe en una; el proyecto le añadió una fila al `selector` para ello.
- **Version bump:** minor
- **Status:** aplazada a la Fase 7 (2026-10-25): decidir primero el destino por defecto

## Reglas (patch)

## P4. Pedir `/clear` al cerrar cada tarea o PR, no solo cada fase

- **Source:** `c2cfab6` (QA-11); hoy en `.claude/gw/selector.md` y `.claude/gw/opt-tokens.md` del proyecto
- **What changes:** con la tarea o el PR cerrado, todo subido y la bitácora al día, el asistente pide un `/clear` en
  una línea, con el porqué. `templates/*/AGENTS.md` ya lo recomienda al cerrar una fase o una tarea grande; se amplía
  a cada tarea y PR fusionado y se nombra en `selector` (al cerrar un bloque) y en `opt-tokens`.
- **Why it is general:** contexto limpio en cada tarea es el ahorro más barato, y «abre sesión nueva» es incómodo en
  la nube.
- **Version bump:** patch
- **Status:** aprobada (2026-10-25)

## P5. Migrar desde una copia a mano: qué esperar

- **Source:** instalación @ `a6a513c` (17 propuestas `.gw-nuevo` fusionadas a mano)
- **What changes:** un párrafo en `docs/es/aplicar.md` ↔ `docs/en/` y en `gw-init`: si el proyecto venía de una copia
  a mano, saldrán muchas propuestas; se fusionan skill por skill y lo propio del proyecto va a
  `.claude/gw/<skill>.md`.
- **Why it is general:** es el camino de todos los proyectos anteriores al flujo (portal, Tarkor, instalador, este).
- **Version bump:** patch
- **Status:** aprobada (2026-10-25)

## Ya está en el flujo

- `core.hooksPath` sin activar tras simplificar el arranque (retro del primer PR): `doctor.py` lo comprueba
  (`hooks-path`) y `session-start.sh` avisa.

## Para hablar

- Quitar el pie de atribución que el servidor añade a los PR creados desde la sesión (`092707d`, QA-10;
  `.claude/gw/pr.md`): es una preferencia de la persona, no un fallo. Cabría como opción de `pr` si se quiere en más
  proyectos.
- Comprobar en `bitacora.py` las citas a `taskId` que no existen (idea de `tools/roadmap/cobertura.py`, QA-9): solo
  si otro proyecto lo pide.
- Primer PR en un repo sin `main` (retro del primer PR, propuesta 4): ver si `aplicar.md` lo cubre al tocar P5.

## Se queda en el proyecto

- Todas las notas `.claude/gw/*.md` (idioma, referencias de diseño, rutas `docs/`), la tutoría y las notas de
  aprendizaje por tarea, la fase de diseño sin código, las filas propias del `selector` y `designReferences`.
- `tools/qa/autoria.sh`, el `commit-msg` por persona, `.claude/hooks/autora-git.sh` y las ramas `raquel/`.
- `opt-tokens` con pagos únicos y compactación a 300k; el presupuesto de compactaciones por tarea.
