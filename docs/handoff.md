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
| Siguiente paso | D62 hecho (2026-11-17; aviso del `pre-push` si el CI de la rama está en rojo; falta mirar su CI); antes, D96 + D61 cerrados con su revisión. Siguiente: elegir con el usuario la siguiente tarea de la `0.8`. Presupuesto de compactaciones: 1 |

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

1. 2026-11-17 — D62: el `pre-push`, una vez pasa, avisa sin bloquear si el último CI de una rama que se sube (su punta en el remoto; no borrados, ramas nuevas ni etiquetas) está en rojo o GitHub no lo arrancó, con el commit y `ci-status.py --sha … --failed`; verde, en marcha, sin CI, sin `gh`/token o error, calla; claves nuevas `prepushCiWarn` (true) y `prepushCiWarnTimeout` (10 s en total; pasado, una línea). 8 tests nuevos en `test_hooks.PrePushCiWarn` con `ci-status.py` simulado.
2. 2026-11-17 — Arreglos de la revisión de D96 + D61 (4 hallazgos): `preflight` pide un commit nuevo si la bitácora ya está commiteada, no pregunta la fecha a git sin `logRows`, fecha con `--no-merges` como el `pre-push`; config.md dice «el `pre-push`, con `logRows`». Hallazgos 5 y 6, a pendiente (`0.8`).
3. 2026-11-17 — D96 + D61: `handoff.cellHardLimit` (1600; 0 = apagado) hace fallar `check` sin `--strict` (y el `commit-msg` y el `pre-push`); `handoff.py preflight` corre sin subir el `check` con fecha y el `clash` con `origin/<protectedBranch>` del `pre-push`, en el `check` de la plantilla y en `tests/check.sh`.
4. 2026-11-16 — Arreglos de la revisión de D95 (8 hallazgos): `add-pending --section` es siempre un `### título` dentro de «Pendiente» (sin distinguir mayúsculas ni `#`; se crea al final de ella); `add-*` se saltan los bloques cercados, normalizan `* `/`1. ` a `- `, quitan líneas en blanco internas y fechas repetidas y comparan rutas resueltas; `decisionsFile` vale `docs/records/decisions.md` en la plantilla y en este repo (por defecto del esquema, `""`); fila de `config.md` con sus 5 celdas. Tres leves, a `pending.md`
5. 2026-11-16 — Arreglos de la revisión de D94 (5 hallazgos): `push.sh` clasifica solo las líneas de git y del remoto (la salida de un gancho `pre-push` que pasó ya no cuenta como rechazo), amplía los fallos transitorios (red inalcanzable, SSL, 408, 5xx con texto), reintenta solo la comprobación si `ls-remote` falla tras un push correcto y fija upstream y `origin/<rama>` si el remoto ya tenía el commit; fila de `pushRetryDelays` completa; n.º 5, 7 y 8 a `pending.md`

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
