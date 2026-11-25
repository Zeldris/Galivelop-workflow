# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9.0` publicada en `main`: `ccr-d1e2d496-0vzck8`** = `main` = `8357389` (2026-11-24). La `0.9` queda cerrada; la siguiente es la `0.10` «Estable» |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.9.0` en `main`** (`8357389`, las tres fases hechas: revisión con 7 hallazgos arreglados, retro D176/D177, `reviewed.sh`; CI de `4b9b5e4` en verde). Release de GitHub `v0.9.0` publicada (2026-11-24, sesión local; etiqueta sobre `8357389`) |
| Siguiente paso | **La `0.9.1`** (parche B48-B56, `docs/roadmap.md`: B48-B54 y B57 hechos; sigue B55), luego la `0.10` «Estable» (E28 primero). Evolutivos de la recogida a la `0.11` (E87-E92). `task.py current` sigue en E86 (solo lo cambia el usuario). Presupuesto de compactaciones: 2 |

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

1. 2026-11-25 — B54: `review-scope.py` avisa (stderr) de un árbol con cambios sin confirmar y admite `--worktree` (confirmado, preparado, sin preparar y sin seguimiento; no con `--trivial`, exit 2 con el motivo); copia instalada y ficha `docs/tasks/B54.md`. `test_review_scope` (37) en verde; check completo pendiente.
2. 2026-11-25 — B53: `red-without-fix.sh` decide por ruta (clave nueva `redWithoutFix.testPathRegex`: una ruta de test se rechaza, exit 2, sin leer su contenido) y `testRegex` queda con marcadores anclados al inicio de línea (una docstring o prosa ya no rechaza código); esquema, plantilla, docs es/en, copia instalada y ficha `docs/tasks/B53.md`. `test_red_without_fix` y `test_config` en verde; check completo con un solo fallo (la lista de claves de `redWithoutFix` en `test_config`), arreglado.
3. 2026-11-25 — B52: `entry_regex` (`handoff.py`) lee el id en cualquier celda de una fila de tabla (la primera que empieza con id: `| 1 | **B3** |`), y `doctor.py` avisa (`plan ids`) si ninguna entrada del plan casa con `taskId`; filas en ambos `troubleshooting.md`. `test_doctor` (186) y `HandoffNextId` (10) en verde; check completo pendiente.
4. 2026-11-25 — B51: `gw-update` paso 1 comprueba `HEAD..origin/<protectedBranch>` y para (con `merge-main.py` o rama nueva, y el aviso del ledger); paso 2, comprobar que la clave existe antes de recomendarla. Solo texto de skill y copias; tests de skills y check completo pendientes.
5. 2026-11-25 — B49: `other-repo-read.py` exenta la palabra `<dir>/scripts/apply.py` tras un intérprete `python*` (`apply_script_words`); otro script del clon o una lectura en el mismo comando siguen avisando. `test_other_repo_read` (23) en verde; check completo pendiente.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
