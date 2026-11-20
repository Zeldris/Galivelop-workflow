# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9`: `ccr-d1e2d496-0vzck8`**, con `main` fusionado. `main` = `4ca45d0` = **`0.8.1`**. `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.8.1` publicada** (`main` = `4ca45d0`, 2026-11-19; CI en verde; etiqueta y release `v0.8.1` creadas desde una sesión local) |
| Siguiente paso | **`0.9` «Front»**: la recogida de apertura (H24) ya está hecha; las tareas de la recogida ya están (E65-E77; bloques E65-E71 y E72-E74 revisados, 2026-11-20; E75-E77 sin revisar), así que sigue A12 (decidida: Q-10 a Q-16 respondidas; ficha `docs/tasks/A12.md`; trozos: 1 esquema y 2a (scripts que leían `language`) hechos; por hacer 2b (doctor, names-check, REVIEW, test_repo, skills, sesión) y 3 idioma del agente; el 2b quita las vistas `language`/`visibleLanguages` de `config.compat_views`) y luego E4, E5, E7, E9-E16, E42 y E50. **Al cerrar el desarrollo de la `0.9`, antes de publicarla:** recogida y `0.8.2` (D142 y los arreglos que traiga; preguntas Q-4 a Q-6). Presupuesto de compactaciones: 1 (A12) |

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

1. 2026-11-20 — A12 trozo 2a: `apply.py`, `commit-message.py`, `reviewed.sh`, `merge-branch.sh`, `backport.sh`, `handoff.py`, `merge-main.py` y `task.py` leen `languages.docs.primary` en vez de `language`; una prueba de esquema 2 cada uno
2. 2026-11-20 — A12 trozo 1, revisión: 6 hallazgos arreglados (respaldo `en` de plantillas, `--init` valida con `semantic_errors`, `ui` admite etiquetas BCP 47, migración con `languages` no objeto, pista ISO solo de patrón con `--root`, `--code-language` de un solo valor)
3. 2026-11-20 — A12 trozo 1: bloque `languages` en `gw.json` (`schemaVersion` 2, migración de `language`/`visibleLanguages`, validación ISO 639-1, `config.languages()`), `apply.py --init` con `--code-language`/`--docs-language`/`--public-language`; tests en `test_config.py` y `test_apply.py`
4. 2026-11-20 — E76: `measure.py` (`gw-opt-tokens`) muestra aparte el arranque fijo (sistema, herramientas, MCP, con la estimación de `context_guard.py`) por llamada × llamadas y el coste del proyecto (el resto); sin `context_guard.py`, `Fixed startup: unknown`; tests en `test_measure.py`
5. 2026-11-20 — E75: `grilling` (sección del flujo) apunta cada ronda en el archivo de preguntas con `questions.py add` (respuestas vacías), la sube con la bitácora nombrando sus `Q-<n>` y solo entonces la presenta, numerada con esos ids; test en `test_skills.py`

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
