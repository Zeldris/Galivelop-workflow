# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **Parche `0.8.2`: `version/0.8.2`**, desde `main` (`4ca45d0` = **`0.8.1`**). La `0.9` sigue en `ccr-d1e2d496-0vzck8`. `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **Oleada 1 de la `0.8.2` fusionada** (D142, D144, D145, D147, D149-D152, D154, D157-D160; check completo en verde, 841 tests) y versión subida a `0.8.2` (CHANGELOG a medias). `main` = `4ca45d0` = `0.8.1` |
| Siguiente paso | **Parche `0.8.2`, oleada 2** con `gw-orchestrate-dealer` (worktrees desde la punta actual): D146, D148+D164 (plantillas `AGENTS.md` y guía de instalación), D153, D155, D156 (toca `session-start.sh`, tras D142), D161, D162, D163, D165, D166; cada rama con su revisión, la última fusión sin `--defer-check`. Luego revisión `MISSING_ITEMS` de la oleada, CHANGELOG/README de la `0.8.2`, fases antes de `main`, publicar, fusionar en la `0.9` (ojo: clave `language` en `main` frente a `languages.docs.primary` de A12) y cerrarla. Q-7 y Q-8 esperan al usuario. Presupuesto de compactaciones: 2 |

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

1. 2026-11-22 — Oleada 1 de la `0.8.2`: D142/D147 (el selector para si el modelo o el esfuerzo no casan; `models.py session-check` al arrancar), D144/D145/D151 (`measure.py` mide la sesión en curso y no otra rama), D149/D150 (`scope-guard.py`), D152/D160 (`tests-for.py`, `ci-local.py`), D154/D157 (`handoff.py`), D158/D159 (`doctor.py`); cada rama revisada (Findings: 4+4+2 aceptados; menores a `pending.md`). Versión a `0.8.2`; quitado el resto `skills/gw-seo/` (solo `.pyc` de la `0.9`) que rompía `test_skills`.
2. 2026-11-22 — Rama `version/0.8.2` abierta desde `main`: filas D142-D166 y H26 del roadmap es/en, propuestas de H26 (`docs/proposals/2026-11-22-*.md`), Q-4 a Q-6 y el fallo de `measure.py` renombrado a D144 en `pending.md`
3. 2026-11-19 — Fase 2 de la `0.8.1`: `/gw-opt-tokens` y `/retro` decididas por el usuario (P3-P4 aplicadas; D142, D143 y B47 apuntados en `pending.md`).
4. 2026-11-19 — Fase 1 del 0.8.1 (revisión del bloque D141/H25): 2 hallazgos aceptados (doc de metrics.py y config.md: cuenta por id y cierre por merge) y 3 leves a pendientes de la 0.10.
5. 2026-11-19 — Sello del parche 0.8.1 (H25): CHANGELOG es/en con D128-D141, README en 0.8.1, version.py 0.8.1 y apply.py .; check completo en verde sobre 9feae0a antes del sello.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
