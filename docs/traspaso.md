# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-76251061-b1yiwq` (sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `9b97d7b` = **release `v0.1.0`** (2026-10-22) |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **5. Piloto: Portal-Galivelop** — publicado en el portal (`673602b`); propuestas decididas (2026-10-22), aplicándolas para `v0.2.0` |
| Último punto estable | Reparto filas 1-3 (Portal P1, P16 y P9) hechas; P9: el `content` de la plantilla ya no cubre scripts de skills ni `.md` fuera de `docs/` y la raíz |
| Siguiente paso | Fila 4 del reparto: **Portal P2 (a, b)** (versión obligatoria si cambia algo copiable; mensajes «edición local o copia anterior»). Luego las filas 5-19 en orden; tres fases y `v0.2.0` (la entrada `0.2.0` del CHANGELOG se escribe al publicar, con las filas hechas) |

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

1. 2026-10-22 — Portal P9: `content` por defecto `^docs/`, los `.md` de documentación de la raíz y los `.md` de
   `.claude/skills/`; guías ES/EN alineadas y test con rutas que deben ser código.
2. 2026-10-22 — Portal P16: el `pre-push` busca marcadores y `*.rej`/`*.orig` en `base..local` al subir a la rama
   protegida (también commits ya subidos a otra rama); 3 casos nuevos en los tests.
3. 2026-10-22 — Portal P1: `pre-push` y gancho de PR leen `content`/`reviewMark` (y si la rama es protegida) de la
   punta remota de la rama protegida; las rutas del flujo son siempre código; 11 casos nuevos en los tests.
4. 2026-10-22 — Decididas las 25 propuestas pendientes (portal y Tarkor): 22 aprobadas, 3 aplazadas; reparto para `v0.2.0`.
5. 2026-10-22 — Tercera recogida de Tarkor (`76ec6aeb`, 99 commits): 4 propuestas para `orchestrate-dealer` (arreglos con
   `sonnet`, arreglos de un archivo en la principal, solo lo grave antes del PR, rama de partida del worktree).
6. 2026-10-22 — **Release `v0.1.0`** (`9b97d7b`): segunda subida a `main` con las tres fases; segunda recogida de Tarkor
   aplicada; `version.py` y `release.yml`.
7. 2026-10-22 — **Primera subida a `main`** (`603ca36`) siguiendo las tres fases del flujo.
8. 2026-10-22 — **Fase 4 cerrada.** Plantillas ES/EN, `aplicar.py --init`, guías y skills `gw-*`; prueba con un agente sin
   contexto sobre un repo vacío superada; 9 puntos de la guía corregidos.
9. 2026-10-22 — Fase 3 completa en local: config, ganchos de subida y de PR, arranque y recuperación, `doctor.py`,
   utilidades y `aplicar.py`; el flujo ya se aplica a este repo (sus propios `pre-commit` y `pre-push` activos).
10. 2026-10-21 — **Fase 2 cerrada.** Skills portadas y validadas (Agent Skills, ≤200 líneas, mención a Matt Pocock);
   `opt-ai` añadida como opcional a petición del usuario; `gw-harvest` + `recoger.py`; primera recogida real.

## Pendiente

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
