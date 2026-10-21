# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `claude/galivelop-workflow-inicio` |
| Fase en curso | **0. Verificar** (plan §9) |
| Último punto estable | Fase 0: doc oficial, pruebas, tres casos reales y estándares; notas en `docs/investigacion/` |
| Siguiente paso | Esperar la decisión del usuario: plan en dos etapas (agente → instalador sin IA) y decisiones abiertas |

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

1. 2026-10-21 — Fase 0: estándares (AGENTS.md, Agent Skills, Copier), mejoras y problemas conocidos en
   `docs/investigacion/estandares.md`.
2. 2026-10-21 — Fase 0: Portal-Galivelop leído (solo lectura) y tabla de la mejor versión de cada pieza.
3. 2026-10-21 — Fase 0: inventario de Tarkor e Instalador-WMF-Tarkor (solo lectura) en
   `docs/investigacion/casos-reales.md`; piezas genéricas que el plan no recoge y choques con el plan.
4. 2026-10-21 — Fase 0: la nube no carga plugins declarados en el repo; `.claude/skills/` sí; repo privado como
   marketplace funciona desde la CLI. Propuesta en `docs/investigacion/plugins.md`.
5. 2026-10-21 — Sonda mínima de plugin y marketplace (`.claude-plugin/`, skills `gw-ping*`, `.claude/settings.json`).
6. 2026-10-21 — Plan guardado tal cual en `docs/plan.md` (y `docs/plan.en.md`); bitácora creada.

## Pendiente

- **Decisión del usuario:** distribución para la nube (probar D, A de respaldo) y claves de `gw.json` en inglés.
- **Decisión del usuario:** ampliar el inventario (§3) con lo de `casos-reales.md`; `check` como lista.
- **Decisión del usuario:** portar pieza a pieza (tabla de `casos-reales.md`) en vez de «del portal».
- Fase 0: probar la opción D (setup script del entorno); quitar las skills `gw-ping*` al cerrar.
- **Decisión del usuario:** plan en dos etapas (etapa 1: un agente aplica el flujo leyendo el repo; etapa 2:
  instalador sin IA), `AGENTS.md` como fuente de reglas.
- A `main`, solo con confirmación del usuario.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
