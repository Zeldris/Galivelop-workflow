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
| Siguiente paso | **Recogida H26 hecha** (2026-11-22, `docs/proposals/2026-11-22-*.md`; Q-4 a Q-6 respondidas): el usuario decide las propuestas; luego, `0.8.2` (D142, D144 y los arreglos aprobados) en `version/0.8.2` desde `main`, y después la `0.9`. Presupuesto de compactaciones: 1 (E42) |

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

1. 2026-11-22 — H26, recogida de cierre de la `0.9` y del `0.8.2` sobre 10 proyectos al día (fetch + ff): 7 traen propuestas (24, en `docs/proposals/2026-11-22-*.md`), portal, labs y private-project-4 nada; Q-4 a Q-6 respondidas; el fallo de `measure.py` de `pending.md` pasa de «D142» (repetido) a D144
2. 2026-11-21 — E75-E77 revisadas (5 hallazgos arreglados, `Findings: 5`): `questions.py add` acepta cada `--rec` junto a su pregunta (como lo escribe `grilling`); `measure.py` cuenta solo las llamadas reales para el arranque fijo, dice que su total baja con menos llamadas, no lo calcula en el log de un subagente y, si la copia instalada de `context_guard.py` falla, prueba la del repo; los leves, en `pending.md`
3. 2026-11-21 — E50 hecha: `whole-read.py` cuenta las imágenes distintas que la sesión lee con `Read` y, en `screenshotSheet.after` (3) y sus múltiplos, aconseja montarlas en una hoja con `screenshotSheet.command` (o un ejemplo genérico); `ignorePaths`, `extensions`; vale con `wholeReadWarnBytes` a 0; la cuenta se borra con `forget`
4. 2026-11-21 — E42 documentada: `gw-seo` en README.md ↔ README.es.md (29 skills) y hecha en el roadmap es/en; sin sección sin publicar en el CHANGELOG (se escribe al publicar la `0.9`).
5. 2026-11-21 — E42 traída y revisada (13 hallazgos arreglados, `Findings: 13`): skill `gw-seo` (SKILL.md, references con fechas, note.md, LICENSE MIT de claude-seo) y `scripts/check_seo.py` con sus tests, en inglés y sin rutas del portal; copias en `.claude/` y `.agents/`; docs es/en y roadmap quedan para otro trozo

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
