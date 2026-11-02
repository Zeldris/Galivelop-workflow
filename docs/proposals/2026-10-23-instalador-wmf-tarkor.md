# Harvest instalador-wmf-tarkor — 2026-10-23 (piloto de la Fase 6)

De `97440ecc` a `89bb2eeb` (`scripts/recoger.py`, 15 commits). Es el piloto de Galivelop-workflow `0.2.0`, fusionado en
`main` con el PR #5. La copia del flujo está al día: ninguna skill ni ningún script del flujo cambia en el proyecto. Las
ideas salen del registro `docs/registros/piloto-galivelop-workflow.md` («Para Galivelop-workflow») y de la retro
`docs/registros/retro-2026-10-22-piloto-galivelop.md`.

Lo que coincide con WMF está en [`2026-10-23-world-maker-fantasy.md`](2026-10-23-world-maker-fantasy.md):

- `revisado.sh`, puntos 20 y 4: P1 de WMF;
- gancho del PR, puntos 16 y 17: P5;
- test de `opt-tokens/medir.py`, punto 6: P7;
- rutas enlazadas en el worktree, punto 1: P10;
- CI propia, punto 3: P11.

## P1. Un `taskId` con grupo de captura rompe `bitacora.py closed`

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (punto 19) @ `89bb2eeb`
- **What changes:** `scripts/config.py` (o `bitacora.py`) convierte los grupos con captura de `taskId` en grupos sin
  captura, o rechaza el patrón con un mensaje que diga cómo escribirlo. Lleva un caso en los tests con
  `(INS|FLU)-\d+`.
- **Why it is general:** `(A|B)-\d+` es la forma natural de escribir varios prefijos, y hoy el `pre-push` se cae sin
  decir por qué. Comprobado aquí: el `findall` de la línea 95 devuelve 4 grupos por coincidencia y el desempaquetado
  `a, b` da `ValueError`.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P2. `doctor.py` acepta «Siguientes pasos»

- **Source:** registro (punto 4) @ `89bb2eeb`
- **What changes:** `NEXT_STEP` pasa a `siguientes? pasos?|next steps?` (`scripts/doctor.py:36`).
- **Why it is general:** una bitácora con el título en plural da FAIL sin motivo.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P3. `relatedTests` con filtro de rutas y carpeta por orden

- **Source:** registro (punto 2) @ `89bb2eeb`
- **What changes:** cada orden de `relatedTests` admite:
  - `paths`, una regex de los archivos que le tocan;
  - `cwd`, la carpeta donde se ejecuta. `{files}` llega relativo a esa carpeta.
- **Why it is general:** hoy cada proyecto con la app en una subcarpeta escribe un script que filtra rutas y les quita
  el prefijo; aquí es `tools/qa/tests-app.sh`.
- **Version bump:** minor
- **Status:** aprobada (2026-10-23)

## P4. Que toda skill lea sus notas del proyecto en `.claude/gw/<skill>.md`

- **Source:** registro (punto 7) @ `89bb2eeb`
- **What changes:** hoy solo `opt-ai`, `opt-tokens` y `scout-updates` leen su nota. Con esto, una línea común en cada
  skill, y en la guía `writing-for-agents`, que diga que se lee `.claude/gw/<skill>.md` si existe.
- **Why it is general:** las notas del resto de skills (`pr`, `retro`, `grilling`…) acaban en un runbook aparte que
  la skill no encuentra.
- **Version bump:** minor
- **Status:** aprobada (2026-10-23)

## P5. Cómo llamar a la persona en las plantillas

- **Source:** registro (punto 8) @ `89bb2eeb`
- **What changes:** una clave del config para el tratamiento (por ejemplo «la usuaria») que `aplicar.py` aplique al
  copiar `AGENTS.md`, `CLAUDE.md` y `GLOSSARY.md`, o bien una redacción neutra en las plantillas.
- **Why it is general:** hoy se corrige a mano en cada proyecto.
- **Version bump:** minor (o patch con la redacción neutra, que no añade clave)
- **Status:** aprobada (2026-10-23)

## P6. `staleRefs` puede saltarse carpetas

- **Source:** registro (punto 9) @ `89bb2eeb`
- **What changes:** una lista de globs que `enlaces-md.py` no revisa. Hoy solo se salta la bitácora, y los `retro-*.md`,
  que citan rutas antiguas, chocan.
- **Version bump:** minor
- **Status:** aprobada (2026-10-23)

## P7. Camino «sin cupo de Actions, CI pasado en local»

- **Source:** registro (punto 14) y retro (fila `ci-local.py`) @ `89bb2eeb`
- **What changes:** hoy `revision-antes-de-main.sh` exige el CI en verde o bloquea. La propuesta es aceptar un registro
  del CI pasado en local, con la confirmación de la persona. El proyecto lo resolvió con su `ci-local.py` (FLU-3), y
  WMF fusionó sin PR por el mismo motivo.
- **Why it is general:** sin cupo de Actions, el flujo bloquea la subida a `main` en todos los proyectos. Es lo más
  delicado de esta recogida, porque relaja una puerta; antes hay que decidir qué cuenta como prueba.
- **Version bump:** minor
- **Status:** aprobada por el usuario (2026-10-23) y aplicada en `0.4.0`: el check en local vale cuando el CI no
  arranca, solo con la confirmación de la persona y dicho como «comprobado solo en local»; el gancho sigue bloqueando
  la fusión sin CI y nombra ese camino.

## P8. Los tests de los scripts del flujo no llegan al proyecto

- **Source:** registro (punto 15) @ `89bb2eeb`
- **What changes:** `aplicar.py` no copia `tests/test_*`, así que la regla de `REVIEW.md` «cada cambio en un script
  lleva su test» no se puede cumplir en el proyecto. Hay dos salidas:
  - copiar los tests junto con los scripts (minor);
  - documentar que esos scripts se prueban en el repo del flujo y no se editan en el proyecto (patch).
- **Version bump:** patch o minor, según la salida
- **Status:** aprobada (2026-10-23)

## P9. `aplicar.md`, más claro para quien migra desde una copia anterior

- **Source:** registro (puntos 5, 10, 11, 12 y 13) @ `89bb2eeb`
- **What changes:** en `docs/es/aplicar.md` ↔ `docs/en/apply.md`:
  - avisar antes del paso de copiar de que un `.gitignore` con `.claude/*` ignora `.claude/gw*`;
  - qué hacer con los archivos de una skill que el flujo sustituye (banco y evals de `scout-updates`);
  - quitar a mano los ganchos viejos de `settings.json`, y la CLI de `recuperar.py` para quien migra;
  - subir al paso 0 lo de `add_repo` sin registrar el repo como raíz;
  - cómo correr `install` a mano, ya que solo corre cuando cambian los lockfiles.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## Se queda en el proyecto

- `tools/qa/en-app.sh`, `tests-app.sh`, `instalar-entorno.sh`, la CI propia con Windows y Rust, y `tools/banco/`. La
  parte general va en P3 y en P10 de WMF.
- Lo que la retro rechazó o dejó como propio del proyecto: `/clear` tras un PR, el runbook por tramos, `REVIEW.md` con
  los scripts del flujo, la prueba del paso 6 en una rama desechable, y que `AGENTS.md` apunte a `gw.json` en vez de
  copiar el check (rechazado por la usuaria).
