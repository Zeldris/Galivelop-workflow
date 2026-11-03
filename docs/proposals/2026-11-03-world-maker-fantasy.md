# Harvest world-maker-fantasy — 2026-11-03

De `88a7299d` a `7dee044c` (`scripts/harvest.py`). 179 commits; sin cambios propios en skills ni scripts del flujo.

Sin skills ni scripts cambiados en el proyecto; las copias antiguas del flujo no son cambios. Las ideas salen de
`docs/registros/propuestas-flujo.md` (P1-P15, @ `58f191e6`, arreglos de WMF @ `f2e83984`) y de los retros. Flujo
comparado en `ee709bc` (rama actual, 0.5 en curso; nombres ya en inglés).

## P1. `recover.py --estado` enseña también las ramas remotas con trabajo nuevo

- **Source:** `docs/registros/retro-2026-11-03-gh-en-la-deck.md` @ `e2642fa1` (retro)
- **What changes:** además de los worktrees locales, `--estado` lista la fila «en curso» de cada rama remota con commits más nuevos que la protegida.
- **Why it is general:** con varias cuentas o máquinas, la matriz de `main` no dice lo que otra rama ya hizo; casi se repite una ronda entera de pruebas. Cualquier proyecto con relevos entre cuentas lo sufre.
- **Version bump:** minor
- **Status:** proposed

## P2. `reviewed.sh`: el aviso de fallo sugiere `--footer` (y la línea por defecto si `commitNext` está activo)

- **Source:** `docs/registros/retro-2026-11-03-gh-en-la-deck.md` @ `e2642fa1` y `propuestas-flujo.md` P6 @ `58f191e6` (retro + script)
- **What changes:** si el commit de la marca falla en el `commit-msg`, el error dice `bash reviewed.sh --footer "Siguiente: <paso>"`; con `commitNext: true`, la marca lleva por defecto «Siguiente: crear el PR». Hoy `scripts/reviewed.sh` (l. 125-126) solo dice «retry: bash $0» y su `--footer` es siempre manual.
- **Why it is general:** cualquier proyecto con `commitNext` choca con esto en cada PR a la protegida.
- **Version bump:** patch
- **Status:** proposed

## P3. Tests de las skills instaladas, aislados del proyecto donde corren

- **Source:** `propuestas-flujo.md` P2 y P3 @ `f2e83984` (test)
- **What changes:** `skills/gw-media-content/scripts/test_figures.py` (`test_log_path_through_the_config_reader…`, l. ~404-410) busca `scripts/config.py` y `schema/` tres carpetas arriba, que solo existen en el repo del flujo (instalado da FileNotFoundError; usar `.claude/gw/` si no están). `skills/gw-opt-ai/scripts/test_measure.py` (`run_main`, l. ~34 y ~200) deja que `measure.main()` lea el `.claude/gw/gw-opt-ai.md` del proyecto; parchear `measure.repo_root` a `None`.
- **Why it is general:** `apply.py` instala los `test_*.py` con la skill; en cualquier proyecto con el check que los corre fallan o cambian de resultado según la config local.
- **Version bump:** patch
- **Status:** proposed

## P4. `red-without-fix.sh` / `rojo-sin-arreglo`: avisar de una orden con `|` sin `pipefail`

- **Source:** `docs/registros/retro-2026-10-26-lore-enciclopedia.md` (retro)
- **What changes:** avisar o fallar si la orden de prueba lleva una tubería sin `pipefail` (un `bash -c "… | grep"` da falso verde), y recomendar `--fails-with` en vez de filtrar con `grep`. El script actual tiene `--fails-with` pero no ese aviso.
- **Why it is general:** el falso verde es del propio método de rojo-sin-arreglo, no del proyecto.
- **Version bump:** patch
- **Status:** proposed

## P5. `gw-orchestrate-dealer`: un encargo de reemplazo global lleva su `grep` y la lista de excepciones

- **Source:** `docs/registros/retro-2026-10-26-lore-enciclopedia.md` (retro → skill)
- **What changes:** una línea en la plantilla de encargo: si la regla es «sustituir X por Y», incluir el `grep` que muestra todas las apariciones antes de editar y las excepciones que no se tocan. La skill ya pide el `grep` de usos para cambios de función (SKILL.md l. 72-75), no para reemplazos globales.
- **Why it is general:** sin ello el subagente aplica la regla también donde el nombre es correcto.
- **Version bump:** patch
- **Status:** proposed

## P6. Revisión corta del diff de cada tarea al cerrarla

- **Source:** `docs/registros/retro-2026-11-03-plan-imagenes.md` (retro, «La propuesta 1 vale para cualquier proyecto»)
- **What changes:** regla (skill `gw-selector`/guía de cierre de tarea): al cerrar una tarea, una revisión corta de su diff, no solo `/code-review` antes de la rama protegida. A decidir con el usuario: el flujo ya avisa de que las revisiones cortas por rama pierden roturas cruzadas.
- **Why it is general:** los fallos se pagan más caros cuanto más tarde se detectan.
- **Version bump:** minor
- **Status:** proposed

## P7. `bitacora.py`/`handoff.py`: avisar de «PR abierto» o «en borrador» sin URL de PR

- **Source:** `docs/registros/retro-2026-10-26-ins-33.md` (retro)
- **What changes:** comprobación nueva en la bitácora: una fila que afirma «PR abierto» / «en borrador» sin URL se avisa («hecho» vs «afirmado»).
- **Why it is general:** el estado de un PR en la bitácora lo lee la sesión siguiente sin poder verificarlo.
- **Version bump:** minor
- **Status:** proposed

## P8. `config-guard.py`: más escrituras de git en `GIT_WRITES`

- **Source:** `propuestas-flujo.md` P11 @ `58f191e6` (script; WMF lo marca «sin verificar a fondo»)
- **What changes:** `GIT_WRITES` (`scripts/config-guard.py` l. 81 = checkout, restore, rm, mv, clean) no incluye `reset --hard`, `stash pop`, `merge`, `checkout <rama>`, y trata una ruta `$VAR` como la raíz. Reproducir antes de arreglar.
- **Why it is general:** el guardián de rutas protegidas se salta esas escrituras en cualquier proyecto.
- **Version bump:** patch
- **Status:** proposed

## P9. `subagent-cap.py`: limpiar el contador `gw-subagents-<sesión>`

- **Source:** `propuestas-flujo.md` P14 @ `58f191e6` (script)
- **What changes:** borrar los contadores viejos (`scripts/subagent-cap.py`, `counter_path`, l. 89-91) al crear uno nuevo; hoy se acumulan en `tempfile.gettempdir()` en una máquina de larga vida.
- **Why it is general:** cualquier máquina que dure (no un contenedor efímero) los acumula.
- **Version bump:** patch
- **Status:** proposed

## P10. `check.py` de `gw-media-content`: comprobar todas las piezas con un código propio para los avisos

- **Source:** `propuestas-flujo.md` P7 @ `58f191e6` (skill)
- **What changes:** sin argumentos `check.py` sale con 2 (l. 1157-1159) aunque su doc dice que una carpeta puede ser `<dir>` entero; una opción (p. ej. `--warnings-as-notice`) devolvería la comprobación de todas las piezas al `check` del proyecto sin filtrar su texto en inglés.
- **Why it is general:** cualquier proyecto con `mediaContent` quiere validar `docs/media` en su check.
- **Version bump:** minor
- **Status:** proposed

## P11. `commit-msg` de la plantilla: no fallar fuera de un árbol de trabajo

- **Source:** `propuestas-flujo.md` P4 @ `f2e83984` (plantilla de gancho)
- **What changes:** `templates/githooks/commit-msg` l. 90 corre `git diff --cached` sin comprobar `git rev-parse --is-inside-work-tree`; falla en un repo desnudo o un test que lo llama desde fuera.
- **Why it is general:** afecta a los tests de ganchos de cualquier proyecto; baja prioridad.
- **Version bump:** patch
- **Status:** proposed

## P12. `doctor.py`: no recomendar `/gw-update` para un gancho propio sin cabecera

- **Source:** `propuestas-flujo.md` P12 @ `58f191e6` (script)
- **What changes:** ante un `.githooks/<x>` sin cabecera (`scripts/doctor.py` l. 314-315 avisa «(no header)» y manda a `/gw-update`), distinguir «propio a propósito» (p. ej. una lista en la config) de «antiguo», porque `/gw-update` lo sobrescribiría.
- **Why it is general:** quien personaliza un gancho recibe un consejo destructivo.
- **Version bump:** patch
- **Status:** proposed

## P13. Plantilla de `CLAUDE.md`: nombrar `.claude/gw.json` entre lo que protege `config-guard`

- **Source:** `propuestas-flujo.md` P15 @ `58f191e6` (plantilla)
- **What changes:** el aviso de permisos de `templates/claude/` debe nombrar también `.claude/gw.json` (no aparece hoy).
- **Why it is general:** lo protege el guardián en todos los proyectos.
- **Version bump:** patch
- **Status:** proposed

## P14. Revisión pendiente de P8, P9, P10, P13 (sin verificar a fondo por WMF)

- **Source:** `propuestas-flujo.md` @ `58f191e6` (script)
- **What changes:** `bitacora.py closed` acepta un id en cualquier línea fechada; `before-stop.py` y los `protectedPaths` (parar con la bitácora tocada, borrador sin commit); `prepush-branches.sh` comprueba la bitácora solo en la punta; `GLUED_ITEM` con falsos positivos. Primero reproducir cada uno; ninguno está confirmado.
- **Why it is general:** son comprobaciones del flujo, no del proyecto, pero requieren un caso que falle antes de tocar nada.
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- `.githooks/commit-msg` propio de WMF (sin cabecera, textos en español): es suyo a propósito; el flujo cubre lo general en #11 y `commitNext`.
- `docs/registros/retro-2026-11-03-gh-en-la-deck.md`, candidata 2 (QA-286): varios PR a la vez chocan en la bitácora; ya aplicada en `docs/runbooks/ramas-y-main.md` de WMF.
- `retro-2026-11-03-gh-en-la-deck.md`, «sin candidata»: `gh` en el sandbox Flatpak de la Deck (QA-285); es del entorno de WMF.
- `retro-2026-11-03-plan-imagenes.md` (IMG-*): cadena fotorreal, LoRA, `hoja.sh`; contenido del proyecto, salvo la propuesta 1 (arriba, #6).
- `retro-2026-10-27-ins-34.md`, `retro-2026-10-27-limpieza.md`, `retro-2026-11-02-gw-update-0.4.3.md`: sin ideas propias (remiten a P1-P15).

## Already here

- P1 (`recuperar.py --estado` con las filas de otros worktrees): `scripts/recover.py` (`other_worktrees()`, `WORKTREE_ROW`) y `docs/records/pending.md` l. 30 («WMF P3», 0.5, hecho).
- P5 (línea final `Siguiente:`): `commitNext` en `.claude/gw.json`, `scripts/commit-message.py` l. 236 y `GW_NO_NEXT`; el flujo la exige a todo commit, no solo a `CLAUDECODE=1` (diferencia menor).
- Skills nacidas `opt-ai`, `opt-tokens`, `orchestrate-dealer`, `selector`, `scout-updates`: copias con nombre anterior de `gw-opt-ai`, `gw-opt-tokens`, `gw-orchestrate-dealer`, `gw-selector`, `gw-scout-updates` (en `skills/`; WMF no tiene las `gw-*`, solo las viejas). No traen diferencias que proponer.
- Retro `plan-imagenes`/`ins-33`: la regla «tarea sin id toma el siguiente libre» y la bitácora por filas ya están en `docs/roadmap.md` (D22, D23) y `AGENTS.md`.
