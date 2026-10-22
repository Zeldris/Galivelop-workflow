# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `claude/galivelop-workflow-inicio` (`main` creada el 2026-10-21 en `f2739f1`) |
| Check | `bash tests/comprobar.sh` — en verde en local; el CI no arranca desde el bloque B (los jobs mueren en ~2 s sin pasos: ¿cuota de Actions?) |
| Fase en curso | **5. Piloto: Portal-Galivelop** (plan §9) — sin empezar; necesita una sesión del portal con permiso del usuario |
| Último punto estable | Fase 4 cerrada: un agente sin contexto aplicó el flujo a un proyecto Python vacío solo con `docs/en/apply.md` (doctor sin FAIL, idempotente, push por los ganchos, subida a `main` sin marca rechazada); guía corregida con lo que encontró |
| Siguiente paso | Usuario: decidir el CI (cuota de Actions) y si se sube a `main` (con `/code-review` antes); después, Fase 5 en una sesión del portal |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; falta ver el CI en verde)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [ ] 5. Piloto: Portal-Galivelop
- [ ] 6. Piloto: Tarkor, instalador y VeriNews
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.1.0` sin publicar. `main` existe (en el cierre de la Fase 0); la rama por defecto en GitHub sigue siendo la de
trabajo hasta que el usuario la cambie en Settings → Branches.

## Hecho (10 últimas)

1. 2026-10-22 — **Fase 4 cerrada.** Plantillas ES/EN, `aplicar.py --init`, guías y skills `gw-*`; prueba con un agente sin
   contexto sobre un repo vacío superada; 9 puntos de la guía corregidos.
2. 2026-10-22 — Fase 3 completa en local: config, ganchos de subida y de PR, arranque y recuperación, `doctor.py`,
   utilidades y `aplicar.py`; el flujo ya se aplica a este repo (sus propios `pre-commit` y `pre-push` activos).
3. 2026-10-21 — **Fase 2 cerrada.** Skills portadas y validadas (Agent Skills, ≤200 líneas, mención a Matt Pocock);
   `opt-ai` añadida como opcional a petición del usuario; `gw-harvest` + `recoger.py`; primera recogida real.
4. 2026-10-21 — **Fase 1 cerrada** (CI en verde en Linux y macOS). VeriNews_AI leído en solo lectura: cuarto caso
   y piloto sin Node; aporta el gancho de PR por Bash, el pre-commit antisecretos y `registro_sesion.py`.
5. 2026-10-21 — Fase 1: esqueleto (LICENSE, `.gitattributes`, README ES/EN, CHANGELOG `0.1.0`, `docs/es/flujo.md` ↔
   `docs/en/workflow.md`, `tests/test_repo.py`, `tests/comprobar.sh`, CI `comprobar.yml`). Plan: skill `gw-harvest`.
6. 2026-10-21 — **Fase 0 cerrada.** Plan revisado (§0: dos etapas, copia en el repo como base, `AGENTS.md`,
   claves en inglés, `check` como lista, marca versionada, portar pieza a pieza). `AGENTS.md` + `CLAUDE.md` de este
   repo. Sondas `gw-ping*` y `.claude/settings.json` de prueba quitadas.
7. 2026-10-21 — Fase 0: estándares (AGENTS.md, Agent Skills, Copier), mejoras y problemas conocidos en
   `docs/investigacion/estandares.md`.
8. 2026-10-21 — Fase 0: Portal-Galivelop leído (solo lectura) y tabla de la mejor versión de cada pieza.
9. 2026-10-21 — Fase 0: inventario de Tarkor e Instalador-WMF-Tarkor (solo lectura) en
   `docs/investigacion/casos-reales.md`; piezas genéricas que el plan no recoge y choques con el plan.
10. 2026-10-21 — Fase 0: la nube no carga plugins declarados en el repo; `.claude/skills/` sí; repo privado como
   marketplace funciona desde la CLI. Propuesta en `docs/investigacion/plugins.md`.

## Pendiente

- Propuestas aprobadas pendientes por fase: `docs/propuestas/2026-10-21-reparto.md`.

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
