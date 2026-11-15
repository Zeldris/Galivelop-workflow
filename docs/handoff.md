# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.7` «Preguntar»: `ccr-d1e2d496-0vzck8`** (hace de `version/0.7.0`), con `main` fusionado. `main` = `cd856ca` = **`0.6.2`** (2026-11-15, etiqueta y release `v0.6.2`). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.6.2` en `main`** (`cd856ca`, 2026-11-15; CI en verde). Etiqueta y release `v0.6.2` creadas por el agente desde una sesión local (`gh release create`, 2026-11-15) con los textos de `docs/records/release-v0.6.2.md` |
| Siguiente paso | Cerrar la **`0.7.0`** en esta rama: repaso de la documentación (CHANGELOG, README, `docs/es` ↔ `docs/en`, roadmap), `/code-review` contra `origin/main`, fases 2 y 3 y publicación. E58-E61, a la `0.8`. Presupuesto de compactaciones: 1 |

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

1. 2026-11-15 — Parche `0.6.2` (D109-D121) en `main` (`cd856ca`, CI en verde) y release `v0.6.2` publicada por el agente con `gh release create` y los textos de `docs/records/release-v0.6.2.md`; `version/0.6.2` fusionada en esta rama (propuestas de H21 con su estado de aquí, roadmap con D109-D121 hechos, leves del parche a pendientes)
2. 2026-11-15 — Recogida de cierre de la `0.7` (H21) sobre 9 proyectos: 5 traen ideas, 4 sin nada nuevo; 15 propuestas (`docs/proposals/2026-11-15-*.md`): D109-D115 (arreglos) al parche `0.6.2`, E58-E61 a la `0.8`, 4 no aprobadas (usuario). La P3 del portal se une a la P3 de world-maker-fantasy (avisos de lectura por Bash); `pending.md` B2 deja de decir que `apply.py` no pone `merge=union` (B32)
3. 2026-11-15 — Revisión de B37+E56+E57 (desde `f18432c`): 6 arreglos (las órdenes `sleep` de dos tests de `test_check_summary` escalan con su espera; `wait_for` devuelve el valor del predicado; el CI elige el factor por `runner.os`; el gancho de E56 acaba en `|| true`; regla de `testMap` para `tests/waits.py`; el escáner ve `timeout = n`; los tests de `WaitFor` quitan el factor del entorno, que en el CI de macOS movía sus plazos simulados), 3 leves a pendientes y 1 rechazado (`GW_TEST_TIMEOUT_SCALE` es de los tests de este repo, no una clave de proyecto)
4. 2026-11-15 — E57: la skill `retro`, en su sección del flujo, propone al cerrar un bloque o versión una tarea `B` de barrido con los leves de `pendingFile` del script que más tenga (mejor uno que tocó el bloque), para la siguiente versión no empezada; el usuario elige cuáles entran. Copia en `.claude/skills/retro/`; test en `tests/test_skills.py`
5. 2026-11-15 — E56: gancho `PreToolUse` `scripts/generated-copy.py` sobre `Edit`/`Write`/`MultiEdit`/`NotebookEdit` que, solo en este repo (en `WORKFLOW_ONLY_SCRIPTS`; registrado en `.claude/settings.json`, no en la plantilla), avisa sin bloquear al editar una copia generada (`.claude/gw/scripts/`, `.claude/gw/schema/`, `.claude/skills/`, `.githooks/`, `.claude/agents/`) con la ruta de su fuente; las notas de `.claude/gw/*.md` no cuentan. 8 tests

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md) (84 entradas); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
