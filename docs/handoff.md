# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.8`: `ccr-d1e2d496-0vzck8`**, con `main` fusionado. `main` = `7a6d1bd` = **`0.7.1`** (2026-11-16, parche desde `version/0.7.1`). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.7.1` en `main`** (`7a6d1bd`, 2026-11-16; CI en verde). Etiqueta y release `v0.7.1` creadas por el agente desde una sesión local (2026-11-16, a petición del usuario) |
| Siguiente paso | **Grupo C de la `0.8`, oleada 2B, en obra** (2026-11-18) con `gw-orchestrate-dealer`: C4+C5 (`questions-guard.py`, gancho `PreToolUse` de preguntas abiertas; tarea en curso = rama `agent/<id>-` o marca `gw/current-task` de `task.py current`, `I-lifecycle.md`) en el worktree `.claude/worktrees/C4-questions-guard` (encargo `brief-C45.md` del scratchpad); luego revisión, arreglos, fusión con el check completo y revisor de lo que falte de la oleada 2. Oleada 3: C12, C13, A11. No fusionar ni editar el árbol mientras corre un check. Presupuesto de compactaciones: 2 |

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

1. 2026-11-18 — Grupo C de la `0.8`, oleada 2A (worktrees en paralelo, cada rama revisada y arreglada): C11 cerrada (`handoff.py close-row <id>` exige la ficha cerrada: casillas con test o `== sección`, Verification con sha y orden; `trace.py` muestra la ficha y su decision log; regla «Task record» de `REVIEW.md`), C6+C7 (`modes.questions`, `mode.py list|line|set` con edición en su sitio y escritura atómica, `config-guard.py` pide permiso ante `mode.py set`, skill `gw-mode`, línea de modos al empezar sesión). C11 y C7 cerradas con su propio `close-row`. Check completo de la fusión en verde salvo la copia instalada de `trace.py`, sincronizada en este commit. 10 hallazgos leves a `pending.md`.
2. 2026-11-17 — Grupo C de la `0.8`, oleada 1 (worktrees en paralelo, cada rama revisada y arreglada): C1-C3+C10 (`questions.py` add/answer/list/count, `docs/questions.md` con `questions.path`, aviso de preguntas abiertas no vistas al empezar sesión, regla de subagentes), C8 (`careful.py` pregunta antes de órdenes destructivas, `modes.careful` y `modes.carefulWorktrees`) y C11, primera mitad (ficha `docs/tasks/<id>.md` y entradas en `docs/tasks/<id>/`, `task.py new/log/resolve`, el `commit-msg` las exige en `feat`/`fix` que tocan código). Check completo de la oleada en verde (`1e33ab4`). Leves, a `pending.md`.
3. 2026-11-17 — Grupo B de la `0.8`, oleada 3b (worktrees en paralelo, cada rama revisada y arreglada): D14 (`trace.py --no-docs`; una fila por id con la traducción como `also`; salida separada en `declared` y `deduced`), B42 (los tests marcan sus procesos con `GW_TEST_PROC_MARK` en vez de `pgrep -f`; `tests-for.py --run` corre una sesión por unidad con la salida a archivo y `testUnitTimeout`; el cuelgue era sobrecarga, no un cerrojo), D62 (el aviso de CI del `pre-push` mata su grupo al interrumpirse, agrupa las ramas por sha, da rutas absolutas y avisa si no lee su clave) y D95 (`split_lines` respeta el fin de cada línea; cerrojo por repo en las órdenes que escriben, `handoff.lockWait`; `check.sh` corre solo `preflight --strict`). D87 y E49, marcados hechos en el roadmap. Leves de la revisión, a `pending.md` (`0.9`). Check completo y tests de la oleada en verde.
4. 2026-11-17 — Grupo B de la `0.8`, oleada 3a (worktrees en paralelo, cada rama revisada y arreglada): D87+E49 (`gw-init` ofrece licencia doble MIT + CC BY-NC-SA 4.0 con plantillas en `templates/licenses/`, sin pisar las existentes; regla «sin firmas» en el `CLAUDE.md` con `agentSignatures: false` mediante `<!-- if !clave -->`; `push.sh` y bloque `.gitignore` en la skill), D94 (`reviewed.sh` aconseja `push.sh` en vez de refspec) y B31 n.º 5 (marcador del aviso de contexto por transcript, `contextGuard.warnedMax`, cerrojo). Las plantillas de licencia, en `UNMARKED` de `version.py`. Leves, a `pending.md`. Check completo en verde.
5. 2026-11-17 — Grupo B de la `0.8`, oleada 2 (worktrees en paralelo, cada rama revisada y arreglada): D80+D126 (`doctor.py` avisa de un sello de `gw-scout-updates` caducado, `scoutMaxAgeDays`; el inventario lee la versión de Rust), D83+D127 (`apply.py --update` añade a `staleRefs` lo que renombra; `--init` escribe un bloque `.gitignore` por stack con marca, `gitignoreStacks` y `--stack`), E53+E63 (regla de CI en `patterns.md`; invariantes y «Navegadores» en la plantilla de `REVIEW.md`) y E64 (dealer). Leves de la revisión, a `pending.md`. Check completo y tests de la oleada en verde.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
