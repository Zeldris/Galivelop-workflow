# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9.0` publicada en `main`: `ccr-d1e2d496-0vzck8`** = `main` = `8357389` (2026-11-24). La `0.9` queda cerrada; la siguiente es la `0.10` «Estable» |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.9.0` en `main`** (`8357389`, las tres fases hechas: revisión con 7 hallazgos arreglados, retro D176/D177, `reviewed.sh`; CI de `4b9b5e4` en verde). Release de GitHub `v0.9.0` publicada (2026-11-24, sesión local; etiqueta sobre `8357389`) |
| Siguiente paso | **La `0.10` «Estable»** (E8, E28-E31…, `docs/roadmap.md`); `task.py current` sigue en E86 (solo lo cambia el usuario). Presupuesto de compactaciones: 2 |

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

1. 2026-11-24 — H28 (recogida de apertura de la 0.10): 6 archivos en docs/proposals/2026-11-24-*.md con 15 propuestas generales (10 arreglos patch, 5 evolutivos minor); state.json al día; private-project-4 sin novedades y private-project-1 sin recoger (add_repo denegado). Pendiente: respuestas del usuario a las 4 preguntas, check completo en curso.
2. 2026-11-24 — D178 (siete hallazgos de la revisión de D176-D178): `closed_roadmap_ids` cuenta cerrado solo si el estado empieza por la palabra `done`; `task_rows` ignora claves que no son `taskId`; el `pre-push` lee la hoja de ruta del sha subido (`handoff.py check --roadmap`); la exención `Related:` admite prefijo de versión; `**ver**`/`**see**` exentos; paréntesis contados en toda la entrada; esquema sin `minLength` repetido y con la excepción descrita. Un test rojo sin cada arreglo (`test_commit_message`, `test_utils -k closed_id`); check completo pendiente.
3. 2026-11-23 — D178 (Q-7, Q-8, Q-39 contestadas «ok» a las recomendaciones): `recover.py --state` imprime tras una compactación el aviso de modelo de D142 (`compact_model_check`; el gancho de inicio no corre ahí y `doctor.py` no deja otro comando); Q-8 sin cambios; `handoff.py` exime ids tras «revisión»/«review» y entre paréntesis, `pendingClosedIdCheck` encendido aquí y cinco entradas de `pending.md` con el id entre paréntesis (0 avisos con `--strict`). `test_session_log` (caso d178, rojo sin el arreglo) y `test_utils -k closed_id` en verde; check completo pendiente.
4. 2026-11-23 — D176/D177 (retro de la `0.9`, R1 y R2, aprobadas): el `commit-msg` avisa de pedir `/clear` al dejar hecha una fila de tarea (`clearOnTaskClose`; no usa `clearAfterTask`, que no ve el commit en curso) y `handoff.py check` avisa de entradas abiertas de `pending.md` que citan un id cerrado (`pendingClosedIdCheck`, apagado aquí: Q abierta). `test_commit_message` (86) y `HandoffPendingFile` (17) en verde, rojo sin cada arreglo; check completo del `pre-push` en verde. R3 ya lo cubre B43.
5. 2026-11-23 — D176 y D177 (retro 0.9 R1/R2): el aviso de /clear del commit-msg cuenta cerrar una fila (clearOnTaskClose); handoff check avisa de pendientes abiertos que citan un id cerrado (pendingClosedIdCheck, desactivada aquí: ~60 entradas de revisión citan a propósito su tarea)

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
