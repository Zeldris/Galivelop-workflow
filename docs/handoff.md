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
| Último punto estable | **`0.8.0` publicada** (`main` = `b3825b8`, 2026-11-18; CI en verde; etiqueta y release `v0.8.0` creadas desde una sesión local) |
| Siguiente paso | **Parche `0.8.1` sellado** (H25: D128-D141, CHANGELOG, README, `version.py 0.8.1` y `apply.py .`; check completo en verde antes del sello). Ahora las fases antes de `main` (revisión del bloque desde el último `Findings:`, `/gw-opt-tokens`, `/retro`, `reviewed.sh`), con confirmación del usuario; luego `0.9` (E65-E76). Presupuesto de compactaciones: 0 |

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

1. 2026-11-19 — Sello del parche 0.8.1 (H25): CHANGELOG es/en con D128-D141, README en 0.8.1, version.py 0.8.1 y apply.py .; check completo en verde sobre 9feae0a antes del sello.
2. 2026-11-19 — D141: el Findings: de un merge cierra el bloque de revisión y cuenta en metrics.py quality (antes --no-merges lo ignoraba y recover.py --state avisaba de una revisión ya hecha); visto al empezar el cierre del 0.8.1.
3. 2026-11-19 — Segunda oleada del 0.8.1 fusionada (D129+D130, D135, D137) y revisada: 7 hallazgos arreglados (guarda de filas de handoff.py, pendingFile de apply.py) y 5 leves a pendientes de la 0.10.
4. 2026-11-19 — Revisión del bloque de la primera oleada del 0.8.1: 11 hallazgos aceptados y arreglados (uno descartado por falso), entre ellos scope-guard llamaba a workflow_dir con la firma vieja y apagaba B44 sin aviso; claves nuevas workflowRepository y workflowClone. Check de la oleada en verde salvo la copia del esquema, arreglada.
5. 2026-11-18 — Primera oleada del parche 0.8.1 fusionada: D128 (gancho duplicado por cambio de matcher; doctor lo detecta), D131, D132 (review-scope.py busca la copia del flujo o falla con la orden), D133, D134, D136, D138, D139 y D140. D131 dejó las plantillas en 151 líneas (tope 150), arreglado. Conflicto del roadmap en D132, resuelto.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
