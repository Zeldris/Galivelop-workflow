# Harvest private-project-4 — 2026-11-15

De `e1c64573` a `6cc80cc4` (`scripts/harvest.py`). 14 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro (`docs/records/retro-2026-11-14-fase0.md`). Recogida de cierre de la `0.7` (usuario, 2026-11-15).

Sin nada nuevo desde la recogida anterior: `private-project-2`, `private-project-3`, `instalador-wmf-tarkor` y
`labs-log-detective`.

## P1. `reviewed.sh` y el `pre-push` no dejan crear la rama protegida

- **Source:** `docs/records/retro-2026-11-14-fase0.md` P6 @ `cd88eaa` (retro)
- **What changes:** con `origin/<protegida>` sin crear, `scripts/reviewed.sh` falla al traerla y no da la marca, y el
  `pre-push` exige la marca para crearla: un círculo (el proyecto lo rompió creando `main` con la API). `reviewed.sh`
  toma como base la raíz de la rama cuando la protegida no existe en el remoto, con su test.
- **Why it is general:** le pasa a cualquier proyecto nuevo que adopta el flujo antes de tener `main`.
- **Version bump:** patch
- **Status:** proposed

## P2. `recover.py --state` compara el commit local con el de `origin/<rama>`

- **Source:** `docs/records/retro-2026-11-14-fase0.md` P3 @ `cd88eaa` (retro)
- **What changes:** `--state` imprime el commit local y el de `origin/<rama>` y si va al día, por delante o por
  detrás; el paso 2 de «Al empezar» de `AGENTS.md` (y su plantilla) apunta a esa salida.
- **Why it is general:** el paso 2 se hace a mano en cada arranque y falla a menudo (`rev-parse` de varias
  referencias da «Needed a single revision»; pasó también en la sesión de esta recogida).
- **Version bump:** minor
- **Status:** proposed

## P3. `gw-selector` avisa si la sesión no se abrió en la carpeta del repo

- **Source:** `docs/records/retro-2026-11-14-fase0.md` P1 @ `cd88eaa` (retro)
- **What changes:** un script pequeño compara el directorio de trabajo con `git rev-parse --show-toplevel` y
  `gw-selector`, que corre aunque no cargue `.claude/settings.json`, lo dice en su línea.
- **Why it is general:** abierta fuera del repo, la sesión no carga ganchos y nada lo avisa (`doctor.py` solo si se
  corre).
- **Version bump:** minor
- **Status:** proposed

## P4. La plantilla de `AGENTS.md` nombra `ci-status.py` al mirar el CI

- **Source:** `docs/records/retro-2026-11-14-fase0.md` P2 @ `cd88eaa` (retro)
- **What changes:** «mira el CI» de `templates/{es,en}/AGENTS.md` nombra `python3 .claude/gw/scripts/ci-status.py` y
  su `--failed`, como el `AGENTS.md` de este repo.
- **Why it is general:** sin el nombre, el agente lee el CI con la API de GitHub (~560k tokens en 9 llamadas).
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- Lo demás de la retro (P4-P5) y los commits de la fase 0: trabajo del dominio del proyecto.
