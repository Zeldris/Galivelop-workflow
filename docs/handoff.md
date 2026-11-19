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
| Siguiente paso | **`0.9` «Front»**: la recogida de apertura (H24) ya está hecha; tareas E75-E76 de la recogida (E65-E74 hechas; bloque E65-E71 revisado, 2026-11-19), en orden, y luego A12, E4, E5, E7, E9-E16, E42 y E50. **Al cerrar el desarrollo de la `0.9`, antes de publicarla:** recogida y `0.8.2` (D142 y los arreglos que traiga; preguntas Q-4 a Q-6). Presupuesto de compactaciones: 0 |

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

1. 2026-11-19 — E74: gancho `other-repo-read.py` (`PreToolUse` en Read, Grep, Glob y Bash): avisa, sin bloquear, cuando la sesión principal (evento sin `agent_id`) lee una ruta fuera del proyecto y dentro de otro repositorio git, con la regla del subagente; clave `otherRepoReadWarn` (`true`) para apagarlo
2. 2026-11-19 — E77: el push y el check largo, en segundo plano con `timeout` de 5400000 ms (90 min) en `AGENTS.md` y sus plantillas, `gw-opt-tokens.md` (cualquier subida) y la subida final de `gw-orchestrate-dealer` (usuario, Q-7 a Q-9; Q-8, que `push.sh` anuncie el alcance, no)
3. 2026-11-19 — E73: clave `projectSkillPrefix` (`""`; nunca `gw-`): `apply.py --init --project-skill-prefix` la escribe y `gw-init` la pregunta; `doctor.py` avisa (`skill prefix`) de cada skill propia (sin `metadata.source` del flujo) que no la lleva, con el renombrado
4. 2026-11-19 — E72: clave `generated` (`[{command, paths}]`, `[]`): `generated-check.py` (en el `check` de la plantilla) corre cada orden y falla si cambia, añade o quita archivos bajo sus `paths`, con la orden `git add`; `doctor.py` avisa (`generated files`) si la clave tiene entradas y el `check` no lo corre
5. 2026-11-19 — E71: `ci-local.py --validate` corre también `actionlint -shellcheck=` sobre los workflows (claves `ciActionlint`, `auto` por defecto, y `actionlintVersion`, `1.7.12`); la plantilla de CI lo instala en GitHub en un venv; `doctor.py` avisa (`workflow lint`) si hay workflows y el `check` no los valida

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
