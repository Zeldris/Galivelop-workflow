# Harvest world-maker-fantasy — 2026-11-05

De `b995f816` a `d35bfaa1` (`scripts/harvest.py`). 44 commits: la actualización del flujo v0.4.3 → v0.5.0 en WMF, más
tandas de la ronda de la puerta y el cierre del paso 3.3. Sin skills ni scripts del flujo cambiados en el proyecto
(las copias son de versiones anteriores del flujo). Lo nuevo y general sale de `docs/records/propuestas-flujo.md`
(P16-P19; P1-P15 ya se recogieron el 2026-11-03) y de `docs/records/retro-2026-11-04-gw-update-0.5.0.md`. Los
demás retros y registros listados por el informe son los de las cosechas anteriores (la carpeta se renombró a
`docs/records/`). Comprobado contra el flujo en `c259346`.

## P1. `apply.py --update` siembra la plantilla de la bitácora encima de la que se mueve

- **Source:** `docs/records/propuestas-flujo.md` P16 @ `662e7dd9` (script)
- **What changes:** con `"log": "docs/registros/traspaso.md"` (un nombre propio dentro de la carpeta que se mueve a
  `docs/records/`), `apply.py --update --dry-run` planea el `move docs/records` y además `create
  docs/records/traspaso.md` con la plantilla; en WMF la bitácora se sobrescribió y hubo que recuperarla de `HEAD`.
  La guarda `moved_to` (`scripts/apply.py` ~l. 342) solo cubre la ruta movida como archivo, no el archivo que llega
  dentro de una carpeta movida (`plan_move` de `recordsDir`/`proposalsDir`). Sembrar solo si, tras los movimientos,
  el archivo no existe. Reproducido con el flujo actual; añadir su caso en `tests/test_apply.py`.
- **Why it is general:** cualquier proyecto con la bitácora en una carpeta de nombre viejo y un nombre de archivo
  propio pierde la bitácora al pasar a la `0.5`; es el archivo que sostiene los relevos.
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → D51

## P2. `apply.py` conserva un script viejo porque otro archivo cita el mismo nombre en otra ruta

- **Source:** `docs/records/propuestas-flujo.md` P18, primera parte @ `662e7dd9` (script)
- **What changes:** `plan_old_scripts` (`scripts/apply.py` ~l. 1007) busca el nombre con
  `(?<![\w.-])<viejo>(?![\w-])`, que casa también `tools/qa/fusionar.sh` o `tools/qa/mapa-agente.py` (precedidos por
  `/`) y un comentario. Debe casar la ruta entera `.claude/gw/scripts/<nombre>` (o el nombre solo cuando va tras un
  espacio o `"` en un gancho/CI que lo corre). Test con un `gw.json` cuyo `check` llama `tools/qa/<mismo nombre>`.
- **Why it is general:** cualquier proyecto con un script propio que se llame como uno viejo del flujo
  (`fusionar.sh`, `mapa-agente.py`) se queda con la copia vieja y un aviso falso; en WMF se quitaron a mano.
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → D52

## P3. `ownedFiles`: archivos del flujo que el proyecto ha hecho suyos a propósito

- **Source:** `docs/records/propuestas-flujo.md` P18, segunda parte, y `docs/records/retro-2026-11-04-gw-update-0.5.0.md`
  R3 @ `662e7dd9` / `9dcc3986` (retro)
- **What changes:** una clave de `.claude/gw.json` (p. ej. `ownedFiles`, lista de rutas, defecto `[]`, explicada en
  `docs/es/config.md`). `apply.py` no los actualiza ni propone `.gw-new`, `--check` los da como «propios» y puede salir
  con 0, y `doctor.py` deja de recomendar `/gw-update` para un gancho sin cabecera que esté en la lista. Recoge
  también el P12 del 2026-11-03 (doctor y gancho sin cabecera, no elegida) y lo amplía a `--check`.
- **Why it is general:** `apply.py --check` sale 1 para siempre en WMF por un `commit-msg` propio (decisión del
  proyecto); una comprobación siempre en rojo deja de mirarse y esconde el siguiente fallo de verdad. Cualquier
  proyecto que personalice un gancho o un script del flujo cae en lo mismo.
- **Version bump:** minor
- **Status:** aprobada (2026-11-05) → D53

## P4. `ciOnPush`: dejar `check.yml` solo en los pull request

- **Source:** `docs/records/propuestas-flujo.md` P17 @ `662e7dd9` (plantilla de CI)
- **What changes:** una clave de `.claude/gw.json` (p. ej. `ciOnPush`, defecto `true`: el comportamiento actual,
  `push` fuera de la protegida y `pull_request` en `templates/github/check.yml`) que, en `false`, deja solo
  `pull_request`. Documentada en `docs/es/config.md` y leída por `apply.py` al instalar el CI (o por un paso previo del
  job, como `ciPython`, para no tocar el archivo). Avisar en la doc de que `ciIgnore` y los checks requeridos siguen
  yendo por nombre. Encaja con D49 (el CI completo se mira al cerrar el bloque): esta clave es para quien prefiere
  gastar la cuota solo en los PR.
- **Why it is general:** un proyecto con su propio CI (`ci.yml`, solo PR y `main`) duplica el trabajo en cada PR y
  gasta cuota de Actions en cada push; hoy `check.yml` es obligatorio y no se puede acotar sin editarlo (y editarlo
  lo deja como «propio»; ver D45).
- **Version bump:** minor
- **Status:** aprobada (2026-11-05) → D54

## P5. `gw-update`: la reconciliación de cada `.gw-new` va a un subagente que devuelve la tabla de desvíos

- **Source:** `docs/records/retro-2026-11-04-gw-update-0.5.0.md` R2 @ `8f084761` y `propuestas-flujo.md` P19 @
  `9dcc3986` (retro → skill)
- **What changes:** en `skills/gw-update/SKILL.md` (pasos 3 y 4, hoy sin subagentes), mandar la comparación de cada
  `.gw-new` (y los diffs largos de `AGENTS.md`, `REVIEW.md`, `CHANGELOG` y el `--dry-run`) a un subagente barato que
  devuelva la tabla «desvío · arriba · decisión», con la decisión de fusión en la sesión principal; y una línea para
  que el `/code-review` de la rama de actualización deje fuera las copias idénticas del flujo
  (`.claude/gw/`, `.claude/skills/gw-*`), que fueron el 89 % de las 326 rutas revisadas. Enlazar con
  `gw-orchestrate-dealer` en vez de repetir el método.
- **Why it is general:** en WMF la sesión principal leyó los diffs ella misma (21k, 14k, 16k, 22k) y compactó dos
  veces en 12 minutos; ya van dos actualizaciones con el mismo patrón, y le pasa a todo proyecto con desvíos
  locales.
- **Version bump:** minor
- **Status:** aprobada (2026-11-05) → B19

## Stays in the project

- `docs/records/retro-2026-11-04-cierre-3.3.md` (candidatas 1-4): `escenario.sh preparar … fuera:<lugar>`,
  `marca-hallazgo.py --ver`, la regla de «sin ver» en `rondas-de-pruebas.md` y el arranque de 58k por subagente de
  tanda (`QA-124`): herramientas y reglas del juego y de su ronda de pruebas.
- `docs/records/retro-2026-11-04-gw-update-0.5.0.md` R1 (`QA-296`): las reglas de `/gw-update` en
  `docs/runbooks/skills-wmf.md` son de la organización de WMF; lo general sube como P5.
- `.githooks/commit-msg` propio de WMF (sin cabecera, `commitNext` también fuera de Claude Code): suyo a propósito;
  lo general es P3.
- Tandas 86-88 de la ronda de la puerta, `P253`, `P367`, `P180`, `P191`, y el cierre del paso 3.3: contenido del juego.
- `bitacora-check.sh` con identidad propia para el CI y el `gw-allow-secret` del comentario de `pre-commit` (PR 84):
  ajustes del `check.yml` y los ganchos de WMF.

## Already here

- `docs/records/retro-2026-11-03-ronda-puerta.md` (revisión por bloques, `siguiente-id.py`, humo con lo real): ya
  recogidas el 2026-11-04 (`B18`, `D48`, `E24`).
- `docs/records/propuestas-flujo.md` P1-P15 y las ideas de los retros anteriores (renombrados a `docs/records/`): ya
  en `2026-11-03-world-maker-fantasy.md` y anteriores.
- Las copias de `gw-orchestrate-dealer`, `gw-update` y los scripts que el informe lista como «older copies» son
  versiones antiguas del flujo, no cambios del proyecto.
