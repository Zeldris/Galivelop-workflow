# Harvest galivelop-developer — 2026-10-27

De `never` a `70b0396a` (`scripts/recoger.py`, 24 commits desde `7822eec`; el proyecto usa la v0.3.0, sin cambios
propios en skills ni scripts del flujo: todo son copias antiguas). Primera recogida de la `1.0.0`. Las ideas salen de
`docs/registros/retro-2026-10-25-aplicar-flujo.md` @ `f92d90a` y `docs/registros/retro-2026-10-25-f0.md` @ `6e2e8e5`.

`galivelop-image-generator` y `galivelop-voice-generator` no se recogieron: son privados y la sesión no pudo añadirlos
(permiso denegado). Quedan para una sesión que los tenga.

Política de versiones (plan §7): lo que es corrección va a un parche `0.4.x`; lo nuevo, a la `1.0.0`.

## P1. `doctor.py` con `hooks-path` en FAIL rompe el CI

- **Source:** `docs/registros/retro-2026-10-25-aplicar-flujo.md` @ `f92d90a` (retro, punto 1)
- **What changes:** `check_hooks_path` (`scripts/doctor.py` ~l.188-197) da FAIL si `core.hooksPath` no está puesto,
  también en el CI, donde nadie lo pone. Con `CI=true`, WARN; una frase en `docs/es|en/aplicar.md` §1 y en
  `problemas.md`. Con su test.
- **Why it is general:** todo proyecto que pone `doctor.py` en `check` (lo que recomienda la guía para un proyecto
  sin tests) tiene el CI en rojo.
- **Version bump:** patch → `0.4.3` (corrección)
- **Status:** proposed

## P2. `gw-init` clona la última etiqueta, no la rama por defecto

- **Source:** `docs/registros/retro-2026-10-25-aplicar-flujo.md` @ `f92d90a` (retro, punto 2)
- **What changes:** `skills/gw-init/SKILL.md` §1 y `docs/es|en/aplicar.md` (requisitos) dicen
  `git clone --branch vX.Y.Z` con la última de `git ls-remote --tags`. Lo de cambiar la rama por defecto de GitHub a
  `main` ya está en «Pendiente» de la bitácora (lo hace el usuario).
- **Why it is general:** mientras la rama por defecto no sea `main`, cualquier proyecto nuevo coge una versión vieja
  (aquí, la 0.1.0 en vez de la 0.3.0).
- **Version bump:** patch → `0.4.3` (solo documentación)
- **Status:** proposed

## P3. Aviso: el gancho `PreToolUse` no está activo en la sesión que aplica el flujo

- **Source:** `docs/registros/retro-2026-10-25-aplicar-flujo.md` @ `f92d90a` (retro, punto 3)
- **What changes:** `.claude/settings.json` creado a mitad de sesión no se carga hasta la siguiente. `aplicar.md`
  §5/§6 y `gw-init` lo avisan: hasta abrir una sesión nueva, la marca se comprueba a mano
  (`bash scripts/revisado.sh`) antes del PR.
- **Why it is general:** la primera sesión de cada proyecto queda sin la guarda del PR sin saberlo.
- **Version bump:** patch → `0.4.3` (solo documentación)
- **Status:** proposed

## P4. `doctor.py` avisa de `bash -n` con varios archivos

- **Source:** `docs/registros/retro-2026-10-25-f0.md` @ `6e2e8e5`
- **What changes:** `bash -n a b` solo comprueba `a` (los demás son argumentos). `doctor.py` da WARN si una orden de
  `check` es `bash -n` con más de un archivo, con la orden que lo arregla (una por archivo). El `check` de este
  proyecto no cae en el caso; la retro dice que `galivelop-image-generator` sí.
- **Why it is general:** un check que parece cubrir varios scripts y solo mira uno da verde falso.
- **Version bump:** patch → `0.4.3` (aviso nuevo de un fallo silencioso)
- **Status:** proposed

## P5. `orchestrate-dealer`: el último bloque lo cubre la revisión de la rama

- **Source:** `docs/registros/retro-2026-10-25-f0.md` @ `6e2e8e5`
- **What changes:** `skills/orchestrate-dealer/SKILL.md` (~l.89-100) pide revisión corta por bloque sin excepción.
  Excepción: si la revisión de toda la rama contra la protegida va justo después y ya está decidida, el último bloque
  no se revisa aparte (matizando la regla «el código de un subagente tiene su propia revisión»).
- **Why it is general:** la revisión del último bloque repite los leves que saca la de la rama (~200k de Sonnet por
  fase en este proyecto).
- **Version bump:** minor → `1.0.0` (cambia una regla del reparto)
- **Status:** proposed

## P6. Script que lee el estado del CI por la API

- **Source:** `docs/registros/retro-2026-10-25-f0.md` @ `6e2e8e5`
- **What changes:** la mitad ya está (`scripts/ci-local.py` reproduce el CI; `doctor.py` `ci access` avisa sin
  token). Falta un lector suelto del estado de Actions de una rama o commit (`scripts/ci-estado.py`), que reutilice la
  lógica de token y `gh` de `revision-antes-de-main.sh`, para «mirar el CI de la última subida» (`AGENTS.md`).
- **Why it is general:** `AGENTS.md` pide mirar el CI al cerrar cada bloque y no da cómo sin `gh`.
- **Version bump:** minor → `1.0.0` (script nuevo)
- **Status:** proposed

## P7. Versiones de Python del CI en `gw.json`

- **Source:** `docs/registros/retro-2026-10-25-f0.md` @ `6e2e8e5`
- **What changes:** `templates/github/comprobar.yml` fija `python-version: "3.x"`. Una clave opcional (p. ej.
  `ciPython: ["3.10", "3.13"]`) en `templates/gw.json`, el esquema, `config.md` y `config.py`, que la plantilla del CI
  recorra en matriz.
- **Why it is general:** un proyecto con un mínimo de Python más viejo que el de `ubuntu-latest` nunca lo prueba.
- **Version bump:** minor → `1.0.0` (clave nueva)
- **Status:** proposed

## P8. `.gitignore` por stack desde `aplicar.py --init`

- **Source:** `docs/registros/retro-2026-10-25-f0.md` @ `6e2e8e5`
- **What changes:** plantillas de `.gitignore` por stack (python, node…) que `aplicar.py --init` añade en un bloque
  con marca, sin pisar el existente y con las excepciones del flujo.
- **Why it is general:** el primer subagente de este proyecto subió `.pyc`; pasa en cualquier proyecto nuevo.
- **Version bump:** minor → `1.0.0` (función nueva)
- **Status:** proposed

## Stays in the project

- Nada: las dos retros solo traen ideas generales; skills y scripts son copias de la 0.3.0 sin cambios.
