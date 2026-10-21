# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `claude/galivelop-workflow-inicio` |
| Fase en curso | **0. Verificar** (plan §9) |
| Último punto estable | Fase 0: doc oficial, pruebas y dos casos reales; notas en `docs/investigacion/` |
| Siguiente paso | Esperar la decisión del usuario sobre la distribución en la nube (probar D / respaldo A) y las claves de `gw.json` |

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

1. 2026-10-21 — Fase 0: inventario de Tarkor e Instalador-WMF-Tarkor (solo lectura) en
   `docs/investigacion/casos-reales.md`; piezas genéricas que el plan no recoge y choques con el plan.
2. 2026-10-21 — Fase 0: la nube no carga plugins declarados en el repo; `.claude/skills/` sí; repo privado como
   marketplace funciona desde la CLI. Propuesta en `docs/investigacion/plugins.md`.
3. 2026-10-21 — Sonda mínima de plugin y marketplace (`.claude-plugin/`, skills `gw-ping*`, `.claude/settings.json`).
4. 2026-10-21 — Plan guardado tal cual en `docs/plan.md` (y `docs/plan.en.md`); bitácora creada.

## Pendiente

- **Decisión del usuario:** distribución para la nube (probar D, A de respaldo) y claves de `gw.json` en inglés.
- **Decisión del usuario:** ampliar el inventario (§3) con lo de `casos-reales.md`; `check` como lista.
- Fase 0: leer Portal-Galivelop (fuente principal del plan) y compararlo con los dos casos.
- Fase 0: probar la opción D (setup script del entorno); quitar las skills `gw-ping*` al cerrar.
- A `main`, solo con confirmación del usuario.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
