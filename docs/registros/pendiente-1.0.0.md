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
- [x] **Portal P3** (2026-10-26): `gw-media-content` deja un `web.md` opcional con el bloque del muro, en forma
  genérica (canal `web`: `estado`, `fecha`, `texto` por idioma, `muro`; `--idiomas-web`).
  [`2026-10-26-portal-galivelop.md`](../propuestas/2026-10-26-portal-galivelop.md)

## De la recogida del 2026-10-26 (segunda)

Decididas el 2026-10-27; las correcciones (INS P8, VeriNews P3, P4 y la parte Java de P11) van en la `0.4.2`.

- [ ] **VeriNews P1:** `ciIgnore`, estados de CI ajenos (p. ej. un despliegue) que no bloquean la fusión.
  [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **VeriNews P2:** firmas del agente también en el cuerpo de PR, issues y comentarios de GitHub, y aviso de un
  `user.email` `noreply@anthropic.com`. [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **INS P12 + WMF P4:** el check en una orden con resumen y la salida recortada.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../propuestas/2026-10-26-instalador-wmf-tarkor-2.md),
  [`2026-10-26-world-maker-fantasy-2.md`](../propuestas/2026-10-26-world-maker-fantasy-2.md)
- [ ] **INS P9:** `bitacora.py own-row --staged`, la propia fila comprobada al hacer el commit.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../propuestas/2026-10-26-instalador-wmf-tarkor-2.md)
- [ ] **VeriNews P6:** `revisado.sh` avisa del código sin revisar desde la última marca.
  [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **VeriNews P5:** `rojo-sin-arreglo.sh --fix-at <commit>` y distinguir un rojo de compilación de uno de la
  aserción. [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **Portal P4:** `orchestrate-dealer`, los repos que solo se leen se clonan aparte y sin registrar.
  [`2026-10-26-portal-galivelop-2.md`](../propuestas/2026-10-26-portal-galivelop-2.md)
- [ ] **INS P10:** `doctor.py` avisa de worktrees ya fusionados.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../propuestas/2026-10-26-instalador-wmf-tarkor-2.md)
- [ ] **VeriNews P7:** `bitacora.py set-row`. [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **VeriNews P8:** `doctor.py` avisa de `cd <carpeta> && …` sin `worktreeLinks`.
  [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **INS P11:** `scout-updates` lee la versión de Rust del proyecto.
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../propuestas/2026-10-26-instalador-wmf-tarkor-2.md)
- [ ] **VeriNews P9:** el encargo de revisión lleva `git diff --stat`.
  [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **INS P13 + Portal P5:** en la plantilla de `REVIEW.md`, la regla de invariantes y el apartado «Navegadores».
  [`2026-10-26-instalador-wmf-tarkor-2.md`](../propuestas/2026-10-26-instalador-wmf-tarkor-2.md),
  [`2026-10-26-portal-galivelop-2.md`](../propuestas/2026-10-26-portal-galivelop-2.md)
- [ ] **VeriNews P10:** textos menores (`/clear` tras un commit `WIP:`, `perPage: 1`, `git fetch -q && git status -sb`).
  [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [ ] **VeriNews P11 (archivos borrados):** `tests-relacionados.sh` incluye los archivos borrados en `{files}` o corre
  todo si un push solo borra. [`2026-10-26-verinews_ai.md`](../propuestas/2026-10-26-verinews_ai.md)
- [x] **Del arreglo de INS P8** (arreglado en la `0.4.2`, `4aecf5c`): `prepush-ramas.sh` comprueba la bitácora como
  queda en la punta que se sube, así que un log malo en un commit intermedio se arregla con un commit nuevo encima.

## De la retro del parche `0.4.2`

[`retro-2026-10-27-parche-0-4-2.md`](retro-2026-10-27-parche-0-4-2.md), aprobadas por el usuario el 2026-10-27.

- [ ] **P3 (`doctor.py`):** avisar de un `core.hooksPath` absoluto que apunta al `.githooks` del checkout principal
  (los worktrees correrían los ganchos de otra rama), con la orden que lo arregla
  (`git config core.hooksPath .githooks`). Test del aviso y de su motivo.
- [ ] **P4 (`commit-msg`):** comprobar la línea `Siguiente:` en los mensajes, también los de fusión que escribe
  `fusionar.sh` (o que `fusionar.sh` la exija en su mensaje). Escape `GW_NO_NEXT=1` para un mensaje legítimo sin
  ella, y el aviso lo dice. Misma familia que la comprobación de firmas del agente.
- [ ] **P5 (regla QUOTED del `pre-commit`):** sin falsos positivos en `.md` (una etiqueta de traducción citada como
  ejemplo). Tests de los dos lados: un secreto real en un `.md` sigue bloqueado.

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

- [x] **Labs P3:** las skills `to-spec` y `wayfinder`, con un destino Markdown local por defecto. ✅ 2026-10-26:
  `docs/specs/<fecha>-<tema>.md` y `docs/mapas/<tema>.md` (cada ticket, una casilla); cambiable desde
  `.claude/gw/<skill>.md`; filas nuevas en el `selector`. [`2026-10-25-labs-log-detective.md`](../propuestas/2026-10-25-labs-log-detective.md)
