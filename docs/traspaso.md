# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `claude/galivelop-workflow-inicio` (`main` creada el 2026-10-21 en `f2739f1`) |
| Check | `bash tests/comprobar.sh` — en verde en local |
| Fase en curso | **1. Esqueleto** (plan §9, etapa 1) — hecho a falta del CI en verde |
| Último punto estable | Fase 1: LICENSE, README ES/EN, CHANGELOG `0.1.0`, `plugin.json` 0.1.0, `tests/comprobar.sh` y CI (Linux + macOS); `gw-harvest` añadida al plan |
| Siguiente paso | Comprobar el CI en GitHub; si está en verde, cerrar la Fase 1 y empezar la 2 (skills) |

### Fases

- [x] 0. Verificar (2026-10-21)
- [ ] 1. Esqueleto
- [ ] 2. Skills
- [ ] 3. Ganchos y scripts
- [ ] 4. Plantillas y aplicación
- [ ] 5. Piloto: Portal-Galivelop
- [ ] 6. Piloto: Tarkor e instalador
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.1.0` sin publicar. `main` existe (en el cierre de la Fase 0); la rama por defecto en GitHub sigue siendo la de
trabajo hasta que el usuario la cambie en Settings → Branches.

## Hecho (10 últimas)

1. 2026-10-21 — Fase 1: esqueleto (LICENSE, `.gitattributes`, README ES/EN, CHANGELOG `0.1.0`, `docs/es/flujo.md` ↔
   `docs/en/workflow.md`, `tests/test_repo.py`, `tests/comprobar.sh`, CI `comprobar.yml`). Plan: skill `gw-harvest`.
2. 2026-10-21 — **Fase 0 cerrada.** Plan revisado (§0: dos etapas, copia en el repo como base, `AGENTS.md`,
   claves en inglés, `check` como lista, marca versionada, portar pieza a pieza). `AGENTS.md` + `CLAUDE.md` de este
   repo. Sondas `gw-ping*` y `.claude/settings.json` de prueba quitadas.
3. 2026-10-21 — Fase 0: estándares (AGENTS.md, Agent Skills, Copier), mejoras y problemas conocidos en
   `docs/investigacion/estandares.md`.
4. 2026-10-21 — Fase 0: Portal-Galivelop leído (solo lectura) y tabla de la mejor versión de cada pieza.
5. 2026-10-21 — Fase 0: inventario de Tarkor e Instalador-WMF-Tarkor (solo lectura) en
   `docs/investigacion/casos-reales.md`; piezas genéricas que el plan no recoge y choques con el plan.
6. 2026-10-21 — Fase 0: la nube no carga plugins declarados en el repo; `.claude/skills/` sí; repo privado como
   marketplace funciona desde la CLI. Propuesta en `docs/investigacion/plugins.md`.
7. 2026-10-21 — Sonda mínima de plugin y marketplace (`.claude-plugin/`, skills `gw-ping*`, `.claude/settings.json`).
8. 2026-10-21 — Plan guardado tal cual en `docs/plan.md` (y `docs/plan.en.md`); bitácora creada.

## Pendiente

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
