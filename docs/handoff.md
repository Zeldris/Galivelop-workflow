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
| Último punto estable | **`0.7.1` en `main`** (`7a6d1bd`, 2026-11-16; CI en verde). Etiqueta y release `v0.7.1` creadas por el agente desde una sesión local (2026-11-16, a petición del usuario) |
| Siguiente paso | Grupo B de la `0.8` cerrado (oleadas 1, 2, 3a y 3b). Mirar el CI de la subida del cierre (`python3 scripts/ci-status.py`; el de macOS vigila el `set -m` de `push.sh`) y elegir con el usuario el siguiente grupo de la `0.8` (C1-C13, D68, E32-E35, A11-A12, front E4-E16, D7/B9, E42, E50). `contextGuard.window` = 200000 en este repo (usuario, 2026-11-17). Presupuesto de compactaciones: 1 |

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

1. 2026-11-17 — Grupo B de la `0.8`, oleada 3b (worktrees en paralelo, cada rama revisada y arreglada): D14 (`trace.py --no-docs`; una fila por id con la traducción como `also`; salida separada en `declared` y `deduced`), B42 (los tests marcan sus procesos con `GW_TEST_PROC_MARK` en vez de `pgrep -f`; `tests-for.py --run` corre una sesión por unidad con la salida a archivo y `testUnitTimeout`; el cuelgue era sobrecarga, no un cerrojo), D62 (el aviso de CI del `pre-push` mata su grupo al interrumpirse, agrupa las ramas por sha, da rutas absolutas y avisa si no lee su clave) y D95 (`split_lines` respeta el fin de cada línea; cerrojo por repo en las órdenes que escriben, `handoff.lockWait`; `check.sh` corre solo `preflight --strict`). D87 y E49, marcados hechos en el roadmap. Leves de la revisión, a `pending.md` (`0.9`). Check completo y tests de la oleada en verde.
2. 2026-11-17 — Grupo B de la `0.8`, oleada 3a (worktrees en paralelo, cada rama revisada y arreglada): D87+E49 (`gw-init` ofrece licencia doble MIT + CC BY-NC-SA 4.0 con plantillas en `templates/licenses/`, sin pisar las existentes; regla «sin firmas» en el `CLAUDE.md` con `agentSignatures: false` mediante `<!-- if !clave -->`; `push.sh` y bloque `.gitignore` en la skill), D94 (`reviewed.sh` aconseja `push.sh` en vez de refspec) y B31 n.º 5 (marcador del aviso de contexto por transcript, `contextGuard.warnedMax`, cerrojo). Las plantillas de licencia, en `UNMARKED` de `version.py`. Leves, a `pending.md`. Check completo en verde.
3. 2026-11-17 — Grupo B de la `0.8`, oleada 2 (worktrees en paralelo, cada rama revisada y arreglada): D80+D126 (`doctor.py` avisa de un sello de `gw-scout-updates` caducado, `scoutMaxAgeDays`; el inventario lee la versión de Rust), D83+D127 (`apply.py --update` añade a `staleRefs` lo que renombra; `--init` escribe un bloque `.gitignore` por stack con marca, `gitignoreStacks` y `--stack`), E53+E63 (regla de CI en `patterns.md`; invariantes y «Navegadores» en la plantilla de `REVIEW.md`) y E64 (dealer). Leves de la revisión, a `pending.md`. Check completo y tests de la oleada en verde.
4. 2026-11-17 — Grupo B de la `0.8`, oleada 1 (subagentes, cada rama revisada y arreglada): D63 (`check.yml` con `workflow_call`; `release.yml` hace `verify` → `check` → `release`), D14 (`trace.py <id>`: filas, bitácora, pendiente, commits y documentos de un id o rango) y D94/D96 (`push.sh` con `pushLsRemoteTimeout`, mensajes que mandan a `push.sh`, `cellHardLimit` validado solo si se fija). Check completo y tests de la oleada en verde.
5. 2026-11-17 — Arreglos de la revisión de B31 (5 hallazgos): el aviso va como `block` con `reason` (el `systemMessage` solo lo ve el usuario), una vez por tramo, sin bucle por `stop_hook_active`; solo con la ventana conocida (`cutoff`/`window` escritos en `contextGuard` o id `[1m]`: el transcript no trae `[1m]`); texto distinto con el presupuesto justo gastado o ya superado; mira primero la cola acotada (`stopTranscriptBytes`) y el corte. N.º 5 (marcador único por git dir), a `pending.md` (`0.8`).

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
