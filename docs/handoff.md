# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.7` «Preguntar»: `ccr-d1e2d496-0vzck8`** (hace de `version/0.7.0`), con `main` fusionado. `main` = `c1e75c8` = **`0.7.0`** (2026-11-15, etiqueta y release `v0.7.0`). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.7.0` en `main`** (`c1e75c8`, 2026-11-15; CI en verde). Etiqueta y release `v0.7.0` creadas por el agente desde una sesión local (`gh release create`, 2026-11-15, a petición del usuario) con los textos de `docs/records/release-v0.7.0.md` |
| Siguiente paso | El usuario decide la recogida H22 (`docs/proposals/2026-11-15-instalador-wmf-tarkor.md`: P1 a la `0.7.1` como D122, P2 a E58); luego el barrido B38. Presupuesto de compactaciones: 1 |

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

1. 2026-11-15 — Recogida de apertura de la `0.8` (H22) sobre 9 proyectos: solo el instalador trae ideas (`docs/proposals/2026-11-15-instalador-wmf-tarkor.md`): P1 (aviso de bucle de compactación que no pide `/clear` si pesa el sistema, al `0.7.1`) y P2 (a E58), pendientes del usuario; P3 ya estaba
2. 2026-11-15 — Versión `0.7.0` en `main` (`c1e75c8`): fase 3 con `gw-reviewer` (8 arreglos), B40 (`version.py --release` cuenta la recogida que trajo el parche) y textos de la release en `docs/records/release-v0.7.0.md`; la publica el usuario en local.
3. 2026-11-15 — Fase 2 de la `0.7.0`: `/gw-opt-tokens` y `/retro` (`retro-2026-11-15-release-0-7-0.md`), aprobadas por el usuario: E62 (`gw-worker` con el modelo y el esfuerzo de la llamada para todos los peldaños, nuevo `gw-reviewer` y aviso de `subagent-cap.py`), B39 (`measure.py` sin argumentos de `git config` como archivos) y B38 (barrido de `handoff.py`) a la `0.8`
4. 2026-11-15 — Fase 1 de la `0.7.0`: lo que quedaba desde el último `Findings:` (`95a54e7`) era trivial (arreglo de `test_waits.py` de `3bc4d53`, sellos de versión de `b44cd14`; la `0.6.2` fusionada ya pasó su fase 1), revisado en la sesión (B27) sin hallazgos; CI de `b44cd14` en verde y check entero en local
5. 2026-11-15 — Parche `0.6.2` (D109-D121) en `main` (`cd856ca`, CI en verde) y release `v0.6.2` publicada por el agente con `gh release create` y los textos de `docs/records/release-v0.6.2.md`; `version/0.6.2` fusionada en esta rama (propuestas de H21 con su estado de aquí, roadmap con D109-D121 hechos, leves del parche a pendientes)

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md) (84 entradas); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
