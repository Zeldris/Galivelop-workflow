# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-76251061-b1yiwq` (sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `9b97d7b` = **release `v0.1.0`** (2026-10-22) |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **5. Piloto: Portal-Galivelop** — hecho y publicado en el `main` del portal (`673602b`); recogida hecha, 21 propuestas pendientes de decisión |
| Último punto estable | Tercera recogida de Tarkor (`11a201b7`→`76ec6aeb`) en `docs/propuestas/2026-10-22-world-maker-fantasy-2.md` (4 propuestas patch para `orchestrate-dealer`); la del portal (21 propuestas, P1 grave) sigue pendiente de decisión |
| Siguiente paso | **Esperando la decisión del usuario** sobre las propuestas del portal (`2026-10-22-portal-galivelop.md`, empezar por P1: leer la política de la rama protegida remota, no del commit subido, y contar `gw.json` como código) y las 4 de Tarkor (`2026-10-22-world-maker-fantasy-2.md`). Luego aplicar lo aprobado con `orchestrate-dealer`, tres fases y `v0.1.1` |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [ ] 5. Piloto: Portal-Galivelop
- [ ] 6. Piloto: Tarkor, instalador y VeriNews
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.1.0` publicada. Para la siguiente: `release.yml` con lanzamiento manual desde Actions que cree la etiqueta (la
sesión en la nube no puede subir etiquetas: 403 del proxy).

## Hecho (10 últimas)

1. 2026-10-22 — Tercera recogida de Tarkor (`76ec6aeb`, 99 commits): 4 propuestas para `orchestrate-dealer` (arreglos con
   `sonnet`, arreglos de un archivo en la principal, solo lo grave antes del PR, rama de partida del worktree).
2. 2026-10-22 — **Release `v0.1.0`** (`9b97d7b`): segunda subida a `main` con las tres fases; segunda recogida de Tarkor
   aplicada; `version.py` y `release.yml`.
3. 2026-10-22 — **Primera subida a `main`** (`603ca36`) siguiendo las tres fases del flujo.
4. 2026-10-22 — **Fase 4 cerrada.** Plantillas ES/EN, `aplicar.py --init`, guías y skills `gw-*`; prueba con un agente sin
   contexto sobre un repo vacío superada; 9 puntos de la guía corregidos.
5. 2026-10-22 — Fase 3 completa en local: config, ganchos de subida y de PR, arranque y recuperación, `doctor.py`,
   utilidades y `aplicar.py`; el flujo ya se aplica a este repo (sus propios `pre-commit` y `pre-push` activos).
6. 2026-10-21 — **Fase 2 cerrada.** Skills portadas y validadas (Agent Skills, ≤200 líneas, mención a Matt Pocock);
   `opt-ai` añadida como opcional a petición del usuario; `gw-harvest` + `recoger.py`; primera recogida real.
7. 2026-10-21 — **Fase 1 cerrada** (CI en verde en Linux y macOS). VeriNews_AI leído en solo lectura: cuarto caso
   y piloto sin Node; aporta el gancho de PR por Bash, el pre-commit antisecretos y `registro_sesion.py`.
8. 2026-10-21 — Fase 1: esqueleto (LICENSE, `.gitattributes`, README ES/EN, CHANGELOG `0.1.0`, `docs/es/flujo.md` ↔
   `docs/en/workflow.md`, `tests/test_repo.py`, `tests/comprobar.sh`, CI `comprobar.yml`). Plan: skill `gw-harvest`.
9. 2026-10-21 — **Fase 0 cerrada.** Plan revisado (§0: dos etapas, copia en el repo como base, `AGENTS.md`,
   claves en inglés, `check` como lista, marca versionada, portar pieza a pieza). `AGENTS.md` + `CLAUDE.md` de este
   repo. Sondas `gw-ping*` y `.claude/settings.json` de prueba quitadas.
10. 2026-10-21 — Fase 0: estándares (AGENTS.md, Agent Skills, Copier), mejoras y problemas conocidos en
   `docs/investigacion/estandares.md`.

## Pendiente

- Propuestas aprobadas pendientes por fase: `docs/propuestas/2026-10-21-reparto.md`.

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
