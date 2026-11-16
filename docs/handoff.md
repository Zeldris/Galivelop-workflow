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
| Siguiente paso | Release `v0.7.1` publicada. Siguiente: la tarea de la `0.8` que elija el usuario (B41 y el resto de su roadmap). Presupuesto de compactaciones: 1 |

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

1. 2026-11-16 — `0.7.1` en `main` (`7a6d1bd`): CI de `64770b0` en verde, check entero en local, `reviewed.sh` y subida con confirmación del usuario; textos de la release en `release-v0.7.1.md`
2. 2026-11-16 — E58: `whole-read.py` también vigila Bash (`cat`, `sed` sin `-n` y parecidas, con `cd` y sin cuerpos de heredoc); claves `readPointers` (orden que sustituye la lectura), `wholeReadRepeatOnly` (por defecto solo avisa al releer entero un archivo sin cambios en la sesión) y `wholeReadStaleDays`
3. 2026-11-16 — E59: `recover.py --state` da la línea «Remote» (al día, por delante, por detrás o divergida de `origin/<rama>`, con la orden que lo arregla); el paso 2 de «Al empezar» de `AGENTS.md` y las plantillas apunta a ella
4. 2026-11-16 — E60: el `commit-msg` avisa, sin rechazar, de un mensaje de arreglos de revisión sin `Findings:` (clave `metrics.quality.findingsWords`, `[]` lo apaga; con `commitRefs` o `commitNext`)
5. 2026-11-16 — E61: `handoff.py set-row` y `close-row` imprimen la fila tal como queda y `n/límite` (copia en `.claude/gw/scripts/`, tests en `test_utils.py`)

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
