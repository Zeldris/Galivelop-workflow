# Harvest world-maker-fantasy — 2026-10-25 (ventana de la 0.4.0)

De `4d54eeaf` a `076fe877` (`scripts/recoger.py`, 71 commits; `main` del proyecto tras fusionar
`claude/interfaz-imagenes`). La copia del flujo está al día: ninguna skill ni ningún script del flujo cambia en el
proyecto. Las ideas salen de las retros `docs/registros/retro-2026-10-23-pruebas-mundo-vivo.md` y
`docs/registros/retro-2026-10-25-interfaz-imagenes.md` (la de `imagenes-local` dice «nada general»).

## P1. `bitacora.py check` también en un `commit-msg` del flujo

- **Source:** `docs/registros/retro-2026-10-25-interfaz-imagenes.md` (punto 5) y `.githooks/commit-msg` @ `7410fd78`
- **What changes:** plantilla `templates/githooks/commit-msg` (y la copia de este repo) que, si el commit toca el
  `log` de la config, vuelca `git show :<log>` a un temporal y corre `bitacora.py check <tmp> --date "$(date +%F)"`;
  sin `log` en la config o si el commit lo borra, no comprueba. Excluye `MERGE_HEAD`, `REVERT_HEAD` y similares.
  `aplicar.py` ya sabe convivir con un `commit-msg` ajeno (propuesta `.gw-nuevo`).
- **Why it is general:** hoy el fallo de la bitácora (p. ej. la fecha de «Actualizado») solo salta en el `pre-push`,
  con varios commits ya apilados: en el proyecto hubo que rehacer dos con `reset --soft`. Avisar en el commit cuesta
  lo mismo y ahorra el rehacer.
- **Version bump:** minor (gancho nuevo)
- **Status:** aprobada (2026-10-25)

## P2. `orchestrate-dealer`: comprobar la precondición antes de repartir una tanda manual

- **Source:** `docs/registros/retro-2026-10-23-pruebas-mundo-vivo.md` (T1) @ `076fe877` (aplicada en el proyecto en
  `75b0be29`, QA-216)
- **What changes:** una viñeta en la regla de tandas manuales o de extremo a extremo de
  `skills/orchestrate-dealer/SKILL.md`: «antes de repartir una tanda, comprueba que el estado de partida da la
  precondición de cada comprobación; si no, el primer trozo es prepararla».
- **Why it is general:** en las tandas 22-27 varias comprobaciones pedían un estado que el escenario de partida no
  daba; se repartieron igual y se perdieron llamadas enteras de subagente.
- **Version bump:** patch
- **Status:** aprobada (2026-10-25)

## P3. La fila de tarea de la bitácora dice en qué fase antes de la rama protegida está

- **Source:** `docs/registros/retro-2026-10-25-interfaz-imagenes.md` (punto 4) @ `7410fd78`
- **What changes:** en `templates/es/log.md` y `templates/en/log.md`, la fila «Fase en curso» / tarea admite
  «fases antes de `main`: 1 hecha (`<commit>`), 2 pendiente…»; y una línea en la guía de la bitácora.
- **Why it is general:** la usuaria tuvo que preguntar si se estaban saltando las fases porque la bitácora no lo
  decía; una sesión nueva tampoco lo sabría sin leer el historial.
- **Version bump:** patch
- **Status:** aprobada (2026-10-25)

## Ya está en el flujo

- Worktree del `pre-push` fuera de `.git/` (QA-227, `tools/qa/host.sh` @ `b943c223`, Vite 8 niega `**/.git/**`):
  `templates/githooks/pre-push` ya lo dice y existe `worktreeDir`. Solo cabe nombrar Vite junto a jest en ese
  comentario la próxima vez que se toque.
- Commit de la marca sin `Siguiente:` hecho a mano (`bcf11cf8`): `revisado.sh --footer` existe desde la 0.3.0; el
  proyecto lo tendrá con `gw-update`.
- Copia del `pre-commit` de la base en el CI (`a819fe9d`): la plantilla `comprobar.yml` ya la copia dentro del repo
  (`.gw-ci/`), no a `$RUNNER_TEMP`, así que la raíz sale bien.
- A `main` sin PR con el CI pasado en local (QA-215): es la P7 del instalador, aplicada en la `0.4.0`.

## Se queda en el proyecto

- `tools/qa/ci-local.sh` (podman, `host.sh`): un `ci-local` genérico sería otra pieza grande; queda como idea.
- Tests de navegador con Playwright (QA-219), escenarios `mv-*.dump` y su check (QA-217, QA-220, `e488fe1b`).
- Reglas de `opt-ai` de imágenes y de `opt-tokens` del proyecto.
- «Subagentes con Opus para lo mecánico» (retro, punto 6): lo cubre `selector`.
