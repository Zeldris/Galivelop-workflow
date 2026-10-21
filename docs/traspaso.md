# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `claude/galivelop-workflow-inicio` |
| Fase en curso | **0. Verificar** (plan §9) |
| Último punto estable | Plan guardado en `docs/plan.md` y bitácora creada |
| Siguiente paso | Fase 0: leer la doc oficial de plugins, marketplaces y hooks; anotar en `docs/investigacion/plugins.md` |

### Fases

- [ ] 0. Verificar
- [ ] 1. Esqueleto
- [ ] 2. Skills
- [ ] 3. Ganchos y scripts
- [ ] 4. Plantillas e init
- [ ] 5. Piloto: Portal-Galivelop
- [ ] 6. Piloto: Tarkor
- [ ] 7. Rodaje
- [ ] 8. Público

## Para la próxima publicación

Nada aún (no hay versión publicada; `main` no existe todavía).

## Hecho (10 últimas)

1. 2026-10-21 — Plan guardado tal cual en `docs/plan.md` (y `docs/plan.en.md`); bitácora creada.

## Pendiente

- Fase 0: responder las dudas de la §8 del plan (repo privado como marketplace en la nube; nombres exactos de
  campos de `plugin.json`, `marketplace.json`, `hooks.json`) y decidir si las claves de `gw.json` pasan a inglés.
- A `main`, solo con confirmación del usuario.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
