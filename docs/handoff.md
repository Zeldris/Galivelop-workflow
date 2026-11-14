# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.6` «Medir»: `ccr-d1e2d496-0vzck8`** (hace de `version/0.6.0` mientras la sesión solo pueda subir a esta rama). `main` = `a1a9705` = **`0.6.0`** (2026-11-14, etiqueta y release `v0.6.0`). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.6.0` en `main`** (`a1a9705`, 2026-11-14), CI en verde. Etiqueta y release `v0.6.0` creadas por el agente desde una sesión local (`gh release create`, 2026-11-14) con los textos de `docs/records/release-v0.6.0.md`. Fusionada `version/0.5.2` (traía `docs/records/release-v0.5.2.md`) |
| Siguiente paso | **Parche `0.6.1`**: D97-D108 hechas; fases 1 y 2 hechas (retro `docs/records/retro-2026-11-14-patch-0-6-1.md`, T2 aplazada). Ola D104-D108 fusionada y revisada (4 medios arreglados; leves en `docs/records/pending.md`), check completo en verde. **Ahora, fase 3:** `/code-review` en un subagente limpio del diff desde `c44d5cb` (D104-D108), arreglos con `Findings:`, luego `bash scripts/reviewed.sh` y subida a `main` con confirmación del usuario; después `docs/records/release-v0.6.1.md` y la `0.7` (E51, E52, B36 y E41 ampliada). Presupuesto de compactaciones: 1 (va 1 en esta sesión: tras cerrar, `/clear`). |

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

## Hecho (5 últimas)

1. 2026-11-14 — D104-D106, D108: «Pendiente» sale a `pendingFile` (`move-pending`, `check --strict`); `roadmap.py check` compara los ids de los dos roadmaps; `tests-for.py --run` pasa shellcheck a los `.sh` cambiados; el `commit-msg` pide `/clear` al cerrar fase o versión con el presupuesto pasado. Revisión: 4 medios arreglados, leves a pendientes
2. 2026-11-14 — D107: el encargo del dealer pide la subida final en primer plano y la sesión principal para con `TaskStop` al subagente que no vuelve con su commit ya subido
3. 2026-11-14 — Fase 2 del parche `0.6.1`: medida de `/gw-opt-tokens` y retro; aprobadas T1, R1, R2, R3 y T3 (D104-D108), T2 aplazada
4. 2026-11-14 — Fase 1 del parche `0.6.1`: `/code-review` contra `main`, 10 hallazgos arreglados con sus tests en `apply.py`, `harvest.py`, `red-without-fix.sh` y `commit-message.py` (detalle en el commit `fix(D101)`)
5. 2026-11-14 — D97, D98, D100, D101: el commit-msg rechaza Findings/Retries fuera del bloque de trailers; red-without-fix.sh aparta el arreglo en una copia bajo .git, sin git stash; apply.py no avisa de nombres viejos en el roadmap ni propone nombres inexistentes; harvest descarta ideas cuyas líneas ya estaban en la última recogida. Parche 0.6.1 completo (D97-D103)

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md) (67 entradas); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
