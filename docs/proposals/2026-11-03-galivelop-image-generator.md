# Harvest galivelop-image-generator — 2026-11-03

De `never` a `e11f87a2` (`scripts/harvest.py`). Primera recogida; el proyecto usa la v0.4.0.

El proyecto aplica el flujo v0.4.0 (de antes del renombrado A8) y no tiene cambios propios en skills ni scripts del flujo. Todo lo "cambiado" o "nacido" son copias viejas. Lo valioso está en las retros.

## P1. `harvest.py` toma por "nacidas" las skills con el nombre anterior a A8

- **Source:** `.claude/skills/{opt-ai,opt-tokens,orchestrate-dealer,scout-updates,selector}/SKILL.md` @ `fc88e6c` (skill nueva, falso positivo)
- **What changes:** `harvest.py` (~línea 301, rama `else` de `skills_new`) debería mapear los nombres de `apply.OLD_SKILLS` (`selector` -> `gw-selector`, etc.) y comparar con la skill actual, o con `earlier_match`, en vez de listarlas como nacidas. Los scripts del proyecto con nombre español (`recuperar.py`, `bitacora.py`, etc., `OLD_SCRIPTS`) y los `.claude/gw/*.md` de notas conviene tratarlos igual.
- **Why it is general:** cualquier proyecto en 0.4.0 aún sin pasar por `/gw-update` produce el mismo ruido y puede llevar a proponer copias viejas como "skills nuevas". `apply.py` ya conoce los nombres viejos; `harvest.py` no.
- **Version bump:** patch (arreglo)
- **Status:** proposed

## P2. `pre-commit`: `KEY_FORMATS` deja pasar claves pegadas a una letra o dígito

- **Source:** `docs/registros/retro-2026-10-25-diseno.md` R7 @ `9cd91ca` (retro)
- **What changes:** en `templates/githooks/pre-commit` (línea 63) el borde izquierdo `(^|[^A-Za-z0-9])` no detecta `"x=\nsk-ant-…"`, `a%3Dsk-…` ni `1AKIA…`. Hay que buscar un borde que siga evitando `musk-tells-…` sin abrir ese hueco (por ejemplo, exigir el borde solo para `sk-` y no para `AKIA`/`ghp_`, que tienen prefijo propio). Va con un caso en los tests. `private-check.py` lee la misma variable.
- **Why it is general:** es un hueco de seguridad del gancho que instalan todos los proyectos. El borde sigue en el flujo actual (comprobado en la línea 63).
- **Version bump:** patch (arreglo)
- **Status:** proposed

## P3. `pre-commit` toma por secreto un diccionario de tests (clave = ruta absoluta, valor = código de error)

- **Source:** `docs/registros/retro-2026-10-25-f1.md` R3b @ `fe7d968` (retro)
- **What changes:** afinar `QUOTED` (líneas 80-88 de `templates/githooks/pre-commit`) para que no salte con `"/ruta/absoluta": "E123"` o con ejemplos literales en retros; hoy solo se esquiva con `gw-allow-secret` o reescribiendo el código.
- **Why it is general:** falso positivo reproducible en cualquier proyecto con rutas absolutas en tests. Hay que ver si el flujo ya excluye `tests/` o rutas; no lo encontré. Mejor comprobarlo con el caso concreto antes de decidir.
- **Version bump:** patch
- **Status:** proposed

## P4. Rama de trabajo sin seguimiento a la protegida

- **Source:** `docs/registros/retro-2026-10-25-f1.md` R3a @ `fe7d968` (retro)
- **What changes:** `git switch -c <rama> origin/main` deja la rama siguiendo a `origin/main` y un `git push` sin destino apunta a `main` (solo lo frena el `pre-push`). Proponer `--no-track` en la plantilla de `AGENTS.md` / `gw-init`, o un aviso de `doctor.py` cuando la rama de trabajo tiene upstream protegido. No hay `--no-track` en ningún sitio del flujo actual.
- **Why it is general:** el riesgo es de cualquier proyecto con rama protegida.
- **Version bump:** minor (aviso nuevo de `doctor.py`); patch si solo es texto de la plantilla
- **Status:** proposed

## P5. Test de portabilidad de shell (bash 3.2) como comprobación de `doctor.py` o `pre-commit`

- **Source:** `docs/registros/retro-2026-10-27-f2-0.md` R4 @ `0ebd00c` (retro)
- **What changes:** una comprobación sobre `git ls-files '*.sh' .githooks/*` que rechace `mapfile`, arrays asociativos y `mktemp` sin `XXXXXX`. Hoy la regla es solo de criterio (`templates/*/REVIEW.md`) y existe un test en el propio flujo (`tests/test_hooks.py:993`), pero no una comprobación en los proyectos.
- **Why it is general:** cualquier proyecto con la regla de bash 3.2 (viene en la plantilla de `REVIEW.md`).
- **Version bump:** minor
- **Status:** proposed

## P6. `apply.py` aplica una versión sin publicar sin avisar

- **Source:** `docs/registros/retro-2026-10-25-diseno.md` R3 @ `9cd91ca` (retro)
- **What changes:** avisar si la fuente no es un tag ni `main`, y guardar el commit de origen para que `--check` compare con él (`--check` falló solo porque el flujo avanzó). No encontré ni aviso ni commit guardado en `apply.py`.
- **Why it is general:** es el modo de instalación de cualquier proyecto mientras la `0.5` no esté publicada.
- **Version bump:** minor
- **Status:** proposed

## P7. `/code-review` se ahoga en una rama que aplica el flujo

- **Source:** `docs/registros/retro-2026-10-25-diseno.md` R2 @ `9cd91ca` (retro)
- **What changes:** un modo de `is-code.sh` o de la fase 1 de `AGENTS.md` que separe archivos del flujo (por manifiesto) de los propios: los propios enteros, los del flujo solo su delta. 9.600 líneas copiadas taparon 4 archivos propios.
- **Why it is general:** pasa en cualquier primera aplicación del flujo y en cada actualización grande. Es el más caro de implementar.
- **Version bump:** minor
- **Status:** proposed

## P8. Plantilla de `AGENTS.md`: "Lee la bitácora" reaparece como `cat` del archivo entero

- **Source:** `docs/registros/retro-2026-10-25-f0.md` R1 @ `169de4b` (retro)
- **What changes:** redactar el paso 1 como «el estado que da el gancho de inicio o `recover.py --state`; el archivo entero solo si falta algo». El `AGENTS.md` de este repo ya lo hace («si el gancho ya mostró su estado, lee solo lo que recortó»), pero la plantilla instalada no lo trae (`templates/AGENTS.md` no existe en esa ruta; comprobar `templates/es|en/AGENTS.md`).
- **Why it is general:** gasto de tokens en cada sesión de cualquier proyecto.
- **Version bump:** patch (texto)
- **Status:** proposed

## P9. La línea de la plantilla de `CLAUDE.md` no dispara `selector` al empezar una tarea

- **Source:** `docs/registros/retro-2026-10-25-diseno.md` R1 @ `9cd91ca` (retro)
- **What changes:** redactar «Antes de la primera herramienta de cada tarea nueva: una línea con skill + modelo (`gw-selector`)» y que `recover.py --state` lo recuerde. El `CLAUDE.md` de este repo ya lo dice así; `gw-selector` pide «one line» (SKILL.md:38), pero no el "antes de la primera herramienta" ni el recordatorio en `recover.py`.
- **Why it is general:** la conducta falló aun con la línea presente.
- **Version bump:** patch (texto de la plantilla); minor si se añade el recordatorio en `recover.py`
- **Status:** proposed

## P10. `domain-modeling/ADR-FORMAT.md` con encabezados en inglés en un proyecto `es`

- **Source:** `docs/registros/retro-2026-10-25-diseno.md` R4 @ `9cd91ca` (retro)
- **What changes:** que diga que los encabezados van en el `language` del proyecto (hoy trae «Consequences», «Considered Options» fijos, línea 23).
- **Why it is general:** afecta a todo proyecto en español. Ojo: la skill viene de mattpocock y las `SKILL.md` son solo en inglés; el cambio sería una frase de instrucción.
- **Version bump:** patch
- **Status:** proposed

## P11. `scout-updates`: el `source` con el nombre de otro proyecto la hizo elegir para leer otro repo

- **Source:** `docs/registros/retro-2026-10-25-f0.md` R4 @ `169de4b` (retro)
- **What changes:** el `source` de `gw-scout-updates` sigue diciendo «generalised from the Tarkor and installer gw-scout-updates» (cabecera de la skill). Quitar el nombre del proyecto o decir en la descripción que no sirve para leer otro repo. Cuidado: las demás skills también citan Tarkor/installer en `source`.
- **Why it is general:** el metadato lo ve cualquier proyecto que instale la skill.
- **Version bump:** patch
- **Status:** proposed

## P12. `harvest.py` marca `writing-for-agents` 0.4.0 como "cambiada en el proyecto" cuando es una copia vieja

- **Source:** `.claude/skills/writing-for-agents/SKILL.md` @ `fc88e6c` (skill; falso positivo)
- **What changes:** el diff es solo +0 −9 líneas, las 9 de la sección «Documents read every session» que el flujo añadió en 0.4.3; el proyecto no editó nada. `earlier_match` no la reconoce como copia vieja (probablemente porque la versión 0.4.0 de esta skill no está en el historial del flujo o el cuerpo difiere en algo mínimo). Revisar por qué.
- **Why it is general:** mismo ruido en cualquier proyecto con skills de terceros de versiones previas.
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- `.claude/gw/scripts/config.py`, `.claude/gw/scripts/doctor.py`: no son cambios del proyecto; son las copias 0.4.0 (cabecera `v0.4.0`, nombres españoles `recuperar.py`, `registro_sesion`). El flujo actual (0.4.3) ya los superó. Hay que pasar `/gw-update`.
- `docs/registros/retro-2026-10-27-f2-0.md` R5 («`compaction_budget` en `recuperar.py` se queda en el proyecto»): la persona decidió dejarlo local. En el flujo, `recover.py` solo pide comparar las compactaciones con el presupuesto de la bitácora (líneas 380-383), sin avisar de que se pasó. Se puede reconsiderar como minor si el proyecto lo aporta, pero no hay código en el material recogido para juzgarlo.

## Already here

- `docs/registros/retro-2026-10-25-f0.md` R3 (`ciPython` para matriz de Python): D19, hecho (`364966d`), en `docs/roadmap.md`.
- `docs/registros/retro-2026-10-27-f2-0.md` R3 (`bitacora.py set-row`): D23 `handoff.py set-row`, hecho (`0403f2b`); falta, a lo sumo, la frase de `&&`/`set -e` en `AGENTS.md` (criterio, opcional).
- `docs/registros/retro-2026-10-27-f2-0.md` R5 (`opt-tokens` reparte entre proyecto y flujo): `skills/gw-opt-tokens/SKILL.md` paso 5 ya dice que los cambios a archivos copiados van al flujo.
- `docs/registros/retro-2026-10-25-diseno.md` R7 LEVE (`commit-msg`, nombres con acentos): `templates/githooks/commit-msg:90` ya usa `-c core.quotepath=false` (falta `-z`; no verificado si importa).
- `.claude/skills/{opt-ai,opt-tokens,orchestrate-dealer,scout-updates,selector}/SKILL.md`: copias con el nombre viejo de `skills/gw-{opt-ai,opt-tokens,orchestrate-dealer,scout-updates,selector}/SKILL.md`. La comparación solo difiere en el renombrado (`gw-`, `medir.py` -> `measure.py`, `recuperar.py --estado` -> `recover.py --state`, versión 0.4.0 -> 0.4.3). `gw-selector` tiene además las filas de `wayfinder`, `to-spec` y `gw-media-content`; `gw-orchestrate-dealer` tiene más texto (~95 líneas de diferencia). Nada mejor en el proyecto. `apply.py` ya las migra con `OLD_SKILLS`.
- `.claude/skills/writing-for-agents/SKILL.md`: el flujo ya tiene la sección «Documents read every session» (0.4.3).
- `.claude/skills/{gw-doctor,gw-init,gw-update,pr,retro}` y `session-start.sh`: iguales a copias viejas del flujo (informe), sin cambios propios.
