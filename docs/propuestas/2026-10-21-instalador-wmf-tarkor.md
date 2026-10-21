# Harvest instalador-wmf-tarkor — 2026-10-21

De `never` a `97440ecc7c4c` (`scripts/recoger.py`). Mismas 15 skills copiadas que Tarkor, con notas de proyecto; sus
skills nacidas (`opt-ai`, `to-questionnaire`) son idénticas a las de Tarkor: ver P12 y P13 del harvest de
`world-maker-fantasy`. Lo que ya trae `casos-reales.md` (gancho de `main` con `git ls-remote`, matcher anclado, `pre-push` con stdin) no se repite.

## P1. Lista de casos de prueba del gancho de `main`

- **Source:** `docs/registros/retro-2026-10-21-flujo.md:25` (propuesta 1) @ 97440ecc7c4c (retro, test)
- **What changes:** `tests/` incluye, contra un repo temporal, estos casos de `revision-antes-de-main.sh`: otra base, sin marca, marca igual a la rama en GitHub, `update_pull_request` sin base, fusión automática, `update_pull_request_branch` ignorado, `head` como `dueño:rama`, error de `origin` visible.
- **Why it is general:** el gancho solo se había probado a mano y la revisión halló siete fallos en lo traído; `casos-reales.md` pide tests de ganchos pero solo existen 8 casos de `pre-push`.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## P2. Comprobación de identificadores y referencias obsoletos

- **Source:** `docs/registros/retro-2026-10-21-flujo.md:25` (propuesta 2) @ 97440ecc7c4c (retro, test)
- **What changes:** `enlaces-md.py` (o un test hermano) acepta `staleRefs` en el config, patrones que no deben aparecer en `docs/` ni en el README (insensible a mayúsculas, números de dos cifras, rutas con espacios, saltando bitácora y `.claude/`). `/gw-update` lo rellena al renumerar.
- **Why it is general:** renombrar ids de tarea al traer el flujo dejó «fase 3.5» en dos documentos; solo lo vio la revisión.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P3. Editar ganchos y `settings.json` pide permiso en modo automático

- **Source:** `docs/registros/retro-2026-10-21-flujo.md:25` (propuesta 3) @ 97440ecc7c4c (retro, doc)
- **What changes:** línea en `docs/<lang>/problemas.md` y en `aplicar.md`: el clasificador del modo automático bloquea editar `.claude/hooks/` y `.claude/settings.json`; pedir permiso antes, y que `aplicar.py` lo diga al ir a tocarlos.
- **Why it is general:** `/gw-init` y `/gw-update` escriben justo esos archivos; el fallo aparece a mitad de la aplicación.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## P4. Lo que depende del equipo de la persona no se da por probado

- **Source:** `CLAUDE.md` § «Pruebas» @ 97440ecc7c4c (regla)
- **What changes:** línea en la plantilla de `CLAUDE.md`: lo que depende de una máquina concreta (otro sistema operativo, un dispositivo) no se declara probado con tests; se apunta como pendiente en el plan, con quién lo comprueba.
- **Why it is general:** evita cerrar tareas con una prueba que nunca corrió donde importa.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## Se queda en el proyecto

- `.claude/skills/orchestrate-dealer/SKILL.md` (+69 −70) y `selector` (+36 −51): traducción y rutas; nuestra versión ya es la genérica.
- `.claude/skills/domain-modeling/SKILL.md` (+5): glosario y ADR de su producto.
- Reglas de Tauri, Flatpak, `INS-n`, pruebas `app/e2e` con tauri-driver: stack del instalador.
- `retro-2026-10-21-flujo.md:8` (medida): 432 llamadas y 4 compactaciones; ya recogido en `opt-tokens`.

## Ya está aquí

- Leer documentos por trozos (`retro-2026-10-21-flujo.md:25`, propuesta 4): el paso de `opt-tokens` sobre lecturas enteras lo cubre; solo falta en el `proyecto.md` de cada repo.
- Tope de compactación de 200k en `settings.json`: en `aplicar.py` (plan §5.4).
- Reparte la copia mecánica con `orchestrate-dealer` (hallazgo de la medida): ya es regla del `selector` («traer de otro repo»).
