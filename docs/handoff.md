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
| Siguiente paso | **`0.9` «Front»**: E75-E77 sin revisar; **E5 hecha** (2026-11-21; Q-36 abierta: `node_modules` solo en `front.dir`). Sigue **E7** (plantilla de CI con `front.py run full`, Q-35, `Related: E5`), luego E78 (sello de capturas, Q-34), E42 y E50. **Al cerrar el desarrollo de la `0.9`, antes de publicarla:** recogida y `0.8.2` (D142 y los arreglos que traiga; preguntas Q-4 a Q-6). Presupuesto de compactaciones: 2 (E5) |

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

1. 2026-11-21 — E5 cerrada: criterios de la ficha marcados, roadmap con E5 y E9-E16 hechas, Q-36 apuntada (`node_modules` solo en `front.dir`); arreglado el test de «macOS sin Docker», que veía el Docker real del runner (CI rojo en `aec7bba`)
2. 2026-11-21 — E5 trozo 3, revisión (tanda 2): 7 hallazgos arreglados: `check.sh` corre `front.py run full` con `front.tokens` (rojo con el motivo si no puede), doctor con procedimiento manual de capturas, `X.Y.Z` y `check-attr -z`, CI con `lts/*` y navegadores de la matriz, `stylelintFiles` relativo a la raíz (esquema, docs, README de la plantilla), `front.nodeCacheDays` y humo real de `run fast` sobre el ejemplo
3. 2026-11-21 — E5 trozo 3, revisión (tanda 1, `front.py`): 6 hallazgos arreglados: caché por hash del lock, sello solo tras `npm ci` correcto, navegadores en la ruta de Playwright de cada plataforma con `revisionOverrides`, copia solo de lo seguido por git y Stylelint desde la raíz con `--config` de `front.dir` (falla si ningún glob casa); falta la tanda 2
4. 2026-11-21 — E5 trozo 2, revisión: 13 hallazgos arreglados; `node_modules` fuera del árbol (caché en el git-dir y copia temporal), `gw-config.ts` perezoso, `stable` falla cerrado sin `baseURL` y pone el estilo antes del primer pintado, touch targets con excepciones WCAG 2.5.8 y `exclude`, overflow sin lo recortado, hex corto en `front.py`, Stylelint ignora lo generado, test con `killpg`, `--forbid-only` y salto por revisión de Chromium; en el CI la clase se salta (sin Chromium), aceptación solo en local; falta el trozo 3
5. 2026-11-21 — E5 trozo 2 (plantillas de prueba): `templates/front/` en TypeScript (`package.json` con versiones fijadas y su lock, `playwright.config.ts` con `gwConfig` que lee `playwright.projects.json`, fixture automática `stable`, helpers de layout y de axe, `.stylelintrc.json`, README) y `tests/fixtures/front-sample` (sitio estático, tokens, lo generado y especificaciones con un caso verde y uno rojo por helper, más Stylelint verde y rojo); `tests/test_front_sample.py` lo corre en Linux con node (se omite sin node, sin Chromium o fuera de Linux); `version.py` ignora `node_modules` y lo ignorado por git, los JSON de la plantilla van en `UNMARKED` y el puerto del ejemplo es libre (`test_waits` cumplido); falta el trozo 3 (checks)

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
