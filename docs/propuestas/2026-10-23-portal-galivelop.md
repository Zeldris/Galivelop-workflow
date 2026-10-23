# Harvest portal-galivelop — 2026-10-23

De `673602b` a `245fbb6` (`scripts/recoger.py`). Es la recogida de la `0.4.0`, la primera hecha por la regla «una
recogida al empezar cada versión». El portal no cambió ninguna skill ni script del flujo: sus scripts son copias de
`58d1fe8` y `3b47af1`, y las ideas de su retro ya están en la P11 de `2026-10-22-portal-galivelop.md` (aprobada). Lo
nuevo son las líneas «Propuesta para el flujo» y la revisión del flujo 0.3.0 en «Pendiente» de su `docs/traspaso.md`
(`d685270`, `245fbb6`). Cada hallazgo se ha mirado contra nuestro código actual (`646614d`); lo que no se reproduce va
a «Ya está aquí» y lo que ya teníamos en «Pendiente» de nuestra bitácora no se repite.

Las otras tres recogidas de esta versión no traen nada para el flujo:

- **World-Maker-Fantasy** (`e433d1d` → `4d54eea`): solo la fila 21 del registro del piloto, ahora comprobada en la
  Deck.
- **Instalador-WMF-Tarkor** (`89bb2ee`, sin commits nuevos en `main`; la rama del piloto ya está en `main`).
- **VeriNews_AI** (`a9b5761`, sin commits nuevos en `main`; `ccr-1f38cee7-r36bua` es anterior y solo toca su
  bitácora).

## P1. `recoger.py` no ve las «Propuesta para el flujo» de la bitácora

- **Source:** `docs/traspaso.md` @ `245fbb6` (líneas «Propuesta para el flujo …» de «Pendiente»)
- **What changes:** `recoger.py` informa también de las líneas de cualquier `.md` cambiado que empiecen por «Propuesta
  para el flujo» / «Proposal for the workflow» (y la skill `gw-harvest` lo dice), además de las secciones «For
  Galivelop-workflow».
- **Why it is general:** los proyectos apuntan lo que piden al flujo donde trabajan, en la bitácora; esta recogida lo
  encontró solo leyendo la bitácora a mano. Es el mismo hueco que la P21 de la recogida anterior, en otro sitio.
- **Version bump:** patch (entra en la `0.4.0`)
- **Status:** aprobada (usuario, 2026-10-23) y aplicada en la `0.4.0`

## P2. Un sitio en el CI para los pasos propios del proyecto (`ci.setup` / `ci.after`)

- **Source:** `docs/traspaso.md` @ `245fbb6` («`aplicar.py --update` sustituyó `comprobar.yml` … Pasó otra vez en la
  0.3.0»)
- **What changes:** retomar lo aplazado en la P13 de `2026-10-22-portal-galivelop.md`: claves `ci.setup` y `ci.after`
  en `.claude/gw.json` que la plantilla de `comprobar.yml` incluye, y `aplicar.py --update` deja de tomar como «copia
  anterior» un `comprobar.yml` con pasos añadidos (lo propone como `.gw-nuevo`).
- **Why it is general:** la P13 se aplazó «hasta que un proyecto las pida»; el portal las pide, tras perder dos veces
  Node 22, la caché de npm y su build en una actualización.
- **Version bump:** minor
- **Status:** aplazada a la siguiente versión (usuario, 2026-10-23): necesita claves nuevas en la configuración

## P3. `recuperar.py`: el gancho espera 1 s la entrada y puede leer otra sesión

- **Source:** `docs/traspaso.md` @ `245fbb6` (revisión del 2026-10-23)
- **What changes:** `hook_transcript` espera más (o hasta EOF con tope) antes de caer al transcript más nuevo de la
  carpeta, y el aviso de `--estado` dice cuándo ha caído a «el más nuevo», que puede ser de otra sesión abierta.
- **Why it is general:** con dos sesiones a la vez en el mismo repo, el estado tras una compactación puede venir de la
  sesión equivocada.
- **Version bump:** patch
- **Status:** aprobada (usuario, 2026-10-23) y aplicada en la `0.4.0`: espera 3 s y avisa al caer al más nuevo

## P4. Plantilla `CLAUDE.md` (ES): «El modelo de la sesión la elige» → «lo elige»

- **Source:** `docs/traspaso.md` @ `245fbb6`; nuestro `templates/es/CLAUDE.md` línea 7-8
- **What changes:** la concordancia de la frase.
- **Why it is general:** sale en el `CLAUDE.md` de todos los proyectos en español.
- **Version bump:** patch (entra en la `0.4.0`)
- **Status:** aprobada (usuario, 2026-10-23) y aplicada en la `0.4.0`

## P5. Menores de la revisión del flujo 0.3.0 que se reproducen o son plausibles

- **Source:** `docs/traspaso.md` @ `d685270` («Revisión del flujo 0.3.0 … Propuestas para el flujo»)
- **What changes:** al «Pendiente» de nuestra bitácora, como menores (lo leve no se arregla en el PR que lo encontró):
  - `config.py related`: un `cwd` con `..` o absoluto en `relatedTests` se acepta y el `cd` sale del repo; `validate`
    debería rechazarlo (como se pide ya para `worktreeDir`).
  - `session-start.sh`: al acabar la orden antes del tope, `kill -- -$wd` no es un grupo (sin control de trabajos) y el
    `sleep` del vigilante queda vivo hasta el tope (inofensivo, pero queda un proceso).
  - `revision-antes-de-main.sh`: sondea `gh api repos/<o>/<r>` en cada llamada (coste por llamada al gancho), y juzga
    cambios de título o base sobre un PR cerrado.
  - `doctor.py`: da por bueno un `npm run check` citado en un comentario; avisos del glosario repetidos al variar las
    mayúsculas (por comprobar).
  - `pre-push`: `worktreeDir` dentro del propio repo (el worktree aparece como archivos sin seguir) y un
    `checkWrapper` que limpia el entorno (pierde `PATH`); que `validate` avise de los dos.
  - El portal: `pre-push` y `revision-antes-de-main.sh` leen la política de la punta de `main`, y si esa config está
    rota ni el arreglo puede subir. Es a propósito (fallan cerrados, P1 de la recogida anterior); se apunta cómo se
    sale: arreglarla con un PR revisado, o la persona sube a mano.
- **Why it is general:** son del código del flujo; cada uno lo tiene cualquier proyecto.
- **Version bump:** patch, cuando se arreglen
- **Status:** aprobada (usuario, 2026-10-23): apuntados en «Pendiente» de `docs/traspaso.md`

## Ya está aquí

- `bitacora.py closed` sí cuenta `- [x] **ID**`, `- [x] ID`, `* [X] \`ID\`` y los tachados: probado con
  `Ctx.closed_ids` sobre el patrón por defecto (`646614d`). No se reproduce.
- `enlaces-md.py` con symlinks hacia fuera: resuelve el destino (`resolve()`) y exige que quede dentro de la raíz
  (línea 93), así que un symlink hacia fuera ya es un problema.
- Los dos `pre-push` «que dejan pasar si no pueden traer la punta remota» (revisión del 2026-10-23): el actual falla
  cerrado (`the remote main is at …, which this clone does not have`, desde `3b47af1`).
- Entrecomillado de `checkWrapper` repetido en tres sitios, pid reutilizado en los worktrees huérfanos y
  `update_pull_request` con `state:open` en un PR cerrado: ya en «Pendiente» de `docs/traspaso.md`.

## Se queda en el proyecto

- `test_medir.py` (llega con `opt-tokens`) no lo corre `npm run check`: es el check del portal; como mucho,
  `aplicar.md` puede decir que los tests de las skills copiadas entran en el check del proyecto (va con la P2 si se
  aprueba).
- `AGENTS.md` del portal cita `opt-ai`, opcional y no instalada: la plantilla ya dice «si hubo medidas con un modelo de
  IA local».
- La tarea «Proyectos semanal» y el «About» del repo: del portal.
