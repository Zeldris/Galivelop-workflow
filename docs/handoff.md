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
| Siguiente paso | `/code-review` de B37+E56+E57 (diff desde el último `Findings:`), de la retro del bloque `0.7` (`docs/records/retro-2026-11-15-block-0-7.md`). B37, E56 y E57 hechos. Presupuesto de compactaciones: 1 |

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

1. 2026-11-15 — E57: la skill `retro`, en su sección del flujo, propone al cerrar un bloque o versión una tarea `B` de barrido con los leves de `pendingFile` del script que más tenga (mejor uno que tocó el bloque), para la siguiente versión no empezada; el usuario elige cuáles entran. Copia en `.claude/skills/retro/`; test en `tests/test_skills.py`
2. 2026-11-15 — E56: gancho `PreToolUse` `scripts/generated-copy.py` sobre `Edit`/`Write`/`MultiEdit`/`NotebookEdit` que, solo en este repo (en `WORKFLOW_ONLY_SCRIPTS`; registrado en `.claude/settings.json`, no en la plantilla), avisa sin bloquear al editar una copia generada (`.claude/gw/scripts/`, `.claude/gw/schema/`, `.claude/skills/`, `.githooks/`, `.claude/agents/`) con la ruta de su fuente; las notas de `.claude/gw/*.md` no cuentan. 8 tests
3. 2026-11-15 — B37: `tests/waits.py` con `timeout(n)` y `wait_for(pred, n)` escalados por `GW_TEST_TIMEOUT_SCALE` (por defecto 1; uno no numérico o ≤ 0 falla cerrado); las esperas literales de `test_hooks`, `test_check_summary`, `test_session_log` y `test_red_without_fix` pasan por él; `tests/test_waits.py` rechaza un `timeout=`, plazo o bucle de sondeo literal nuevo (`# not a wait` para lo que no lo es); el CI de macOS pone 3
4. 2026-11-15 — Cierre del bloque `0.7`: revisión desde el último `Findings:` (arreglos de test de B36) sin hallazgos; retro aprobada (B37, E56 y E57 a la `0.7`); E51 marcado hecho en el roadmap español
5. 2026-11-15 — E55: con `gw.json` ilegible, el `pre-commit` comprueba autor y committer con el `authorDeny` de `HEAD` (`config.py --rev HEAD author-check`); solo sin uno legible allí (primer commit, ausente o roto) avisa y sigue. Copia `.githooks/` igual; 6 tests con el motivo

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md) (73 entradas); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
