# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.6` «Medir»: `ccr-d1e2d496-0vzck8`** (hace de `version/0.6.0` mientras la sesión solo pueda subir a esta rama). `main` = `5afda88` = **`0.6.1`** (2026-11-14, etiqueta y release `v0.6.1`). `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.6.1` en `main`** (`5afda88`, 2026-11-14; excepción a A-6 aprobada por el usuario). Etiqueta y release `v0.6.1` creadas por el agente desde una sesión local (`gh release create`, 2026-11-14) con los textos de `docs/records/release-v0.6.1.md` |
| Siguiente paso | La **`0.7`**: B36 (con B32), luego E41 ampliada, en serie con `gw-orchestrate-dealer` (recogida H20 ya hecha). Presupuesto de compactaciones: 2 |

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

1. 2026-11-14 — E52: (cerrada: plantillas de bitácora y gw-*.md y diff vX→vY de REVIEW/GLOSSARY en el ensayo) `apply.py --dry-run --summary` (recuentos por acción, `propose`/`merge`, renombrados y avisos; solo con `--dry-run`, si no falla con la orden que lo arregla) y `rename  viejo -> nuevo` en el resumen (rutas, scripts, skills, ganchos); docs es/en y `gw-update` al día
2. 2026-11-14 — E51: `ci-local.py --validate` analiza el YAML de cada workflow (clave `ciYamlCheck`, sección propia de `tests/check.sh`, en `templates/gw.json`); el lector rechaza ya un escalar plano con `: `
3. 2026-11-14 — Parche 0.6.1 publicado en main (5afda88): fase 3 con 5 hallazgos arreglados (3d89111), versión y CHANGELOG (d28a1a1), notas de la release para publicar desde local
4. 2026-11-14 — D104-D106, D108: «Pendiente» sale a `pendingFile` (`move-pending`, `check --strict`); `roadmap.py check` compara los ids de los dos roadmaps; `tests-for.py --run` pasa shellcheck a los `.sh` cambiados; el `commit-msg` pide `/clear` al cerrar fase o versión con el presupuesto pasado. Revisión: 4 medios arreglados, leves a pendientes
5. 2026-11-14 — D107: el encargo del dealer pide la subida final en primer plano y la sesión principal para con `TaskStop` al subagente que no vuelve con su commit ya subido

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md) (70 entradas); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
