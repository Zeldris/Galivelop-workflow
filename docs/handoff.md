# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **Parche `0.7.1`: `version/0.7.1`**, sacada de `main` (`c1e75c8` = **`0.7.0`**, 2026-11-15, etiqueta y release `v0.7.0`). La `0.8` sigue en `ccr-d1e2d496-0vzck8`; `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.7.0` en `main`** (`c1e75c8`, 2026-11-15; CI en verde; release `v0.7.0` publicada) |
| Siguiente paso | Fase 2 de la `0.7.1` aplicada (`retro-2026-11-16-patch-0-7-1.md`): D123-D125 hechos; B41 a la `0.8`; T1 aplazada. Siguiente: CI de este commit, fase 3 (`/code-review` de D123-D125 en un `gw-reviewer`, `reviewed.sh`), `bash scripts/check.sh`, `main` y fusionar `main` en `ccr-d1e2d496-0vzck8`. Presupuesto de compactaciones: 1 |

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

1. 2026-11-16 — Fase 2 de la `0.7.1`: `/gw-opt-tokens` (arranque de 94k, ~82k del sistema) y `/retro`; el usuario aprueba R1-R3 (D123-D125) y B41 (barrido de `merge-branch.sh`, a la `0.8`) y aplaza T1 (quitar conectores sin uso); D123 (`templates/gw.json` en `testMap`), D124 (`version.py` avisa al sellar si falta la recogida) y D125 (`ci-status.py`: job cancelado sin pasos, con la orden para relanzarlo) hechos
2. 2026-11-16 — Fase 1 de la `0.7.1`: `/code-review` en un `gw-reviewer` limpio, 5 hallazgos de D122 arreglados: el consejo de quitar conectores solo con un arranque por encima de `warn` y una sola regla (`context_guard.system_weighs_most`), la conversación arrastrada (resumen de compactación, primer prompt) contada aparte del sistema, el mismo `hook_chars` en el aviso y la lista de `recover.py`, y la clave `contextGuard.systemAdvice`; un leve a `pending.md`
3. 2026-11-16 — D122 (parche `0.7.1`): con el presupuesto de compactaciones pasado y el resto del sistema como mayor culpable del arranque, `recover.py --state` pide quitar conectores que no se usan en vez de `/clear` (`context_guard.system_is_largest`); la alarma de bucle de compactación, igual; tests en `test_context_guard.py` y `test_session_log.py`
4. 2026-11-15 — Fase 2 de la `0.7.0`: `/gw-opt-tokens` y `/retro` (`retro-2026-11-15-release-0-7-0.md`), aprobadas por el usuario: E62 (`gw-worker` con el modelo y el esfuerzo de la llamada para todos los peldaños, nuevo `gw-reviewer` y aviso de `subagent-cap.py`), B39 (`measure.py` sin argumentos de `git config` como archivos) y B38 (barrido de `handoff.py`) a la `0.8`
5. 2026-11-15 — Fase 1 de la `0.7.0`: lo que quedaba desde el último `Findings:` (`95a54e7`) era trivial (arreglo de `test_waits.py` de `3bc4d53`, sellos de versión de `b44cd14`; la `0.6.2` fusionada ya pasó su fase 1), revisado en la sesión (B27) sin hallazgos; CI de `b44cd14` en verde y check entero en local

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md) (85 entradas); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
