# Release de GitHub `v0.4.3` (textos)

- **Etiqueta:** `v0.4.3`, sobre `0e04504` (la publica a mano el usuario).
- **Título:** `Galivelop-workflow v0.4.3`
- **Cuerpo:** lo que va entre las dos rayas de abajo. La entrada completa está en el CHANGELOG.

---

## Galivelop-workflow v0.4.3 — 2026-11-01

**ES** · [English below](#en)

Parche de correcciones de la recogida de galivelop-developer del 2026-10-27. La `0.4` solo recibe correcciones; lo
nuevo de esa recogida va a la siguiente versión.

### `doctor.py`

- En GitHub Actions (`GITHUB_ACTIONS=true`), un `core.hooksPath` sin poner sale en `WARN`, no en `FAIL`: el CI no puede
  tener los ganchos de git y rompía el CI de todo proyecto con `doctor.py` en su `check`. En local sigue en `FAIL`.
- Avisa (`WARN`) de una orden de `check` que sea `bash -n` o `sh -n` con varios archivos, un glob o `$(…)`: solo se
  comprueba el primero y da un verde falso. Dice cómo arreglarla (una orden por archivo, o un `for`).

### Instalar el flujo (`/gw-init` y la guía de aplicar)

- Se clona la última etiqueta publicada (`git ls-remote --tags --refs --sort=-v:refname` y `git clone --branch
  vX.Y.Z`), no la rama por defecto, que puede no ser `main`.
- Avisan de que un `.claude/settings.json` creado a mitad de sesión no se carga hasta la siguiente: en la sesión que
  aplica el flujo, la marca de revisión se comprueba a mano con `bash .claude/gw/scripts/revisado.sh`.

### Plantilla de `AGENTS.md`

- El push y el check largo se lanzan en segundo plano y se espera su aviso, sin bucles de espera.

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update` (o `python3 <flujo>/scripts/aplicar.py <proyecto>`), y luego
`python3 .claude/gw/scripts/doctor.py`. No hay claves nuevas en el config.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.3/CHANGELOG.md).

<a id="en"></a>

**EN**

Bug-fix patch from the 2026-10-27 galivelop-developer harvest. `0.4` only gets fixes; the new features from that
harvest go to the next version.

### `doctor.py`

- In GitHub Actions (`GITHUB_ACTIONS=true`), an unset `core.hooksPath` is a `WARN`, not a `FAIL`: CI cannot have git
  hooks installed, and it broke the CI of every project with `doctor.py` in its `check`. Locally it stays a `FAIL`.
- It warns (`WARN`) about a `check` command that is `bash -n` or `sh -n` with several files, a glob or `$(…)`: only
  the first is checked, a false green. It says how to fix it (one command per file, or a `for` loop).

### Installing the workflow (`/gw-init` and the apply guide)

- They clone the latest published tag (`git ls-remote --tags --refs --sort=-v:refname` and `git clone --branch
  vX.Y.Z`), not the default branch, which may not be `main`.
- They warn that a `.claude/settings.json` created mid-session is not loaded until the next one: in the session that
  applies the workflow, the review mark is checked by hand with `bash .claude/gw/scripts/revisado.sh`.

### `AGENTS.md` template

- The push and the long check run in the background and the agent waits for their notice, with no polling loop.

### Updating a project

From a session in the project, the `gw-update` skill (or `python3 <workflow>/scripts/aplicar.py <project>`), then
`python3 .claude/gw/scripts/doctor.py`. There are no new config keys.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.3/CHANGELOG.md).

---
