# Pendiente para la `1.0.0`

Los evolutivos aprobados que no entran en la `0.4.x` (plan §7) y esperan en la rama `version/1.0.0`. Cada línea
apunta a su propuesta, que lleva el detalle; al aplicarla, se tacha aquí con la fecha y el commit, y la entrada va al
CHANGELOG de la `1.0.0`.

## De la recogida del 2026-10-26

- [ ] **WMF P2:** detectar un id de tarea dado de alta a la vez en dos ramas al traer `main` (`bitacora.py` o un
  script nuevo). [`2026-10-26-world-maker-fantasy.md`](../propuestas/2026-10-26-world-maker-fantasy.md)
- [ ] **WMF P3:** `recuperar.py --estado` enseña los otros worktrees con su rama y su fila de la bitácora.
  [`2026-10-26-world-maker-fantasy.md`](../propuestas/2026-10-26-world-maker-fantasy.md)
- [ ] **INS P3 (segunda parte):** un `ci-local` genérico que lee `docs/registros/ci-local.md` (la corrección mínima
  ya está en la `0.4.1`). [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [ ] **INS P5:** `recuperar.py` cuenta las compactaciones desde el inicio de la tarea (`merge-base` con la rama
  protegida), no de toda la sesión. [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [ ] **INS P6:** el `pre-commit` comprueba las tareas cerradas frente a «Hecho» (hoy solo `prepush-ramas.sh`).
  [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [ ] **INS P7:** cuatro frases en skills (`orchestrate-dealer`: buscar las otras apariciones de un fallo de patrón y
  repartir también los arreglos de la revisión; `pr`: `/clear` tras fusionar; revisión: hallazgos a un archivo).
  [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [ ] **Portal P2:** avisos y reglas (`pkill -f` se mata a sí mismo; runbooks de tareas programadas revisados como
  código; marcar en `REVIEW.md` los datos que caducan). [`2026-10-26-portal-galivelop.md`](../propuestas/2026-10-26-portal-galivelop.md)
- [ ] **Portal P3:** `gw-media-content` deja un `web.md` opcional con el bloque del muro, en forma genérica.
  [`2026-10-26-portal-galivelop.md`](../propuestas/2026-10-26-portal-galivelop.md)

## De la retro del parche `0.4.1`

- [ ] **P3:** el `pre-push` no repite un check ya en verde sobre el mismo árbol y las mismas órdenes (caché en el
  directorio común de git, con tests de árbol distinto, órdenes distintas y rojo que no se guarda).
  [`retro-2026-10-26-parche-0-4-1.md`](retro-2026-10-26-parche-0-4-1.md)

## Del usuario

- [ ] **Autoría sin firmas** (usuario, 2026-10-26): una opción en `gw.json`, la comprobación en `commit-msg` (sin
  `Co-Authored-By`, `Claude-Session` ni «Generated with Claude Code») y las plantillas limpias de firmas. Hoy es
  solo una regla de `AGENTS.md`.

## De recogidas anteriores

- [ ] **Labs P3:** las skills `to-spec` y `wayfinder`, con un destino Markdown local por defecto (aplazada el
  2026-10-25: decidir antes ese destino). [`2026-10-25-labs-log-detective.md`](../propuestas/2026-10-25-labs-log-detective.md)
