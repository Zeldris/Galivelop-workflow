# Harvest instalador-wmf-tarkor — 2026-10-26 (ventana de la 0.4.1)

De `89bb2eeb` a `f399a63d` (`scripts/recoger.py`, 59 commits; `main` del proyecto tras INS-43). Las ideas salen de
las retros de INS-43 (`ins43`) y de los parches que el proyecto aplicó a su copia del flujo. Según el plan §7, la
`0.4` solo recibe correcciones: lo evolutivo va marcado «para la 1.0.0».

## P1. Los tests de `scout-updates` pasan también instalados en un proyecto

- **Source:** parche del proyecto @ `8ebd50c` (skill)
- **What changes:** `skills/scout-updates/scripts/test_compare.py:109` busca `config.py` tres carpetas arriba, que solo
  vale en este repo; instalado (`.claude/skills/…` con los scripts en `.claude/gw/scripts/`) da 1 FAIL y 1 ERROR (también
  «default root is never the current directory», ~línea 153). Buscar `config.py` en las dos rutas; unas 8-10 líneas.
- **Why it is general:** reproducido en una instalación de prueba; falla en todo proyecto que corra los tests de sus
  skills.
- **Version bump:** patch (corrección)
- **Status:** propuesta

## P2. `rojo-sin-arreglo.sh` con el test en el mismo archivo que el arreglo

- **Source:** retro de INS-43 @ `f399a63d` (script)
- **What changes:** si un archivo del arreglo es también el del test, el `git stash` quita el test con el arreglo y el
  script dice «the test also passes WITHOUT the fix». Detectarlo y fallar con un mensaje que lo diga (y cómo seguir:
  separar el test o pasar la orden de un test que no esté en ese archivo); unas 15-25 líneas y su caso en los tests.
- **Why it is general:** reproducido en un repo de prueba: el mensaje actual es falso y empuja a dar por malo un test
  bueno. Ya salió como nota en `2026-10-23-world-maker-fantasy.md`.
- **Version bump:** patch (corrección)
- **Status:** propuesta

## P3. `revision-antes-de-main.sh` con check-runs en rojo por pago o tope de gasto

- **Source:** parche del proyecto (retro de INS-43) (script)
- **What changes:** hoy un check-run que GitHub cierra en rojo porque la cuenta no tiene cuota (aviso de pago, tope de
  gasto) bloquea sin salida (líneas 44, 512, 671-677; `NO_CI` solo cubre «ningún CI ha reportado»). La corrección
  mínima: tratarlo como «CI que no arrancó», con la misma salida que ya tiene `AGENTS.md` (check en local y
  confirmación del usuario). El `ci-local` genérico que lee `docs/registros/ci-local.md` va **para la 1.0.0**.
- **Why it is general:** cualquier proyecto sin cuota de Actions se queda sin forma de crear el PR; la regla ya dice
  que un CI que no arranca cuenta como rojo y se sustituye con confirmación, pero el gancho no lo reconoce.
- **Version bump:** patch (corrección); el `ci-local`, minor → 1.0.0
- **Status:** propuesta

## P4. `opt-tokens` y `retro` se contradicen sobre aplicar en la copia del flujo

- **Source:** retro de INS-43 (R1) @ `43fbad8`/`5053220` (skill)
- **What changes:** `skills/opt-tokens/SKILL.md:77` («Apply what is approved») choca con `skills/retro/SKILL.md:62`
  («Do not patch the copied workflow files locally»). Una frase en `opt-tokens` paso 5: lo que toca archivos copiados
  del flujo se manda al flujo (como en `retro`), no se parchea en el proyecto.
- **Why it is general:** dos skills del flujo dicen lo contrario; el proyecto parcheó su copia por seguir `opt-tokens`.
- **Version bump:** patch (corrección de texto)
- **Status:** propuesta

## P5. Compactaciones contadas desde el inicio de la tarea — para la 1.0.0

- **Source:** `ins43` R1 @ `5053220` (script)
- **What changes:** `recuperar.py:107` `count_compactions` cuenta toda la sesión; el parche usa el `merge-base` contra
  la rama protegida como inicio de la tarea. Unas 25 líneas.
- **Version bump:** minor → **para la 1.0.0** (evolutivo)
- **Status:** propuesta

## P6. El `pre-commit` comprueba las tareas cerradas frente a «Hecho» — para la 1.0.0

- **Source:** retro de INS-43 (script)
- **What changes:** hoy solo lo hace `prepush-ramas.sh:75`, con commits ya apilados; adelantarlo al commit. 15-25 líneas.
- **Version bump:** minor → **para la 1.0.0** (evolutivo)
- **Status:** propuesta

## P7. Textos de skills — para la 1.0.0

- **Source:** retro de INS-43 (skill)
- **What changes:** cuatro frases nuevas, cada una de 1-4 líneas:
  - `orchestrate-dealer` (línea 66): ante un fallo de patrón, buscar sus otras apariciones antes de cerrar;
  - `pr`: tras fusionar, recomendar `/clear`;
  - `orchestrate-dealer`: los arreglos de la revisión también se reparten a subagentes;
  - revisión: los hallazgos van a un archivo, no solo a la conversación.
- **Why it is general:** cuatro olvidos que se repitieron en el proyecto; ninguno es un fallo del flujo actual.
- **Version bump:** patch cada una, pero son novedades → **para la 1.0.0**
- **Status:** propuesta

## Ya está aquí

- `bitacora.py check` en el commit: `templates/githooks/commit-msg` de la 0.4.0.

## Se queda en el proyecto

- `worktreeLinks` y `.git/info/exclude`: el enlace lo crea `tools/qa/en-app.sh` del proyecto, no el flujo.
