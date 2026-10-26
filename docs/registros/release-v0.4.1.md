# Release de GitHub `v0.4.1` (textos)

- **Etiqueta:** `v0.4.1`, sobre `56212e8` (la publica a mano el usuario).
- **Título:** `Galivelop-workflow v0.4.1`
- **Cuerpo:** lo que va entre las dos rayas de abajo. La entrada completa está en el CHANGELOG.

---

## Galivelop-workflow v0.4.1 — 2026-10-26

**ES** · [English below](#en)

Parche de correcciones de la recogida del 2026-10-26. La `0.4` solo recibe correcciones; los evolutivos de esa
recogida van a la `1.0.0`.

### Raíz del repo y worktrees

- Los scripts hallan la raíz del repo dentro de un worktree enlazado: `config.py` y los `.sh` piden la raíz a git sin
  `GIT_DIR`, `GIT_WORK_TREE` ni `GIT_INDEX_FILE` heredados.
- `find_root` prefiere el directorio actual cuando es del mismo repo que `$CLAUDE_PROJECT_DIR` (un worktree
  enlazado); si no, `$CLAUDE_PROJECT_DIR`; sin ninguno de los dos, falla cerrado y pide `--root`.

### `rojo-sin-arreglo`

- Rechaza también una edición dentro de un método de test indentado: mira las líneas que encierran cada cambio, no
  solo la cabecera del hunk.
- Se niega, con un mensaje que dice cómo seguir, cuando el archivo del arreglo tiene sin commitear cambios que tocan
  código de test (el stash quitaba el test junto con el arreglo).

### CI y nube

- `revision-antes-de-main.sh` reconoce el CI que GitHub no arrancó por facturación o límite de gasto: bloquea igual,
  pero dice que no se ejecutó nada y nombra el camino de «comprobado solo en local».
- Sin aviso falso de «sesión abierta fuera del repo» en la nube (`CLAUDE_CODE_REMOTE=true`): ni en `doctor.py`, ni en
  `opt-tokens/medir.py`, ni en `recuperar.py --estado`, ni en `registro_sesion.py`, ni en `session-start.sh`. Fuera
  de la nube el aviso sigue.

### Skills

- **`opt-tokens`:** un cambio a un archivo copiado del flujo (`.claude/gw/scripts/`, `.claude/skills/`, los ganchos)
  no se parchea en el proyecto: va al flujo, como dice `retro`.
- **`scout-updates`:** sus tests pasan también en la copia instalada (`.claude/skills/scout-updates/scripts`).
- **`gw-harvest`:** clona los proyectos solo para lectura en una carpeta temporal, sin registrarlos (sus `CLAUDE.md`,
  `AGENTS.md` y skills entraban en cada llamada, ~17 % del gasto), y los verifica con un subagente por proyecto en
  paralelo.
- **`orchestrate-dealer`:**
  - el encargo corta a las ~25 llamadas (tope ~30);
  - si la sesión no se abre en la raíz del repo (la nube arranca en `/home/user`), los worktrees se crean a mano con
    `git -C <repo> worktree add`;
  - el encargo dice cómo esperar (`run_in_background` y su aviso, nunca `sleep` en primer plano ni sondeos) y cómo
    subir (salida a un archivo y el motivo del `pre-push` leído antes de reintentar).

### Actualizar un proyecto

Desde una sesión del proyecto, la skill `gw-update` (o `python3 <flujo>/scripts/aplicar.py <proyecto>`), y luego
`python3 .claude/gw/scripts/doctor.py`. No hay claves nuevas en el config.

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.1/CHANGELOG.md).

<a id="en"></a>

**EN**

Bug-fix patch from the 2026-10-26 harvest. `0.4` only gets fixes; that harvest's new features go to `1.0.0`.

### Repo root and worktrees

- Scripts find the repo root inside a linked worktree: `config.py` and the `.sh` scripts ask git for the root without
  inherited `GIT_DIR`, `GIT_WORK_TREE` or `GIT_INDEX_FILE`.
- `find_root` prefers the current directory when it is in the same repo as `$CLAUDE_PROJECT_DIR` (a linked
  worktree); else `$CLAUDE_PROJECT_DIR`; with neither, it fails closed and asks for `--root`.

### `rojo-sin-arreglo`

- Also refuses an edit inside an indented test method: it reads the lines enclosing each change, not only the hunk
  header.
- Refuses, with a message saying how to proceed, when the fix file has uncommitted changes touching test code (the
  stash removed the test along with the fix).

### CI and cloud

- `revision-antes-de-main.sh` recognises CI that GitHub did not start because of billing or a spending limit: it
  still blocks, but says nothing ran and names the "checked only locally" path.
- No false "session opened outside the repo" warning in the cloud (`CLAUDE_CODE_REMOTE=true`): not in `doctor.py`,
  `opt-tokens/medir.py`, `recuperar.py --estado`, `registro_sesion.py` or `session-start.sh`. Outside the cloud the
  warning stays.

### Skills

- **`opt-tokens`:** a change to a file copied from the workflow (`.claude/gw/scripts/`, `.claude/skills/`, the hooks)
  is not patched in the project: it goes to the workflow, as `retro` says.
- **`scout-updates`:** its tests also pass in the installed copy (`.claude/skills/scout-updates/scripts`).
- **`gw-harvest`:** clones the projects read-only into a scratch folder without registering them (their `CLAUDE.md`,
  `AGENTS.md` and skills entered every call, ~17 % of the spend), and checks them with one subagent per project in
  parallel.
- **`orchestrate-dealer`:**
  - the brief stops at ~25 calls (cap ~30);
  - when the session is not opened at the repo root (the cloud starts in `/home/user`), worktrees are created by
    hand with `git -C <repo> worktree add`;
  - the brief says how to wait (`run_in_background` and its notification, never a foreground `sleep` or polling) and
    how to push (output to a file, and the `pre-push` reason read before retrying).

### Updating a project

From a session in the project, the `gw-update` skill (or `python3 <workflow>/scripts/aplicar.py <project>`), then
`python3 .claude/gw/scripts/doctor.py`. There are no new config keys.

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.4.1/CHANGELOG.md).

---
