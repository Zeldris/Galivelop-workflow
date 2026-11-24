# Harvest private-project-2 — 2026-11-24

De `d173bc5` a `014f7ff` (`scripts/harvest.py`). 256 commits; ningún skill ni script del flujo cambiado (solo código
del proyecto). Lo nuevo sale de siete archivos `docs/records/retro-*`.

## P1. `handoff.py next-id` lee ids en celdas de tabla

- **Source:** `docs/records/retro-2026-11-22-b3-worker.md` (script)
- **What changes:** `next-id` reconoce ids como `**B3**` en celdas de la hoja de ruta (hoy devuelve `B1`), y
  `doctor.py` avisa si ningún id del plan casa con `taskId`.
- **Why it is general:** la skill `retro` depende de `next-id`; D134 solo mejoró el texto del error.
- **Version bump:** patch (arreglo)
- **Status:** proposed

## P2. `red-without-fix.sh` decide por ruta, no por contenido

- **Source:** `retro-2026-11-22-b4-aider.md` (script)
- **What changes:** un archivo de código cuya docstring dice «test» ya no se rechaza: se decide por ruta o `testMap`,
  no por `grep` del contenido (`redWithoutFix.testRegex` cubre solo en parte).
- **Why it is general:** rechazo falso en código corriente.
- **Version bump:** patch (arreglo)
- **Status:** proposed

## P3. Regla de `REVIEW.md`: un comando externo con tiempo límite mata su grupo de procesos

- **Source:** `retro-2026-11-22-b3-worker.md` (`run_group`) (plantilla)
- **What changes:** una regla en `templates/{es,en}/REVIEW.md` (hay reglas de `pkill`, no esta).
- **Why it is general:** cualquier proyecto que lance procesos con `timeout`.
- **Version bump:** patch
- **Status:** proposed

## P4. El resumen del reparto contrasta el valor esperado con el código

- **Source:** `retro-2026-11-22-b4-aider.md` B4.c (skill `gw-orchestrate-dealer`)
- **What changes:** si el encargo da un valor esperado, el subagente lo compara con el código y, si no cuadra, lo
  devuelve como `QUESTIONS` (el canal existe, la regla no).
- **Why it is general:** un valor esperado equivocado en un encargo (`think_sent` False/True) se vuelve test mal escrito.
- **Version bump:** patch
- **Status:** proposed

## P5. Aviso de `/clear` por subpaso (`Findings:`)

- **Source:** `retro-2026-11-23-version-0.7.0.md` P1 (generaliza Q-64) (script)
- **What changes:** el `commit-msg` o `session-start.sh` avisa en el segundo commit con `Findings:` desde el último
  `/clear` o compactación. Alternativa de Q-64: por contexto superior a ~100k tras un commit que cierra un paso.
  Se deciden juntas.
- **Why it is general:** medido: 6,1 M tokens sin `/clear` frente a 2,3-3,8 M con él.
- **Version bump:** minor (evolutivo; con D176 `clearOnTaskClose` solapa: mirar antes)
- **Status:** proposed

## P6. `gw-update`: parar si la rama va por detrás de la protegida

- **Source:** `retro-2026-11-24-gw-update-0.9.0.md` P1 @ `618a52c` (skill); es el mismo texto que
  `2026-11-24-galivelop-image-generator.md` P4. `workflowClone` hermano (P5) y `other-repo-read.py` (P3): con P1 y P2 de ese archivo.
- **Version bump:** patch
- **Status:** proposed (unida a la otra)

## Stays in the project / a medias

- Candidatas débiles o por medir: `orchestratorModel` (`retro-2026-11-23-version-0.6.0.md` P3, sin evidencia) y el
  revisor anidado en `gw-reviewer` (~21k de arranque; el proyecto sigue midiendo; ya están
  `2026-11-22-private-project-5` P2 y E82).
- Por comprobar aquí: `merge-branch.sh` ante un ledger sin confirmar, `reviewed.sh`/`check.sh` y `metrics.ledger`
  (0.4.0), y el aviso de `doctor.py` con `testMap` vacío.
- De proyecto: `gdev/`, bancos de medida, Q-xxx, `ciPython`, aider/qwen.
