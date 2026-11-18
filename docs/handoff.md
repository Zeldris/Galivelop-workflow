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
| Siguiente paso | **`0.8` acotada** (usuario, 2026-11-18): queda D68 (`changelog.d/`), E33 (anclas de revisión) y E35 (`flaky`) en una oleada en paralelo con `gw-orchestrate-dealer`; después D7 (`AGENTS.md` sin `@include`, `.agents/skills`) y B9 (opencode; medir su alcance antes). Luego, sellar la `0.8` (CHANGELOG, documentación, fases 1-3 y `main`). El front y A12 pasan a la `0.9`; E32, B38 y lo leve de `pending.md`, a la `0.10` «Estable». Presupuesto de compactaciones: 2 |

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

1. 2026-11-18 — Reparto nuevo de versiones (usuario, 2026-11-18): la `0.8` pasa a «Preguntas y otros agentes» y se cierra con D68, E33, E35, D7 y B9; nueva `0.9` «Front» (A12, E4, E5, E7, E9-E16, E42, E50); la «Estable» pasa a `0.10`, solo correcciones y revisiones (con E32 y B38), y lo evolutivo de las recogidas va a la `1.x` (plan §7 y regla de versiones del roadmap). Lo de `pending.md` marcado `0.9`, a `0.10`.
2. 2026-11-18 — Grupo C de la `0.8`, oleada 3 (worktrees en paralelo, cada rama revisada y arreglada): A11 (plan §4.5 «Modos de trabajo», regla «Cuatro modos» de `AGENTS.md`, columna «Modes» de `gw-selector`), C13 (`scope-guard.py`, gancho `PreToolUse` de Edit/Write con `scopeGuard.mode` off/warn/block/auto, `--staged` en el `pre-commit`, `deviations.jsonl` y `task.py deviations`, `task.py new --related`) y C12 (`spikeBranch`: `spike/<tema>` sin ficha ni `Refs:` con trailer `Spike:`; el `pre-push` y `merge-branch.sh` no dejan llevarla a una rama de trabajo ni a `main`). Revisiones: C13 1 grave + 4 medios + 2 leves arreglados, C12 1 medio + 5 leves; el resto, a `pending.md`. Check completo de la oleada en verde (`636582a`, tras renombrar una variable en español). C12 y C13 cerradas con `close-row`; grupo C completo.
3. 2026-11-18 — Grupo C de la `0.8`, oleada 2B: C4+C5 (`questions-guard.py`, gancho `PreToolUse` de Edit/Write: en modo restrictivo rechaza código con preguntas abiertas de la tarea en curso, en modo guía avisa una vez; tarea en curso = rama `agent/<id>-` o marca `gw/current-task` por worktree, `task.py current <id>|--clear`; `task.py new` no cambia una marca ajena; `config-guard.py` pregunta ante `questions.py accept-risk` y `task.py current`; `close-row` borra la marca de su tarea). Dos rondas de revisión (11 + 1 hallazgos arreglados). C4 cerrada con `close-row`, C5 hecha. Fusión `ccf3037` con el check completo de la oleada en verde. Leves, a `pending.md`.
4. 2026-11-18 — Grupo C de la `0.8`, oleada 2A (worktrees en paralelo, cada rama revisada y arreglada): C11 cerrada (`handoff.py close-row <id>` exige la ficha cerrada: casillas con test o `== sección`, Verification con sha y orden; `trace.py` muestra la ficha y su decision log; regla «Task record» de `REVIEW.md`), C6+C7 (`modes.questions`, `mode.py list|line|set` con edición en su sitio y escritura atómica, `config-guard.py` pide permiso ante `mode.py set`, skill `gw-mode`, línea de modos al empezar sesión). C11 y C7 cerradas con su propio `close-row`. Check completo de la fusión en verde salvo la copia instalada de `trace.py`, sincronizada en este commit. 10 hallazgos leves a `pending.md`.
5. 2026-11-17 — Grupo C de la `0.8`, oleada 1 (worktrees en paralelo, cada rama revisada y arreglada): C1-C3+C10 (`questions.py` add/answer/list/count, `docs/questions.md` con `questions.path`, aviso de preguntas abiertas no vistas al empezar sesión, regla de subagentes), C8 (`careful.py` pregunta antes de órdenes destructivas, `modes.careful` y `modes.carefulWorktrees`) y C11, primera mitad (ficha `docs/tasks/<id>.md` y entradas en `docs/tasks/<id>/`, `task.py new/log/resolve`, el `commit-msg` las exige en `feat`/`fix` que tocan código). Check completo de la oleada en verde (`1e33ab4`). Leves, a `pending.md`.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
