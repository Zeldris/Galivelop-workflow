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
| Siguiente paso | Grupo A de la `0.8` cerrado (D96, D61, D62, B31; cada uno revisado y con sus arreglos; CI de `6f533fa` en verde, 2026-11-17). Siguiente: decidir con el usuario `contextGuard.window` de este repo (sin ella B31 calla aquí) y elegir el siguiente grupo de la `0.8`. Presupuesto de compactaciones: 1 |

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

1. 2026-11-17 — Arreglos de la revisión de B31 (5 hallazgos): el aviso va como `block` con `reason` (el `systemMessage` solo lo ve el usuario), una vez por tramo, sin bucle por `stop_hook_active`; solo con la ventana conocida (`cutoff`/`window` escritos en `contextGuard` o id `[1m]`: el transcript no trae `[1m]`); texto distinto con el presupuesto justo gastado o ya superado; mira primero la cola acotada (`stopTranscriptBytes`) y el corte. N.º 5 (marcador único por git dir), a `pending.md` (`0.8`).
2. 2026-11-17 — B31: el gancho `Stop` (`before-stop.py`) avisa *antes* de la próxima compactación, sin bloquear: con el presupuesto de compactaciones de la tarea ya gastado y el contexto del tramo (último turno del transcript) en `contextGuard.nearRatio` (0,8; 0 = apagado) del corte, una línea propone cerrar el paso (bitácora, commit y push, `/clear`; si pesa más el sistema, D122, que `/clear` no lo baja); una vez por tramo (`<git dir>/gw-context-warn`), calla si no lee el transcript. `context_guard.near_cutoff(_once)`, `recover.budget_count`; 15 tests nuevos.
3. 2026-11-17 — Arreglos de la revisión de D62 (5 hallazgos): el aviso de CI del `pre-push` lee el repo de GitHub del remoto al que se sube (`--repo`; otro servidor, calla), avisa también si no ha informado ningún CI con `.github/workflows` y `ciOnPush` no `false`, no mira un push forzado, no se cuelga tras matar `gh`, y la doc da `.claude/gw/scripts/ci-status.py`. Los n.º 3, 5, 8 y 9, a `pending.md` (`0.8`). 13 tests en `PrePushCiWarn`.
4. 2026-11-17 — D62: el `pre-push`, una vez pasa, avisa sin bloquear si el último CI de una rama que se sube (su punta en el remoto; no borrados, ramas nuevas ni etiquetas) está en rojo o GitHub no lo arrancó, con el commit y `ci-status.py --sha … --failed`; verde, en marcha, sin CI, sin `gh`/token o error, calla; claves nuevas `prepushCiWarn` (true) y `prepushCiWarnTimeout` (10 s en total; pasado, una línea). 8 tests nuevos en `test_hooks.PrePushCiWarn` con `ci-status.py` simulado.
5. 2026-11-17 — Arreglos de la revisión de D96 + D61 (4 hallazgos): `preflight` pide un commit nuevo si la bitácora ya está commiteada, no pregunta la fecha a git sin `logRows`, fecha con `--no-merges` como el `pre-push`; config.md dice «el `pre-push`, con `logRows`». Hallazgos 5 y 6, a pendiente (`0.8`).

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
