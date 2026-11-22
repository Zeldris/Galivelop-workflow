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
| Siguiente paso | **Cerrar la `0.9`** en una sesión nueva (P5 de la retro de la `0.8.2`): P1, P3 y P4 de `pending.md`, y luego las fases antes de `main`. Q-7 y Q-8 esperan al usuario. E79-E83 van a la `1.0`. Presupuesto de compactaciones: 2 |

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

1. 2026-11-22 — `0.8.2` publicada en `main` (`a725647`), release `v0.8.2` publicada y fusionada en la `0.9` (H26): conflictos resueltos con la forma `languages.docs.primary` de A12, preguntas de la `0.9` renumeradas de Q-7..Q-36 a Q-9..Q-38 (Q-7 y Q-8 son las de la `0.8.2`), copias instaladas regeneradas. Release `v0.8.2` de GitHub publicada (desde una sesión local del usuario).
2. 2026-11-22 — `0.8.2` subida a `main` (`a725647`): fase 1 (D142 medio arreglado, 5 menores a `pending.md`), fase 2 (retro con 6 propuestas aprobadas: P2 aplicada en `REVIEW.md`, P1/P3/P4 a la `0.9`, P6 a la `0.10`) y fase 3 (`reviewed.sh`). Textos de la release en `docs/records/release-v0.8.2.md`; la release, desde una sesión local.
3. 2026-11-22 — Oleada 2 de la `0.8.2`: D146/D153 (`gw-reviewer` sin `Agent`; encargo con prueba en rojo), D148/D164 (plantillas `AGENTS.md`, un repo por sesión en la nube), D155 (`findingsWords` solo con frases), D156/D166 (aviso de arranque sin la parte del sistema; filas abiertas del roadmap en `recover.py --state`), D161/D165 (`apply.py --summary` con recuento y `legacyNamesSkip`), D162/D163 (CI sin correr en un push solo del ledger; retro sin ids de letra). Findings: 1+4 aceptados; menores y un test de tiempo frágil con carga a `pending.md`.
4. 2026-11-22 — Oleada 1 de la `0.8.2`: D142/D147 (el selector para si el modelo o el esfuerzo no casan; `models.py session-check` al arrancar), D144/D145/D151 (`measure.py` mide la sesión en curso y no otra rama), D149/D150 (`scope-guard.py`), D152/D160 (`tests-for.py`, `ci-local.py`), D154/D157 (`handoff.py`), D158/D159 (`doctor.py`); cada rama revisada (Findings: 4+4+2 aceptados; menores a `pending.md`). Versión a `0.8.2`; quitado el resto `skills/gw-seo/` (solo `.pyc` de la `0.9`) que rompía `test_skills`.
5. 2026-11-22 — Rama `version/0.8.2` abierta desde `main`: filas D142-D166 y H26 del roadmap es/en, propuestas de H26 (`docs/proposals/2026-11-22-*.md`), Q-4 a Q-6 y el fallo de `measure.py` renombrado a D144 en `pending.md`

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
