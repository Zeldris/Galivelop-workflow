# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`ccr-96d7a385-yx2p8o`** (sesión 2026-11-26), sacada de `ccr-d1e2d496-0vzck8` (`7cb0d10`); `main` = `664c0dd` = **`0.9.1`** |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.9.1` en `main`** (`664c0dd`, 2026-11-26; las tres fases hechas: revisión de B58-B61 con 3 leves arreglados, retro, `reviewed.sh`; CI de `664c0dd` en verde). Release de GitHub `v0.9.1` publicada (2026-11-26, sesión local; etiqueta sobre `664c0dd`) |
| Siguiente paso | **`0.10` «Estable»**, barridos pequeños primero (usuario, 2026-11-26): **B43, B62 y D180 fusionados** (revisados y arreglados; check completo diferido a la última fusión). B63 en arreglos de su revisión (1 media, 2 leves); se fusiona el último, sin `--defer-check`, y se sube. Después, D180: validar en `config.py validate` las claves `/` y `../` de `wholeReadDenyPaths`. Luego E28-E30 y al final E8/E31. Fase 7 (rodaje) en paralelo. Presupuesto de compactaciones: 2 |

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

1. 2026-11-26 — Fase 2 de la `0.9.1`: `/gw-opt-tokens` y `/retro` (`docs/records/retro-2026-11-26-release-0-9-1.md`), aprobadas por el usuario. Aplicadas B59 (el check para en segundos en un clon superficial, `tests/test_check_shallow.py`), B60 (el encargo de `gw-orchestrate-dealer` nombra `task.py log`) y B61 (`review-scope.py --worktree` en los `config.md`); B58 (`checkCacheIgnore`: la caché del check ignora el ledger, `check-green.sh strip`); B62 (aviso de `Findings:`) y D180 (barrido de `whole-read.py`) a la `0.10`. Versión `0.9.1` subida (`8ee45f27`).
2. 2026-11-26 — D179: 17 arreglos de la revisión de la fase 1 de la `0.9.1` (n.º 1-14, 16-18; el 15 va a la `0.11` y el 19 a la `0.10`, en `pending.md`): `before-stop.py` (CI `none` cuenta como pendiente; caché de estados por sha), `red-without-fix.sh` (tabulador en `testRegex`; rutas absolutas), `handoff.py` (id en otra celda solo para next-id y nunca tras un guion del texto), `doctor.py` (`plan ids` con `$GW_TASK_ID`; aviso del clon con las carpetas probadas), `config.py` (URL SSH; carpetas de otro dueño), `review-scope.py`, `pre-push`, `other-repo-read.py`, roadmap y `config.md`; cada arreglo con su test, copias instaladas idénticas. Check completo pendiente.
3. 2026-11-26 — B56: dos reglas «(criterio)» en `templates/{es,en}/REVIEW.md` (un test no depende de que exista lo que comprueba; un comando con tiempo límite mata su grupo de procesos) y, en `gw-orchestrate-dealer` (tres copias), el encargo contrasta el valor esperado con el código y devuelve `QUESTIONS` si no cuadra; ficha `docs/tasks/B56.md`. Check completo pendiente.
4. 2026-11-25 — B55: el `pre-push` (y su plantilla) imprime en stderr, al tomar el bloqueo del check, «check lock held (a long check is running…)» y la ruta del registro con `tail -f`; la propuesta decía `push.sh`, pero el registro y el bloqueo nacen en el gancho, que `push.sh` ya muestra. Caso nuevo en `test_hooks`; ficha `docs/tasks/B55.md`.
5. 2026-11-25 — B54: `review-scope.py` avisa (stderr) de un árbol con cambios sin confirmar y admite `--worktree` (confirmado, preparado, sin preparar y sin seguimiento; no con `--trivial`, exit 2 con el motivo); copia instalada y ficha `docs/tasks/B54.md`. `test_review_scope` (37) en verde; check completo en verde (`CHECK OK`, sobre `d656634`).

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
