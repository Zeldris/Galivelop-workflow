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
| Siguiente paso | **Cerrar la `0.9`** (E84-E86, los tres leves de D166 y los de D161/D165 y D162 hechos): los leves que quedan de `pending.md` marcados `0.9` y las fases antes de `main`. Q-7 y Q-8 esperan al usuario. E79-E83 van a la `1.0`. Presupuesto de compactaciones: 2 |

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

1. 2026-11-22 — E86/D171 (WIP; tres leves de la revisión de D166): `recover.py` admite una `v` opcional en la rama de versión (`release/v0.8.2`) y su docstring dice qué error no se esconde; filas `releaseCheckBranches` y `roadmapFiles` de `config.md` (es/en) al día; test `test_state_roadmap_line_accepts_a_v_before_the_version`. **Falta:** confirmar `test_session_log.py` y `tests/check.sh` en verde (lanzados, sin resultado aún), y marcar los tres leves en `pending.md`.
2. 2026-11-22 — D170 (medios de la revisión de E85): el test de `commandKillGrace` espera `ready.txt` (manejador instalado) y usa `commandTimeout=3`; cabecera de `whole-read.py` y filas `wholeReadShortLines` de `config.md` (es/en) dicen la excepción `cat F | head -n N`; los seis leves y tres observaciones, en `pending.md`.
3. 2026-11-22 — D169 (antes D143; leve de `pending.md`): el `pre-commit` avisa, sin impedir el commit, si un `scripts/` preparado difiere de su copia en `.claude/gw/scripts/` (orden: `python3 scripts/apply.py .`); clave `installedCopyWarn` (defecto `true`; esquema y `config.md` es/en); `PreCommitInstalledCopy` en `test_hooks.py` (rojo sin el arreglo).
4. 2026-11-22 — D168 (leve de `pending.md`): `gw-selector` lee de `metrics.py quality --period month` solo la tabla «By model» (`sed -n '/^## By model/,$p'`, unos 430 caracteres en vez de ~14 000), no el informe entero; copias regeneradas con `apply.py .`; `test_skills.py` en verde.
5. 2026-11-22 — D167 (leve de `pending.md`): la copia instalada `.agents/skills/gw-opt-tokens/scripts/` fallaba (5 errores, 9 fallos) porque `measure.py` y `test_measure.py` buscaban `schema/` y `scripts/` solo a tres niveles (`.claude/gw/`); ahora también en `../.claude/gw/` del proyecto. Arreglado en el origen (`skills/gw-opt-tokens/scripts/`) y regenerado con `apply.py .`; los 53 tests pasan en ambas copias.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
