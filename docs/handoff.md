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
| Siguiente paso | **`0.9` «Front»**: E75-E77 sin revisar; **E5, E7 y E78 hechas** (2026-11-21). **E42 traída** (falta su documentación es/en y marcarla en el roadmap). Sigue E50. **Al cerrar el desarrollo de la `0.9`, antes de publicarla:** recogida y `0.8.2` (D142 y los arreglos que traiga; preguntas Q-4 a Q-6). Presupuesto de compactaciones: 1 (E42) |

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

1. 2026-11-21 — E42 traída: skill `gw-seo` (SKILL.md, references con fechas, note.md, LICENSE MIT de claude-seo) y `scripts/check_seo.py` con sus tests, en inglés y sin rutas del portal; copias en `.claude/` y `.agents/`; docs es/en y roadmap quedan para otro trozo
2. 2026-11-21 — E78 hecha: `front.py run full --update-snapshots` (Linux o Docker) devuelve al árbol las capturas nuevas o cambiadas y escribe la versión fijada de Playwright en `front.snapshotStamp`; falla con 2 en `fast` o sin versión exacta; `doctor.py` propone la orden
3. 2026-11-21 — E7 hecha: `front.py install --matrix` (navegadores de la matriz), la plantilla de CI corre `front.py run full` tras «Check» con `front.tokens` (Q-35) y monta node, guía «Pruebas de front» en `patterns.md` es/en; Q-36 documentada en `templates/front/README.md`
4. 2026-11-21 — E5 cerrada: criterios de la ficha marcados, roadmap con E5 y E9-E16 hechas, Q-36 apuntada (`node_modules` solo en `front.dir`); arreglado el test de «macOS sin Docker», que veía el Docker real del runner (CI rojo en `aec7bba`)
5. 2026-11-21 — E5 trozo 3, revisión (tanda 2): 7 hallazgos arreglados: `check.sh` corre `front.py run full` con `front.tokens` (rojo con el motivo si no puede), doctor con procedimiento manual de capturas, `X.Y.Z` y `check-attr -z`, CI con `lts/*` y navegadores de la matriz, `stylelintFiles` relativo a la raíz (esquema, docs, README de la plantilla), `front.nodeCacheDays` y humo real de `run fast` sobre el ejemplo

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
