# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9`: `ccr-d1e2d496-0vzck8`**, con `main` fusionado. `main` = `a725647` = **`0.8.2`** (fusionada aquí). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.8.2` publicada** (`main` = `a725647`, 2026-11-22; las tres fases hechas, retro decidida; release `v0.8.2` de GitHub publicada desde una sesión local del usuario) y fusionada en la `0.9` |
| Siguiente paso | **Cerrar la `0.9`** (E84-E86, D158, D161/D162/D165/D166, D171-D175 y whole-read.py hechos; P1 y P4 comprobados): solo queda D160 (`.gw-ci/` a `$RUNNER_TEMP`, opcional, un intento revertido) y las fases antes de `main` (código, entorno con retro, cierre). Q-7 y Q-8 esperan al usuario. E79-E83 van a la `1.0`. **La retro de la `0.9` debe leer en `pending.md` «Para la retro de la `0.9`»** (fallo: no se pidió `/clear` al cerrar tareas). Presupuesto de compactaciones: 2 |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [x] 6. Piloto: Tarkor e instalador (2026-10-23; private-project-1, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Lanzamiento (antes «Público»; plan §9, A7)

## Para la próxima publicación

**Política de versiones** (usuario, 2026-11-01, plan §7): solo la última menor publicada recibe parches (hoy la `0.5`);
los evolutivos van a la siguiente menor que no esté en obra (`docs/roadmap.md`). Cada versión se publica en este repo
(público), a lo sumo una al día. La sesión en la nube no puede subir etiquetas (403 del proxy): la release, a mano o
desde una sesión local.

**Orden de publicación** (usuario, 2026-11-15): primero el parche `0.6.2` (D109-D115) desde su rama `version/0.6.2`, sacada de `main`; después la `0.7.0` desde esta rama, con `main` ya traído.

## Hecho (5 últimas)

1. 2026-11-23 — D175 (P1 y P4 de la `0.9`): ya estaban hechos (E84 `push.sh --wip` y E86 reparto de la revisión de la fase 1); comprobado con `test_push.py` (31) y `test_before_stop.py` (125) en verde y marcados en `pending.md`. De la `0.9` solo quedan D160 (`.gw-ci/`, intento revertido), una observación sin acción y el fallo del `/clear` para la retro.
2. 2026-11-23 — D174 (los cuatro leves de D172 y P3): el aviso de copia instalada del `pre-commit` compara con la copia preparada, no con la del disco; `pending_ids` usa `(?<![A-Za-z0-9_])` (ids como `#12`); `ci_ledger_path` rechaza también `+`, `!` inicial y `\`; la nota «session model check did not run» exige un `Session:` anterior en la transcripción. P3 ya lo cubría `whole-read.py` (E85, D170, D173). Un test rojo sin cada arreglo; `test_models` (16), `PreCommitInstalledCopy` (5), `test_apply` (260), `test_utils` y `test_whole_read` (67) en verde. Quedan de `0.9`: P1 (`push.sh --wip`) y P4 (reparto de la revisión de la fase 1 en `gw-orchestrate-dealer`).
3. 2026-11-23 — D173 (leves de la revisión de E85, `whole-read.py`): `head -n +200` cuenta; `-` es la entrada estándar; el rango pasa por etapas de paso antes y después (`| cat |`, `| head -n 200 | cat -n`) y también tras un rango; solo se aplica con un único archivo o entrada (`cat a b | head -n 200` no avisa); etiqueta sin dobles espacios y con `< archivo`. Dos casos nuevos en `test_whole_read.py` (67 en verde) y `test_session_log.py` (124) con el escrito atómico de `alive.txt`. Ocho entradas de `pending.md` marcadas. Falta de `0.9` en `pending.md`: P1, P3 y P4 y los cuatro leves de D172.
4. 2026-11-23 — D172 (`/code-review` del bloque `eb6c8cc`…`ca88948`, subagente limpio): 1 importante arreglado: el aviso de copia instalada del `pre-commit` (D169) corría en proyectos con `scripts/` propio y mandaba a un `apply.py` que no tienen; ahora solo en el repo del flujo (`config.is_workflow`), con test rojo sin el arreglo. Cuatro leves y una observación, en `pending.md`. Siguen los leves de `whole-read.py`.
5. 2026-11-23 — D171 (leves de la revisión de D158): `WORKFLOW_NAME`, `plugin_field` e `is_workflow` viven solo en `config.py` (`doctor.py` y `review-scope.py` los importan, «un dato, un sitio»); `check_workflow_clone` calla también cuando el repo del propio script es el flujo (`doctor.py --root <proyecto>` desde un clon); `handoff.py archive` usa `today()` (local) y no la fecha UTC; test `test_workflow_clone_is_quiet_when_run_from_the_workflow_repo_on_a_project` (rojo sin el arreglo); copias regeneradas con `apply.py .`. `test_doctor.py`, `test_review_scope.py`, `test_config.py` y `test_config_guard.py` en verde; los tres leves, marcados en `pending.md`.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
