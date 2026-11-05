# Harvest galivelop-image-generator — 2026-11-05

De `849b3012` a `71a69a34` (`scripts/harvest.py`), recogida de inicio de la `0.6`. 126 commits; sin skills del flujo
cambiadas ni skills nuevas (`gw-orchestrate-dealer`, `gw-update` y los scripts de `.claude/gw/scripts/` son copias
de la `0.5.0`).

Sin nada nuevo desde la última recogida: `instalador-wmf-tarkor` (`a73f8812`), `labs-log-detective` (`bc501f91`),
`portal-galivelop` (`dd327106`), `private-project-2` (`70b0396a`), `private-project-3` (`195bb867`) y
`world-maker-fantasy` (`d35bfaa1`).

## P1. `measure.py` mide el registro de un subagente

- **Source:** `docs/records/retro-2026-11-05-f4.md` @ `e42e654` (retro, propuesta 4)
- **What changes:** `skills/gw-opt-tokens/scripts/measure.py` descarta toda línea con `isSidechain` (línea ~235), y
  en `subagents/agent-*.jsonl` lo llevan todas: `--session <subagents/agent-….jsonl>` da «No calls in that period»
  (reproducido). No descartarlas cuando el archivo es de un subagente (o no tiene líneas principales), con su test.
- **Why it is general:** sin esa medida no se sabe en qué gastan los implementadores (en F4, el 66 % de la tarea).
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → B20 (`0.5.2`)

## P2. `harvest.py` no repite las ideas de un archivo renombrado

- **Source:** esta misma recogida: las retros de 2026-10-25/27 y `retro-2026-11-04-f2-motor.md`, movidas de
  `docs/registros/` a `docs/records/`, salieron enteras como nuevas (script)
- **What changes:** `scripts/harvest.py` compara con `git diff --no-renames`; detectar renombrados (`-M`) y comparar
  con la ruta vieja. De paso, el recorte `[:2000]` de una idea dice «… (truncated)» en vez de cortar en silencio.
- **Why it is general:** cada proyecto que aplique A8 (nombres en inglés) mueve sus retros y la siguiente recogida las
  da otra vez por nuevas (ya era un leve conocido en «Pendiente»).
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → D57 (`0.5.2`)

## P3. La plantilla de la bitácora y `close-row` con `logRows` apagado

- **Source:** `docs/records/retro-2026-11-05-plan-piezas.md` @ `d4c5532` (retro)
- **What changes:** `templates/es/log.md:17` (y `en`) escribe siempre el párrafo de `logRows`; que `apply.py` solo lo
  escriba con `"logRows": true`. `handoff.py close-row` sale con 0 sin escribir nada cuando está apagado: que avise y
  salga con 1 como `set-row`.
- **Why it is general:** un proyecto con `logRows: false` gastó 4 llamadas (~26k de contexto) en descubrir que no
  aplicaba.
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → D58 (`0.5.2`)

## P4. `Siguiente:` obligatorio en la plantilla pero `commitNext` apagado

- **Source:** `docs/records/retro-2026-11-05-plan-piezas.md` @ `d4c5532` (retro)
- **What changes:** `commit-message.py` ya lo exige con `commitNext: true` (D31), pero `templates/gw.json` lo trae en
  `false` y `templates/es/AGENTS.md:70` da la regla como obligatoria. O `commitNext: true` por defecto, o que
  `doctor.py` avise del desajuste.
- **Why it is general:** la regla escrita y el gancho dicen cosas distintas en todo proyecto nuevo.
- **Version bump:** patch
- **Status:** aprobada (2026-11-05) → D59 (`0.5.2`, `commitNext: true` por defecto)

## P5. Aviso de CI en rojo al subir

- **Source:** `docs/records/retro-2026-11-05-f4.md` @ `e42e654` (retro, propuesta 3)
- **What changes:** el `pre-push` (o `check.sh`), si hay `gh`, avisa sin bloquear cuando el último CI de la rama está
  en rojo, con `scripts/ci-status.py`.
- **Why it is general:** se acumularon dos subidas sobre un CI roto; con D49 (el `pre-push` solo con los tests
  relacionados) el CI pesa más. Complementa D49 y D56.
- **Version bump:** minor
- **Status:** aprobada (2026-11-05) → D62 (`0.7`)

## P6. `check.yml` invocable con `workflow_call`

- **Source:** `docs/records/retro-2026-11-05-release-install.md` @ `c14bf1e` (retro, P2)
- **What changes:** `templates/github/check.yml` añade `workflow_call:` para que un `release.yml` haga
  `uses: ./.github/workflows/check.yml` y `needs: check` en vez de copiar sus pasos; el `release.yml` del flujo puede
  hacer lo mismo.
- **Why it is general:** quien imita el proceso de versiones copia a mano los pasos de `check.yml` y se desvían
  (`ciInstall`, versión de Python: dos fallos en una release).
- **Version bump:** minor
- **Status:** aprobada (2026-11-05) → D63 (`0.7`)

## Stays in the project

- `gimg/doctor.py`: el doctor del motor de imágenes; solo comparte nombre con el del flujo.
- Retros de 2026-10-25 (diseño, f0, f1), 2026-10-27-f2-0 y 2026-11-04-f2-motor: ya recogidas
  (`2026-11-03-galivelop-image-generator.md`, `2026-11-04-galivelop-image-generator.md`; D32, D37, B14, B17); solo
  cambiaron de ruta.
- De `retro-2026-11-05-f4.md`: el test inestable de cancelar y Chrome/tmpfs/`Browser.close`.
- De `retro-2026-11-05-plan-piezas.md`: paridad de los CHANGELOG, opciones de `gimg` en la documentación y la entrada
  de CHANGELOG en `REVIEW.md`.
- De `retro-2026-11-05-release-install.md`: P1 (test que compara `release.yml` con `check.yml`), que sobra con P6.
- La ventana de compactación en 140k: ajuste del proyecto.
