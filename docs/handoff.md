# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9`: `ccr-d1e2d496-0vzck8`**, con `main` fusionado. `main` = `4ca45d0` = **`0.8.1`**. `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.8.1` publicada** (`main` = `4ca45d0`, 2026-11-19; CI en verde; etiqueta y release `v0.8.1` creadas desde una sesión local) |
| Siguiente paso | **`0.9` «Front»**: la recogida de apertura (H24) ya está hecha; tareas E66-E76 de la recogida (E65 hecha), en orden, y luego A12, E4, E5, E7, E9-E16, E42 y E50. Presupuesto de compactaciones: 0 |

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

1. 2026-11-19 — E65: scripts/merge-main.py (fetch, commit del ledger si es lo único sucio, si no se niega, merge --no-edit) con tests/test_merge_main.py (11); el paso 5 de AGENTS.md y de las plantillas apunta a él
2. 2026-11-19 — Release v0.8.1 publicada en GitHub desde una sesión local (comprobada); H25 cerrada y la rama pasa a la 0.9.
3. 2026-11-19 — `0.8.1` subida a `main` (`4ca45d0`) tras `reviewed.sh`; textos de la release en `docs/records/release-v0.8.1.md`.
4. 2026-11-19 — Fase 2 de la `0.8.1`: `/gw-opt-tokens` y `/retro` decididas por el usuario (P3-P4 aplicadas; D142, D143 y B47 apuntados en `pending.md`).
5. 2026-11-19 — Fase 1 del 0.8.1 (revisión del bloque D141/H25): 2 hallazgos aceptados (doc de metrics.py y config.md: cuenta por id y cierre por merge) y 3 leves a pendientes de la 0.10.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
