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
| Siguiente paso | D94 hecho; siguiente: D95 (`handoff.py add-pending` y `add-decision`). Presupuesto de compactaciones: 1 |

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

1. 2026-11-16 — D94: `scripts/push.sh [<rama>]` sube con reintentos (`pushRetryDelays`, por defecto 2, 4, 8 y 16 s, solo ante fallos de red o HTTP 5xx) y da éxito solo si `git ls-remote` coincide con la rama local; un rechazo (gancho, non-fast-forward, 403) falla de inmediato con la orden que lo arregla; `AGENTS.md` y las plantillas apuntan a él
2. 2026-11-16 — Revisión del bloque E58-E61 + B41 (8 hallazgos arreglados): `whole-read.py` no cuenta la salida a un archivo o a un filtro (`| head`, `> o`), cierra el `cd` de una subshell, entiende `<<\EOF` y los valores de opción (`nl -b a`, `sed -l`), apunta dos lecturas a la vez (cerrojo) y olvida las de la sesión tras `/clear` o compactación (`recover.py --state`); `merge-branch.sh` solo escribe la oleada cuando entra su primera fusión; `handoff.py move-pending` no tira prosa que nombra `pending.md`; el aviso de `Findings:` no mira los trailers ni una negación; `context_guard` no calcula culpables si no los usa. Dos leves, a `pending.md`
3. 2026-11-16 — B41: `merge-branch.sh` guarda la base de una oleada de `--defer-check` (`<git common dir>/gw/merge-wave-<rama>`) y la fusión que la cierra corre los tests relacionados de toda ella; «nothing to merge» con la oleada abierta la cierra (y sin ofrecer deshacer `HEAD`), sin ella avisa de que no corrió nada; el dealer pide un solo check; `context_guard.Measure` lee el transcript y calcula los culpables una vez por `--state`
4. 2026-11-16 — `0.7.1` en `main` (`7a6d1bd`): CI de `64770b0` en verde, check entero en local, `reviewed.sh` y subida con confirmación del usuario; textos de la release en `release-v0.7.1.md`
5. 2026-11-16 — E58: `whole-read.py` también vigila Bash (`cat`, `sed` sin `-n` y parecidas, con `cd` y sin cuerpos de heredoc); claves `readPointers` (orden que sustituye la lectura), `wholeReadRepeatOnly` (por defecto solo avisa al releer entero un archivo sin cambios en la sesión) y `wholeReadStaleDays`

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
