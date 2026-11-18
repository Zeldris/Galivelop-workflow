# Harvest instalador-wmf-tarkor — 2026-11-18

De `8ae98626` a `f60399b3` (`scripts/harvest.py`). 65 commits (la mayoría `chore(INS-63): métricas en el ledger`); ninguna
skill ni script del flujo cambiados y 2 retros (`docs/records/retro-2026-11-16-ins-63-67.md` @ `f1b2a3e`,
`docs/records/retro-2026-11-18-flu-12.md` @ `a6eff94`, la de la actualización a `0.8.0`). Recogida de
apertura de la `0.9` (2026-11-18).

## P1. `gw-update` deja un gancho registrado dos veces cuando la plantilla le cambia el matcher

- **Source:** `docs/records/retro-2026-11-18-flu-12.md` @ `a6eff94` (retro). Lo mismo, visto en la misma
  actualización, en galivelop-image-generator, private-project-2, private-project-3 y private-project-5 (sus
  propuestas de hoy lo unen aquí).
- **What changes:** `scripts/apply.py` (fusión de `hooks`, ~566-585) junta por evento + matcher + `command`: la `0.8.0`
  pasó `whole-read.py` de `Read` a `^(Read|Bash)$` y el proyecto se quedó con las dos entradas, así que el gancho corre
  dos veces en cada `Read`. La fusión quita del proyecto el `command` del flujo que la plantilla ya registra en el
  mismo evento con otro matcher (no toca los ganchos propios del proyecto). `scripts/doctor.py` da `FAIL` con un mismo
  `command` dos veces en un evento, con la orden que lo arregla. Casos en `tests/`: un `settings.json` de `0.7.x`
  con `Read` → `whole-read.py` queda solo con `^(Read|Bash)$` tras `--update`, y el `FAIL` de `doctor.py` con su
  motivo.
- **Why it is general:** le pasó a los cinco proyectos que actualizaron a la `0.8.0` con ese gancho; cualquier cambio
  futuro de matcher repite el fallo.
- **Version bump:** patch (`0.8.1`: es un fallo de la `0.8.0`)
- **Status:** aprobada (2026-11-18) → D128

## P2. Validar `.github/workflows/` con `actionlint` en el check cuando el proyecto tiene workflows

- **Source:** `.claude/gw.json` y `tools/dev/instalar-entorno.sh` @ `f775360`, `b846a81`, `6462754` (retro P2 @ `f1b2a3e`)
- **What changes:** `templates/gw.json` (y `docs/es/config.md` ↔ `docs/en/config.md`) documenta un paso `actionlint -shellcheck=`
  en `check` para proyectos con `.github/workflows/`, y `scripts/doctor.py` avisa si hay workflows y el `check` no los
  valida. Se fija la versión de `actionlint-py` y se instala con el mismo `pip` que la comprueba (`b846a81`); `-shellcheck=`
  evita que local (sin shellcheck) y CI (con él) den resultados distintos (`6462754`).
- **Why it is general:** un workflow inválido solo falla al correr en el CI; en el proyecto un `app.yml` roto pasó el
  check local. Cualquier proyecto con Actions está igual.
- **Version bump:** minor (clave y aviso nuevos)
- **Status:** aprobada (2026-11-18) → E71

## Joined to another proposal

- La plantilla de `AGENTS.md` nombra `pendingFile` aunque el proyecto no lo tenga fijado (retro `flu-12`): es el
  `gw.json` migrado sin la clave, private-project-2 P1 (`2026-11-18-private-project-2.md`); con la clave escrita por
  `apply.py`, la plantilla acierta.

## Already here

- Ensayo de `gw-update` con resumen y el detalle aparte (retro `flu-12`, ~4,6k tokens leídos dos veces): E52
  (`apply.py --update --dry-run --summary`, `2026-11-14-private-project-3.md` P3) y el subagente que lee el ensayo
  largo en `skills/gw-update/SKILL.md`.

- Retro P1, `commit-msg` rechaza `Findings:`/`Retries:` fuera del último párrafo: es D97 (`docs/roadmap.md`, hecho
  2026-11-14; `scripts/commit-message.py` ~23 y ~229). No hay otro proyecto que añadir aquí: el rechazo ya existe.
  Un `Refs:` suelto ya da «no Refs trailer».
- Retro P3, `roadmap.py show <id> --detail`: D55 ya imprime la fila de cada idioma con su sección `## `
  (`scripts/roadmap.py`, `show`); lo que pide el proyecto (la sección de la tarea en su plan) es de su propio documento.

## Stays in the project

- `tools/dev/instalar-entorno.sh` (instalación de `actionlint-py` con la versión fijada): el resto del script es del
  entorno del instalador; lo general es P1.
- `fix(INS-63): e2e espera a que la variante anterior suelte los puertos` (`953aac8`): prueba e2e del instalador.
