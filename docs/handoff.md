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
| Siguiente paso | **Sellar la `0.8.0`** (usuario, 2026-11-18): CHANGELOG, versión, README y roadmap hechos; fase 1 sin hallazgos; fase 2 decidida (retro: P1-P3 aplicadas como B44-B46, P5 → B43 en la `0.10`, P4 rechazada). Falta la fase 3: `/code-review` de B44-B46, check completo, `reviewed.sh` y `main` con confirmación del usuario. Presupuesto de compactaciones: 2 |

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

1. 2026-11-18 — Sello de la `0.8.0` preparado: entrada del CHANGELOG (es/en), `version.py 0.8.0` y `apply.py .` (cabeceras y copias), README con el estado y lo nuevo de la `0.8`, roadmap con D68, E33 y E35 hechas; el ítem abierto de `push.sh` en macOS pasa a la `0.10`.
2. 2026-11-18 — D7 fusionado: `apply.py` copia las skills también en `agentsSkillsDir` (por defecto `.agents/skills`, para opencode y Codex) con huérfanos, `--check` y ganchos al día; AGENTS.md ya era legible sin `@include`; 8 hallazgos de revisión arreglados; check completo en verde. B9 mínimo hecho: guía `other-agents.md` es/en y regla de modelos externos en `gw-selector` (Q-1). Q-2: la recogida del 2026-11-15 cuenta para la `0.8`.
3. 2026-11-18 — E35 fusionado: `test-run.py` reintenta una clase que falla (`flaky.retries`), la apunta en `<git common dir>/gw/flaky.jsonl`, el resumen del check lo dice y tras `flaky.proposeAfter` propone arreglarla; revisión con 4 hallazgos arreglados; check completo en verde.
4. 2026-11-18 — Oleada D68+E33 fusionada (fragmentos de CHANGELOG en `changelog.d/`; contrato de revisión con anclas); check de la oleada en rojo por la clave nueva en `templates/gw.json`, el orden de `test_version.py` y la copia de gw-harvest, arreglados. Respuestas Q-1..Q-3: B9 mínimo, recogida si ninguna cuenta, sin `REVIEW.md` en la raíz.
5. 2026-11-18 — Reparto nuevo de versiones (usuario, 2026-11-18): la `0.8` pasa a «Preguntas y otros agentes» y se cierra con D68, E33, E35, D7 y B9; nueva `0.9` «Front» (A12, E4, E5, E7, E9-E16, E42, E50); la «Estable» pasa a `0.10`, solo correcciones y revisiones (con E32 y B38), y lo evolutivo de las recogidas va a la `1.x` (plan §7 y regla de versiones del roadmap). Lo de `pending.md` marcado `0.9`, a `0.10`.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
