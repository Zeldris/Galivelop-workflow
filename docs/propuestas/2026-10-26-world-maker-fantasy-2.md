# Harvest world-maker-fantasy — 2026-10-26 (segunda recogida)

De `948ea734` a `88a7299d` (`scripts/recoger.py`, 73 commits; el proyecto sigue en el flujo v0.2.0). Numeración
seguida de `2026-10-26-world-maker-fantasy.md`.

## P4. Check en una orden con resumen y salida recortada

- **Source:** `docs/registros/retro-2026-10-26-arreglos-puerta.md` @ `1e55634a` (script)
- **What changes:** se junta con P12 de `2026-10-26-instalador-wmf-tarkor-2.md`: el `scripts/check.sh` de la 1.0.0
  ya corre el check en una orden; faltan el resumen OK/FALLA por orden, la salida recortada de lo que falla y
  comprobar una revisión concreta.
- **Why it is general:** ver P12 del Instalador.
- **Version bump:** minor → 1.0.0
- **Status:** propuesta (se decide junto con P12 del Instalador)

## P5. Nota sobre ids de tareas de otro proyecto en `REVIEW.md`

- **Source:** `docs/registros/retro-2026-10-26-ins-31.md` @ `b36fb05f` (plantilla)
- **What changes:** una línea opcional en la plantilla de `REVIEW.md`: los ids de tareas de otro repo (p. ej.
  `INS-31` en WMF) se citan con su repo y no cuentan como tarea sin hito. El mecanismo en sí (`externalTaskIds`, la
  QA-259) se queda en el proyecto.
- **Why it is general:** pasa en cualquier par de repos que se trabajen juntos; aun así, es poco frecuente.
- **Version bump:** minor → 1.0.0
- **Status:** propuesta (valor bajo)

## Stays in the project

- `externalTaskIds` (QA-259): depende de `cobertura.py` y del roadmap de WMF.

## Ya está

- Tope de llamadas por subagente en las tandas de arreglos (QA-257): en el flujo desde `cc1bd8c`/`e5640fd`.
