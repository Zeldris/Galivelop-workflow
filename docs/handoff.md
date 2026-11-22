# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9`: `ccr-d1e2d496-0vzck8`**, con `main` fusionado. `main` = `a725647` = **`0.8.2`** (fusionada aquí). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.8.2` publicada** (`main` = `a725647`, 2026-11-22; las tres fases hechas, retro decidida; release `v0.8.2` de GitHub publicada desde una sesión local del usuario) y fusionada en la `0.9` |
| Siguiente paso | **Cerrar la `0.9`** (E84-E86 hechas): los leves de `pending.md` marcados `0.9` y las fases antes de `main`. Q-7 y Q-8 esperan al usuario. E79-E83 van a la `1.0`. Presupuesto de compactaciones: 2 |

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

1. 2026-11-22 — E86 (P4 de la retro de la `0.8.2`): clave nueva `review.splitLines` (objeto `review`, defecto 600 líneas cambiadas sin lo `vendored`, 0 = nunca reparte; `config.py review_split_lines`, esquema, plantilla y `docs/{es,en}/config.md`); `gw-orchestrate-dealer` reparte la revisión de fase 1 por encima de ese tope en dos o más revisores por grupos de `review-scope.py` más uno corto que cruza los contratos. Test nuevo en `test_config.py` (en rojo sin el arreglo); copias aplicadas. Revisión: 5 hallazgos arreglados (excepción de un arreglo de un archivo restaurada, cómo contar las líneas y que un diff trivial nunca se reparte, clave en el `.claude/gw.json` del repo, caso del CLI).
2. 2026-11-22 — E85 (P3 de la retro de la `0.8.2`): `whole-read.py` avisa también de un rango largo por `Bash` (`sed -n A,Bp`, `head -n N`) del `log` o de un `roadmapFiles` por encima de `wholeReadWarnBytes` con `recover.py --state` o `roadmap.py show <id>`; un rango de `wholeReadShortLines` líneas o menos (clave nueva, 40) se calla; `cat` de un `roadmapFiles` también avisa; arreglado que `head -n 80 < F` tomara el 80 por descriptor. Tests en `test_whole_read.py` (clase `Ranges`); el matcher de `Bash` ya estaba en el gancho.
3. 2026-11-22 — E84 (P1 de la retro de la `0.8.2`): `push.sh --wip <rama>` sube un último commit `WIP:` sin esperar al check, nunca a la rama protegida ni sin `WIP:` (falla con el motivo); el `pre-push` lo deja pasar con `GW_PUSH_WIP=1` y lo apunta en `<git dir>/gw-wip-pushes`; `before-stop.py` lo recomienda con commits sin subir y último `WIP:`. la revisión (4 hallazgos: `--wip` mantiene private-check, authorDeny, spike y conflictos; config inválida; `--no-follow-tags`; pista solo con `push.sh` que lo admita y sin verde apuntado) arreglada; 13 tests de gancho y 4 del Stop, en rojo sin el arreglo; docs es/en en `config.md`
4. 2026-11-22 — `0.8.2` publicada en `main` (`a725647`), release `v0.8.2` publicada y fusionada en la `0.9` (H26): conflictos resueltos con la forma `languages.docs.primary` de A12, preguntas de la `0.9` renumeradas de Q-7..Q-36 a Q-9..Q-38 (Q-7 y Q-8 son las de la `0.8.2`), copias instaladas regeneradas. Release `v0.8.2` de GitHub publicada (desde una sesión local del usuario).
5. 2026-11-22 — `0.8.2` subida a `main` (`a725647`): fase 1 (D142 medio arreglado, 5 menores a `pending.md`), fase 2 (retro con 6 propuestas aprobadas: P2 aplicada en `REVIEW.md`, P1/P3/P4 a la `0.9`, P6 a la `0.10`) y fase 3 (`reviewed.sh`). Textos de la release en `docs/records/release-v0.8.2.md`; la release, desde una sesión local.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
