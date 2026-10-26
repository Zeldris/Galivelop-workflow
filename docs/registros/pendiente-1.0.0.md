# Pendiente para la `1.0.0`

Los evolutivos aprobados que no entran en la `0.4.x` (plan §7) y esperan en la rama `version/1.0.0`. Cada línea
apunta a su propuesta, que lleva el detalle; al aplicarla, se tacha aquí con la fecha y el commit, y la entrada va al
CHANGELOG de la `1.0.0`.

## De la recogida del 2026-10-26

- [x] **WMF P2** (2026-10-26): `bitacora.py clash` detecta un id de tarea dado de alta a la vez en dos ramas para
  tareas distintas; lo corren el `pre-push` (contra `main` y los merges nuevos; aviso con otras ramas) y el
  `pre-commit` de un merge con conflictos. [`2026-10-26-world-maker-fantasy.md`](../propuestas/2026-10-26-world-maker-fantasy.md)
- [x] **WMF P3** (2026-10-26): `recuperar.py --estado` enseña los otros worktrees con su rama y su fila de la bitácora.
  [`2026-10-26-world-maker-fantasy.md`](../propuestas/2026-10-26-world-maker-fantasy.md)
- [x] **INS P3 (segunda parte)** (2026-10-26): `ci-local.py` corre el CI de GitHub en local y, con `--apuntar`, lo
  deja en `ciLocalLog`; el gancho de PR acepta esa línea verde si el CI no arrancó (la corrección mínima, en la `0.4.1`). [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [x] **INS P5** (2026-10-26): `recuperar.py` cuenta las compactaciones desde el inicio de la tarea (`merge-base` con la rama
  protegida), no de toda la sesión. [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [x] **INS P6** (2026-10-26): el `pre-commit` comprueba las tareas cerradas frente a «Hecho» (`bitacora.py closed --staged`).
  [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [x] **INS P7** (2026-10-26): cuatro frases en skills (`orchestrate-dealer`: buscar las otras apariciones de un fallo de patrón y
  repartir también los arreglos de la revisión; `pr`: `/clear` tras fusionar; revisión: hallazgos a un archivo).
  [`2026-10-26-instalador-wmf-tarkor.md`](../propuestas/2026-10-26-instalador-wmf-tarkor.md)
- [x] **Portal P2** (2026-10-26): avisos y reglas (`pkill -f` se mata a sí mismo; runbooks de tareas programadas revisados como
  código; marcar en `REVIEW.md` los datos que caducan). [`2026-10-26-portal-galivelop.md`](../propuestas/2026-10-26-portal-galivelop.md)
- [ ] **Portal P3:** `gw-media-content` deja un `web.md` opcional con el bloque del muro, en forma genérica.
  [`2026-10-26-portal-galivelop.md`](../propuestas/2026-10-26-portal-galivelop.md)

## De la retro del parche `0.4.1`

- [x] **P3** (2026-10-26, `4e3af46`, `b50ccb6`, `f50072e`): el `pre-push` no repite un check ya en verde sobre el
  mismo árbol y las mismas órdenes (caché en el directorio común de git, con tests de árbol distinto, órdenes
  distintas y rojo que no se guarda). Documentada en la `1.0.0` del CHANGELOG, `config.md`, `problemas.md` y
  `AGENTS.md`; falta, como mejora posible, que `fusionar.sh` también apunte el verde.
  [`retro-2026-10-26-parche-0-4-1.md`](retro-2026-10-26-parche-0-4-1.md)

## Del usuario

- [x] **Autoría sin firmas** (2026-10-26, `7b3c91c`, `f7de072`, `7785a98`): `agentSignatures` en `gw.json` (por
  defecto `true`; este repo, `false`) y `aplicar --init --agent-signatures`; con `false`, el `commit-msg` rechaza un
  `Co-Authored-By` de Claude (`noreply@anthropic.com` o nombre de modelo), `Claude-Session`, «Generated with Claude
  Code» y el enlace de sesión a principio de línea, sin mirar comentarios ni lo que va tras las tijeras de
  `commit -v`; se salta en rebase. Plantillas `AGENTS.md`, `config`, `aplicar`, `problemas`, mapa y CHANGELOG.

## De recogidas anteriores

- [ ] **Labs P3:** las skills `to-spec` y `wayfinder`, con un destino Markdown local por defecto (aplazada el
  2026-10-25: decidir antes ese destino). [`2026-10-25-labs-log-detective.md`](../propuestas/2026-10-25-labs-log-detective.md)
