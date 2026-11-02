# Harvest world-maker-fantasy — 2026-10-23 (piloto de la Fase 6)

De `76ec6aeb` a `e433d1d2` (`scripts/recoger.py`, 39 commits). Es el piloto de Galivelop-workflow `0.2.0`, fusionado
en `main` sin PR por falta de cupo de Actions, con el CI pasado en local. La copia del flujo está al día: ninguna
skill ni ningún script del flujo cambia en el proyecto. Las ideas salen del registro
`docs/registros/piloto-galivelop-workflow.md` («For Galivelop-workflow») y de la retro
`docs/registros/retro-2026-10-23-piloto-galivelop.md`.

Las que coinciden con el instalador se proponen solo aquí y se señalan con «(también el instalador)». El instalador
tiene su propia recogida, [`2026-10-23-instalador-wmf-tarkor.md`](2026-10-23-instalador-wmf-tarkor.md).

## Fallos (patch)

## P1. `revisado.sh` cuenta los archivos sin seguimiento y solo lee la primera línea del Estado (también el instalador)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (fricciones 22, 23 y 26) @ `e433d1d2`; retro 2026-10-23
  (propuesta 2); instalador, registro (punto 20) @ `89bb2eeb`
- **What changes:** en `scripts/revisado.sh`:
  - `git status --porcelain --untracked-files=no`, para no obligar a guardar con stash los borradores sin commit;
  - leer el párrafo entero de `**Estado:**`, no solo la primera línea (`grep -m1`), y aceptar «aprobad*»;
  - el error dice qué palabras valen, y la skill `retro` fija la forma de esa línea;
  - una opción para añadir la línea `Siguiente:` al commit de la marca, para los proyectos cuyo `commit-msg` la exige.
- **Why it is general:** es la fricción más repetida en los dos pilotos y bloquea el cierre antes de `main`.
  Comprobado aquí: la línea 28 cuenta los archivos sin seguimiento y la 51 usa `grep -m1`.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P2. `pre-commit` no limpia `GIT_DIR` en un worktree enlazado

- **Source:** registro (fricción 27, «Ganchos») @ `e433d1d2`
- **What changes:** `templates/githooks/pre-commit` hace `unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE` antes de
  `git -C "$hookdir" rev-parse`, como ya hacen `session-start.sh`, `pre-push` y `revision-antes-de-main.sh`. Lleva un
  caso en `tests/test_ganchos.py`.
- **Why it is general:** un merge dentro de un worktree enlazado falla en cualquier proyecto. Comprobado aquí: las
  líneas 15-17 del gancho no limpian esas variables.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P3. `doctor.py`: WARN falso por el nombre del script y `reviewMark` ignorado sin aviso

- **Source:** registro (fricciones 2 y 17) @ `e433d1d2`
- **What changes:**
  - `stale_flow_hooks` reconoce un gancho del flujo por su cabecera o su contenido, no solo por el nombre. Hoy un
    `session-start.sh` propio del proyecto da WARN.
  - `MUST_BE_TRACKED` incluye la ruta de `reviewMark` que haya en el config.
- **Why it is general:** el WARN falso empuja a borrar un gancho que deja la nube sin entorno, y una marca ignorada
  por `.gitignore` rompe el `pre-push` sin explicarlo.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P4. `bitacora.py closed` y `check`, más estrictos

- **Source:** registro (fricción 14, dos puntos de «For Galivelop-workflow») @ `e433d1d2`
- **What changes:**
  - `closed` cuenta como apuntada solo la línea tachada de «Hecho», o la que empieza por fecha y nombra el id
    tachado.
  - `check` falla si una fila «Tarea en curso» no tiene rama, aunque haya otras filas buenas.
- **Why it is general:** hoy una tarea se da por cerrada con un punto sin tachar.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P5. Gancho del PR: salir pronto y explicar mejor (también el instalador)

- **Source:** registro (fricciones 18 y 24) @ `e433d1d2`; retro 2026-10-23 (propuesta 5); instalador, registro
  (puntos 16 y 17) @ `89bb2eeb`
- **What changes:** en `scripts/revision-antes-de-main.sh`:
  - salir antes de lanzar Python si la orden no es `git push` ni de PR. Hoy el patrón `*gh*pr*` también casa con
    «github» o «projects»;
  - si falta `python3` y la orden no es de las suyas, no fallar cerrado;
  - comprobar el acceso con `gh api user` y no con `gh auth status`;
  - con el PR ya cerrado o fusionado, decirlo en vez de pedir un `gw.json` en su rama.
- **Why it is general:** los falsos bloqueos frenan órdenes que no tienen nada que ver con el PR.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P6. `es-codigo.sh` distingue una regex de `content` inválida de otros fallos

- **Source:** registro (fricción 25) @ `e433d1d2`
- **What changes:** hoy cualquier fallo del Python incrustado (por ejemplo, un BrokenPipe con `| head -1`) se lee
  como «content regex invalid». Hay que distinguir los casos.
- **Why it is general:** un mensaje que no es el motivo real hace perder tiempo en cualquier proyecto.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P7. Tests y medidas de las skills (también el instalador)

- **Source:** registro (fricciones 4, 5 y 6) @ `e433d1d2`; retro 2026-10-23; instalador, registro (punto 6)
- **What changes:**
  - traer a `skills/opt-tokens/scripts/` el test de WMF, `tools/qa/tests/test_medir.py` (8 casos);
  - `medir.py --hours 0` avisa si la sesión mezcla ventanas de compactación;
  - `opt-ai/scripts/medir.py` añade una tabla por turno;
  - `aplicar.md` dice que los tests de las skills se descubren con `-s <skill>/scripts`.
- **Why it is general:** un proyecto que exige un test a cada herramienta se para con `medir.py`.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P8. `scout-updates`: títulos en el idioma del proyecto

- **Source:** registro (fricción 8) @ `e433d1d2`
- **What changes:** `compare.py` acepta los títulos en el `language` del proyecto (`sello`, `Restricciones`…).
- **Why it is general:** un proyecto en español no puede usar la memoria de la skill sin traducir sus títulos.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## P9. `doctor.py` avisa de términos repetidos en `GLOSSARY.md`

- **Source:** registro (fricción 15) @ `e433d1d2`
- **What changes:** un WARN si el mismo `**Término**:` aparece dos veces.
- **Version bump:** patch
- **Status:** aprobada (2026-10-23)

## Claves nuevas del config (minor)

## P10. El `pre-push` en monorepos y sandboxes: `checkWrapper` y rutas enlazadas en el worktree (también el instalador)

- **Source:** registro (fricciones 3, 20 y 21) @ `e433d1d2`; instalador, registro (punto 1) @ `89bb2eeb`
- **What changes:**
  - `checkWrapper`: un prefijo del proyecto para cada orden de `check` y `relatedTests` (en WMF, `tools/qa/host.sh`);
  - una lista de rutas que se enlazan del checkout principal en el worktree del `pre-push`. Hoy solo se enlazan
    `node_modules` y `.venv` de la raíz, y los de `backend/` y `app/`, el `target/` de Cargo o `.env` no llegan;
  - crear el worktree dentro de `.git/` en vez de `$TMPDIR` (el sandbox Flatpak de la Steam Deck no lo ve);
  - el log de cada orden con `mktemp`. Hoy es `gw-pre-push-check-$n.log`, y dos subidas a la vez se pisan.
  - Afecta a `templates/githooks/pre-push`, `schema/gw.schema.json`, `scripts/config.py` y `docs/<lang>/config`.
- **Why it is general:** sin esto, un proyecto con la app en una subcarpeta no puede usar el `pre-push` del flujo:
  WMF lo reescribió y el instalador se apaña con su propio `en-app.sh`.
- **Version bump:** minor
- **Status:** aprobada (2026-10-23)

## P11. CI y entorno: `ciInstall`, paso `setup` y `comprobar.yml` que no duplique

- **Source:** registro (fricciones 11 y 16) @ `e433d1d2`; instalador, registro (punto 3)
- **What changes:**
  - `ciInstall`, separado de `install`;
  - un paso `setup` que `session-start.sh` corra después de `install`. Hoy los ganchos de inicio corren en paralelo;
  - `doctor.py` no propone `comprobar.yml` si otro workflow ya corre el `check`;
  - `aplicar.md` explica el paso `pre-commit --rango` como pieza suelta para una CI que ya exista.
- **Why it is general:** la plantilla de CI solo vale para una plataforma sin Rust, y los dos pilotos se quedaron
  con su CI propia.
- **Version bump:** minor
- **Status:** aprobada (2026-10-23)

## P12. `enlaces-md.py`: carpetas que enlazan desde la raíz (`linkRoots`)

- **Source:** registro (fricción 14) @ `e433d1d2`
- **What changes:** una clave `linkRoots`, o como mínimo decir en la skill `pr` que la descripción guardada enlaza
  desde su carpeta.
- **Version bump:** minor (o patch si solo se documenta)
- **Status:** aprobada (2026-10-23)

## P13. `scout-updates`: carpeta de la memoria configurable y banco por pares a ciegas

- **Source:** registro (fricciones 9 y 10) @ `e433d1d2`
- **What changes:**
  - `scoutDir` en `gw.json`;
  - traer como opción del paso 5 el banco de WMF, `tools/qa/banco-calidad.py`, con su test. Antes hay que revisarlo.
- **Version bump:** minor
- **Status:** aprobada (2026-10-23)

## No se propone

- **Mensajes de los scripts en el `language` del proyecto** (fricción 7): va contra la regla de que los mensajes de los
  scripts estén en inglés con la orden que arregla el fallo. Se descarta salvo que el usuario decida otra cosa.
- **Acceso de lectura al repo del flujo desde los pilotos** (fricción 13): no es código, sino una decisión del dueño.
  Ya la cubre la distribución por plugin de la Fase 9.

## Ya está en el flujo

- Archivos del flujo ignorados por git: `doctor.py` (`check_ignored`). Solo faltaba `reviewMark`, que va en P3.
- `rojo-sin-arreglo.sh --fails-with REGEX`. Falta una opción para exigir que se ejecute exactamente un test
  (fricción 14): patch pequeño, cabe con P4.
- Qué hacer si `aplicar.py` lo bloquea el clasificador: `docs/es/aplicar.md`. Cabe subirlo al paso 2.
- `REVIEW.md` y `GLOSSARY.md` que ya existen: `docs/es/aplicar.md`.

## Se queda en el proyecto

- `tools/qa/host.sh` y el sandbox Flatpak de la Steam Deck. La parte general va en P10.
- Los logs de `tests-vitest.sh`, `escenario.sh`, `matriz-pruebas.py`, `*.kate-swp` y el runbook de rondas, de la retro
  2026-10-22.
- Lo que decidió el piloto: `protectedPaths`, `content`, `designReferences`, `relatedTests` con vitest, el `ci.yml`
  propio y los duplicados de `tools/qa` unificados.
